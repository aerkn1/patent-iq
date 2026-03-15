from __future__ import annotations

from pathlib import Path

from patentiq_etl.bronze.source_registry import PATSTAT_TABLES, REFERENCE_TABLES, REGISTER_TABLES
from patentiq_etl.common.io import candidate_files, copy_to_parquet
from patentiq_etl.common.types import BuildSettings, StageResult


def _ingest_table_group(directory: Path, out_dir: Path, table_map: dict[str, list[str]]) -> tuple[list[str], list[str], dict[str, int], list[str]]:
    """Land one logical source family into Bronze parquet files and collect stage metadata."""
    inputs: list[str] = []
    outputs: list[str] = []
    metrics: dict[str, int] = {}
    warnings: list[str] = []

    for logical_name, stems in table_map.items():
        matches = candidate_files(directory, stems)
        if not matches:
            warnings.append(f"Skipped `{logical_name}` because no matching raw file was found.")
            continue
        source_path = matches[0]
        out_path = out_dir / f"{logical_name}.parquet"
        row_count = copy_to_parquet(source_path, out_path)
        inputs.append(str(source_path))
        outputs.append(str(out_path))
        metrics[f"{logical_name}_rows"] = row_count
    return inputs, outputs, metrics, warnings


def ingest_generic_bronze(settings: BuildSettings) -> StageResult:
    """Generate source-faithful Bronze parquet for PATSTAT, Register, and reference inputs."""
    result = StageResult(
        stage="bronze",
        status="success",
        summary="Generated source-faithful Bronze Parquet from PATSTAT, Register, and reference inputs.",
        methods=[
            "Copied raw CSV, compressed CSV, JSONL, and Parquet sources to source-preserving Bronze Parquet.",
            "Preserved source schemas rather than applying downstream family-first normalization in Bronze.",
        ],
        calculations=[
            "Bronze metrics are row-count and file-presence certifications only.",
        ],
        downstream_impacts=[
            "These Bronze parquet tables are the only allowed inputs for bounded scope seeding and all later Silver builds.",
            "Schema drift here propagates into family scope, citation, legal status, and Market Intelligence logic downstream.",
        ],
        doc_refs=[
            "docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md",
            "docs/next-phase-v2/10-patentiq-v2-bronze-silver-gold-knowledge-tree.md",
            "docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md",
        ],
    )

    for directory, table_map in [
        (settings.raw_patstat_dir, PATSTAT_TABLES),
        (settings.raw_register_dir, REGISTER_TABLES),
        (settings.raw_refs_dir, REFERENCE_TABLES),
    ]:
        inputs, outputs, metrics, warnings = _ingest_table_group(directory, settings.bronze_dir, table_map)
        result.inputs.extend(inputs)
        result.outputs.extend(outputs)
        result.metrics.update(metrics)
        result.warnings.extend(warnings)

    result.metrics["bronze_total_row_count"] = sum(
        value for key, value in result.metrics.items() if key.endswith("_rows") and isinstance(value, int)
    )
    return result
