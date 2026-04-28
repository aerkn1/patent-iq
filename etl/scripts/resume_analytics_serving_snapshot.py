from __future__ import annotations

import argparse
from pathlib import Path

import duckdb

from _bootstrap import bootstrap


ETL_ROOT = bootstrap()

from patentiq_etl.common.config import load_settings  # noqa: E402
from patentiq_etl.common.io import ensure_dir, write_text_json  # noqa: E402
from patentiq_etl.common.types import utc_now_iso  # noqa: E402
from patentiq_etl.serving.run import (  # noqa: E402
    _analytics_source_tables,
    _cleanup_dir,
    _copy_source_table,
    _duckdb_size_literal,
    _serving_dir,
    _serving_snapshot_temp_budget_bytes,
    _serving_snapshot_temp_dir,
    _serving_snapshot_threads,
    _snapshot_tables,
    _sql_path_literal,
    _summarize_publication_serving_artifact,
    _summarize_snapshot_path,
)


def _existing_tables(con: duckdb.DuckDBPyConnection) -> set[str]:
    return set(_snapshot_tables(con))


def _resume_analytics_snapshot(analytics_path: Path, settings, *, run_analyze: bool) -> tuple[list[str], list[str]]:
    if not analytics_path.exists():
        raise SystemExit(f"Analytics snapshot does not exist: {analytics_path}")

    analytics_sources = _analytics_source_tables(settings)
    temp_dir = _serving_snapshot_temp_dir(analytics_path)
    warnings: list[str] = []

    _cleanup_dir(temp_dir)
    ensure_dir(temp_dir)

    con = duckdb.connect(str(analytics_path))
    try:
        con.execute("set preserve_insertion_order=false")
        con.execute(f"set threads={_serving_snapshot_threads(settings)}")
        con.execute(f"set temp_directory='{_sql_path_literal(temp_dir)}'")
        con.execute(
            f"set max_temp_directory_size='{_duckdb_size_literal(_serving_snapshot_temp_budget_bytes(settings, temp_dir))}'"
        )

        existing = _existing_tables(con)
        missing_tables = [table_name for table_name in analytics_sources if table_name not in existing]

        for table_name in missing_tables:
            source_path = analytics_sources[table_name]
            print(f"Copying missing analytics table `{table_name}` from {source_path}")
            _copy_source_table(con, source_path, table_name, warnings)

        if run_analyze:
            try:
                print("Running ANALYZE on analytics snapshot")
                con.execute("analyze")
            except Exception as exc:  # pragma: no cover - operational fallback
                warnings.append(f"ANALYZE skipped after manual analytics resume: {exc}")

        print("Running CHECKPOINT on analytics snapshot")
        con.execute("checkpoint")
        final_tables = _snapshot_tables(con)
        return final_tables, warnings
    finally:
        con.close()
        _cleanup_dir(temp_dir)


def _rewrite_serving_metadata(settings, warnings: list[str]) -> None:
    serving_dir = _serving_dir(settings)
    core_path = serving_dir / "core_serving.duckdb"
    analytics_path = serving_dir / "analytics_serving.duckdb"
    semantic_path = serving_dir / "semantic_serving.duckdb"
    market_path = serving_dir / "market_serving.duckdb"
    publication_path = serving_dir / "publication_serving"
    manifest_path = serving_dir / "serving_snapshot_manifest.json"
    audit_path = serving_dir / "serving_snapshot_audit.json"

    core_info = _summarize_snapshot_path(core_path)
    analytics_info = _summarize_snapshot_path(analytics_path)
    semantic_info = _summarize_snapshot_path(semantic_path)
    market_info = _summarize_snapshot_path(market_path)
    publication_info = _summarize_publication_serving_artifact(publication_path) if publication_path.exists() else None

    manifest_snapshots = {
        "core": {
            "filename": core_path.name,
            "tables": core_info["tables"],
            "bytes": core_info["bytes"],
        },
        "analytics": {
            "filename": analytics_path.name,
            "tables": analytics_info["tables"],
            "bytes": analytics_info["bytes"],
        },
        "semantic": {
            "filename": semantic_path.name,
            "tables": semantic_info["tables"],
            "bytes": semantic_info["bytes"],
        },
        "market": {
            "filename": market_path.name,
            "tables": market_info["tables"],
            "bytes": market_info["bytes"],
        },
    }
    if publication_info is not None:
        manifest_snapshots["publication"] = {
            "filename": publication_path.name,
            "tables": publication_info["tables"],
            "bytes": publication_info["bytes"],
        }

    built_at = utc_now_iso()
    manifest_payload = {
        "serving_release": f"{settings.snapshot_date}-serving",
        "contract_version": "1",
        "built_at": built_at,
        "source_gold_release": settings.release_id,
        "snapshots": manifest_snapshots,
    }

    audit_snapshots = {
        "core": {
            "path": str(core_path),
            "bytes": core_info["bytes"],
            "table_stats": core_info["table_stats"],
        },
        "analytics": {
            "path": str(analytics_path),
            "bytes": analytics_info["bytes"],
            "table_stats": analytics_info["table_stats"],
        },
        "semantic": {
            "path": str(semantic_path),
            "bytes": semantic_info["bytes"],
            "table_stats": semantic_info["table_stats"],
        },
        "market": {
            "path": str(market_path),
            "bytes": market_info["bytes"],
            "table_stats": market_info["table_stats"],
        },
    }
    if publication_info is not None:
        audit_snapshots["publication"] = {
            "path": str(publication_path),
            "bytes": publication_info["bytes"],
            "table_stats": publication_info["table_stats"],
        }

    audit_payload = {
        "serving_release": manifest_payload["serving_release"],
        "source_gold_release": settings.release_id,
        "built_at": built_at,
        "snapshots": audit_snapshots,
        "warnings": warnings,
    }

    write_text_json(manifest_path, manifest_payload)
    write_text_json(audit_path, audit_payload)


def main() -> None:
    parser = argparse.ArgumentParser(description="Resume a partially built analytics_serving.duckdb in place.")
    parser.add_argument(
        "--skip-analyze",
        action="store_true",
        help="Skip ANALYZE after copying missing tables. CHECKPOINT and metadata rewrite still run.",
    )
    args = parser.parse_args()

    settings = load_settings(ETL_ROOT)
    serving_dir = _serving_dir(settings)
    analytics_path = serving_dir / "analytics_serving.duckdb"

    final_tables, warnings = _resume_analytics_snapshot(
        analytics_path,
        settings,
        run_analyze=not args.skip_analyze,
    )
    resume_warning = "analytics_serving.duckdb was manually resumed after a disk-full interruption."
    if resume_warning not in warnings:
        warnings.insert(0, resume_warning)
    _rewrite_serving_metadata(settings, warnings)

    print(f"Analytics snapshot completed with {len(final_tables)} tables.")
    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"- {warning}")


if __name__ == "__main__":
    main()
