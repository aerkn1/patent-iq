from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic_core import to_jsonable_python


def _prompts_dir() -> Path:
    # prompts.py -> backend/application/llm/prompts.py
    return Path(__file__).resolve().parent / "prompts"


_PROMPT_CACHE: dict[str, str] = {}


def load_prompt(name: str) -> str:
    if name in _PROMPT_CACHE:
        return _PROMPT_CACHE[name]

    path = _prompts_dir() / name
    text = path.read_text(encoding="utf-8")
    _PROMPT_CACHE[name] = text
    return text


def render_prompt(template: str, *, data_obj: dict[str, Any]) -> str:
    # Ensure JSON serialization is stable even if upstream payloads contain
    # pandas/numpy types.
    jsonable = to_jsonable_python(data_obj)
    data_json = json.dumps(jsonable, ensure_ascii=False, indent=2, sort_keys=True)
    return template.replace("{{DATA_JSON}}", data_json)
