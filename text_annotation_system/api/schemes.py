from __future__ import annotations

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import Response

from core.scheme_manager import SchemeManager
from models.scheme import AnnotationScheme, AnnotationClass

router = APIRouter(prefix="/api/schemes", tags=["schemes"])

scheme_manager: SchemeManager = None  # type: ignore


def init(s_m: SchemeManager):
    global scheme_manager
    scheme_manager = s_m


@router.get("")
async def list_schemes():
    return scheme_manager.list_schemes()


@router.get("/{scheme_id}")
async def get_scheme(scheme_id: str):
    scheme = scheme_manager.get(scheme_id)
    if scheme is None:
        raise HTTPException(status_code=404, detail="Scheme not found")
    return scheme.to_dict()


@router.post("")
async def create_scheme(body: dict):
    scheme = AnnotationScheme(
        name=body.get("name", "New Scheme"),
        prompt_header=body.get("prompt_header", ""),
        classes=[AnnotationClass.from_dict(c) for c in body.get("classes", [])],
    )
    created = scheme_manager.create(scheme)
    return created.to_dict()


@router.put("/{scheme_id}")
async def update_scheme(scheme_id: str, body: dict):
    scheme = scheme_manager.get(scheme_id)
    if scheme is None:
        raise HTTPException(status_code=404, detail="Scheme not found")
    if "name" in body:
        scheme.name = body["name"]
    if "prompt_header" in body:
        scheme.prompt_header = body["prompt_header"]
    if "classes" in body:
        scheme.classes = [AnnotationClass.from_dict(c) for c in body["classes"]]
    updated = scheme_manager.update(scheme)
    return updated.to_dict()


@router.delete("/{scheme_id}")
async def delete_scheme(scheme_id: str):
    ok = scheme_manager.delete(scheme_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Scheme not found")
    return {"ok": True}


@router.post("/{scheme_id}/export")
async def export_scheme(scheme_id: str):
    json_str = scheme_manager.export_scheme(scheme_id)
    if json_str is None:
        raise HTTPException(status_code=404, detail="Scheme not found")
    scheme = scheme_manager.get(scheme_id)
    return Response(
        content=json_str,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={scheme.id}.json"},
    )


@router.post("/import")
async def import_scheme(file: UploadFile = File(...)):
    content = await file.read()
    json_str = content.decode("utf-8")
    try:
        scheme = scheme_manager.import_scheme(json_str)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
    return scheme.to_dict()
