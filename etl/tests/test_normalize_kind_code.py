from __future__ import annotations

from pathlib import Path

import duckdb

from patentiq_etl.common.io import ensure_dir, write_pylist_parquet
from patentiq_etl.common.types import BuildSettings
from patentiq_etl.prebronze.kind_code import normalize_kind_code


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
        epab_source_mode="local_files",
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


def test_normalize_kind_code_builds_complete_seed_from_observed_pairs(tmp_path: Path) -> None:
    settings = _settings(tmp_path)

    write_pylist_parquet(
        [
            {"pat_publn_id": 1, "appln_id": 10, "publn_auth": "EP", "publn_kind": "B2", "publn_date": "2024-01-01"},
            {"pat_publn_id": 2, "appln_id": 10, "publn_auth": "EP", "publn_kind": "C0", "publn_date": "2025-01-01"},
            {"pat_publn_id": 3, "appln_id": 11, "publn_auth": "US", "publn_kind": "B1", "publn_date": "2023-01-01"},
            {"pat_publn_id": 4, "appln_id": 12, "publn_auth": "CN", "publn_kind": "A1", "publn_date": "2022-01-01"},
            {"pat_publn_id": 5, "appln_id": 13, "publn_auth": "ZZ", "publn_kind": "X1", "publn_date": "2021-01-01"},
        ],
        ensure_dir(settings.bounded_patstat_dir) / "tls211_pat_publn.parquet",
    )

    write_pylist_parquet(
        [
            {
                "jurisdiction_code": "EP",
                "kind_code": "B2",
                "universal_stage": "OPPOSITION_SURVIVOR",
                "stage_multiplier": 4.0,
                "is_enforceable": True,
                "legal_status_proxy": "active_grant",
                "mapping_basis": "MANUAL_OVERRIDE",
                "review_status": "docdb_curated",
                "source_reference": "docdb_manual_v1",
            }
        ],
        ensure_dir(settings.raw_refs_dir) / "kind_code_normalization.parquet",
    )

    result = normalize_kind_code(settings).finish()

    assert result.status == "success"
    assert result.metrics["observed_pair_count"] == 5
    assert result.metrics["auto_generated_pair_count"] == 4
    assert result.metrics["review_queue_pair_count"] == 4

    final_path = settings.raw_refs_dir / "kind_code_normalization.parquet"
    review_queue_path = settings.raw_refs_dir / "kind_code_normalization_review_queue.parquet"
    assert final_path.exists()
    assert review_queue_path.exists()

    con = duckdb.connect()
    rows = con.execute(
        """
        select jurisdiction_code, kind_code, universal_stage, stage_multiplier, is_enforceable, mapping_basis, review_status
        from read_parquet(?)
        where observed_publn_count > 0
        order by jurisdiction_code, kind_code
        """,
        [str(final_path)],
    ).fetchall()
    assert rows == [
        ("CN", "A1", "PENDING_APPLICATION", 0.2, False, "AUTO_PREFIX_RULE", "needs_docdb_review"),
        ("EP", "B2", "OPPOSITION_SURVIVOR", 4.0, True, "MANUAL_OVERRIDE", "docdb_curated"),
        ("EP", "C0", "UNITARY_GRANT", 1.0, True, "AUTO_EP_SPECIAL_RULE", "needs_docdb_review"),
        ("US", "B1", "STANDARD_GRANT", 1.0, True, "AUTO_PREFIX_RULE", "needs_docdb_review"),
        ("ZZ", "X1", "OTHER", 0.0, False, "UNMAPPED_OTHER_AUTO", "unmapped_needs_review"),
    ]

    review_rows = con.execute(
        "select jurisdiction_code, kind_code from read_parquet(?) order by jurisdiction_code, kind_code",
        [str(review_queue_path)],
    ).fetchall()
    assert review_rows == [("CN", "A1"), ("EP", "C0"), ("US", "B1"), ("ZZ", "X1")]


