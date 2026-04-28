from __future__ import annotations

import hashlib
import html
import json
import re
from pathlib import Path
from typing import Any, Iterable

import duckdb
import pandas as pd


_WHITESPACE_RE = re.compile(r"\s+")
_TAG_RE = re.compile(r"<[^>]+>")
_BRACKETED_MARKER_RE = re.compile(r"^\s*(?:\[\d+\]|\(\d+\)|\d+\.)\s*")


def ensure_dir(path: str | Path) -> Path:
    """Create one directory and return it as a Path."""
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def normalize_ws(value: Any) -> str | None:
    """Collapse repeated whitespace and return `None` for empty values."""
    if value is None:
        return None
    text = _WHITESPACE_RE.sub(" ", str(value)).strip()
    return text or None


def sanitize_semantic_text(value: Any) -> str | None:
    """Normalize text-provider payloads into plain semantic-safe strings."""
    text = normalize_ws(value)
    if text is None:
        return None
    text = html.unescape(text)
    text = _TAG_RE.sub(" ", text)
    text = _BRACKETED_MARKER_RE.sub("", text)
    text = _WHITESPACE_RE.sub(" ", text).strip()
    return text or None


def duckdb_connect() -> duckdb.DuckDBPyConnection:
    """Return one local DuckDB connection with stable ETL defaults."""
    con = duckdb.connect()
    con.execute("set preserve_insertion_order=false")
    return con


def parquet_row_count(path: str | Path) -> int:
    """Return row count for one parquet file or dataset path."""
    parquet_path = Path(path)
    if not parquet_path.exists():
        return 0
    source = str(parquet_path / "*.parquet") if parquet_path.is_dir() else str(parquet_path)
    con = duckdb_connect()
    return int(con.execute("select count(*) from read_parquet(?)", [source]).fetchone()[0])


def parquet_columns(path: str | Path) -> list[str]:
    """Return column names for one parquet file or dataset path."""
    parquet_path = Path(path)
    source = str(parquet_path / "*.parquet") if parquet_path.is_dir() else str(parquet_path)
    con = duckdb_connect()
    rows = con.execute("describe select * from read_parquet(?)", [source]).fetchall()
    return [row[0] for row in rows]


def table_exists(path: str | Path) -> bool:
    """Return whether one expected parquet source path exists."""
    return Path(path).exists()


def candidate_files(directory: str | Path, stems: Iterable[str]) -> list[Path]:
    """Return matching candidate files for logical stems in stable path order."""
    root = Path(directory)
    if not root.exists():
        return []
    lowered_stems = [stem.lower() for stem in stems]
    matches: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        name = path.name.lower()
        if any(name == stem or name.startswith(stem + ".") for stem in lowered_stems):
            matches.append(path)
    return sorted(dict.fromkeys(matches), key=lambda item: str(item))


def copy_to_parquet(source_path: str | Path, out_path: str | Path) -> int:
    """Copy one source file into parquet using a source-aware DuckDB reader."""
    source = Path(source_path)
    target = Path(out_path)
    ensure_dir(target.parent)
    suffix = source.suffix.lower()
    if suffix == ".parquet":
        relation = "read_parquet(?)"
    elif suffix in {".csv", ".gz"} or source.name.endswith(".csv.gz"):
        relation = "read_csv_auto(?, header=true)"
    elif suffix in {".json", ".jsonl"}:
        relation = "read_json_auto(?)"
    else:
        raise ValueError(f"Unsupported source format for parquet copy: {source}")
    con = duckdb_connect()
    con.execute(f"copy (select * from {relation}) to ? (format parquet, compression zstd)", [str(source), str(target)])
    return parquet_row_count(target)


def _ordered_columns(rows: list[dict[str, Any]], columns: list[str] | None) -> list[str]:
    if columns is not None:
        return list(columns)
    ordered: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row.keys():
            if key not in seen:
                ordered.append(key)
                seen.add(key)
    return ordered


def write_pylist_parquet(rows: list[dict[str, Any]], path: str | Path, columns: list[str] | None = None) -> int:
    """Write a list of dictionaries to parquet and return the row count."""
    out_path = Path(path)
    ensure_dir(out_path.parent)
    ordered_columns = _ordered_columns(rows, columns)
    normalized_rows = [{column: row.get(column) for column in ordered_columns} for row in rows]
    if not rows and not ordered_columns:
        raise ValueError("Cannot write an empty parquet without explicit `columns`.")
    frame = pd.DataFrame(normalized_rows, columns=ordered_columns)
    con = duckdb_connect()
    con.register("rows_view", frame)
    con.execute("copy (select * from rows_view) to ? (format parquet, compression zstd)", [str(out_path)])
    return len(rows)


def write_text_json(path: str | Path, payload: Any) -> None:
    """Write one JSON payload with UTF-8 and deterministic formatting."""
    out_path = Path(path)
    ensure_dir(out_path.parent)
    with out_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True, default=str)
        handle.write("\n")


def append_jsonl(path: str | Path, record: Any) -> None:
    """Append one JSON object as a line-delimited UTF-8 record."""
    out_path = Path(path)
    ensure_dir(out_path.parent)
    with out_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True, default=str))
        handle.write("\n")


def stable_hash_embedding(text: str | None, dims: int = 32) -> list[float]:
    """Return one deterministic non-negative bag-of-tokens embedding that sums to 1."""
    if dims <= 0:
        raise ValueError("`dims` must be positive.")
    tokens = re.findall(r"[A-Za-z0-9_]+", (text or "").lower())
    if not tokens:
        return [0.0] * dims
    buckets = [0.0] * dims
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        slot = int.from_bytes(digest[:4], "little") % dims
        buckets[slot] += 1.0 + min(len(token), 20) / 20.0
    total = sum(buckets)
    return [round(value / total, 6) for value in buckets]


__all__ = [
    "candidate_files",
    "copy_to_parquet",
    "duckdb_connect",
    "ensure_dir",
    "normalize_ws",
    "parquet_columns",
    "parquet_row_count",
    "append_jsonl",
    "sanitize_semantic_text",
    "stable_hash_embedding",
    "table_exists",
    "write_pylist_parquet",
    "write_text_json",
]
