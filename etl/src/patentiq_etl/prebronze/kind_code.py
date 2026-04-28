from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

from patentiq_etl.common.io import candidate_files, ensure_dir, parquet_columns
from patentiq_etl.common.types import BuildSettings, StageResult


LOGGER = logging.getLogger(__name__)

FINAL_COLUMNS = [
    "jurisdiction_code",
    "kind_code",
    "universal_stage",
    "stage_multiplier",
    "is_enforceable",
    "legal_status_proxy",
    "mapping_basis",
    "review_status",
    "source_reference",
    "observed_publn_count",
    "first_seen_publn_date",
    "last_seen_publn_date",
]


def _read_table(path: Path) -> pd.DataFrame:
    if path.suffix == ".parquet":
        con = duckdb.connect()
        cursor = con.execute("select * from read_parquet(?)", [str(path)])
        columns = [column[0] for column in cursor.description]
        return pd.DataFrame.from_records(cursor.fetchall(), columns=columns)
    if path.suffix in {".csv", ".gz"} or path.name.endswith(".csv.gz"):
        return pd.read_csv(path)
    raise ValueError(f"Unsupported kind-code seed format: {path}")


def _write_frame_parquet(frame: pd.DataFrame, out_path: Path) -> None:
    ensure_dir(out_path.parent)
    con = duckdb.connect()
    con.register("frame_view", frame)
    con.execute("copy (select * from frame_view) to ? (format parquet, compression zstd)", [str(out_path)])


def _candidate_ref_path(directory: Path, stems: list[str]) -> Path | None:
    matches = candidate_files(directory, stems)
    return matches[0] if matches else None


def _normalize_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return False
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    return text in {"1", "true", "t", "yes", "y"}


def _normalize_seed_frame(frame: pd.DataFrame) -> pd.DataFrame:
    alias_map = {
        "jurisdiction_code": ["jurisdiction_code", "country_code", "auth"],
        "kind_code": ["kind_code", "publn_kind", "kind"],
        "universal_stage": ["universal_stage", "stage"],
        "stage_multiplier": ["stage_multiplier", "weight"],
        "is_enforceable": ["is_enforceable", "enforceable"],
        "legal_status_proxy": ["legal_status_proxy", "status_proxy"],
        "mapping_basis": ["mapping_basis"],
        "review_status": ["review_status"],
        "source_reference": ["source_reference"],
    }
    lowered = {column.lower(): column for column in frame.columns}
    normalized: dict[str, pd.Series] = {}
    for target, candidates in alias_map.items():
        source = next((lowered[candidate.lower()] for candidate in candidates if candidate.lower() in lowered), None)
        if source is None:
            normalized[target] = pd.Series([None] * len(frame))
        else:
            normalized[target] = frame[source]
    out = pd.DataFrame(normalized)
    out["jurisdiction_code"] = out["jurisdiction_code"].astype("string").str.upper().str.strip()
    out["kind_code"] = out["kind_code"].astype("string").str.upper().str.strip()
    out["universal_stage"] = out["universal_stage"].astype("string").str.upper().str.strip()
    out["legal_status_proxy"] = out["legal_status_proxy"].astype("string").str.lower().str.strip()
    out["stage_multiplier"] = pd.to_numeric(out["stage_multiplier"], errors="coerce").fillna(0.0)
    out["is_enforceable"] = out["is_enforceable"].map(_normalize_bool)
    out["mapping_basis"] = out["mapping_basis"].astype("string").fillna("SEEDED_INPUT")
    out["review_status"] = out["review_status"].astype("string").fillna("seeded_unreviewed")
    out["source_reference"] = out["source_reference"].astype("string").fillna("seed_input")
    out = out.dropna(subset=["jurisdiction_code", "kind_code"])
    out = out[out["jurisdiction_code"] != ""]
    out = out[out["kind_code"] != ""]
    return out.drop_duplicates(subset=["jurisdiction_code", "kind_code"], keep="last").reset_index(drop=True)


