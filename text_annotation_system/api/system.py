from __future__ import annotations

import asyncio
from typing import Callable

from fastapi import APIRouter

router = APIRouter(prefix="/api/system", tags=["system"])

_shutdown_fn: Callable | None = None


def init(shutdown_fn: Callable):
    global _shutdown_fn
    _shutdown_fn = shutdown_fn


@router.post("/shutdown")
async def shutdown():
    fn = _shutdown_fn
    if fn:
        fn()
    return {"ok": True}
