from __future__ import annotations

from fastapi import APIRouter, HTTPException

from async_batch_inference import AsyncBatchConfig, AsyncBatchInference
from core.security import decrypt_config, has_config, save_config

router = APIRouter(prefix="/api/config", tags=["config"])

_data_dir: str = ""


def init(data_dir: str):
    global _data_dir
    _data_dir = data_dir


@router.get("/status")
async def config_status():
    configured = has_config(_data_dir)
    models: list[str] = []
    if configured:
        try:
            _, _, models = decrypt_config(_data_dir)
        except Exception:
            pass
    return {"configured": configured, "models": models}


@router.post("/set")
async def set_config(body: dict):
    api_key = body.get("api_key", "").strip()
    base_url = body.get("base_url", "").strip()
    models = body.get("models", [])
    if isinstance(models, str):
        models = [m.strip() for m in models.split(",") if m.strip()]
    models = [m.strip() for m in models if m.strip()]
    if not all([api_key, base_url, models]):
        raise HTTPException(status_code=400, detail="api_key, base_url, and at least one model are required")
    save_config(_data_dir, api_key, base_url, models)
    return {"ok": True}


@router.post("/test")
async def test_config(body: dict = None):
    if not has_config(_data_dir):
        raise HTTPException(status_code=400, detail="API key not configured")
    try:
        api_key, base_url, models = decrypt_config(_data_dir)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to decrypt config: {str(e)}")
    model_name = ""
    if body:
        model_name = body.get("model", "").strip()
    if not model_name and models:
        model_name = models[0]
    if not model_name:
        raise HTTPException(status_code=400, detail="No model available for testing")
    config = AsyncBatchConfig(api_key=api_key, base_url=base_url, model=model_name)
    engine = AsyncBatchInference(config)
    try:
        result = await engine.single(
            [{"role": "user", "content": "Hi, reply with OK."}],
        )
        return {"ok": True, "answer": result.get("answer", ""), "model": model_name}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"API call failed: {str(e)}")
