import hashlib
from pathlib import Path

import duckdb

from config.settings import get_settings
from infrastructure.repositories.publication_repository import PublicationRepository


def _publication_bucket(publication_id: str) -> str:
    return hashlib.sha256(publication_id.upper().encode("utf-8")).hexdigest()[:2]


def _numeric_bucket(value: int) -> str:
    return str(abs(int(value)) % 256)


def _write_partition_parquet(
    dataset_root: Path,
    partition_key: str,
    partition_value: str,
    select_sql: str,
) -> None:
    partition_dir = dataset_root / f"{partition_key}={partition_value}"
    partition_dir.mkdir(parents=True, exist_ok=True)
    output_path = partition_dir / "part.parquet"
    with duckdb.connect() as con:
        con.execute(f"COPY ({select_sql}) TO '{output_path}' (FORMAT PARQUET)")


def _write_parquet(path: Path, select_sql: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect() as con:
        con.execute(f"COPY ({select_sql}) TO '{path}' (FORMAT PARQUET)")


def test_publication_repository_prefers_sharded_publication_serving_artifact_for_hot_methods(
    tmp_path: Path,
    monkeypatch,
) -> None:
    serving_dir = tmp_path / "serving"
    publication_path = serving_dir / "publication_serving"
    publication_path.mkdir(parents=True)
    manifest_path = serving_dir / "serving_snapshot_manifest.json"
    manifest_path.write_text(
        """
        {
          "serving_release": "test-serving",
          "contract_version": "1",
          "snapshots": {
            "publication": {
              "filename": "publication_serving",
              "tables": [
                "publication_member_by_number",
                "application_evidence_by_appln",
                "publication_claim_by_number",
                "family_publications_by_family"
              ]
            }
          }
        }
        """.strip(),
        encoding="utf-8",
    )

    publication_bucket = _publication_bucket("EP2606406A1")
    family_bucket = _numeric_bucket(101)
    appln_bucket = _numeric_bucket(11223344)

    _write_partition_parquet(
        publication_path / "publication_member_by_number",
        "publication_bucket",
        publication_bucket,
        """
        select * from (
            values
                (
                    26064061::bigint,
                    11223344::bigint,
                    101::bigint,
                    'EP2606406A1'::varchar,
                    'EP'::varchar,
                    '2606406'::varchar,
                    'A1'::varchar,
                    DATE '2013-07-10',
                    true,
                    false,
                    false,
                    'mega_cluster_bounded'::varchar,
                    '2026-03-15'::varchar,
                    'under_fire'::varchar,
                    'fully_active'::varchar,
                    'under_fire'::varchar,
                    1::bigint,
                    true
                ),
                (
                    26064062::bigint,
                    11223344::bigint,
                    101::bigint,
                    'EP2606406B1'::varchar,
                    'EP'::varchar,
                    '2606406'::varchar,
                    'B1'::varchar,
                    DATE '2018-11-14',
                    false,
                    true,
                    false,
                    'mega_cluster_bounded'::varchar,
                    '2026-03-15'::varchar,
                    'under_fire'::varchar,
                    'fully_active'::varchar,
                    'under_fire'::varchar,
                    1::bigint,
                    true
                )
        ) as t(
            pat_publn_id,
            appln_id,
            docdb_family_id,
            publication_number_full,
            publn_auth,
            publn_nr,
            publn_kind,
            publn_date,
            is_application_stage,
            is_grant_stage,
            is_modifier_stage,
            scope_type,
            snapshot_date,
            family_composite_status,
            mart_family_composite_status,
            effective_family_composite_status,
            active_opposition_application_count,
            opposition_overlay_active
        )
        """,
    )

    _write_partition_parquet(
        publication_path / "application_evidence_by_appln",
        "appln_bucket",
        appln_bucket,
        """
        select * from (
            values (
                11223344::bigint,
                'Signal routing for adaptive network switching'::varchar,
                'en'::varchar,
                'An adaptive routing system for network traffic.'::varchar,
                'en'::varchar,
                DATE '2012-12-19',
                77::bigint,
                true,
                true,
                'Acme Licensing GmbH'::varchar,
                DATE '2026-03-15',
                'pending_examination'::varchar,
                'REGISTER_CORE'::varchar,
                DATE '2026-03-15',
                0.81::double,
                DATE '2014-01-12',
                'EXAM'::varchar,
                'PENDING'::varchar,
                120::bigint,
                false,
                null::varchar,
                null::varchar,
                null::date,
                false,
                null::varchar,
                null::varchar,
                null::varchar,
                false,
                null::varchar,
                'Meyer IP'::varchar,
                'DE'::varchar
            )
        ) as t(
            appln_id,
            title_text,
            title_language_code,
            abstract_text,
            abstract_language_code,
            appln_filing_date,
            reg101_id,
            register_record_present,
            ep_registered_license_flag,
            ep_licensee_names,
            register_snapshot_date,
            ep_display_status_text,
            status_source,
            display_snapshot_date,
            ep_proc_step_maturity_score,
            ep_search_report_mailed_date,
            ep_latest_proc_phase_code,
            ep_latest_proc_result_code,
            ep_proc_time_limit_days,
            ep_register_is_unitary_patent,
            ep_register_up_status_code,
            ep_register_up_status_text,
            ep_register_up_event_latest_date,
            ep_opposition_active,
            ep_opposition_status_text,
            ep_opponent_names,
            ep_opponent_agent_names,
            ep_appeal_active,
            ep_appeal_result_text,
            ep_register_lead_agent_name,
            ep_register_lead_agent_country
        )
        """,
    )

    _write_partition_parquet(
        publication_path / "publication_claim_by_number",
        "publication_bucket",
        publication_bucket,
        """
        select * from (
            values (
                'EP2606406A1'::varchar,
                'A routing apparatus comprising an adaptive signal controller.'::varchar,
                'en'::varchar
            )
        ) as t(
            publication_number_full,
            claim_1_text,
            claim_1_language_code
        )
        """,
    )

    _write_partition_parquet(
        publication_path / "family_publications_by_family",
        "family_bucket",
        family_bucket,
        """
        select * from (
            values
                (
                    101::bigint,
                    'EP2606406A1'::varchar,
                    'EP'::varchar,
                    'A1'::varchar,
                    DATE '2013-07-10',
                    true,
                    false,
                    false
                ),
                (
                    101::bigint,
                    'EP2606406B1'::varchar,
                    'EP'::varchar,
                    'B1'::varchar,
                    DATE '2018-11-14',
                    false,
                    true,
                    false
                )
        ) as t(
            docdb_family_id,
            publication_number_full,
            publn_auth,
            publn_kind,
            publn_date,
            is_application_stage,
            is_grant_stage,
            is_modifier_stage
        )
        """,
    )

    monkeypatch.setenv("PATENTIQ_V2_ARTIFACT_MODE", "local_fs")
    monkeypatch.setenv("PATENTIQ_V2_LOCAL_ARTIFACT_ROOT", str(serving_dir))
    monkeypatch.setenv("PATENTIQ_V2_SERVING_MANIFEST_PATH", str(manifest_path))
    monkeypatch.setenv("PATENTIQ_V2_RAW_PARQUET_FALLBACK_ENABLED", "false")
    get_settings.cache_clear()

    repository = PublicationRepository()

    member = repository.get_publication_member("ep2606406a1")
    title = repository.get_title_for_application(11223344)
    abstract = repository.get_abstract_for_application(11223344)
    claim = repository.get_claim_for_publication("EP2606406A1")
    register = repository.get_register_evidence(11223344)
    related = repository.get_related_family_publications(101, "EP2606406A1", limit=6)
    filing_date = repository.get_filing_date_for_application(11223344)
    family_rows, family_total = repository.get_family_publications(101, limit=10, offset=0)
    family_summary = repository.get_family_publication_summary(101)

    assert repository.artifacts() == [publication_path]
    assert member is not None
    assert member["publication_number_full"] == "EP2606406A1"
    assert member["publn_kind"] == "A1"
    assert title == {"title_text": "Signal routing for adaptive network switching", "language_code": "en"}
    assert abstract == {"abstract_text": "An adaptive routing system for network traffic.", "language_code": "en"}
    assert claim == {
        "claim_text": "A routing apparatus comprising an adaptive signal controller.",
        "language_code": "en",
        "claim_sequence_no": 1,
    }
    assert filing_date == "2012-12-19"
    assert register["register_record_present"] is True
    assert register["ep_register_lead_agent_name"] == "Meyer IP"
    assert len(related) == 1
    assert related[0]["publication_number_full"] == "EP2606406B1"
    assert family_total == 2
    assert len(family_rows) == 2
    assert family_rows[0]["publication_number_full"] == "EP2606406B1"
    assert family_rows[0]["appln_id"] == 11223344
    assert family_summary == {
        "publication_count": 2,
        "application_stage_count": 1,
        "grant_stage_count": 1,
        "modifier_stage_count": 0,
        "office_count": 1,
    }

    get_settings.cache_clear()


def test_publication_repository_does_not_fall_back_to_raw_when_serving_snapshot_is_present(
    tmp_path: Path,
    monkeypatch,
) -> None:
    serving_dir = tmp_path / "serving"
    publication_path = serving_dir / "publication_serving"
    publication_path.mkdir(parents=True)
    etl_data_root = tmp_path / "etl_data"
    manifest_path = serving_dir / "serving_snapshot_manifest.json"
    manifest_path.write_text(
        """
        {
          "serving_release": "test-serving",
          "contract_version": "1",
          "snapshots": {
            "publication": {
              "filename": "publication_serving",
              "tables": [
                "publication_member_by_number",
                "application_evidence_by_appln",
                "publication_claim_by_number"
              ]
            }
          }
        }
        """.strip(),
        encoding="utf-8",
    )

    publication_bucket = _publication_bucket("EP2606406A1")
    appln_bucket = _numeric_bucket(11223344)

    _write_partition_parquet(
        publication_path / "publication_member_by_number",
        "publication_bucket",
        publication_bucket,
        """
        select * from (
            values (
                26064061::bigint,
                11223344::bigint,
                101::bigint,
                'EP2606406A1'::varchar,
                'EP'::varchar,
                '2606406'::varchar,
                'A1'::varchar,
                DATE '2013-07-10',
                true,
                false,
                false,
                'mega_cluster_bounded'::varchar,
                '2026-03-15'::varchar,
                null::varchar,
                null::varchar,
                null::varchar,
                null::bigint,
                null::boolean
            )
        ) as t(
            pat_publn_id,
            appln_id,
            docdb_family_id,
            publication_number_full,
            publn_auth,
            publn_nr,
            publn_kind,
            publn_date,
            is_application_stage,
            is_grant_stage,
            is_modifier_stage,
            scope_type,
            snapshot_date,
            family_composite_status,
            mart_family_composite_status,
            effective_family_composite_status,
            active_opposition_application_count,
            opposition_overlay_active
        )
        """,
    )
    _write_partition_parquet(
        publication_path / "application_evidence_by_appln",
        "appln_bucket",
        appln_bucket,
        """
        select * from (
            values (
                11223344::bigint,
                null::varchar,
                null::varchar,
                null::varchar,
                null::varchar,
                DATE '2012-12-19',
                null::bigint,
                null::boolean,
                null::boolean,
                null::varchar,
                null::date,
                null::varchar,
                null::varchar,
                null::date,
                null::double,
                null::date,
                null::varchar,
                null::varchar,
                null::bigint,
                null::boolean,
                null::varchar,
                null::varchar,
                null::date,
                null::boolean,
                null::varchar,
                null::varchar,
                null::varchar,
                null::boolean,
                null::varchar,
                null::varchar,
                null::varchar
            )
        ) as t(
            appln_id,
            title_text,
            title_language_code,
            abstract_text,
            abstract_language_code,
            appln_filing_date,
            reg101_id,
            register_record_present,
            ep_registered_license_flag,
            ep_licensee_names,
            register_snapshot_date,
            ep_display_status_text,
            status_source,
            display_snapshot_date,
            ep_proc_step_maturity_score,
            ep_search_report_mailed_date,
            ep_latest_proc_phase_code,
            ep_latest_proc_result_code,
            ep_proc_time_limit_days,
            ep_register_is_unitary_patent,
            ep_register_up_status_code,
            ep_register_up_status_text,
            ep_register_up_event_latest_date,
            ep_opposition_active,
            ep_opposition_status_text,
            ep_opponent_names,
            ep_opponent_agent_names,
            ep_appeal_active,
            ep_appeal_result_text,
            ep_register_lead_agent_name,
            ep_register_lead_agent_country
        )
        """,
    )
    (publication_path / "publication_claim_by_number").mkdir(parents=True, exist_ok=True)

    _write_parquet(
        etl_data_root / "bronze" / "bronze_patstat_appln_title.parquet",
        """
        select 11223344::bigint as appln_id, 'en'::varchar as appln_title_lg, 'Raw fallback title'::varchar as appln_title
        """,
    )
    _write_parquet(
        etl_data_root / "bronze" / "bronze_patstat_appln_abstr.parquet",
        """
        select 11223344::bigint as appln_id, 'en'::varchar as appln_abstract_lg, 'Raw fallback abstract'::varchar as appln_abstract
        """,
    )
    _write_parquet(
        etl_data_root / "bronze" / "bronze_patstat_appln.parquet",
        """
        select 11223344::bigint as appln_id, DATE '2012-12-19' as appln_filing_date
        """,
    )
    _write_parquet(
        etl_data_root / "bronze" / "bronze_epab_publication.parquet",
        """
        select 'epab-1'::varchar as epab_doc_id, 'EP2606406A1'::varchar as publication_number_full
        """,
    )
    _write_parquet(
        etl_data_root / "bronze" / "bronze_epab_claims.parquet",
        """
        select 'epab-1'::varchar as epab_doc_id, 1::bigint as claim_sequence_no, 'en'::varchar as language_code, 'Raw fallback claim'::varchar as claim_text_plain
        """,
    )
    _write_parquet(
        etl_data_root / "silver" / "silver_ep_register_core.parquet",
        """
        select
            11223344::bigint as appln_id,
            77::bigint as reg101_id,
            true::boolean as register_record_present,
            true::boolean as ep_registered_license_flag,
            'Raw fallback licensee'::varchar as ep_licensee_names,
            DATE '2026-03-15' as register_snapshot_date
        """,
    )

    monkeypatch.setenv("PATENTIQ_V2_ARTIFACT_MODE", "local_fs")
    monkeypatch.setenv("PATENTIQ_V2_LOCAL_ARTIFACT_ROOT", str(serving_dir))
    monkeypatch.setenv("PATENTIQ_V2_SERVING_MANIFEST_PATH", str(manifest_path))
    monkeypatch.setenv("PATENTIQ_V2_ETL_DATA_ROOT", str(etl_data_root))
    monkeypatch.setenv("PATENTIQ_V2_RAW_PARQUET_FALLBACK_ENABLED", "true")
    get_settings.cache_clear()

    repository = PublicationRepository()

    assert repository.get_title_for_application(11223344) is None
    assert repository.get_abstract_for_application(11223344) is None
    assert repository.get_claim_for_publication("EP2606406A1") is None
    register = repository.get_register_evidence(11223344)
    assert register["register_record_present"] is None
    assert register["ep_licensee_names"] is None

    get_settings.cache_clear()


def test_publication_repository_falls_back_to_raw_when_publication_dataset_is_temporarily_missing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    serving_dir = tmp_path / "serving"
    publication_path = serving_dir / "publication_serving"
    publication_path.mkdir(parents=True)
    etl_data_root = tmp_path / "etl_data"
    manifest_path = serving_dir / "serving_snapshot_manifest.json"
    manifest_path.write_text(
        """
        {
          "serving_release": "test-serving",
          "contract_version": "1",
          "snapshots": {
            "publication": {
              "filename": "publication_serving",
              "tables": [
                "publication_member_by_number",
                "application_evidence_by_appln"
              ]
            }
          }
        }
        """.strip(),
        encoding="utf-8",
    )

    publication_bucket = _publication_bucket("EP2606406A1")

    _write_partition_parquet(
        publication_path / "publication_member_by_number",
        "publication_bucket",
        publication_bucket,
        """
        select * from (
            values (
                26064061::bigint,
                11223344::bigint,
                101::bigint,
                'EP2606406A1'::varchar,
                'EP'::varchar,
                '2606406'::varchar,
                'A1'::varchar,
                DATE '2013-07-10',
                true,
                false,
                false,
                'mega_cluster_bounded'::varchar,
                '2026-03-15'::varchar,
                null::varchar,
                null::varchar,
                null::varchar,
                null::bigint,
                null::boolean
            )
        ) as t(
            pat_publn_id,
            appln_id,
            docdb_family_id,
            publication_number_full,
            publn_auth,
            publn_nr,
            publn_kind,
            publn_date,
            is_application_stage,
            is_grant_stage,
            is_modifier_stage,
            scope_type,
            snapshot_date,
            family_composite_status,
            mart_family_composite_status,
            effective_family_composite_status,
            active_opposition_application_count,
            opposition_overlay_active
        )
        """,
    )

    _write_parquet(
        etl_data_root / "bronze" / "bronze_patstat_appln_title.parquet",
        """
        select 11223344::bigint as appln_id, 'en'::varchar as appln_title_lg, 'Raw fallback title'::varchar as appln_title
        """,
    )
    _write_parquet(
        etl_data_root / "bronze" / "bronze_patstat_appln_abstr.parquet",
        """
        select 11223344::bigint as appln_id, 'en'::varchar as appln_abstract_lg, 'Raw fallback abstract'::varchar as appln_abstract
        """,
    )

    monkeypatch.setenv("PATENTIQ_V2_ARTIFACT_MODE", "local_fs")
    monkeypatch.setenv("PATENTIQ_V2_LOCAL_ARTIFACT_ROOT", str(serving_dir))
    monkeypatch.setenv("PATENTIQ_V2_SERVING_MANIFEST_PATH", str(manifest_path))
    monkeypatch.setenv("PATENTIQ_V2_ETL_DATA_ROOT", str(etl_data_root))
    monkeypatch.setenv("PATENTIQ_V2_RAW_PARQUET_FALLBACK_ENABLED", "true")
    get_settings.cache_clear()

    repository = PublicationRepository()

    assert repository.get_title_for_application(11223344) == {
        "title_text": "Raw fallback title",
        "language_code": "en",
    }
    assert repository.get_abstract_for_application(11223344) == {
        "abstract_text": "Raw fallback abstract",
        "language_code": "en",
    }

    get_settings.cache_clear()


def test_publication_repository_suggestions_use_publication_serving_snapshot(
    tmp_path: Path,
    monkeypatch,
) -> None:
    serving_dir = tmp_path / "serving"
    publication_path = serving_dir / "publication_serving"
    publication_path.mkdir(parents=True)
    manifest_path = serving_dir / "serving_snapshot_manifest.json"
    manifest_path.write_text(
        """
        {
          "serving_release": "test-serving",
          "contract_version": "1",
          "snapshots": {
            "publication": {
              "filename": "publication_serving",
              "tables": ["publication_member_by_number"]
            }
          }
        }
        """.strip(),
        encoding="utf-8",
    )

    _write_partition_parquet(
        publication_path / "publication_member_by_number",
        "publication_bucket",
        "aa",
        """
        select * from (
            values
                (
                    26064061::bigint,
                    11223344::bigint,
                    57400072::bigint,
                    'EP2606406A1'::varchar,
                    'EP'::varchar,
                    '2606406'::varchar,
                    'A1'::varchar,
                    DATE '2013-07-10',
                    true,
                    false,
                    false,
                    'mega_cluster_bounded'::varchar,
                    '2026-03-15'::varchar
                ),
                (
                    26064062::bigint,
                    11223344::bigint,
                    57400072::bigint,
                    'EP2606406B1'::varchar,
                    'EP'::varchar,
                    '2606406'::varchar,
                    'B1'::varchar,
                    DATE '2018-11-14',
                    false,
                    true,
                    false,
                    'mega_cluster_bounded'::varchar,
                    '2026-03-15'::varchar
                )
        ) as t(
            pat_publn_id,
            appln_id,
            docdb_family_id,
            publication_number_full,
            publn_auth,
            publn_nr,
            publn_kind,
            publn_date,
            is_application_stage,
            is_grant_stage,
            is_modifier_stage,
            scope_type,
            snapshot_date
        )
        """,
    )

    monkeypatch.setenv("PATENTIQ_V2_ARTIFACT_MODE", "local_fs")
    monkeypatch.setenv("PATENTIQ_V2_LOCAL_ARTIFACT_ROOT", str(serving_dir))
    monkeypatch.setenv("PATENTIQ_V2_SERVING_MANIFEST_PATH", str(manifest_path))
    monkeypatch.setenv("PATENTIQ_V2_RAW_PARQUET_FALLBACK_ENABLED", "false")
    get_settings.cache_clear()

    repository = PublicationRepository()
    rows = repository.get_publication_suggestions("EP2606406", limit=5)

    assert [row["publication_id"] for row in rows] == ["EP2606406A1", "EP2606406B1"]
    assert rows[0]["family_id"] == "57400072"

    get_settings.cache_clear()


def test_publication_repository_falls_back_to_legacy_core_snapshot_when_publication_snapshot_is_missing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    serving_dir = tmp_path / "serving"
    serving_dir.mkdir(parents=True)
    manifest_path = serving_dir / "serving_snapshot_manifest.json"
    core_path = serving_dir / "core_serving.duckdb"
    manifest_path.write_text(
        """
        {
          "serving_release": "test-serving",
          "contract_version": "1",
          "snapshots": {
            "core": {
              "filename": "core_serving.duckdb",
              "tables": ["publication_evidence_serving"]
            }
          }
        }
        """.strip(),
        encoding="utf-8",
    )

    with duckdb.connect(str(core_path)) as con:
        con.execute(
            """
            create table publication_evidence_serving as
            select * from (
                values (
                    26064061::bigint,
                    11223344::bigint,
                    101::bigint,
                    'EP2606406A1'::varchar,
                    'EP'::varchar,
                    '2606406'::varchar,
                    'A1'::varchar,
                    DATE '2013-07-10',
                    true,
                    false,
                    false,
                    'mega_cluster_bounded'::varchar,
                    '2026-03-15'::varchar
                )
            ) as t(
                pat_publn_id,
                appln_id,
                docdb_family_id,
                publication_number_full,
                publn_auth,
                publn_nr,
                publn_kind,
                publn_date,
                is_application_stage,
                is_grant_stage,
                is_modifier_stage,
                scope_type,
                snapshot_date
            )
            """
        )

    monkeypatch.setenv("PATENTIQ_V2_ARTIFACT_MODE", "local_fs")
    monkeypatch.setenv("PATENTIQ_V2_LOCAL_ARTIFACT_ROOT", str(serving_dir))
    monkeypatch.setenv("PATENTIQ_V2_SERVING_MANIFEST_PATH", str(manifest_path))
    monkeypatch.setenv("PATENTIQ_V2_RAW_PARQUET_FALLBACK_ENABLED", "false")
    get_settings.cache_clear()

    repository = PublicationRepository()
    member = repository.get_publication_member("ep2606406a1")

    assert repository.artifacts() == [core_path]
    assert member is not None
    assert member["publication_number_full"] == "EP2606406A1"

    get_settings.cache_clear()