def test_normalize_kind_code_preserves_explicit_override_review_status(tmp_path: Path) -> None:
    settings = _settings(tmp_path)

    write_pylist_parquet(
        [
            {"pat_publn_id": 1, "appln_id": 10, "publn_auth": "TW", "publn_kind": "U", "publn_date": "2024-01-01"},
        ],
        ensure_dir(settings.bounded_patstat_dir) / "tls211_pat_publn.parquet",
    )

    write_pylist_parquet(
        [
            {
                "jurisdiction_code": "TW",
                "kind_code": "U",
                "universal_stage": "STANDARD_GRANT",
                "stage_multiplier": 1.0,
                "is_enforceable": True,
                "legal_status_proxy": "active_grant",
                "mapping_basis": "MANUAL_OVERRIDE",
                "review_status": "office_inferred",
                "source_reference": "tipo_office_guidance",
            }
        ],
        ensure_dir(settings.raw_refs_dir) / "kind_code_normalization_manual_overrides.parquet",
    )

    result = normalize_kind_code(settings).finish()

    assert result.status == "success"

    con = duckdb.connect()
    row = con.execute(
        """
        select jurisdiction_code, kind_code, universal_stage, mapping_basis, review_status
        from read_parquet(?)
        where jurisdiction_code = 'TW' and kind_code = 'U'
        """,
        [str(settings.raw_refs_dir / "kind_code_normalization.parquet")],
    ).fetchone()
    assert row == ("TW", "U", "STANDARD_GRANT", "MANUAL_OVERRIDE", "office_inferred")


def test_normalize_kind_code_preserves_explicit_non_enforceable_stage(tmp_path: Path) -> None:
    settings = _settings(tmp_path)

    write_pylist_parquet(
        [
            {"pat_publn_id": 1, "appln_id": 10, "publn_auth": "GB", "publn_kind": "D0", "publn_date": "2024-01-01"},
        ],
        ensure_dir(settings.bounded_patstat_dir) / "tls211_pat_publn.parquet",
    )

    write_pylist_parquet(
        [
            {
                "jurisdiction_code": "GB",
                "kind_code": "D0",
                "universal_stage": "NON_ENFORCEABLE_PUBLICATION",
                "stage_multiplier": 0.0,
                "is_enforceable": False,
                "legal_status_proxy": "non_enforceable_publication",
                "mapping_basis": "MANUAL_OVERRIDE",
                "review_status": "office_inferred",
                "source_reference": "ukipo_wipo_office_inference",
            }
        ],
        ensure_dir(settings.raw_refs_dir) / "kind_code_normalization_manual_overrides.parquet",
    )

    result = normalize_kind_code(settings).finish()

    assert result.status == "success"

    con = duckdb.connect()
    row = con.execute(
        """
        select jurisdiction_code, kind_code, universal_stage, stage_multiplier, is_enforceable, legal_status_proxy
        from read_parquet(?)
        where jurisdiction_code = 'GB' and kind_code = 'D0'
        """,
        [str(settings.raw_refs_dir / "kind_code_normalization.parquet")],
    ).fetchone()
    assert row == ("GB", "D0", "NON_ENFORCEABLE_PUBLICATION", 0.0, False, "non_enforceable_publication")


def test_normalize_kind_code_preserves_office_curated_and_inferred_stages(tmp_path: Path) -> None:
    settings = _settings(tmp_path)

    write_pylist_parquet(
        [
            {"pat_publn_id": 1, "appln_id": 10, "publn_auth": "CZ", "publn_kind": "U1", "publn_date": "2024-01-01"},
            {"pat_publn_id": 2, "appln_id": 20, "publn_auth": "FI", "publn_kind": "L", "publn_date": "2024-01-02"},
            {"pat_publn_id": 3, "appln_id": 30, "publn_auth": "PT", "publn_kind": "E", "publn_date": "2024-01-03"},
            {"pat_publn_id": 4, "appln_id": 40, "publn_auth": "PT", "publn_kind": "T", "publn_date": "2024-01-04"},
        ],
        ensure_dir(settings.bounded_patstat_dir) / "tls211_pat_publn.parquet",
    )

    write_pylist_parquet(
        [
            {
                "jurisdiction_code": "CZ",
                "kind_code": "U1",
                "universal_stage": "STANDARD_GRANT",
                "stage_multiplier": 1.0,
                "is_enforceable": True,
                "legal_status_proxy": "active_grant",
                "mapping_basis": "MANUAL_OVERRIDE",
                "review_status": "office_curated",
                "source_reference": "czech_utility_model_examples",
            },
            {
                "jurisdiction_code": "FI",
                "kind_code": "L",
                "universal_stage": "PENDING_APPLICATION",
                "stage_multiplier": 0.2,
                "is_enforceable": False,
                "legal_status_proxy": "pending_application",
                "mapping_basis": "MANUAL_OVERRIDE",
                "review_status": "office_curated",
                "source_reference": "wipo_handbook_7_3_2",
            },
            {
                "jurisdiction_code": "PT",
                "kind_code": "E",
                "universal_stage": "STANDARD_GRANT",
                "stage_multiplier": 1.0,
                "is_enforceable": True,
                "legal_status_proxy": "active_grant",
                "mapping_basis": "MANUAL_OVERRIDE",
                "review_status": "office_inferred",
                "source_reference": "pt_ep_validation_inference",
            },
            {
                "jurisdiction_code": "PT",
                "kind_code": "T",
                "universal_stage": "STANDARD_GRANT",
                "stage_multiplier": 1.0,
                "is_enforceable": True,
                "legal_status_proxy": "active_grant",
                "mapping_basis": "MANUAL_OVERRIDE",
                "review_status": "office_inferred",
                "source_reference": "pt_ep_validation_inference",
            },
        ],
        ensure_dir(settings.raw_refs_dir) / "kind_code_normalization_manual_overrides.parquet",
    )

    result = normalize_kind_code(settings).finish()

    assert result.status == "success"

    con = duckdb.connect()
    rows = con.execute(
        """
        select jurisdiction_code, kind_code, universal_stage, review_status
        from read_parquet(?)
        order by jurisdiction_code, kind_code
        """,
        [str(settings.raw_refs_dir / "kind_code_normalization.parquet")],
    ).fetchall()
    assert rows == [
        ("CZ", "U1", "STANDARD_GRANT", "office_curated"),
        ("FI", "L", "PENDING_APPLICATION", "office_curated"),
        ("PT", "E", "STANDARD_GRANT", "office_inferred"),
        ("PT", "T", "STANDARD_GRANT", "office_inferred"),
    ]


