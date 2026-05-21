from __future__ import annotations

import os
import sys
import threading
import webbrowser
from pathlib import Path


def _is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def _resource_dir() -> Path:
    if _is_frozen():
        return Path(getattr(sys, "_MEIPASS"))
    return Path(__file__).resolve().parent


def _app_dir() -> Path:
    if _is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _data_dir() -> Path:
    # 从环境变量中获取数据目录
    # 如果环境变量中没有指定数据目录，使用默认数据目录
    # 如果是 macOS，使用 ~/Downloads/TextAnnotationSystem 作为数据目录
    # 如果不是 macOS，使用当前目录的 data 子目录
    env_dir = os.environ.get("TAS_DATA_DIR")
    if env_dir:
        return Path(env_dir).expanduser().resolve()
    if sys.platform == "darwin":
        downloads_dir = Path.home() / "Downloads" / "TextAnnotationSystem"
        downloads_dir.mkdir(parents=True, exist_ok=True)
        return downloads_dir
    else:
        data_dir = _app_dir() / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir


BASE_DIR = _resource_dir()
APP_DIR = _app_dir()
DATA_DIR = _data_dir()
STATIC_DIR = BASE_DIR / "static"

if _is_frozen():
    if str(BASE_DIR) not in sys.path:
        sys.path.insert(0, str(BASE_DIR))

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api import config, files, schemes, tasks
from core.file_handler import FileHandler
from core.scheme_manager import SchemeManager
from core.task_manager import TaskManager

APP_PORT = int(os.environ.get("TAS_PORT", "8765"))


def ensure_dirs():
    for sub in ["schemes", "tasks", "uploads", "outputs"]:
        (DATA_DIR / sub).mkdir(parents=True, exist_ok=True)


_server_ref = None


def _stop_server():
    global _server_ref
    if _server_ref is not None:
        _server_ref.should_exit = True


def create_app() -> FastAPI:
    from api import config, files, schemes, tasks, system

    app = FastAPI(title="Text Annotation System", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    ensure_dirs()

    scheme_manager = SchemeManager(str(DATA_DIR / "schemes"))
    file_handler = FileHandler(str(DATA_DIR / "uploads"), str(DATA_DIR / "outputs"))
    task_manager = TaskManager(
        data_dir=str(DATA_DIR),
        scheme_manager=scheme_manager,
        file_handler=file_handler,
    )

    schemes.init(scheme_manager)
    tasks.init(task_manager)
    files.init(file_handler)
    config.init(str(DATA_DIR))
    system.init(_stop_server)

    app.include_router(schemes.router)
    app.include_router(tasks.router)
    app.include_router(files.router)
    app.include_router(config.router)
    app.include_router(system.router)

    if STATIC_DIR.exists() and any(STATIC_DIR.iterdir()):
        app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

    return app


def open_browser():
    webbrowser.open(f"http://localhost:{APP_PORT}")


def main():
    global _server_ref
    os.chdir(APP_DIR)
    config = uvicorn.Config(
        create_app(),
        host="127.0.0.1",
        port=APP_PORT,
        log_level="warning" if _is_frozen() else "info",
        log_config=None if _is_frozen() else uvicorn.config.LOGGING_CONFIG,
        access_log=not _is_frozen(),
    )
    _server_ref = uvicorn.Server(config)
    threading.Timer(1.5, open_browser).start()
    _server_ref.run()


if __name__ == "__main__":
    main()