def _generate_mapping(jurisdiction_code: str, kind_code: str) -> dict[str, Any]:
    if jurisdiction_code == "EP" and kind_code == "C0":
        return {
            "universal_stage": "UNITARY_GRANT",
            "stage_multiplier": 1.0,
            "is_enforceable": True,
            "legal_status_proxy": "active_grant",
            "mapping_basis": "AUTO_EP_SPECIAL_RULE",
            "review_status": "needs_docdb_review",
            "source_reference": "EP_C0_SPECIAL_RULE",
        }
    if jurisdiction_code == "EP" and kind_code == "B2":
        return {
            "universal_stage": "OPPOSITION_SURVIVOR",
            "stage_multiplier": 3.0,
            "is_enforceable": True,
            "legal_status_proxy": "active_grant",
            "mapping_basis": "AUTO_EP_SPECIAL_RULE",
            "review_status": "needs_docdb_review",
            "source_reference": "EP_B2_SPECIAL_RULE",
        }
    if kind_code.startswith("A"):
        return {
            "universal_stage": "PENDING_APPLICATION",
            "stage_multiplier": 0.2,
            "is_enforceable": False,
            "legal_status_proxy": "pending_application",
            "mapping_basis": "AUTO_PREFIX_RULE",
            "review_status": "needs_docdb_review",
            "source_reference": "PREFIX_A",
        }
    if kind_code.startswith("B"):
        return {
            "universal_stage": "STANDARD_GRANT",
            "stage_multiplier": 1.0,
            "is_enforceable": True,
            "legal_status_proxy": "active_grant",
            "mapping_basis": "AUTO_PREFIX_RULE",
            "review_status": "needs_docdb_review",
            "source_reference": "PREFIX_B",
        }
    if kind_code.startswith("C"):
        return {
            "universal_stage": "POST_GRANT_MODIFIER",
            "stage_multiplier": 0.8,
            "is_enforceable": False,
            "legal_status_proxy": "post_grant_modifier",
            "mapping_basis": "AUTO_PREFIX_RULE",
            "review_status": "needs_docdb_review",
            "source_reference": "PREFIX_C",
        }
    return {
        "universal_stage": "OTHER",
        "stage_multiplier": 0.0,
        "is_enforceable": False,
        "legal_status_proxy": "other",
        "mapping_basis": "UNMAPPED_OTHER_AUTO",
        "review_status": "unmapped_needs_review",
        "source_reference": "UNMAPPED",
    }