def test_normalize_kind_code_preserves_utility_model_and_translation_pairs(tmp_path: Path) -> None:
    settings = _settings(tmp_path)

    write_pylist_parquet(
        [
            {"pat_publn_id": 1, "appln_id": 10, "publn_auth": "BR", "publn_kind": "U2", "publn_date": "2024-01-01"},
            {"pat_publn_id": 2, "appln_id": 20, "publn_auth": "BR", "publn_kind": "Y1", "publn_date": "2024-01-02"},
            {"pat_publn_id": 3, "appln_id": 30, "publn_auth": "DE", "publn_kind": "T1", "publn_date": "2024-01-03"},
            {"pat_publn_id": 4, "appln_id": 40, "publn_auth": "PL", "publn_kind": "U1", "publn_date": "2024-01-04"},
            {"pat_publn_id": 5, "appln_id": 50, "publn_auth": "PL", "publn_kind": "Y1", "publn_date": "2024-01-05"},
            {"pat_publn_id": 6, "appln_id": 60, "publn_auth": "SI", "publn_kind": "T1", "publn_date": "2024-01-06"},
        ],
        ensure_dir(settings.bounded_patstat_dir) / "tls211_pat_publn.parquet",
    )

    write_pylist_parquet(
        [
            {"jurisdiction_code": "BR", "kind_code": "U2", "universal_stage": "PENDING_APPLICATION", "stage_multiplier": 0.2, "is_enforceable": False, "legal_status_proxy": "pending_application", "mapping_basis": "MANUAL_OVERRIDE", "review_status": "office_curated", "source_reference": "br_u2"},
            {"jurisdiction_code": "BR", "kind_code": "Y1", "universal_stage": "STANDARD_GRANT", "stage_multiplier": 1.0, "is_enforceable": True, "legal_status_proxy": "active_grant", "mapping_basis": "MANUAL_OVERRIDE", "review_status": "office_curated", "source_reference": "br_y1"},
            {"jurisdiction_code": "DE", "kind_code": "T1", "universal_stage": "PENDING_APPLICATION", "stage_multiplier": 0.2, "is_enforceable": False, "legal_status_proxy": "pending_application", "mapping_basis": "MANUAL_OVERRIDE", "review_status": "office_curated", "source_reference": "de_t1"},
            {"jurisdiction_code": "PL", "kind_code": "U1", "universal_stage": "PENDING_APPLICATION", "stage_multiplier": 0.2, "is_enforceable": False, "legal_status_proxy": "pending_application", "mapping_basis": "MANUAL_OVERRIDE", "review_status": "office_inferred", "source_reference": "pl_u1"},
            {"jurisdiction_code": "PL", "kind_code": "Y1", "universal_stage": "STANDARD_GRANT", "stage_multiplier": 1.0, "is_enforceable": True, "legal_status_proxy": "active_grant", "mapping_basis": "MANUAL_OVERRIDE", "review_status": "office_inferred", "source_reference": "pl_y1"},
            {"jurisdiction_code": "SI", "kind_code": "T1", "universal_stage": "STANDARD_GRANT", "stage_multiplier": 1.0, "is_enforceable": True, "legal_status_proxy": "active_grant", "mapping_basis": "MANUAL_OVERRIDE", "review_status": "office_inferred", "source_reference": "si_t1"},
        ],
        ensure_dir(settings.raw_refs_dir) / "kind_code_normalization_manual_overrides.parquet",
    )

    result = normalize_kind_code(settings).finish()

    assert result.status == "success"

    con = duckdb.connect()
    rows = con.execute(
        """
        select jurisdiction_code, kind_code, universal_stage, review_status
        from read_parquet(?)
        order by jurisdiction_code, kind_code
        """,
        [str(settings.raw_refs_dir / "kind_code_normalization.parquet")],
    ).fetchall()
    assert rows == [
        ("BR", "U2", "PENDING_APPLICATION", "office_curated"),
        ("BR", "Y1", "STANDARD_GRANT", "office_curated"),
        ("DE", "T1", "PENDING_APPLICATION", "office_curated"),
        ("PL", "U1", "PENDING_APPLICATION", "office_inferred"),
        ("PL", "Y1", "STANDARD_GRANT", "office_inferred"),
        ("SI", "T1", "STANDARD_GRANT", "office_inferred"),
    ]


