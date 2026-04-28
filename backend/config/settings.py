from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[1]


load_dotenv(_backend_root() / ".env")


def _get_env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return int(raw)


def _get_env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _get_env_list(name: str, default: list[str]) -> tuple[str, ...]:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return tuple(default)
    return tuple(part.strip() for part in raw.split(",") if part.strip())


@dataclass(frozen=True)
class RuntimeSettings:
    repo_root: Path
    backend_root: Path
    api_v1_prefix: str
    cors_origins: tuple[str, ...]
    duckdb_path: Path
    duckdb_threads: int
    duckdb_memory_limit: str
    data_cache_dir: Path
    parquet_base_url: str
    hf_model_repo: str
    hf_model_subfolder: str
    hf_token: str | None
    load_ml_models_on_startup: bool


@lru_cache(maxsize=1)
def get_settings() -> RuntimeSettings:
    repo_root = _repo_root()
    backend_root = _backend_root()
    return RuntimeSettings(
        repo_root=repo_root,
        backend_root=backend_root,
        api_v1_prefix=os.getenv("API_V1_PREFIX", "/api/v1"),
        cors_origins=_get_env_list("CORS_ORIGINS", ["http://localhost:3000"]),
        duckdb_path=Path(os.getenv("DUCKDB_PATH", str(repo_root / "analytics.duckdb"))),
        duckdb_threads=_get_env_int("DUCKDB_THREADS", 4),
        duckdb_memory_limit=os.getenv("DUCKDB_MEMORY_LIMIT", "8GB"),
        data_cache_dir=Path(os.getenv("DATA_CACHE_DIR", str(repo_root / "data_cache"))),
        parquet_base_url=os.getenv(
            "PARQUET_BASE_URL",
            "https://huggingface.co/datasets/ardae1/analytics-parquets/resolve/main/patent-iq",
        ).rstrip("/"),
        hf_model_repo=os.getenv("HF_MODEL_REPO", "ardae1/patent-citation-models"),
        hf_model_subfolder=os.getenv("HF_MODEL_SUBFOLDER", "artifacts"),
        hf_token=os.getenv("HF_TOKEN"),
        load_ml_models_on_startup=_get_env_bool("LOAD_ML_MODELS_ON_STARTUP", True),
    )
