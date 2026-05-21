from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


TASK_STATUS_RUNNING = "running"
TASK_STATUS_COMPLETED = "completed"
TASK_STATUS_TERMINATED = "terminated"


def _format_duration(seconds: float) -> str:
    if seconds < 0:
        return ""
    if seconds < 60:
        return f"{seconds:.0f}s"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    if minutes < 60:
        return f"{minutes}m {secs}s"
    hours = int(minutes // 60)
    mins = int(minutes % 60)
    return f"{hours}h {mins}m"


@dataclass
class Task:
    id: str = field(default_factory=lambda: f"task_{uuid.uuid4().hex[:8]}")
    file_name: str = ""
    scheme_id: str = ""
    scheme_name: str = ""
    status: str = TASK_STATUS_RUNNING
    total_rows: int = 0
    completed_rows: int = 0
    target_column: str = ""
    upload_file_path: str = ""
    output_file_path: str = ""
    model: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    finished_at: str = ""

    @property
    def progress_percent(self) -> float:
        if self.total_rows == 0:
            return 0.0
        return round(self.completed_rows / self.total_rows * 100, 1)

    @property
    def duration(self) -> str:
        if not self.created_at:
            return ""
        try:
            start = datetime.fromisoformat(self.created_at)
            end_str = self.finished_at if self.finished_at else datetime.now().isoformat()
            end = datetime.fromisoformat(end_str)
            return _format_duration((end - start).total_seconds())
        except (ValueError, TypeError):
            return ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "file_name": self.file_name,
            "scheme_id": self.scheme_id,
            "scheme_name": self.scheme_name,
            "status": self.status,
            "total_rows": self.total_rows,
            "completed_rows": self.completed_rows,
            "progress_percent": self.progress_percent,
            "target_column": self.target_column,
            "upload_file_path": self.upload_file_path,
            "output_file_path": self.output_file_path,
            "model": self.model,
            "created_at": self.created_at,
            "finished_at": self.finished_at,
            "duration": self.duration,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Task:
        return cls(
            id=data.get("id", f"task_{uuid.uuid4().hex[:8]}"),
            file_name=data.get("file_name", ""),
            scheme_id=data.get("scheme_id", ""),
            scheme_name=data.get("scheme_name", ""),
            status=data.get("status", TASK_STATUS_RUNNING),
            total_rows=data.get("total_rows", 0),
            completed_rows=data.get("completed_rows", 0),
            target_column=data.get("target_column", ""),
            upload_file_path=data.get("upload_file_path", ""),
            output_file_path=data.get("output_file_path", ""),
            model=data.get("model", ""),
            created_at=data.get("created_at", datetime.now().isoformat()),
            finished_at=data.get("finished_at", ""),
        )

    def mark_completed(self):
        self.status = TASK_STATUS_COMPLETED
        self.completed_rows = self.total_rows
        self.finished_at = datetime.now().isoformat()

    def mark_terminated(self):
        self.status = TASK_STATUS_TERMINATED
        self.finished_at = datetime.now().isoformat()
