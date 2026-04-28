from __future__ import annotations

import hashlib
import re
from pathlib import Path

import duckdb

from patentiq_etl.common.io import (
    duckdb_connect,
    ensure_dir,
    normalize_ws,
    parquet_row_count,
    sanitize_semantic_text,
    write_pylist_parquet,
)
from patentiq_etl.common.types import BuildSettings, StageResult
from patentiq_etl.prebronze.consolidate import _staging_root


_CLAIM_ID_RE = re.compile(r'<claim[^>]*\bid="([^"]+)"', re.IGNORECASE)
_CLAIM_NUM_RE = re.compile(r'<claim[^>]*\bnum="([^"]+)"', re.IGNORECASE)


def _publication_number_full(authority: str | None, number: str | None, kind: str | None) -> str | None:
    """Return the canonical EP publication number string used across PATSTAT and semantic joins."""
    if not (authority or number or kind):
        return None
    return f"{authority or ''}{number or ''}{kind or ''}" or None


def _normalize_epab_date(value: str | None) -> str | None:
    """Convert compact EPAB dates like `20240626` into ISO `YYYY-MM-DD` strings."""
    if value is None:
        return None
    compact = str(value).replace("-", "").strip()
    if len(compact) == 8 and compact.isdigit():
        return f"{compact[0:4]}-{compact[4:6]}-{compact[6:8]}"
    return normalize_ws(str(value))


def _parse_claim_metadata(raw_text: str | None, fallback_sequence: int) -> tuple[str | None, int]:
    """Extract claim id and sequence number from one raw claim XML payload when present."""
    if not raw_text:
        return None, fallback_sequence
    claim_id_match = _CLAIM_ID_RE.search(raw_text)
    claim_num_match = _CLAIM_NUM_RE.search(raw_text)
    claim_id = claim_id_match.group(1) if claim_id_match else None
    if claim_num_match:
        claim_num = claim_num_match.group(1).strip()
        if claim_num.isdigit():
            return claim_id, int(claim_num)
    return claim_id, fallback_sequence


def _claim_dedupe_key(publication_number_full: str, claim_sequence_no: int, language_code: str | None) -> str:
    """Return a stable narrow dedupe key for repaired claim rows."""
    material = f"{publication_number_full}|{claim_sequence_no}|{(language_code or '').upper()}"
    return hashlib.sha1(material.encode("utf-8")).hexdigest()


def _safe_chunk_roots(staged_epab_root: Path) -> list[Path]:
    """Return chunk roots whose publication and claims row counts align exactly."""
    safe_roots: list[Path] = []
    for publication_path in sorted(staged_epab_root.rglob("epab_publication.parquet")):
        chunk_root = publication_path.parent
        claims_path = chunk_root / "epab_claims.parquet"
        if not claims_path.exists():
            continue
        con = duckdb_connect()
        publication_count = int(con.execute("select count(*) from read_parquet(?)", [str(publication_path)]).fetchone()[0])
        claims_count = int(con.execute("select count(*) from read_parquet(?)", [str(claims_path)]).fetchone()[0])
        if publication_count == claims_count:
            safe_roots.append(chunk_root)
    return safe_roots


def _repair_chunk(chunk_root: Path) -> tuple[list[dict], list[dict]]:
    """Repair one EPAB chunk into semantic-safe publication and claim rows."""
    con = duckdb_connect()
    publication_rows = con.execute(
        """
        select
            cast("publication.country" as varchar) as publication_authority,
            cast("publication.number" as varchar) as publication_number,
            cast("publication.kind" as varchar) as publication_kind,
            cast("publication.date" as varchar) as publication_date,
            cast("publication.language" as varchar) as language_code
        from read_parquet(?)
        """,
        [str(chunk_root / "epab_publication.parquet")],
    ).fetchall()
    claims_rows = con.execute("select claims from read_parquet(?)", [str(chunk_root / "epab_claims.parquet")]).fetchall()

    publication_records: list[dict] = []
    claim_records: list[dict] = []
    seen_publications: set[str] = set()
    seen_claims: set[str] = set()

    for publication_row, claims_row in zip(publication_rows, claims_rows):
        authority, number, kind, publication_date, language_code = publication_row
        publication_number_full = _publication_number_full(authority, number, kind)
        if not publication_number_full:
            continue
        epab_doc_id = publication_number_full
        if publication_number_full not in seen_publications:
            publication_records.append(
                {
                    "epab_doc_id": epab_doc_id,
                    "publication_number_full": publication_number_full,
                    "publication_authority": authority,
                    "publication_number": number,
                    "publication_kind": kind,
                    "publication_date": _normalize_epab_date(publication_date),
                    "language_code": language_code,
                }
            )
            seen_publications.add(publication_number_full)

        claims_payload = claims_row[0] or []
        for idx, claim_payload in enumerate(claims_payload, start=1):
            if not isinstance(claim_payload, dict):
                continue
            raw_text = claim_payload.get("text")
            claim_text_plain = sanitize_semantic_text(raw_text)
            if not claim_text_plain:
                continue
            claim_id, claim_sequence_no = _parse_claim_metadata(raw_text, idx)
            if claim_sequence_no != 1:
                continue
            claim_language = normalize_ws(claim_payload.get("language"))
            dedupe_key = _claim_dedupe_key(publication_number_full, claim_sequence_no, claim_language)
            if dedupe_key in seen_claims:
                continue
            claim_records.append(
                {
                    "_dedupe_key": dedupe_key,
                    "epab_doc_id": epab_doc_id,
                    "publication_number_full": publication_number_full,
                    "claim_id": claim_id or f"{epab_doc_id}::claim1::{(claim_language or 'UNK').upper()}",
                    "claim_sequence_no": claim_sequence_no,
                    "language_code": claim_language,
                    "claim_text_plain": claim_text_plain,
                }
            )
            seen_claims.add(dedupe_key)
    return publication_records, claim_records