def test_normalize_kind_code_preserves_ep_validation_and_second_utility_pairs(tmp_path: Path) -> None:
    settings = _settings(tmp_path)

    write_pylist_parquet(
        [
            {"pat_publn_id": 1, "appln_id": 10, "publn_auth": "FI", "publn_kind": "T3", "publn_date": "2024-01-01"},
            {"pat_publn_id": 2, "appln_id": 20, "publn_auth": "HR", "publn_kind": "T1", "publn_date": "2024-01-02"},
            {"pat_publn_id": 3, "appln_id": 30, "publn_auth": "CY", "publn_kind": "T1", "publn_date": "2024-01-03"},
            {"pat_publn_id": 4, "appln_id": 40, "publn_auth": "LT", "publn_kind": "T", "publn_date": "2024-01-04"},
            {"pat_publn_id": 5, "appln_id": 50, "publn_auth": "SK", "publn_kind": "U1", "publn_date": "2024-01-05"},
            {"pat_publn_id": 6, "appln_id": 60, "publn_auth": "SK", "publn_kind": "Y1", "publn_date": "2024-01-06"},
            {"pat_publn_id": 7, "appln_id": 70, "publn_auth": "PH", "publn_kind": "U1", "publn_date": "2024-01-07"},
            {"pat_publn_id": 8, "appln_id": 80, "publn_auth": "PH", "publn_kind": "Y1", "publn_date": "2024-01-08"},
        ],
        ensure_dir(settings.bounded_patstat_dir) / "tls211_pat_publn.parquet",
    )

    write_pylist_parquet(
        [
            {"jurisdiction_code": "FI", "kind_code": "T3", "universal_stage": "STANDARD_GRANT", "stage_multiplier": 1.0, "is_enforceable": True, "legal_status_proxy": "active_grant", "mapping_basis": "MANUAL_OVERRIDE", "review_status": "office_curated", "source_reference": "fi_t3"},
            {"jurisdiction_code": "HR", "kind_code": "T1", "universal_stage": "STANDARD_GRANT", "stage_multiplier": 1.0, "is_enforceable": True, "legal_status_proxy": "active_grant", "mapping_basis": "MANUAL_OVERRIDE", "review_status": "office_inferred", "source_reference": "hr_t1"},
            {"jurisdiction_code": "CY", "kind_code": "T1", "universal_stage": "STANDARD_GRANT", "stage_multiplier": 1.0, "is_enforceable": True, "legal_status_proxy": "active_grant", "mapping_basis": "MANUAL_OVERRIDE", "review_status": "office_inferred", "source_reference": "cy_t1"},
            {"jurisdiction_code": "LT", "kind_code": "T", "universal_stage": "STANDARD_GRANT", "stage_multiplier": 1.0, "is_enforceable": True, "legal_status_proxy": "active_grant", "mapping_basis": "MANUAL_OVERRIDE", "review_status": "office_inferred", "source_reference": "lt_t"},
            {"jurisdiction_code": "SK", "kind_code": "U1", "universal_stage": "PENDING_APPLICATION", "stage_multiplier": 0.2, "is_enforceable": False, "legal_status_proxy": "pending_application", "mapping_basis": "MANUAL_OVERRIDE", "review_status": "office_inferred", "source_reference": "sk_u1"},
            {"jurisdiction_code": "SK", "kind_code": "Y1", "universal_stage": "STANDARD_GRANT", "stage_multiplier": 1.0, "is_enforceable": True, "legal_status_proxy": "active_grant", "mapping_basis": "MANUAL_OVERRIDE", "review_status": "office_inferred", "source_reference": "sk_y1"},
            {"jurisdiction_code": "PH", "kind_code": "U1", "universal_stage": "PENDING_APPLICATION", "stage_multiplier": 0.2, "is_enforceable": False, "legal_status_proxy": "pending_application", "mapping_basis": "MANUAL_OVERRIDE", "review_status": "office_inferred", "source_reference": "ph_u1"},
            {"jurisdiction_code": "PH", "kind_code": "Y1", "universal_stage": "STANDARD_GRANT", "stage_multiplier": 1.0, "is_enforceable": True, "legal_status_proxy": "active_grant", "mapping_basis": "MANUAL_OVERRIDE", "review_status": "office_inferred", "source_reference": "ph_y1"},
        ],
        ensure_dir(settings.raw_refs_dir) / "kind_code_normalization_manual_overrides.parquet",
    )

    result = normalize_kind_code(settings).finish()

    assert result.status == "success"

    con = duckdb.connect()
    rows = con.execute(
        """
        select jurisdiction_code, kind_code, universal_stage, review_status
        from read_parquet(?)
        order by jurisdiction_code, kind_code
        """,
        [str(settings.raw_refs_dir / "kind_code_normalization.parquet")],
    ).fetchall()
    assert rows == [
        ("CY", "T1", "STANDARD_GRANT", "office_inferred"),
        ("FI", "T3", "STANDARD_GRANT", "office_curated"),
        ("HR", "T1", "STANDARD_GRANT", "office_inferred"),
        ("LT", "T", "STANDARD_GRANT", "office_inferred"),
        ("PH", "U1", "PENDING_APPLICATION", "office_inferred"),
        ("PH", "Y1", "STANDARD_GRANT", "office_inferred"),
        ("SK", "U1", "PENDING_APPLICATION", "office_inferred"),
        ("SK", "Y1", "STANDARD_GRANT", "office_inferred"),
    ]


