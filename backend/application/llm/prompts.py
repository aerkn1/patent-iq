from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic_core import to_jsonable_python


def _prompts_dir() -> Path:
    return Path(__file__).resolve().parent / "prompts"


_PROMPT_CACHE: dict[str, Any] = {}


# ---------------------------------------------------------------------------
# JSON prompt loader
# ---------------------------------------------------------------------------

def load_prompt_json(name: str) -> dict[str, Any]:
    """Load a structured JSON prompt file and cache it."""
    if name in _PROMPT_CACHE:
        return _PROMPT_CACHE[name]

    path = _prompts_dir() / name
    data = json.loads(path.read_text(encoding="utf-8"))
    _PROMPT_CACHE[name] = data
    return data


# ---------------------------------------------------------------------------
# System prompt assembler
# ---------------------------------------------------------------------------

def build_system_prompt() -> str:
    """Assemble the system prompt text from system.json."""
    cfg = load_prompt_json("system.json")

    lines: list[str] = []
    lines.append(f"You are a {cfg['role']}.")
    lines.append("")

    lines.append("You MUST:")
    for item in cfg["constraints"]["must"]:
        lines.append(f"- {item}")
    lines.append("")

    lines.append("You MUST NOT:")
    for item in cfg["constraints"]["must_not"]:
        lines.append(f"- {item}")
    lines.append("")

    tt = cfg["trace_tokens"]
    lines.append("TRACE TOKENS (REQUIRED FOR VALIDATION)")
    lines.append(f"- {tt['description']}")
    lines.append(f"- A trace token has the exact form: {tt['format']}")
    lines.append(f"  - path: {tt['path_rule']}")
    lines.append(f"  - value: {tt['value_rule']}")
    lines.append("- You may include multiple trace tokens.")
    lines.append("- Do NOT put any extra text inside the [[...]] brackets.")
    lines.append(f"- {tt['validation']}")
    lines.append("")

    lines.append("OUTPUT")
    for rule in cfg["output_rules"]:
        lines.append(f"- {rule}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# User prompt assembler
# ---------------------------------------------------------------------------

def build_user_prompt(prompt_name: str, *, data_obj: dict[str, Any]) -> str:
    """Assemble a user prompt from a JSON config file and inject DATA JSON."""
    cfg = load_prompt_json(prompt_name)

    lines: list[str] = []
    lines.append(cfg["task"])
    lines.append("")

    lines.append("Instructions:")
    for i, instruction in enumerate(cfg["instructions"], 1):
        lines.append(f"{i}) {instruction}")
    lines.append("")

    # Inject data
    jsonable = to_jsonable_python(data_obj)
    data_json = json.dumps(jsonable, ensure_ascii=False, indent=2, sort_keys=True)
    lines.append("DATA:")
    lines.append(data_json)
    lines.append("")

    # Output schema
    lines.append("OUTPUT JSON SHAPE (must match exactly):")
    schema_json = json.dumps(cfg["output_schema"], ensure_ascii=False, indent=2)
    lines.append(schema_json)
    lines.append("")

    # Trace rules
    lines.append("IMPORTANT:")
    for rule in cfg["trace_rules"]:
        lines.append(f"- {rule}")

    return "\n".join(lines)

