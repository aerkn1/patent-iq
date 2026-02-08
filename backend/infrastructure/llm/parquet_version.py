from __future__ import annotations

import hashlib
from pathlib import Path


def _repo_root() -> Path:
    # parquet_version.py -> backend/infrastructure/llm/parquet_version.py
    return Path(__file__).resolve().parents[3]


def compute_parquet_version_hash() -> str:
    """Compute a stable hash representing the current cached parquet versions.

    Uses the .meta sidecar files written by CacheManager (ETag or Content-Length).
    If meta files are missing, falls back to file size + mtime of the parquet.
    """

    cache_dir = (_repo_root() / "data_cache")
    if not cache_dir.exists():
        return "no-cache"

    h = hashlib.sha256()

    meta_files = sorted(cache_dir.glob("*.meta"), key=lambda p: p.name)
    if meta_files:
        for p in meta_files:
            try:
                content = p.read_text().strip()
            except Exception:
                content = ""
            h.update(p.name.encode("utf-8"))
            h.update(b"\0")
            h.update(content.encode("utf-8"))
            h.update(b"\n")
        return h.hexdigest()

    # Fallback: hash parquet sizes/mtimes
    for p in sorted(cache_dir.glob("*.parquet"), key=lambda p: p.name):
        try:
            st = p.stat()
            h.update(p.name.encode("utf-8"))
            h.update(b"\0")
            h.update(str(st.st_size).encode("utf-8"))
            h.update(b"\0")
            h.update(str(int(st.st_mtime)).encode("utf-8"))
            h.update(b"\n")
        except Exception:
            continue

    return h.hexdigest()
