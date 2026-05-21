from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class AnnotationClass:
    name: str
    description: str
    label_type: str = "free"
    options: list[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "label_type": self.label_type,
            "options": list(self.options),
        }

    @classmethod
    def from_dict(cls, data: dict) -> AnnotationClass:
        label_type = data.get("label_type")
        if label_type is None:
            label_type = "free"
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            name=data["name"],
            description=data.get("description", ""),
            label_type=label_type,
            options=data.get("options", []),
        )


@dataclass
class AnnotationScheme:
    name: str
    prompt_header: str
    classes: list[AnnotationClass] = field(default_factory=list)
    id: str = field(default_factory=lambda: f"scheme_{uuid.uuid4().hex[:8]}")
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "prompt_header": self.prompt_header,
            "classes": [c.to_dict() for c in self.classes],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> AnnotationScheme:
        classes = [AnnotationClass.from_dict(c) for c in data.get("classes", [])]
        return cls(
            id=data.get("id", f"scheme_{uuid.uuid4().hex[:8]}"),
            name=data["name"],
            prompt_header=data.get("prompt_header", ""),
            classes=classes,
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
        )

    def touch(self):
        self.updated_at = datetime.now().isoformat()

    def add_class(self, annotation_class: AnnotationClass):
        self.classes.append(annotation_class)
        self.touch()

    def remove_class(self, class_id: str):
        self.classes = [c for c in self.classes if c.id != class_id]
        self.touch()

    def get_class(self, class_id: str) -> Optional[AnnotationClass]:
        for c in self.classes:
            if c.id == class_id:
                return c
        return None

    def update_class(self, class_id: str, **kwargs):
        cls_obj = self.get_class(class_id)
        if cls_obj is None:
            return
        for key, value in kwargs.items():
            if hasattr(cls_obj, key):
                setattr(cls_obj, key, value)
        self.touch()
