from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

from core.task_manager import TaskManager
from models.task import TASK_STATUS_RUNNING

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

task_manager: TaskManager = None  # type: ignore


def init(tm: TaskManager):
    global task_manager
    task_manager = tm


@router.get("")
async def list_tasks():
    return task_manager.list_tasks()


@router.get("/{task_id}")
async def get_task(task_id: str):
    task = task_manager.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.to_dict()


@router.post("")
async def create_task(body: dict):
    file_id = body.get("file_id")
    column = body.get("column")
    scheme_id = body.get("scheme_id")
    file_name = body.get("file_name", "unknown.xlsx")
    model = body.get("model", "")
    batch_size = body.get("batch_size", 20)
    max_concurrency = body.get("max_concurrency", 10)
    try:
        max_concurrency = int(max_concurrency)
        max_concurrency = max(1, min(max_concurrency, 1000))
    except (ValueError, TypeError):
        max_concurrency = 10
    if not all([file_id, column, scheme_id]):
        raise HTTPException(status_code=400, detail="file_id, column, scheme_id are required")
    try:
        task = await task_manager.create_and_run(
            file_id=file_id,
            column=column,
            scheme_id=scheme_id,
            original_file_name=file_name,
            model=model,
            batch_size=batch_size,
            max_concurrency=max_concurrency,
        )
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    return task.to_dict()


@router.post("/{task_id}/terminate")
async def terminate_task(task_id: str):
    ok = task_manager.terminate(task_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Task not found or not running")
    return {"ok": True}


@router.delete("/{task_id}")
async def delete_task(task_id: str):
    ok = task_manager.delete_task(task_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Task not found or still running")
    return {"ok": True}


@router.get("/{task_id}/results")
async def get_task_results(task_id: str):
    results = task_manager.get_task_results(task_id)
    if results is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return results


@router.get("/{task_id}/download")
async def download_task_result(task_id: str):
    output_path = task_manager.get_output_path(task_id)
    if output_path is None:
        raise HTTPException(status_code=404, detail="Output file not found")
    return FileResponse(
        path=str(output_path),
        filename=output_path.name,
        media_type="application/octet-stream",
    )


@router.websocket("/ws/{task_id}/progress")
async def task_progress_ws(websocket: WebSocket, task_id: str):
    await websocket.accept()
    queue: asyncio.Queue = asyncio.Queue()

    def on_progress(task_dict: dict):
        if task_dict.get("id") == task_id:
            try:
                queue.put_nowait(task_dict)
            except asyncio.QueueFull:
                pass

    task_manager.add_progress_callback(on_progress)

    try:
        while True:
            try:
                task_dict = await asyncio.wait_for(queue.get(), timeout=30.0)
                await websocket.send_json(task_dict)
                if task_dict.get("status") != TASK_STATUS_RUNNING:
                    break
            except asyncio.TimeoutError:
                task = task_manager.get_task(task_id)
                if task is None or task.status != TASK_STATUS_RUNNING:
                    if task:
                        await websocket.send_json(task.to_dict())
                    break
    except WebSocketDisconnect:
        pass
    finally:
        task_manager.remove_progress_callback(on_progress)
