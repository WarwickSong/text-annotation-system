# -*- mode: python ; coding: utf-8 -*-

import importlib
from pathlib import Path

block_cipher = None
project_dir = Path.cwd()
static_dir = project_dir / "static"

datas = []
if static_dir.exists():
    datas.append((str(static_dir), "static"))

abi_spec = importlib.util.find_spec("async_batch_inference")
if abi_spec and abi_spec.origin:
    abi_dir = str(Path(abi_spec.origin).parent)
    datas.append((abi_dir, "async_batch_inference"))

hiddenimports = [
    "async_batch_inference",
    "async_batch_inference.config",
    "async_batch_inference.handle",
    "async_batch_inference.inference",
    "async_batch_inference.prompt_manager",
    "openai",
    "pandas",
    "openpyxl",
    "cryptography",
    "uvicorn",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
]

a = Analysis(
    ["main.py"],
    pathex=[str(project_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="TextAnnotationSystem",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="TextAnnotationSystem",
)

app = BUNDLE(
    coll,
    name="TextAnnotationSystem.app",
    icon=None,
    bundle_identifier="local.text-annotation-system",
)
