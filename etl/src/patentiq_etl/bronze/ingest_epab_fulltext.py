from __future__ import annotations

from datetime import date
from pathlib import Path
import json
import duckdb

from patentiq_etl.common.io import normalize_ws, write_pylist_parquet
from patentiq_etl.common.types import BuildSettings, StageResult


def _iter_records(raw_dir: Path) -> list[dict]:
    """Load EPAB JSON or JSONL payloads from disk into a unified record list."""
    records: list[dict] = []
    for path in list(raw_dir.glob("*.jsonl")) + list(raw_dir.glob("*.json")):
        with path.open("r", encoding="utf-8") as handle:
            if path.suffix == ".jsonl":
                for line in handle:
                    line = line.strip()
                    if line:
                        records.append(json.loads(line))
            else:
                payload = json.load(handle)
                if isinstance(payload, list):
                    records.extend(payload)
                else:
                    records.append(payload)
    return records


def _date(text: str | None) -> date | None:
    """Parse EPAB date strings in `YYYY-MM-DD` or compact `YYYYMMDD` form."""
    if not text:
        return None
    compact = text.replace("-", "")
    if len(compact) != 8 or not compact.isdigit():
        return None
    return date(int(compact[0:4]), int(compact[4:6]), int(compact[6:8]))


def _copy_tip_group(source_path: Path, out_path: Path) -> int:
    """Copy one TIP-derived EPAB parquet group into the Bronze layer."""
    con = duckdb.connect()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    con.execute("copy (select * from read_parquet(?)) to ? (format parquet, compression zstd)", [str(source_path), str(out_path)])
    return int(con.execute("select count(*) from read_parquet(?)", [str(out_path)]).fetchone()[0])


def _ingest_tip_epab_extracts(settings: BuildSettings, result: StageResult) -> StageResult:
    """Promote TIP-derived EPAB bounded parquet groups into Bronze EPAB tables."""
    mapping = {
        "epab_publication.parquet": "bronze_epab_publication.parquet",
        "epab_application.parquet": "bronze_epab_application.parquet",
        "epab_abstract.parquet": "bronze_epab_abstract.parquet",
        "epab_claims.parquet": "bronze_epab_claims.parquet",
        "epab_pct.parquet": "bronze_epab_pct.parquet",
        "epab_designated_states.parquet": "bronze_epab_designated_states.parquet",
        "epab_priority_links.parquet": "bronze_epab_priority_links.parquet",
        "epab_parent_links.parquet": "bronze_epab_parent_links.parquet",
        "epab_divisional_links.parquet": "bronze_epab_divisional_links.parquet",
        "epab_applicants.parquet": "bronze_epab_applicants.parquet",
        "epab_inventors.parquet": "bronze_epab_inventors.parquet",
        "epab_representative.parquet": "bronze_epab_representative.parquet",
    }
    publication_source = settings.bounded_epab_dir / "epab_publication.parquet"
    document_out = settings.bronze_dir / "bronze_epab_document.parquet"
    if publication_source.exists():
        result.metrics["bronze_epab_document_rows"] = _copy_tip_group(publication_source, document_out)
        result.outputs.append(str(document_out))
        result.inputs.append(str(publication_source))
    else:
        result.status = "degraded"
        result.warnings.append("TIP EPAB extraction did not produce publication.parquet, so Bronze EPAB document output was skipped.")

    for source_name, bronze_name in mapping.items():
        source_path = settings.bounded_epab_dir / source_name
        if not source_path.exists():
            continue
        out_path = settings.bronze_dir / bronze_name
        result.metrics[out_path.stem + "_rows"] = _copy_tip_group(source_path, out_path)
        result.outputs.append(str(out_path))
        result.inputs.append(str(source_path))
    return result