def _write_empty_abstract(path: Path) -> int:
    """Overwrite the bounded EPAB abstract file with an empty Bronze-compatible contract."""
    return write_pylist_parquet(
        [],
        path,
        columns=["epab_doc_id", "publication_number_full", "language_code", "abstract_text"],
    )


def _write_empty_claims(path: Path) -> int:
    """Overwrite the bounded EPAB claims file with an empty Bronze-compatible contract."""
    return write_pylist_parquet(
        [],
        path,
        columns=[
            "epab_doc_id",
            "publication_number_full",
            "claim_id",
            "claim_sequence_no",
            "language_code",
            "claim_text_plain",
        ],
    )


def _sql_path_list(paths: list[Path]) -> str:
    """Return one SQL path-list literal for DuckDB parquet readers."""
    return "[" + ", ".join("'" + str(path).replace("'", "''") + "'" for path in paths) + "]"


def _finalize_claims_streaming(
    claim_temp_paths: list[Path],
    *,
    repair_root: Path,
    claims_out: Path,
    batch_size: int = 50000,
) -> tuple[int, int]:
    """Deduplicate repaired claim temp parquet incrementally and write one final claims parquet."""
    part_paths: list[Path] = []
    seen_keys: set[str] = set()
    batch_rows: list[dict] = []
    unique_row_count = 0

    def flush_batch(part_index: int) -> None:
        nonlocal batch_rows
        if not batch_rows:
            return
        out_path = repair_root / f"claims_final_part_{part_index:03d}.parquet"
        write_pylist_parquet(batch_rows, out_path)
        part_paths.append(out_path)
        batch_rows = []

    for claim_path in claim_temp_paths:
        con = duckdb_connect()
        rows = con.execute(
            """
            select
                _dedupe_key,
                epab_doc_id,
                publication_number_full,
                claim_id,
                claim_sequence_no,
                language_code,
                claim_text_plain
            from read_parquet(?)
            """,
            [str(claim_path)],
        ).fetchall()
        for dedupe_key, epab_doc_id, publication_number_full, claim_id, claim_sequence_no, language_code, claim_text_plain in rows:
            if dedupe_key in seen_keys:
                continue
            seen_keys.add(dedupe_key)
            batch_rows.append(
                {
                    "epab_doc_id": epab_doc_id,
                    "publication_number_full": publication_number_full,
                    "claim_id": claim_id,
                    "claim_sequence_no": claim_sequence_no,
                    "language_code": language_code,
                    "claim_text_plain": claim_text_plain,
                }
            )
            unique_row_count += 1
            if len(batch_rows) >= batch_size:
                flush_batch(len(part_paths) + 1)

    flush_batch(len(part_paths) + 1)
    if not part_paths:
        return _write_empty_claims(claims_out), 0

    con = duckdb_connect()
    con.execute(
        f"copy (select * from read_parquet({_sql_path_list(part_paths)}, union_by_name=true)) to ? (format parquet, compression zstd)",
        [str(claims_out)],
    )
    return parquet_row_count(claims_out), len(seen_keys)


