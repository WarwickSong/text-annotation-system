from __future__ import annotations

import json

from models.scheme import AnnotationScheme, AnnotationClass


def _build_class_instruction(cls: AnnotationClass) -> str:
    parts = [f"- {cls.name}：{cls.description}"]
    if cls.label_type == "select" and cls.options:
        options_str = "、".join(cls.options)
        parts.append(f"  可选值：{options_str}")
        parts.append(f"  你必须且只能从以上可选值中选择一个，不要输出其他内容。")
    else:
        parts.append("  根据描述合理判断并输出标注内容。")
    return "\n".join(parts)


def _build_output_format(scheme: AnnotationScheme) -> str:
    keys = [cls.name for cls in scheme.classes]
    example = {cls.name: (cls.options[0] if cls.label_type == "select" and cls.options else "...") for cls in scheme.classes}
    example_json = json.dumps(example, ensure_ascii=False)
    lines = [
        "输出格式要求：",
        "1. 必须且只能输出一个JSON对象，不要输出任何其他文字、解释或标记。",
        f"2. JSON的键为：{'、'.join(f'\"{k}\"' for k in keys)}。",
        f"3. 示例格式：{example_json}",
        "4. 对于有可选值的字段，值必须是可选值之一。",
    ]
    return "\n".join(lines)


def build_system_message(scheme: AnnotationScheme) -> str:
    parts: list[str] = []
    if scheme.prompt_header:
        parts.append(scheme.prompt_header.strip())
    parts.append("\n标注要求：")
    for cls in scheme.classes:
        parts.append(_build_class_instruction(cls))
    parts.append("")
    parts.append(_build_output_format(scheme))
    return "\n".join(parts)


def build_messages(scheme: AnnotationScheme, row_text: str) -> list[dict]:
    system_content = build_system_message(scheme)
    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": row_text},
    ]


def build_all_prompts(scheme: AnnotationScheme, texts: list[str]) -> list[list[dict]]:
    return [build_messages(scheme, text) for text in texts]