def test_normalize_kind_code_preserves_at_u1_and_es_r1_stages(tmp_path: Path) -> None:
    settings = _settings(tmp_path)

    write_pylist_parquet(
        [
            {"pat_publn_id": 1, "appln_id": 10, "publn_auth": "AT", "publn_kind": "U1", "publn_date": "2024-01-01"},
            {"pat_publn_id": 2, "appln_id": 20, "publn_auth": "ES", "publn_kind": "R1", "publn_date": "2024-01-02"},
        ],
        ensure_dir(settings.bounded_patstat_dir) / "tls211_pat_publn.parquet",
    )

    write_pylist_parquet(
        [
            {"jurisdiction_code": "AT", "kind_code": "U1", "universal_stage": "STANDARD_GRANT", "stage_multiplier": 1.0, "is_enforceable": True, "legal_status_proxy": "active_grant", "mapping_basis": "MANUAL_OVERRIDE", "review_status": "office_inferred", "source_reference": "at_u1"},
            {"jurisdiction_code": "ES", "kind_code": "R1", "universal_stage": "NON_ENFORCEABLE_PUBLICATION", "stage_multiplier": 0.0, "is_enforceable": False, "legal_status_proxy": "non_enforceable_publication", "mapping_basis": "MANUAL_OVERRIDE", "review_status": "office_curated", "source_reference": "es_r1"},
        ],
        ensure_dir(settings.raw_refs_dir) / "kind_code_normalization_manual_overrides.parquet",
    )

    result = normalize_kind_code(settings).finish()

    assert result.status == "success"

    con = duckdb.connect()
    rows = con.execute(
        """
        select jurisdiction_code, kind_code, universal_stage, review_status
        from read_parquet(?)
        order by jurisdiction_code, kind_code
        """,
        [str(settings.raw_refs_dir / "kind_code_normalization.parquet")],
    ).fetchall()
    assert rows == [
        ("AT", "U1", "STANDARD_GRANT", "office_inferred"),
        ("ES", "R1", "NON_ENFORCEABLE_PUBLICATION", "office_curated"),
    ]