def repair_epab_for_semantic(settings: BuildSettings) -> StageResult:
    """Repair the staged EPAB chunk parquet into Bronze-compatible semantic-support files."""
    result = StageResult(
        stage="repair-epab-for-semantic",
        status="success",
        summary="Repaired the staged EPAB chunk parquet into a deterministic semantic-support subset without rerunning raw EPAB extraction.",
        methods=[
            "Used only EPAB chunk folders whose publication and claims row counts aligned exactly, which allows deterministic row-order pairing.",
            "Derived `publication_number_full` and synthetic `epab_doc_id` keys from EP publication rows, then retained only claim-1 payloads for semantic representative-text use.",
            "Dropped unreliable EPAB abstract payloads and kept PATSTAT abstracts as the universal semantic fallback.",
        ],
        calculations=[
            "Safe EPAB repairability is measured from publication/claims row-count alignment per chunk.",
            "Final EPAB publication rows are deduplicated by `publication_number_full`; final EPAB claims are deduplicated by a stable hash over publication, language, sequence, and text.",
            "This stage intentionally produces a semantic-oriented EPAB subset, not a full historical EPAB restoration.",
        ],
        downstream_impacts=[
            "Bronze can continue using the existing TIP EPAB copy path because the repaired bounded EPAB files are already in Bronze-compatible shape.",
            "Silver semantic representative-text generation can recover EPAB claim-1 coverage where repair is deterministic and fall back to PATSTAT abstracts elsewhere.",
        ],
        doc_refs=[
            "docs/next-phase-v2/16-patentiq-v2-semantic-search-and-comparison-flow-and-guardrails.md",
            "docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md",
        ],
    )

    staged_epab_root = _staging_root(settings) / "raw-bounded" / "epab"
    result.artifacts["staged_epab_root"] = str(staged_epab_root)
    if not staged_epab_root.exists():
        result.status = "failed"
        result.warnings.append("Staged EPAB chunk parquet is missing. Run `consolidate_before_bronze` first.")
        return result

    safe_roots = _safe_chunk_roots(staged_epab_root)
    total_roots = sorted(path.parent for path in staged_epab_root.rglob("epab_publication.parquet"))
    result.metrics["epab_chunk_count"] = len(total_roots)
    result.metrics["epab_safe_chunk_count"] = len(safe_roots)
    result.metrics["epab_unsafe_chunk_count"] = max(len(total_roots) - len(safe_roots), 0)
    if not safe_roots:
        result.status = "degraded"
        result.warnings.append("No EPAB chunk roots could be repaired deterministically from staged publication/claims parquet.")
        return result

    repair_root = ensure_dir(settings.repo_root / "etl" / "data" / "temp" / "epab-semantic-repair")
    for stale_path in repair_root.glob("*.parquet"):
        stale_path.unlink()
    publication_temp_paths: list[Path] = []
    claim_temp_paths: list[Path] = []
    repaired_publication_rows = 0
    repaired_claim_rows = 0

    for index, chunk_root in enumerate(safe_roots, start=1):
        publication_rows, claim_rows = _repair_chunk(chunk_root)
        repaired_publication_rows += len(publication_rows)
        repaired_claim_rows += len(claim_rows)
        publication_temp = repair_root / f"publication_chunk_{index:03d}.parquet"
        claims_temp = repair_root / f"claims_chunk_{index:03d}.parquet"
        if publication_rows:
            write_pylist_parquet(publication_rows, publication_temp)
            publication_temp_paths.append(publication_temp)
        if claim_rows:
            write_pylist_parquet(claim_rows, claims_temp)
            claim_temp_paths.append(claims_temp)

    result.metrics["epab_repaired_publication_row_count_pre_dedupe"] = repaired_publication_rows
    result.metrics["epab_repaired_claim1_row_count_pre_dedupe"] = repaired_claim_rows

    ensure_dir(settings.bounded_epab_dir)
    publication_out = settings.bounded_epab_dir / "epab_publication.parquet"
    claims_out = settings.bounded_epab_dir / "epab_claims.parquet"
    abstract_out = settings.bounded_epab_dir / "epab_abstract.parquet"
    for path in [publication_out, claims_out, abstract_out]:
        if path.exists():
            path.unlink()

    con = duckdb_connect()
    con.execute("set threads=1")
    con.execute("set preserve_insertion_order=false")

    if publication_temp_paths:
        pub_sql = _sql_path_list(publication_temp_paths)
        con.execute(
            f"""
            copy (
                select
                    any_value(epab_doc_id) as epab_doc_id,
                    publication_number_full,
                    any_value(publication_authority) as publication_authority,
                    any_value(publication_number) as publication_number,
                    any_value(publication_kind) as publication_kind,
                    any_value(publication_date) as publication_date,
                    any_value(language_code) as language_code
                from read_parquet({pub_sql}, union_by_name=true)
                group by publication_number_full
            ) to ? (format parquet, compression zstd)
            """,
            [str(publication_out)],
        )
    if claim_temp_paths:
        claims_written, dedupe_key_count = _finalize_claims_streaming(
            claim_temp_paths,
            repair_root=repair_root,
            claims_out=claims_out,
        )
        result.metrics["epab_repaired_claim_dedupe_key_count"] = dedupe_key_count
        result.metrics["epab_repaired_claim1_row_count"] = claims_written
    _write_empty_abstract(abstract_out)

    if publication_out.exists():
        result.outputs.append(str(publication_out))
        result.metrics["epab_repaired_publication_row_count"] = parquet_row_count(publication_out)
    if claims_out.exists():
        result.outputs.append(str(claims_out))
        result.metrics["epab_repaired_claim1_row_count"] = parquet_row_count(claims_out)
    result.outputs.append(str(abstract_out))
    result.metrics["epab_repaired_abstract_row_count"] = parquet_row_count(abstract_out)

    result.inputs.extend([str(path) for path in publication_temp_paths[:1] + claim_temp_paths[:1]])
    result.artifacts["repair_temp_root"] = str(repair_root)
    if result.metrics.get("epab_safe_chunk_count", 0) < result.metrics.get("epab_chunk_count", 0):
        result.warnings.append(
            f"Skipped {result.metrics['epab_unsafe_chunk_count']} EPAB chunk roots whose publication/claims row counts did not align."
        )
    result.warnings.append("EPAB abstracts were intentionally neutralized; PATSTAT abstracts remain the semantic fallback.")
    return result
