from __future__ import annotations

from pathlib import Path

import duckdb

from patentiq_etl.common.io import ensure_dir, parquet_row_count
from patentiq_etl.common.types import BuildSettings
from patentiq_etl.prebronze.repair_epab import repair_epab_for_semantic


def _settings(tmp_path: Path) -> BuildSettings:
    root = tmp_path / "repo"
    return BuildSettings(
        repo_root=root,
        release_id="test-release",
        snapshot_date="2026-03-31",
        year_window_start=2007,
        year_window_end=2026,
        heritage_backfill_start=1996,
        heritage_backfill_end=2006,
        azure_publish_enabled=False,
        vector_sample_pct=0.1,
        active_grant_only_for_semantic=True,
        method_version="test",
        semantic_embedding_method="hash",
        semantic_ann_method="placeholder",
        patstat_source_mode="local_files",
        register_source_mode="local_files",
        epab_source_mode="tip",
        uspto_source_mode="local_files",
        refs_source_mode="local_files",
        tip_env="PROD",
        raw_patstat_dir=root / "etl/data/raw/patstat",
        raw_register_dir=root / "etl/data/raw/register",
        raw_uspto_dir=root / "etl/data/raw/uspto",
        raw_epab_dir=root / "etl/data/raw/epab",
        raw_refs_dir=root / "etl/data/raw/refs",
        bounded_patstat_dir=root / "etl/data/raw-bounded/patstat",
        bounded_register_dir=root / "etl/data/raw-bounded/register",
        bounded_uspto_dir=root / "etl/data/raw-bounded/uspto",
        bounded_epab_dir=root / "etl/data/raw-bounded/epab",
        bounded_refs_dir=root / "etl/data/raw-bounded/refs",
        bounded_seed_dir=root / "etl/data/raw-bounded/_seeds",
        bronze_dir=root / "etl/data/bronze",
        silver_dir=root / "etl/data/silver",
        gold_dir=root / "etl/data/gold",
        ml_dir=root / "etl/data/ml",
        vectors_dir=root / "etl/data/vectors",
        releases_dir=root / "etl/data/releases",
        manifests_dir=root / "etl/manifests",
        journal_path=root / "etl/ETL_IMPLEMENTATION_LOG.md",
        ref_techn_field_ipc=root / "etl/data/raw/refs/wipo_techn_field_ipc.csv",
        scope_type="mega_cluster_bounded",
        field_source="wipo_industry_code",
        selected_wipo_fields=["Computer technology"],
        thresholds={},
        azure={},
        execution={},
    )


def _write_publication_chunk(path: Path, rows: list[tuple[str, str, str, str, str]]) -> None:
    ensure_dir(path.parent)
    values_sql = ", ".join(
        f"('{country}', '{number}', '{kind}', '{pub_date}', '{language}')"
        for country, number, kind, pub_date, language in rows
    )
    con = duckdb.connect()
    con.execute(
        f"""
        copy (
            select
                col0 as "publication.country",
                col1 as "publication.number",
                col2 as "publication.kind",
                col3 as "publication.date",
                col4 as "publication.language"
            from (values {values_sql})
        ) to ? (format parquet, compression zstd)
        """,
        [str(path)],
    )


def _write_claim_chunk(path: Path, claim_rows: list[list[tuple[str | None, str | None, str | None]]]) -> None:
    ensure_dir(path.parent)
    row_sql: list[str] = []
    for claims in claim_rows:
        claim_sql = ", ".join(
            "struct_pack(amendment_statement := "
            + ("NULL::varchar" if amendment is None else f"'{amendment}'")
            + ", language := "
            + ("NULL::varchar" if language is None else f"'{language}'")
            + ", text := "
            + ("NULL::varchar" if text is None else f"'{text}'")
            + ")"
            for amendment, language, text in claims
        )
        row_sql.append(f"([{claim_sql}])")
    con = duckdb.connect()
    con.execute(
        f"copy (select col0 as claims from (values {', '.join(f'({row})' for row in row_sql)})) to ? (format parquet, compression zstd)",
        [str(path)],
    )


def test_repair_epab_for_semantic_salvages_only_safe_claim_chunks(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    safe_root = settings.repo_root / "etl/data/imports/raw-bounded/epab/field=computer-technology/year=2023-2024/family=epab"
    unsafe_root = settings.repo_root / "etl/data/imports/raw-bounded/epab/field=computer-technology/year=2025-2026/family=epab"

    _write_publication_chunk(
        safe_root / "epab_publication.parquet",
        [
            ("EP", "1000001", "A1", "20240101", "EN"),
            ("EP", "1000002", "B1", "20240201", "EN"),
        ],
    )
    _write_claim_chunk(
        safe_root / "epab_claims.parquet",
        [
            [(None, "EN", '<claim id="c-en-0001" num="0001"><claim-text>First claim text.</claim-text></claim>')],
            [(None, "EN", '<claim id="c-en-0001" num="0001"><claim-text>Second claim text.</claim-text></claim>')],
        ],
    )
    _write_publication_chunk(
        unsafe_root / "epab_publication.parquet",
        [("EP", "9999999", "A1", "20250101", "EN")],
    )
    _write_claim_chunk(
        unsafe_root / "epab_claims.parquet",
        [
            [(None, "EN", '<claim id="c-en-0001" num="0001"><claim-text>Unsafe first.</claim-text></claim>')],
            [(None, "EN", '<claim id="c-en-0001" num="0001"><claim-text>Unsafe extra.</claim-text></claim>')],
        ],
    )

    result = repair_epab_for_semantic(settings).finish()

    assert result.status == "success"
    assert result.metrics["epab_chunk_count"] == 2
    assert result.metrics["epab_safe_chunk_count"] == 1
    assert result.metrics["epab_unsafe_chunk_count"] == 1

    publication_out = settings.bounded_epab_dir / "epab_publication.parquet"
    claims_out = settings.bounded_epab_dir / "epab_claims.parquet"
    abstract_out = settings.bounded_epab_dir / "epab_abstract.parquet"

    assert publication_out.exists()
    assert claims_out.exists()
    assert abstract_out.exists()
    assert parquet_row_count(publication_out) == 2
    assert parquet_row_count(claims_out) == 2
    assert parquet_row_count(abstract_out) == 0

    con = duckdb.connect()
    publication_rows = con.execute(
        "select epab_doc_id, publication_number_full, publication_kind from read_parquet(?) order by publication_number_full",
        [str(publication_out)],
    ).fetchall()
    assert publication_rows == [
        ("EP1000001A1", "EP1000001A1", "A1"),
        ("EP1000002B1", "EP1000002B1", "B1"),
    ]

    claim_rows = con.execute(
        "select epab_doc_id, publication_number_full, claim_sequence_no, language_code, claim_text_plain from read_parquet(?) order by publication_number_full",
        [str(claims_out)],
    ).fetchall()
    assert claim_rows == [
        ("EP1000001A1", "EP1000001A1", 1, "EN", "First claim text."),
        ("EP1000002B1", "EP1000002B1", 1, "EN", "Second claim text."),
    ]
