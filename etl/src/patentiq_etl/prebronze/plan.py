from __future__ import annotations

from dataclasses import replace

from patentiq_etl.common.io import ensure_dir, write_text_json
from patentiq_etl.common.types import BuildSettings, StageResult
from patentiq_etl.prebronze.tip_clients import slugify_value


DOC_REFS = [
    "docs/next-phase-v2/28-patentiq-v2-tip-chunked-full-scope-execution-plan.md",
    "docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md",
    "docs/data/epo-tip-client-usage.md",
]


DEFAULT_TABLE_FAMILIES = ["core", "publications", "legal", "register", "epab", "citations"]
DEFAULT_WORKERS = {
    "core": 2,
    "publications": 2,
    "legal": 1,
    "register": 1,
    "epab": 1,
    "citations": 1,
}
HERITAGE_DEFAULT_TABLE_FAMILIES = ["core", "publications", "citations"]
HERITAGE_DEFAULT_WORKERS = {
    "core": 1,
    "publications": 1,
    "citations": 1,
}


def _year_buckets(start: int, end: int, span: int) -> list[tuple[int, int]]:
    """Return contiguous year buckets between the configured bounds."""
    buckets: list[tuple[int, int]] = []
    current = start
    while current <= end:
        bucket_end = min(current + span - 1, end)
        buckets.append((current, bucket_end))
        current = bucket_end + 1
    return buckets


def _plan_tip_chunked_export(
    settings: BuildSettings,
    *,
    horizon_label: str,
    manifest_name: str,
    stage_name: str,
    summary: str,
    doc_refs: list[str],
    blob_root: str,
) -> StageResult:
    """Generate a TIP-to-Blob chunk plan for one named extraction horizon."""
    execution = settings.execution or {}
    span = int(execution.get("chunk_year_span", 3))
    if horizon_label == "heritage":
        table_families = list(execution.get("heritage_table_families", HERITAGE_DEFAULT_TABLE_FAMILIES))
        workers = {**HERITAGE_DEFAULT_WORKERS, **execution.get("heritage_max_workers", {})}
    else:
        table_families = list(execution.get("table_families", DEFAULT_TABLE_FAMILIES))
        workers = {**DEFAULT_WORKERS, **execution.get("max_workers", {})}
    upload_after_chunk = bool(execution.get("upload_after_chunk", True))
    cleanup_after_upload = bool(execution.get("cleanup_after_upload", True))
    blob_container = settings.azure.get("container", "patentiq-data")

    result = StageResult(
        stage=stage_name,
        status="success",
        summary=summary,
        methods=[
            "Split the configured mega-cluster scope into field and year buckets.",
            "Assigned recommended worker counts per table family according to the documented TIP resource envelope.",
            "Prepared deterministic chunk ids and Blob prefixes for resumable export.",
        ],
        calculations=[
            "Chunk ids are built from field slug + year bucket + table family.",
            "Year buckets use the configured chunk span across the configured ETL year window.",
        ],
        downstream_impacts=[
            "This plan drives Blob-first pre-Bronze extraction instead of monolithic local bounded-raw materialization inside TIP.",
            "Chunk manifests enable resume, retry, and local cleanup after verified upload.",
        ],
        doc_refs=doc_refs,
    )

    chunk_manifest_dir = ensure_dir(settings.manifests_dir / "chunks")
    result.outputs.append(str(chunk_manifest_dir))

    year_buckets = _year_buckets(settings.year_window_start, settings.year_window_end, span)
    chunks: list[dict[str, object]] = []
    for field in settings.selected_wipo_fields:
        field_slug = slugify_value(field)
        for year_start, year_end in year_buckets:
            for table_family in table_families:
                if horizon_label == "heritage":
                    chunk_id = f"heritage__{field_slug}__{year_start}_{year_end}__{table_family}"
                else:
                    chunk_id = f"{field_slug}__{year_start}_{year_end}__{table_family}"
                blob_prefix = (
                    f"{blob_root}/"
                    f"{'patstat' if table_family in {'core', 'publications', 'legal', 'citations'} else table_family}/"
                    f"field={field_slug}/year={year_start}-{year_end}/family={table_family}"
                )
                chunks.append(
                    {
                        "chunk_id": chunk_id,
                        "field": field,
                        "field_slug": field_slug,
                        "year_start": year_start,
                        "year_end": year_end,
                        "horizon_label": horizon_label,
                        "table_family": table_family,
                        "status": "pending",
                        "recommended_worker_count": int(workers.get(table_family, 1)),
                        "upload_after_chunk": upload_after_chunk,
                        "cleanup_after_upload": cleanup_after_upload,
                        "azure_container": blob_container,
                        "blob_prefix": blob_prefix,
                    }
                )

    manifest_path = chunk_manifest_dir / manifest_name
    write_text_json(
        manifest_path,
        {
            "release_id": settings.release_id,
            "scope_type": settings.scope_type,
            "horizon_label": horizon_label,
            "snapshot_date": settings.snapshot_date,
            "tip_env": settings.tip_env,
            "year_window_start": settings.year_window_start,
            "year_window_end": settings.year_window_end,
            "chunk_year_span": span,
            "table_families": table_families,
            "selected_wipo_fields": settings.selected_wipo_fields,
            "max_workers": workers,
            "blob_intermediate_enabled": bool(execution.get("blob_intermediate_enabled", True)),
            "chunks": chunks,
        },
    )
    result.outputs.append(str(manifest_path))
    result.metrics["chunk_plan_field_count"] = len(settings.selected_wipo_fields)
    result.metrics["chunk_plan_year_bucket_count"] = len(year_buckets)
    result.metrics["chunk_plan_table_family_count"] = len(table_families)
    result.metrics["chunk_plan_total_chunk_count"] = len(chunks)
    result.metrics["chunk_plan_max_worker_sum"] = sum(int(workers.get(table_family, 1)) for table_family in table_families)
    return result


def plan_tip_chunked_export(settings: BuildSettings) -> StageResult:
    """Generate the main TIP-to-Blob chunk plan for full-scope extraction."""
    return _plan_tip_chunked_export(
        settings,
        horizon_label="main",
        manifest_name="tip_chunk_plan.json",
        stage_name="tip-chunk-plan",
        summary="Generated the TIP chunked export plan for Blob-first full-scope extraction.",
        doc_refs=DOC_REFS,
        blob_root="raw-bounded",
    )


def plan_tip_heritage_chunked_export(settings: BuildSettings) -> StageResult:
    """Generate the heritage-backfill TIP chunk plan for older mega-cluster families."""
    heritage_settings = replace(
        settings,
        year_window_start=settings.heritage_backfill_start,
        year_window_end=settings.heritage_backfill_end,
    )
    return _plan_tip_chunked_export(
        heritage_settings,
        horizon_label="heritage",
        manifest_name="tip_heritage_chunk_plan.json",
        stage_name="tip-heritage-chunk-plan",
        summary="Generated the TIP heritage-backfill chunk plan for older mega-cluster family and citation support.",
        doc_refs=DOC_REFS + ["docs/next-phase-v2/29-patentiq-v2-two-horizon-scope-and-heritage-backfill-policy.md"],
        blob_root="raw-bounded-heritage",
    )
