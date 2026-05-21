from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Optional

from models.scheme import AnnotationScheme


class SchemeManager:
    def __init__(self, schemes_dir: str):
        self._dir = Path(schemes_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    def _scheme_path(self, scheme_id: str) -> Path:
        return self._dir / f"{scheme_id}.json"

    def list_schemes(self) -> list[dict]:
        result = []
        for fp in sorted(self._dir.glob("*.json")):
            try:
                data = json.loads(fp.read_text(encoding="utf-8"))
                result.append({
                    "id": data.get("id", fp.stem),
                    "name": data.get("name", ""),
                    "updated_at": data.get("updated_at", ""),
                })
            except (json.JSONDecodeError, KeyError):
                continue
        return result

    def get(self, scheme_id: str) -> Optional[AnnotationScheme]:
        path = self._scheme_path(scheme_id)
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return AnnotationScheme.from_dict(data)

    def create(self, scheme: AnnotationScheme) -> AnnotationScheme:
        path = self._scheme_path(scheme.id)
        path.write_text(
            json.dumps(scheme.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return scheme

    def update(self, scheme: AnnotationScheme) -> AnnotationScheme:
        scheme.touch()
        path = self._scheme_path(scheme.id)
        if not path.exists():
            raise FileNotFoundError(f"Scheme {scheme.id} not found")
        path.write_text(
            json.dumps(scheme.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return scheme

    def delete(self, scheme_id: str) -> bool:
        path = self._scheme_path(scheme_id)
        if path.exists():
            path.unlink()
            return True
        return False

    def export_scheme(self, scheme_id: str) -> Optional[str]:
        scheme = self.get(scheme_id)
        if scheme is None:
            return None
        return json.dumps(scheme.to_dict(), ensure_ascii=False, indent=2)

    def import_scheme(self, json_str: str) -> AnnotationScheme:
        data = json.loads(json_str)
        scheme = AnnotationScheme.from_dict(data)
        return self.create(scheme)
