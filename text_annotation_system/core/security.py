from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path

from cryptography.fernet import Fernet


_FERNET_KEY_ENV = "TAS_FERNET_KEY"
_SECRET_FILE = "secret.dat"


def _derive_fernet_key() -> bytes:
    env_key = os.environ.get(_FERNET_KEY_ENV)
    if env_key:
        raw = env_key.encode("utf-8")
    else:
        machine_id = os.environ.get("COMPUTERNAME", os.environ.get("HOSTNAME", "default"))
        raw = f"tas-{machine_id}-key".encode("utf-8")
    digest = hashlib.sha256(raw).digest()
    return base64.urlsafe_b64encode(digest)


def _get_fernet() -> Fernet:
    return Fernet(_derive_fernet_key())


def _migrate_payload(obj: dict) -> dict:
    if "model" in obj and "models" not in obj:
        obj["models"] = [obj["model"]] if obj["model"] else []
    return obj


def encrypt_config(api_key: str, base_url: str, models: list[str]) -> bytes:
    payload = json.dumps({
        "api_key": api_key,
        "base_url": base_url,
        "models": models,
    }, ensure_ascii=False).encode("utf-8")
    return _get_fernet().encrypt(payload)


def decrypt_config(data_dir: str) -> tuple[str, str, list[str]]:
    secret_path = Path(data_dir) / _SECRET_FILE
    if not secret_path.exists():
        raise FileNotFoundError("secret.dat not found, please configure API key first")
    encrypted = secret_path.read_bytes()
    payload = _get_fernet().decrypt(encrypted)
    obj = _migrate_payload(json.loads(payload.decode("utf-8")))
    return obj["api_key"], obj["base_url"], obj.get("models", [])


def save_config(data_dir: str, api_key: str, base_url: str, models: list[str]):
    Path(data_dir).mkdir(parents=True, exist_ok=True)
    encrypted = encrypt_config(api_key, base_url, models)
    secret_path = Path(data_dir) / _SECRET_FILE
    secret_path.write_bytes(encrypted)


def has_config(data_dir: str) -> bool:
    return (Path(data_dir) / _SECRET_FILE).exists()


def delete_config(data_dir: str):
    secret_path = Path(data_dir) / _SECRET_FILE
    if secret_path.exists():
        secret_path.unlink()
