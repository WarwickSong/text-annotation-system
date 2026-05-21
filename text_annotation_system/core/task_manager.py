from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Callable, Optional

from async_batch_inference import AsyncBatchConfig, AsyncBatchInference

from core.answer_processor import process_answer
from core.file_handler import FileHandler
from core.prompt_builder import build_all_prompts
from core.security import decrypt_config, has_config
from core.scheme_manager import SchemeManager
from models.scheme import AnnotationScheme
from models.task import Task, TASK_STATUS_RUNNING, TASK_STATUS_COMPLETED, TASK_STATUS_TERMINATED


BATCH_SIZE = 20


class TaskManager:
    def __init__(
        self,
        data_dir: str,
        scheme_manager: SchemeManager,
        file_handler: FileHandler,
    ):
        self._tasks_dir = Path(data_dir) / "tasks"
        self._data_dir = data_dir
        self._tasks_dir.mkdir(parents=True, exist_ok=True)
        self._scheme_manager = scheme_manager
        self._file_handler = file_handler
        self._running_tasks: dict[str, asyncio.Task] = {}
        self._cancelled: set[str] = set()
        self._on_progress: list[Callable] = []

    def add_progress_callback(self, callback: Callable):
        if callback not in self._on_progress:
            self._on_progress.append(callback)

    def remove_progress_callback(self, callback: Callable):
        if callback in self._on_progress:
            self._on_progress.remove(callback)

    def _task_path(self, task_id: str) -> Path:
        return self._tasks_dir / f"{task_id}.json"

    def _save_task(self, task: Task):
        self._tasks_dir.mkdir(parents=True, exist_ok=True)
        path = self._task_path(task.id)
        path.write_text(
            json.dumps(task.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _load_task(self, task_id: str) -> Optional[Task]:
        path = self._task_path(task_id)
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return Task.from_dict(data)

    def list_tasks(self) -> list[dict]:
        result = []
        for fp in sorted(self._tasks_dir.glob("*.json"), reverse=True):
            try:
                data = json.loads(fp.read_text(encoding="utf-8"))
                result.append(data)
            except (json.JSONDecodeError, KeyError):
                continue
        return result

    def get_task(self, task_id: str) -> Optional[Task]:
        return self._load_task(task_id)

    def is_running(self, task_id: str) -> bool:
        return task_id in self._running_tasks

    async def create_and_run(
        self,
        file_id: str,
        column: str,
        scheme_id: str,
        original_file_name: str,
        model: str = "",
        batch_size: int = BATCH_SIZE,
        max_concurrency: int = 10,
    ) -> Task:
        scheme = self._scheme_manager.get(scheme_id)
        if scheme is None:
            raise ValueError(f"Scheme {scheme_id} not found")

        texts = self._file_handler.get_column_values(file_id, column)
        if not texts:
            raise ValueError(f"Column {column} is empty")

        task = Task(
            file_name=original_file_name,
            scheme_id=scheme_id,
            scheme_name=scheme.name,
            status=TASK_STATUS_RUNNING,
            total_rows=len(texts),
            completed_rows=0,
            target_column=column,
            upload_file_path=file_id,
            model=model,
        )
        self._save_task(task)

        atask = asyncio.create_task(
            self._run_task(task, scheme, texts, batch_size, max_concurrency)
        )
        self._running_tasks[task.id] = atask
        atask.add_done_callback(lambda _: self._running_tasks.pop(task.id, None))

        return task

    async def _run_task(
        self,
        task: Task,
        scheme: AnnotationScheme,
        texts: list[str],
        batch_size: int,
        max_concurrency: int,
    ):
        try:
            api_key, base_url, models = decrypt_config(self._data_dir)
        except FileNotFoundError:
            task.mark_terminated()
            self._save_task(task)
            return

        model_name = task.model or (models[0] if models else "")
        config = AsyncBatchConfig(api_key=api_key, base_url=base_url, model=model_name, max_concurrency=max_concurrency)
        engine = AsyncBatchInference(config)
        prompts = build_all_prompts(scheme, texts)
        class_names = [cls.name for cls in scheme.classes]
        all_answers: list[dict[str, str]] = []

        try:
            for i in range(0, len(prompts), batch_size):
                if task.id in self._cancelled:
                    self._cancelled.discard(task.id)
                    break

                batch = prompts[i : i + batch_size]
                try:
                    results = await engine.batch(batch)
                    for r in results:
                        raw = r.get("answer", "")
                        processed = process_answer(raw, scheme)
                        all_answers.append(processed)
                except Exception:
                    break

                task.completed_rows = len(all_answers)
                self._save_task(task)
                self._notify_progress(task)
        except asyncio.CancelledError:
            pass

        if len(all_answers) < len(prompts):
            task.mark_terminated()
            task.completed_rows = len(all_answers)
            if all_answers:
                output_id = self._file_handler.write_annotation_results(
                    file_id=task.upload_file_path,
                    column=task.target_column,
                    class_names=class_names,
                    answers=all_answers,
                    scheme_name=task.scheme_name,
                    original_file_name=task.file_name,
                )
                task.output_file_path = output_id
            self._save_task(task)
            self._notify_progress(task)
        else:
            output_id = self._file_handler.write_annotation_results(
                file_id=task.upload_file_path,
                column=task.target_column,
                class_names=class_names,
                answers=all_answers,
                scheme_name=task.scheme_name,
                original_file_name=task.file_name,
            )
            task.output_file_path = output_id
            task.mark_completed()
            self._save_task(task)
            self._notify_progress(task)

    def terminate(self, task_id: str) -> bool:
        task = self._load_task(task_id)
        if task is None or task.status != TASK_STATUS_RUNNING:
            return False
        self._cancelled.add(task_id)
        atask = self._running_tasks.get(task_id)
        if atask and not atask.done():
            atask.cancel()
        return True

    def get_task_results(self, task_id: str) -> Optional[list[dict]]:
        task = self._load_task(task_id)
        if task is None:
            return None
        try:
            df = self._file_handler.read_file(task.upload_file_path)
        except FileNotFoundError:
            return []
        annotation_cols = [
            c for c in df.columns
            if c.startswith(f"{task.target_column}_标注_")
        ]
        cols = [task.target_column] + annotation_cols
        n = task.completed_rows if task.completed_rows > 0 else len(df)
        return df[cols].head(n).to_dict(orient="records")

    def get_output_path(self, task_id: str) -> Optional[Path]:
        task = self._load_task(task_id)
        if task is None or not task.output_file_path:
            return None
        return self._file_handler.get_output_path(task.output_file_path)

    def delete_task(self, task_id: str) -> bool:
        task = self._load_task(task_id)
        if task is None:
            return False
        if task.status == TASK_STATUS_RUNNING:
            return False
        if task.output_file_path:
            output_path = self._file_handler.get_output_path(task.output_file_path)
            if output_path and output_path.exists():
                output_path.unlink()
        path = self._task_path(task_id)
        if path.exists():
            path.unlink()
        return True

    def _notify_progress(self, task: Task):
        for cb in list(self._on_progress):
            try:
                cb(task.to_dict())
            except Exception:
                pass
