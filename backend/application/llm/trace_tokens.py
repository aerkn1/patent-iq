from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from typing import Any, Iterable, Optional


TRACE_TOKEN_RE = re.compile(r"\[\[(?P<path>[A-Za-z_][A-Za-z0-9_\.\[\]]*)=(?P<value>[^\]]+)\]\]")


class TraceTokenError(ValueError):
    pass


@dataclass(frozen=True)
class TraceToken:
    path: str
    value_raw: str


def extract_trace_tokens(text: str) -> list[TraceToken]:
    if not text:
        return []
    return [TraceToken(m.group("path"), m.group("value").strip()) for m in TRACE_TOKEN_RE.finditer(text)]


def strip_trace_tokens(text: str) -> str:
    if not text:
        return text
    # Remove tokens and normalize whitespace around them.
    out = TRACE_TOKEN_RE.sub("", text)
    out = re.sub(r"\s{2,}", " ", out).strip()
    return out


def _parse_path_segments(path: str) -> list[tuple[str, list[int]]]:
    # segment can be: name or name[0][1]
    segs: list[tuple[str, list[int]]] = []
    for raw_seg in path.split("."):
        if not raw_seg:
            raise TraceTokenError(f"Invalid empty path segment in '{path}'")
        m = re.match(r"^(?P<name>[A-Za-z_][A-Za-z0-9_]*)(?P<idx>(\[[0-9]+\])*)$", raw_seg)
        if not m:
            raise TraceTokenError(f"Invalid path segment '{raw_seg}' in '{path}'")
        name = m.group("name")
        idx_part = m.group("idx") or ""
        indices = [int(x) for x in re.findall(r"\[([0-9]+)\]", idx_part)]
        segs.append((name, indices))
    return segs


def get_by_dotted_path(obj: Any, path: str) -> Any:
    cur = obj
    for name, indices in _parse_path_segments(path):
        if not isinstance(cur, dict):
            raise TraceTokenError(f"Path '{path}' expected dict before '{name}', got {type(cur).__name__}")
        if name not in cur:
            raise TraceTokenError(f"Path '{path}' missing key '{name}'")
        cur = cur[name]
        for idx in indices:
            if not isinstance(cur, list):
                raise TraceTokenError(f"Path '{path}' expected list at '{name}[{idx}]', got {type(cur).__name__}")
            if idx < 0 or idx >= len(cur):
                raise TraceTokenError(f"Path '{path}' index out of range at '{name}[{idx}]'")
            cur = cur[idx]
    return cur


def _normalize_token_value(v: str) -> str:
    vv = v.strip()
    # strip matching quotes
    if (vv.startswith('"') and vv.endswith('"')) or (vv.startswith("'") and vv.endswith("'")):
        vv = vv[1:-1]
    return vv.strip()


def values_match(actual: Any, token_value_raw: str) -> bool:
    tv = _normalize_token_value(token_value_raw)

    if actual is None:
        return tv.lower() in ("null", "none")

    if isinstance(actual, bool):
        return (tv.lower() == "true" and actual is True) or (tv.lower() == "false" and actual is False)

    if isinstance(actual, (int, float)):
        try:
            fv = float(tv)
        except Exception:
            return False
        if math.isnan(fv) or math.isinf(fv):
            return False
        return abs(float(actual) - fv) <= 1e-6

    if isinstance(actual, str):
        return actual == tv

    # Disallow complex evidence comparisons
    return False


def require_and_validate_tokens(
    *,
    texts: Iterable[str],
    input_obj: dict[str, Any],
    require_each_text: bool = True,
) -> list[TraceToken]:
    all_tokens: list[TraceToken] = []
    for t in texts:
        toks = extract_trace_tokens(t)
        if require_each_text and not toks:
            raise TraceTokenError("Missing trace token(s) in required text field")
        for tok in toks:
            actual = get_by_dotted_path(input_obj, tok.path)
            if not values_match(actual, tok.value_raw):
                raise TraceTokenError(
                    f"Trace token value mismatch for '{tok.path}': token='{tok.value_raw}' actual='{actual}'"
                )
        all_tokens.extend(toks)
    return all_tokens


def parse_llm_json_object(content: str) -> dict[str, Any]:
    try:
        data = json.loads(content)
    except Exception as e:
        raise ValueError(f"LLM output is not valid JSON: {e}") from e
    if not isinstance(data, dict):
        raise ValueError("LLM output JSON must be an object")
    return data


def evidence_tokens_to_string(tokens: list[TraceToken]) -> str:
    # Format as 'path=value; path=value' for UI.
    parts = [f"{t.path}={_normalize_token_value(t.value_raw)}" for t in tokens]
    return "; ".join(parts)
