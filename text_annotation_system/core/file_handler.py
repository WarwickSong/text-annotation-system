from __future__ import annotations

import os
import shutil
import uuid
from pathlib import Path
from typing import Optional

import pandas as pd


class FileHandler:
    def __init__(self, uploads_dir: str, outputs_dir: str):
        self._uploads = Path(uploads_dir)
        self._outputs = Path(outputs_dir)
        self._uploads.mkdir(parents=True, exist_ok=True)
        self._outputs.mkdir(parents=True, exist_ok=True)
        self._dataframes: dict[str, pd.DataFrame] = {}

    def save_upload(self, file_name: str, file_bytes: bytes) -> str:
        ext = Path(file_name).suffix.lower()
        file_id = f"upload_{uuid.uuid4().hex[:8]}{ext}"
        dest = self._uploads / file_id
        dest.write_bytes(file_bytes)
        return file_id

    def get_upload_path(self, file_id: str) -> Optional[Path]:
        path = self._uploads / file_id
        return path if path.exists() else None

    def read_file(self, file_id: str) -> pd.DataFrame:
        if file_id in self._dataframes:
            return self._dataframes[file_id].copy()
        path = self.get_upload_path(file_id)
        if path is None:
            raise FileNotFoundError(f"File {file_id} not found")
        ext = path.suffix.lower()
        if ext == ".csv":
            df = pd.read_csv(path)
        elif ext in (".xlsx", ".xls"):
            df = pd.read_excel(path, engine="openpyxl")
        else:
            raise ValueError(f"Unsupported file format: {ext}")
        self._dataframes[file_id] = df
        return df.copy()

    def get_columns(self, file_id: str) -> list[str]:
        df = self.read_file(file_id)
        return df.columns.tolist()

    def get_column_values(self, file_id: str, column: str) -> list[str]:
        df = self.read_file(file_id)
        return df[column].astype(str).tolist()

    def preview_rows(self, file_id: str, n: int = 5) -> list[dict]:
        df = self.read_file(file_id)
        return df.head(n).to_dict(orient="records")

    def write_annotation_results(
        self,
        file_id: str,
        column: str,
        class_names: list[str],
        answers: list[dict[str, str]],
        scheme_name: str,
        original_file_name: str,
    ) -> str:
        df = self.read_file(file_id)
        for cls_name in class_names:
            col_name = f"{column}_标注_{cls_name}"
            values = []
            for ans in answers:
                values.append(ans.get(cls_name, ""))
            padded = values + [""] * (len(df) - len(values))
            df[col_name] = padded[: len(df)]
        out_id = f"output_{uuid.uuid4().hex[:8]}"
        ext = Path(original_file_name).suffix.lower()
        out_name = f"{out_id}{ext}"
        out_path = self._outputs / out_name
        if ext == ".csv":
            df.to_csv(out_path, index=False, encoding="utf-8-sig")
        else:
            df.to_excel(out_path, index=False, engine="openpyxl")
        self._dataframes[out_id] = df
        return out_id

    def get_output_path(self, output_id: str) -> Optional[Path]:
        for ext in (".csv", ".xlsx", ".xls"):
            path = self._outputs / f"{output_id}{ext}"
            if path.exists():
                return path
        return None