def normalize_kind_code(settings: BuildSettings) -> StageResult:
    """Normalize and audit kind-code semantics from consolidated PATSTAT publication coverage before Bronze."""
    result = StageResult(
        stage="normalize-kind-code",
        status="success",
        summary="Completed the pre-Bronze kind-code normalization seed from observed publication kinds, preserved manual rows, and emitted a review queue for remaining DOCDB curation work.",
        methods=[
            "Read the consolidated PATSTAT publication table and aggregated the observed `(publn_auth, publn_kind)` pairs inside the local bounded universe.",
            "Preserved existing kind-code seed rows from `etl/data/raw/refs` and overlaid any explicit manual overrides when present.",
            "Filled missing observed pairs with deterministic office-aware or prefix-aware rules so Bronze can ingest a complete normalization seed before Silver.",
        ],
        calculations=[
            "Observed pair counts and first/last seen dates are computed from the consolidated `tls211_pat_publn` table.",
            "EP `B2` is elevated to `OPPOSITION_SURVIVOR` and EP `C0` to `UNITARY_GRANT`; remaining missing pairs use prefix-based defaults.",
        ],
        downstream_impacts=[
            "This stage replaces ad hoc Silver runtime fallback with an explicit raw reference seed that Bronze can ingest deterministically.",
            "Any remaining `OTHER` or auto-generated rows are surfaced in a review queue before Bronze/Silver rather than being hidden in downstream logic.",
        ],
        doc_refs=[
            "docs/new-feature-ideas/kind-code-normalization-and-tiered-market-weighting-build-guide.md",
            "docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md",
            "docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md",
        ],
    )

    publn_path = settings.bounded_patstat_dir / "tls211_pat_publn.parquet"
    seed_path = settings.raw_refs_dir / "kind_code_normalization.parquet"
    observed_path = settings.raw_refs_dir / "kind_code_normalization_observed_pairs.parquet"
    review_queue_path = settings.raw_refs_dir / "kind_code_normalization_review_queue.parquet"

    result.inputs.append(str(publn_path))
    if not publn_path.exists():
        result.status = "failed"
        result.warnings.append("`tls211_pat_publn.parquet` must exist in the canonical bounded PATSTAT directory before kind-code normalization can run.")
        return result

    ensure_dir(settings.raw_refs_dir)
    seed_input_path = _candidate_ref_path(settings.raw_refs_dir, ["kind_code_normalization", "kind_code_normalization_seed"])
    override_path = _candidate_ref_path(settings.raw_refs_dir, ["kind_code_normalization_manual_overrides", "kind_code_normalization_overrides"])
    if seed_input_path is not None:
        result.inputs.append(str(seed_input_path))
    if override_path is not None:
        result.inputs.append(str(override_path))

    publn_cols = parquet_columns(publn_path)
    lowered = {column.lower(): column for column in publn_cols}
    publn_auth = lowered.get("publn_auth")
    publn_kind = lowered.get("publn_kind")
    publn_date = lowered.get("publn_date")
    if publn_auth is None or publn_kind is None:
        result.status = "failed"
        result.warnings.append("The consolidated PATSTAT publication table is missing `publn_auth` or `publn_kind`.")
        return result

    con = duckdb.connect()
    observed = con.execute(
        f"""
        select
            upper(trim(cast({publn_auth} as varchar))) as jurisdiction_code,
            upper(trim(cast({publn_kind} as varchar))) as kind_code,
            count(*) as observed_publn_count,
            cast(min(try_cast({publn_date} as date)) as varchar) as first_seen_publn_date,
            cast(max(try_cast({publn_date} as date)) as varchar) as last_seen_publn_date
        from read_parquet('{publn_path}')
        where {publn_auth} is not null
          and {publn_kind} is not null
          and trim(cast({publn_kind} as varchar)) <> ''
        group by 1, 2
        order by 1, 2
        """
    ).fetchdf()

    if observed.empty:
        result.status = "failed"
        result.warnings.append("No observed `(publn_auth, publn_kind)` pairs were found in the consolidated publication table.")
        return result

    _write_frame_parquet(observed, observed_path)
    result.outputs.append(str(observed_path))

    seed_frame = pd.DataFrame(columns=["jurisdiction_code", "kind_code", "universal_stage", "stage_multiplier", "is_enforceable", "legal_status_proxy", "mapping_basis", "review_status", "source_reference"])
    if seed_input_path is not None and seed_input_path.exists():
        seed_frame = _normalize_seed_frame(_read_table(seed_input_path))
    if override_path is not None and override_path.exists():
        override_frame = _normalize_seed_frame(_read_table(override_path))
        seed_frame = (
            pd.concat([seed_frame, override_frame], ignore_index=True)
            .drop_duplicates(subset=["jurisdiction_code", "kind_code"], keep="last")
            .reset_index(drop=True)
        )
        override_slice = seed_frame.index[-len(override_frame) :]
        seed_frame.loc[
            override_slice,
            "mapping_basis",
        ] = seed_frame.loc[override_slice, "mapping_basis"].replace({"SEEDED_INPUT": "MANUAL_OVERRIDE"}).fillna("MANUAL_OVERRIDE")
        seed_frame.loc[
            override_slice,
            "review_status",
        ] = seed_frame.loc[override_slice, "review_status"].replace({"seeded_unreviewed": "docdb_curated"}).fillna("docdb_curated")

    seed_lookup = {
        (str(row.jurisdiction_code), str(row.kind_code)): row._asdict()
        for row in seed_frame.itertuples(index=False)
    }

    observed_rows: list[dict[str, Any]] = []
    observed_keys: set[tuple[str, str]] = set()
    auto_generated_count = 0
    for row in observed.itertuples(index=False):
        key = (str(row.jurisdiction_code), str(row.kind_code))
        observed_keys.add(key)
        existing = seed_lookup.get(key)
        if existing is None:
            mapping = _generate_mapping(key[0], key[1])
            auto_generated_count += 1
            base = {
                "jurisdiction_code": key[0],
                "kind_code": key[1],
                **mapping,
            }
        else:
            base = {
                "jurisdiction_code": existing["jurisdiction_code"],
                "kind_code": existing["kind_code"],
                "universal_stage": existing["universal_stage"],
                "stage_multiplier": float(existing["stage_multiplier"]),
                "is_enforceable": _normalize_bool(existing["is_enforceable"]),
                "legal_status_proxy": existing["legal_status_proxy"],
                "mapping_basis": existing["mapping_basis"],
                "review_status": existing["review_status"],
                "source_reference": existing["source_reference"],
            }
        base.update(
            {
                "observed_publn_count": int(row.observed_publn_count),
                "first_seen_publn_date": row.first_seen_publn_date,
                "last_seen_publn_date": row.last_seen_publn_date,
            }
        )
        observed_rows.append(base)

    unobserved_seed_rows: list[dict[str, Any]] = []
    for key, existing in seed_lookup.items():
        if key in observed_keys:
            continue
        unobserved_seed_rows.append(
            {
                "jurisdiction_code": existing["jurisdiction_code"],
                "kind_code": existing["kind_code"],
                "universal_stage": existing["universal_stage"],
                "stage_multiplier": float(existing["stage_multiplier"]),
                "is_enforceable": _normalize_bool(existing["is_enforceable"]),
                "legal_status_proxy": existing["legal_status_proxy"],
                "mapping_basis": existing["mapping_basis"],
                "review_status": existing["review_status"],
                "source_reference": existing["source_reference"],
                "observed_publn_count": 0,
                "first_seen_publn_date": None,
                "last_seen_publn_date": None,
            }
        )

    final_frame = pd.DataFrame(observed_rows + unobserved_seed_rows)
    if final_frame.empty:
        result.status = "failed"
        result.warnings.append("The normalized kind-code seed would be empty.")
        return result

    for column in FINAL_COLUMNS:
        if column not in final_frame.columns:
            final_frame[column] = pd.NA
    final_frame = final_frame[FINAL_COLUMNS].sort_values(
        ["jurisdiction_code", "kind_code", "observed_publn_count"],
        ascending=[True, True, False],
    ).reset_index(drop=True)
    _write_frame_parquet(final_frame, seed_path)
    result.outputs.append(str(seed_path))

    review_queue = final_frame[
        final_frame["review_status"].astype("string").str.lower().isin({"needs_docdb_review", "unmapped_needs_review"})
    ].reset_index(drop=True)
    _write_frame_parquet(review_queue, review_queue_path)
    result.outputs.append(str(review_queue_path))

    result.metrics["observed_pair_count"] = int(len(observed))
    result.metrics["seed_input_pair_count"] = int(len(seed_frame))
    result.metrics["auto_generated_pair_count"] = int(auto_generated_count)
    result.metrics["review_queue_pair_count"] = int(len(review_queue))
    result.metrics["final_pair_count"] = int(len(final_frame))

    if len(review_queue) > 0:
        result.warnings.append(
            "The normalized kind-code seed is operationally complete for Bronze, but some observed pairs still rely on auto-generated or `OTHER` mappings and remain in the review queue."
        )

    return result