def ingest_epab_fulltext(settings: BuildSettings) -> StageResult:
    """Parse raw EPAB payloads into schema-aligned Bronze parquet text-provider tables."""
    result = StageResult(
        stage="bronze-epab-fulltext",
        status="success",
        summary="Parsed EPAB payloads into Bronze text-provider tables for semantic workflows.",
        methods=[
            "Parsed EPAB publication/application anchors, abstracts, and claims from JSON payloads.",
            "Preserved language and sequence fields for English-claim selection and abstract fallback.",
        ],
        calculations=[
            "Bronze EPAB is source-faithful and does not replace PATSTAT/Register metadata for analytical truth.",
        ],
        downstream_impacts=[
            "These Bronze tables feed EP grant claim selection, abstract fallback, and Data Room transparency outputs.",
            "They must remain text-provider tables and not become the canonical source for classifications or parties in downstream analytics.",
        ],
        doc_refs=[
            "docs/data/ep-full-text-publication-database-schema.md",
            "docs/new-feature-ideas/semantic-similarity-and-vector-layer-requirements.md",
            "docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md",
        ],
    )

    if settings.epab_source_mode == "tip":
        return _ingest_tip_epab_extracts(settings, result)

    records = _iter_records(settings.bounded_epab_dir)
    result.inputs.extend([str(path) for path in settings.bounded_epab_dir.glob("*.json*")])
    if not records:
        result.status = "degraded"
        result.warnings.append("No EPAB JSON payloads were found for Bronze parsing.")
        return result

    documents: list[dict] = []
    publications: list[dict] = []
    applications: list[dict] = []
    pct_rows: list[dict] = []
    designated_state_rows: list[dict] = []
    priority_rows: list[dict] = []
    parent_rows: list[dict] = []
    divisional_rows: list[dict] = []
    applicant_rows: list[dict] = []
    inventor_rows: list[dict] = []
    representative_rows: list[dict] = []
    abstracts: list[dict] = []
    claims: list[dict] = []

    for rec in records:
        epab_doc_id = rec.get("epab_doc_id")
        pub = rec.get("publication") or {}
        app = rec.get("application") or {}
        abs_rec = rec.get("abstract") or {}

        documents.append(
            {
                "epab_doc_id": epab_doc_id,
                "publication_number_full": pub.get("publication_number_full") or pub.get("number"),
                "application_number_full": app.get("application_number_full") or app.get("number"),
                "publication_kind": pub.get("kind"),
                "publication_date": _date(pub.get("date")),
            }
        )
        publications.append(
            {
                "epab_doc_id": epab_doc_id,
                "publication_authority": pub.get("authority"),
                "publication_number": pub.get("number"),
                "publication_kind": pub.get("kind"),
                "publication_date": _date(pub.get("date")),
            }
        )
        applications.append(
            {
                "epab_doc_id": epab_doc_id,
                "application_authority": app.get("authority"),
                "application_number": app.get("number"),
                "filing_date": _date(app.get("filing_date")),
            }
        )
        pct = rec.get("pct") or {}
        if pct:
            pct_rows.append(
                {
                    "epab_doc_id": epab_doc_id,
                    "pct_number": pct.get("number"),
                    "pct_authority": pct.get("authority"),
                    "pct_filing_date": _date(pct.get("filing_date")),
                }
            )
        designated_states = rec.get("designated_states") or {}
        for state in designated_states.get("states", []) if isinstance(designated_states, dict) else []:
            designated_state_rows.append(
                {
                    "epab_doc_id": epab_doc_id,
                    "designated_state": state,
                }
            )
        for priority in rec.get("priority", []):
            priority_rows.append({"epab_doc_id": epab_doc_id, **priority})
        for parent in rec.get("parent", []):
            parent_rows.append({"epab_doc_id": epab_doc_id, **parent})
        for divisional in rec.get("divisional", []):
            divisional_rows.append({"epab_doc_id": epab_doc_id, **divisional})
        for applicant in rec.get("applicant", []):
            applicant_rows.append({"epab_doc_id": epab_doc_id, **applicant})
        for inventor in rec.get("inventor", []):
            inventor_rows.append({"epab_doc_id": epab_doc_id, **inventor})
        representative = rec.get("representative")
        if representative:
            representative_rows.append({"epab_doc_id": epab_doc_id, **representative})
        if abs_rec:
            abstracts.append(
                {
                    "epab_doc_id": epab_doc_id,
                    "language_code": abs_rec.get("language"),
                    "abstract_text": normalize_ws(abs_rec.get("text")),
                }
            )
        for claim in rec.get("claims", []):
            claims.append(
                {
                    "epab_doc_id": epab_doc_id,
                    "claim_id": claim.get("claim_id"),
                    "claim_sequence_no": claim.get("sequence_no"),
                    "language_code": claim.get("language"),
                    "claim_text_plain": normalize_ws(claim.get("text")),
                }
            )

    outputs = {
        settings.bronze_dir / "bronze_epab_document.parquet": documents,
        settings.bronze_dir / "bronze_epab_publication.parquet": publications,
        settings.bronze_dir / "bronze_epab_application.parquet": applications,
        settings.bronze_dir / "bronze_epab_pct.parquet": pct_rows,
        settings.bronze_dir / "bronze_epab_designated_states.parquet": designated_state_rows,
        settings.bronze_dir / "bronze_epab_priority_links.parquet": priority_rows,
        settings.bronze_dir / "bronze_epab_parent_links.parquet": parent_rows,
        settings.bronze_dir / "bronze_epab_divisional_links.parquet": divisional_rows,
        settings.bronze_dir / "bronze_epab_applicants.parquet": applicant_rows,
        settings.bronze_dir / "bronze_epab_inventors.parquet": inventor_rows,
        settings.bronze_dir / "bronze_epab_representative.parquet": representative_rows,
        settings.bronze_dir / "bronze_epab_abstract.parquet": abstracts,
        settings.bronze_dir / "bronze_epab_claims.parquet": claims,
    }
    output_columns = {
        settings.bronze_dir / "bronze_epab_document.parquet": [
            "epab_doc_id",
            "publication_number_full",
            "application_number_full",
            "publication_kind",
            "publication_date",
        ],
        settings.bronze_dir / "bronze_epab_publication.parquet": [
            "epab_doc_id",
            "publication_authority",
            "publication_number",
            "publication_kind",
            "publication_date",
        ],
        settings.bronze_dir / "bronze_epab_application.parquet": [
            "epab_doc_id",
            "application_authority",
            "application_number",
            "filing_date",
        ],
        settings.bronze_dir / "bronze_epab_pct.parquet": ["epab_doc_id", "pct_number", "pct_authority", "pct_filing_date"],
        settings.bronze_dir / "bronze_epab_designated_states.parquet": ["epab_doc_id", "designated_state"],
        settings.bronze_dir / "bronze_epab_priority_links.parquet": ["epab_doc_id"],
        settings.bronze_dir / "bronze_epab_parent_links.parquet": ["epab_doc_id"],
        settings.bronze_dir / "bronze_epab_divisional_links.parquet": ["epab_doc_id"],
        settings.bronze_dir / "bronze_epab_applicants.parquet": ["epab_doc_id"],
        settings.bronze_dir / "bronze_epab_inventors.parquet": ["epab_doc_id"],
        settings.bronze_dir / "bronze_epab_representative.parquet": ["epab_doc_id"],
        settings.bronze_dir / "bronze_epab_abstract.parquet": ["epab_doc_id", "language_code", "abstract_text"],
        settings.bronze_dir / "bronze_epab_claims.parquet": ["epab_doc_id", "claim_id", "claim_sequence_no", "language_code", "claim_text_plain"],
    }
    for out_path, rows in outputs.items():
        result.metrics[f"{out_path.stem}_rows"] = write_pylist_parquet(rows, out_path, columns=output_columns[out_path])
        result.outputs.append(str(out_path))
    result.metrics["epab_total_parsed_rows"] = sum(
        value for key, value in result.metrics.items() if key.startswith("bronze_epab_") and key.endswith("_rows")
    )
    return result
