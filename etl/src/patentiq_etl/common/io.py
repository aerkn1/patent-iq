from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable

import duckdb


def ensure_dir(path: Path) -> Path:
    """Create `path` and its parents if needed, then return the same path."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def duckdb_connect() -> duckdb.DuckDBPyConnection:
    """Return a new DuckDB connection for local analytical work."""
    return duckdb.connect()


def candidate_files(directory: Path, stems: Iterable[str]) -> list[Path]:
    """Return existing source files in `directory` that match any logical table stem."""
    patterns = []
    for stem in stems:
        patterns.extend(
            [
                directory / f"{stem}.csv",
                directory / f"{stem}.csv.gz",
                directory / f"{stem}.parquet",
                directory / f"{stem}.jsonl",
                directory / f"{stem}.json",
                directory / f"{stem}.XML",
                directory / f"{stem}.xml",
            ]
        )
    return [path for path in patterns if path.exists()]


def copy_to_parquet(source_path: Path, out_path: Path) -> int:
    """Copy a raw source file into a compressed Bronze parquet artifact and return row count."""
    ensure_dir(out_path.parent)
    con = duckdb_connect()
    suffix = source_path.suffix.lower()
    if suffix == ".parquet":
        con.execute("copy (select * from read_parquet(?)) to ? (format parquet, compression zstd)", [str(source_path), str(out_path)])
    elif suffix in {".csv", ".gz"} or source_path.name.endswith(".csv.gz"):
        con.execute("copy (select * from read_csv_auto(?, header=true)) to ? (format parquet, compression zstd)", [str(source_path), str(out_path)])
    elif suffix == ".jsonl":
        con.execute("copy (select * from read_json_auto(?)) to ? (format parquet, compression zstd)", [str(source_path), str(out_path)])
    else:
        raise ValueError(f"Unsupported generic copy source: {source_path}")
    return parquet_row_count(out_path)


def parquet_row_count(path: Path) -> int:
    """Return the row count of a parquet artifact."""
    con = duckdb_connect()
    return int(con.execute("select count(*) from read_parquet(?)", [str(path)]).fetchone()[0])


def parquet_columns(path: Path) -> list[str]:
    """Return ordered column names for a parquet artifact."""
    con = duckdb_connect()
    rows = con.execute("describe select * from read_parquet(?)", [str(path)]).fetchall()
    return [row[0] for row in rows]


def table_exists(path: Path) -> bool:
    """Return whether a parquet artifact exists at the expected location."""
    return path.exists() and path.suffix == ".parquet"


def write_pylist_parquet(rows: list[dict], out_path: Path, columns: list[str] | None = None) -> int:
    """Write a list-of-dicts payload to parquet, preserving an empty-schema contract if needed."""
    ensure_dir(out_path.parent)
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq

        if rows:
            table = pa.Table.from_pylist(rows)
        else:
            names = columns or []
            table = pa.table({name: pa.array([], type=pa.string()) for name in names})
        pq.write_table(table, out_path, compression="zstd")
        return table.num_rows
    except ModuleNotFoundError:
        if rows:
            import pandas as pd

            frame = pd.DataFrame.from_records(rows)
            con = duckdb_connect()
            con.register("pylist_frame", frame)
            con.execute("copy (select * from pylist_frame) to ? (format parquet, compression zstd)", [str(out_path)])
            return len(frame.index)

        names = columns or []
        con = duckdb_connect()
        projection = ", ".join(f"null::varchar as {name}" for name in names) or "null::varchar as _empty"
        con.execute(f"copy (select {projection} where false) to ? (format parquet, compression zstd)", [str(out_path)])
        return 0


def normalize_ws(text: str | None) -> str | None:
    """Collapse repeated whitespace and trim surrounding space."""
    if text is None:
        return None
    return re.sub(r"\s+", " ", text).strip() or None


def strip_reference_numerals(text: str | None) -> str | None:
    """Remove patent-style reference numerals such as `(14)` from a text string."""
    if text is None:
        return None
    return re.sub(r"\(\d+[A-Za-z]?\)", "", text)


def sanitize_semantic_text(text: str | None) -> str | None:
    """Prepare claim or abstract text for semantic use by stripping tags and numerals."""
    if text is None:
        return None
    text = re.sub(r"<[^>]+>", " ", text)
    text = strip_reference_numerals(text)
    return normalize_ws(text)


def stable_hash_embedding(text: str, dims: int = 32) -> list[float]:
    """Create a deterministic placeholder embedding for MVP semantic packaging tests."""
    vector = [0.0] * dims
    for token in re.findall(r"[A-Za-z0-9_]+", text.lower()):
        slot = hash(token) % dims
        vector[slot] += 1.0
    total = sum(abs(v) for v in vector) or 1.0
    normalized = [round(v / total, 6) for v in vector]
    drift = round(1.0 - sum(normalized), 6)
    if normalized:
        normalized[-1] = round(normalized[-1] + drift, 6)
    return normalized


def write_text_json(path: Path, payload: dict) -> None:
    """Write a JSON payload to disk with stable formatting."""
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def append_jsonl(path: Path, payload: dict) -> None:
    """Append one JSON object as a line-delimited record."""
    ensure_dir(path.parent)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True))
        handle.write("\n")
