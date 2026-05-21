from __future__ import annotations

from fastapi import APIRouter, HTTPException, UploadFile, File

from core.file_handler import FileHandler

router = APIRouter(prefix="/api/files", tags=["files"])

file_handler: FileHandler = None  # type: ignore


def init(fh: FileHandler):
    global file_handler
    file_handler = fh


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    content = await file.read()
    file_id = file_handler.save_upload(file.filename, content)
    columns = file_handler.get_columns(file_id)
    preview = file_handler.preview_rows(file_id, n=5)
    return {
        "file_id": file_id,
        "file_name": file.filename,
        "columns": columns,
        "preview": preview,
    }


@router.get("/{file_id}/preview")
async def preview_file(file_id: str, n: int = 5):
    try:
        preview = file_handler.preview_rows(file_id, n=n)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    return preview


@router.get("/{file_id}/columns")
async def get_columns(file_id: str):
    try:
        columns = file_handler.get_columns(file_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    return columns
