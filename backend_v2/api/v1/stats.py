from fastapi import APIRouter

from config.settings import get_settings
from infrastructure.artifacts import ArtifactLocator

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/runtime")
def get_runtime_stats() -> dict[str, str | int]:
    settings = get_settings()
    artifact_locator = ArtifactLocator(settings=settings)
    runtime = artifact_locator.describe_runtime()
    return {
        "app_name": settings.app_name,
        "api_prefix": settings.api_prefix,
        "duckdb_threads": settings.duckdb_threads,
        "duckdb_memory_limit": settings.duckdb_memory_limit,
        "runtime_profile": runtime["runtime_profile"],
        "artifact_mode": runtime["artifact_mode"],
        "core_serving_duckdb": runtime["core_serving_duckdb"] or "",
        "publication_serving_duckdb": runtime["publication_serving_duckdb"] or "",
    }
