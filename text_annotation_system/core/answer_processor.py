from __future__ import annotations

import json
import re
from typing import Optional

from models.scheme import AnnotationScheme


_PARSE_ERROR_PREFIX = "[解析失败]"
_UNMATCHED_PREFIX = "[?]"


def _extract_json(text: str) -> Optional[dict]:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            pass
    first = text.find("{")
    last = text.rfind("}")
    if first != -1 and last > first:
        try:
            return json.loads(text[first : last + 1])
        except json.JSONDecodeError:
            pass
    return None


def _edit_distance(s1: str, s2: str) -> int:
    m, n = len(s1), len(s2)
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev = dp[0]
        dp[0] = i
        for j in range(1, n + 1):
            temp = dp[j]
            if s1[i - 1] == s2[j - 1]:
                dp[j] = prev
            else:
                dp[j] = 1 + min(prev, dp[j], dp[j - 1])
            prev = temp
    return dp[n]


def _fuzzy_match(value: str, options: list[str]) -> Optional[str]:
    val = value.strip().lower()
    for opt in options:
        if val == opt.strip().lower():
            return opt
    candidates = [opt for opt in options if opt.strip().lower() in val]
    if candidates:
        return max(candidates, key=lambda o: len(o.strip()))
    return min(options, key=lambda o: _edit_distance(val, o.strip().lower()))


def process_answer(raw_answer: str, scheme: AnnotationScheme) -> dict[str, str]:
    parsed = _extract_json(raw_answer)
    if parsed is None:
        result = {}
        for cls in scheme.classes:
            result[cls.name] = f"{_PARSE_ERROR_PREFIX}{raw_answer[:100]}"
        return result

    if not isinstance(parsed, dict):
        parsed = {"value": str(parsed)}

    result = {}
    for cls in scheme.classes:
        value = parsed.get(cls.name, "")
        if value is None:
            value = ""
        value = str(value).strip()

        if cls.label_type == "select" and cls.options:
            exact = False
            for opt in cls.options:
                if value == opt:
                    exact = True
                    break
            if not exact and value:
                matched = _fuzzy_match(value, cls.options)
                if matched is not None:
                    value = matched
                else:
                    value = f"{_UNMATCHED_PREFIX}{value}"
        result[cls.name] = value

    return result
