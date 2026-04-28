import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, get_args, get_origin

from pydantic import Field, TypeAdapter
try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    _PYDANTIC_SETTINGS_AVAILABLE = True
except ImportError:  # pragma: no cover - offline/dev fallback
    from pydantic import BaseModel, ConfigDict

    BaseSettings = BaseModel
    SettingsConfigDict = ConfigDict
    _PYDANTIC_SETTINGS_AVAILABLE = False


REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="PATENTIQ_V2_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "PatentIQ Backend V2"
    app_version: str = "0.1.0"
    api_prefix: str = "/api/v1"
    runtime_profile: str = "local"

    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
            "http://host.docker.internal:3000",
            "http://host.docker.internal:3001",
        ]
    )

    repo_root: Path = REPO_ROOT
    etl_data_root: Path = REPO_ROOT / "etl" / "data"
    duckdb_path: Path = REPO_ROOT / "backend_v2" / ".cache" / "patentiq_v2.duckdb"
    duckdb_threads: int = 2
    duckdb_memory_limit: str = "4GB"
    duckdb_temp_directory: Path = REPO_ROOT / "backend_v2" / ".cache" / "duckdb_tmp"
    artifact_mode: str = "local_fs"
    local_artifact_root: Path = REPO_ROOT / "etl" / "data" / "serving"
    cache_dir: Path = REPO_ROOT / "backend_v2" / ".cache" / "artifacts"
    pending_grant_cache_dir: Path = REPO_ROOT / "backend_v2" / ".cache" / "pending_grant"
    pending_grant_scorer_python: str | None = None
    serving_manifest_path: Path = REPO_ROOT / "etl" / "data" / "serving" / "serving_snapshot_manifest.json"
    serving_manifest_url: str | None = None
    serving_base_url: str | None = None
    core_serving_duckdb_path: Path | None = None
    core_serving_duckdb_url: str | None = None
    analytics_serving_duckdb_path: Path | None = None
    analytics_serving_duckdb_url: str | None = None
    market_serving_duckdb_path: Path | None = None
    market_serving_duckdb_url: str | None = None
    semantic_serving_duckdb_path: Path | None = None
    semantic_serving_duckdb_url: str | None = None
    publication_serving_duckdb_path: Path | None = None
    publication_serving_duckdb_url: str | None = None
    raw_parquet_fallback_enabled: bool = False


def _read_env_file_candidates() -> dict[str, str]:
    candidates = [
        Path.cwd() / ".env",
        REPO_ROOT / ".env",
    ]
    values: dict[str, str] = {}
    for candidate in candidates:
        if not candidate.exists():
            continue
        try:
            for raw_line in candidate.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip("\"'")
                if key and key not in values:
                    values[key] = value
        except OSError:
            continue
    return values


def _coerce_env_value(raw_value: str, annotation: Any) -> Any:
    args = get_args(annotation)
    non_none_args = [candidate for candidate in args if candidate is not type(None)]
    if raw_value == "" and len(non_none_args) != len(args):
        return None

    target = annotation
    if len(non_none_args) == 1:
        target = non_none_args[0]

    origin = get_origin(target)
    if origin is list:
        if raw_value.lstrip().startswith("["):
            return json.loads(raw_value)
        return [part.strip() for part in raw_value.split(",") if part.strip()]
    if target is bool:
        return raw_value.strip().lower() in {"1", "true", "yes", "on"}
    if target is int:
        return int(raw_value)
    if target is Path:
        return Path(raw_value)
    return TypeAdapter(target).validate_python(raw_value)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    if not _PYDANTIC_SETTINGS_AVAILABLE:
        env_file_values = _read_env_file_candidates()
        payload: dict[str, Any] = {}
        for field_name, field_info in Settings.model_fields.items():
            env_name = f"PATENTIQ_V2_{field_name.upper()}"
            raw_value = os.getenv(env_name, env_file_values.get(env_name))
            if raw_value is None:
                continue
            payload[field_name] = _coerce_env_value(raw_value, field_info.annotation)
        return Settings(**payload)
    return Settings()
