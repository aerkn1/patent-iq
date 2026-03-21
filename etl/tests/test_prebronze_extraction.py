from __future__ import annotations

import dataclasses
import json
from pathlib import Path
import textwrap
import zipfile

from patentiq_etl.bronze.ingest_uspto_fulltext import ingest_uspto_fulltext
from patentiq_etl.common.io import parquet_row_count, write_pylist_parquet
from patentiq_etl.common.types import BuildSettings, StageResult
from patentiq_etl.prebronze.extract import _seed_patstat_scope_tip, extract_bounded_raw


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _settings(tmp_path: Path) -> BuildSettings:
    root = tmp_path / "repo"
    return BuildSettings(
        repo_root=root,
        release_id="test-release",
        snapshot_date="2026-03-15",
        year_window_start=2006,
        year_window_end=2026,
        heritage_backfill_start=1996,
        heritage_backfill_end=2005,
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
        selected_wipo_fields=[
            "COMPUTER_TECHNOLOGY",
            "DIGITAL_COMMUNICATION",
            "TELECOMMUNICATIONS",
            "AUDIO_VISUAL_TECHNOLOGY",
            "BASIC_COMMUNICATION_PROCESSES",
            "IT_METHODS_FOR_MANAGEMENT",
            "SEMICONDUCTORS",
            "MEASUREMENT",
            "CONTROL",
            "ELECTRICAL_MACHINERY_APPARATUS_ENERGY",
        ],
        thresholds={},
        azure={},
    )


def test_prebronze_extraction_builds_bounded_raw_slice(tmp_path: Path) -> None:
    settings = _settings(tmp_path)

    _write(
        settings.raw_patstat_dir / "tls201_appln.csv",
        textwrap.dedent(
            """\
            appln_id,docdb_family_id,appln_auth,appln_nr
            1,100,EP,123
            2,200,US,111
            3,300,JP,999
            """
        ),
    )
    _write(
        settings.raw_patstat_dir / "tls211_pat_publn.csv",
        textwrap.dedent(
            """\
            pat_publn_id,appln_id,publn_auth,publn_nr,publn_kind
            10,1,EP,123,A1
            20,2,US,111,B1
            30,3,JP,999,A
            """
        ),
    )
    _write(
        settings.raw_patstat_dir / "tls207_pers_appln.csv",
        textwrap.dedent(
            """\
            person_id,appln_id
            9001,1
            9002,2
            9003,3
            """
        ),
    )
    _write(
        settings.raw_patstat_dir / "tls206_person.csv",
        textwrap.dedent(
            """\
            person_id,person_name
            9001,Alpha Corp
            9002,Beta Corp
            9003,Gamma Corp
            """
        ),
    )
    _write(
        settings.raw_patstat_dir / "tls230_appln_techn_field.csv",
        textwrap.dedent(
            """\
            appln_id,techn_field
            1,COMPUTER_TECHNOLOGY
            2,DIGITAL_COMMUNICATION
            3,BIOTECHNOLOGY
            """
        ),
    )
    _write(
        settings.raw_patstat_dir / "tls212_citation.csv",
        textwrap.dedent(
            """\
            pat_publn_id,cited_pat_publn_id,npl_publn_id
            10,30,
            20,,900
            30,10,
            """
        ),
    )
    _write(
        settings.raw_patstat_dir / "tls214_npl_publn.csv",
        textwrap.dedent(
            """\
            npl_publn_id,npl_biblio
            900,Paper A
            901,Paper B
            """
        ),
    )
    _write(
        settings.raw_patstat_dir / "tls228_docdb_fam_citn.csv",
        textwrap.dedent(
            """\
            docdb_family_id,cited_docdb_family_id
            100,300
            200,400
            300,100
            """
        ),
    )
    _write(
        settings.raw_refs_dir / "wipo_techn_field_ipc.csv",
        textwrap.dedent(
            """\
            ipc_subclass,techn_field
            G06F,COMPUTER_TECHNOLOGY
            """
        ),
    )
    _write(
        settings.raw_register_dir / "reg101_appln.csv",
        textwrap.dedent(
            """\
            id,appln_id
            7001,1
            7002,3
            """
        ),
    )
    _write(
        settings.raw_register_dir / "reg201_proc_step.csv",
        textwrap.dedent(
            """\
            id,step_id
            7001,101
            7002,202
            """
        ),
    )
    _write(
        settings.raw_register_dir / "reg202_proc_step_text.csv",
        textwrap.dedent(
            """\
            step_id,step_text
            101,Search complete
            202,Outside scope
            """
        ),
    )
    _write(
        settings.raw_register_dir / "reg301_event_data.csv",
        textwrap.dedent(
            """\
            id,event_code
            7001,EV1
            7002,EV2
            """
        ),
    )
    _write(
        settings.raw_register_dir / "reg402_event_text.csv",
        textwrap.dedent(
            """\
            event_code,event_text
            EV1,Grant
            EV2,Outside scope
            """
        ),
    )
    _write(
        settings.raw_uspto_dir / "us1.xml",
        textwrap.dedent(
            """\
            <patent-application-publication>
              <publication-reference><document-id><country>US</country><doc-number>111</doc-number><kind>B1</kind><date>20240101</date></document-id></publication-reference>
              <application-reference appl-type="utility"><document-id><doc-number>111</doc-number><date>20230101</date></document-id></application-reference>
              <abstract><p>Sample abstract.</p></abstract>
              <claims><claim id="CLM-1" num="1"><claim-text>Sample claim.</claim-text></claim></claims>
            </patent-application-publication>
            """
        ),
    )
    _write(
        settings.raw_uspto_dir / "us2.xml",
        textwrap.dedent(
            """\
            <patent-application-publication>
              <publication-reference><document-id><country>US</country><doc-number>999</doc-number><kind>A1</kind><date>20240101</date></document-id></publication-reference>
            </patent-application-publication>
            """
        ),
    )
    epab_path = settings.raw_epab_dir / "epab.jsonl"
    epab_path.parent.mkdir(parents=True, exist_ok=True)
    epab_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "epab_doc_id": "doc-1",
                        "publication": {"authority": "EP", "number": "123", "kind": "A1", "publication_number_full": "EP123A1"},
                        "application": {"authority": "EP", "number": "123"},
                    }
                ),
                json.dumps(
                    {
                        "epab_doc_id": "doc-2",
                        "publication": {"authority": "EP", "number": "999", "kind": "A1", "publication_number_full": "EP999A1"},
                        "application": {"authority": "EP", "number": "999"},
                    }
                ),
            ]
        ),
        encoding="utf-8",
    )

    result = extract_bounded_raw(settings).finish()

    assert result.status == "success"
    assert result.metrics["seed_appln_count"] == 2
    assert result.metrics["seed_family_count"] == 2
    assert result.metrics["bounded_citation_edge_count"] == 2
    assert result.metrics["bounded_citation_ghost_target_count"] == 1
    assert result.metrics["uspto_bounded_xml_count"] == 1
    assert result.metrics["epab_bounded_record_count"] == 1

    assert parquet_row_count(settings.bounded_patstat_dir / "tls201_appln.parquet") == 2
    assert parquet_row_count(settings.bounded_patstat_dir / "tls212_citation.parquet") == 2
    assert parquet_row_count(settings.bounded_patstat_dir / "tls214_npl_publn.parquet") == 1
    assert parquet_row_count(settings.bounded_register_dir / "reg101_appln.parquet") == 1
    assert parquet_row_count(settings.bounded_register_dir / "reg202_proc_step_text.parquet") == 1


def test_prebronze_odp_uspto_writes_direct_bronze_and_cleans_temp(tmp_path: Path, monkeypatch) -> None:
    settings = _settings(tmp_path)
    settings = dataclasses.replace(settings, year_window_start=2007, year_window_end=2026, uspto_source_mode="odp_api")
    settings.execution = {"uspto_odp_api_key_env": "TEST_USPTO_ODP_API_KEY", "uspto_odp_delay_seconds": 0}
    monkeypatch.setenv("TEST_USPTO_ODP_API_KEY", "fake-key")

    _write(
        settings.raw_patstat_dir / "tls201_appln.csv",
        textwrap.dedent(
            """\
            appln_id,docdb_family_id,appln_auth,appln_nr
            1,100,US,111
            """
        ),
    )
    _write(
        settings.raw_patstat_dir / "tls211_pat_publn.csv",
        textwrap.dedent(
            """\
            pat_publn_id,appln_id,publn_auth,publn_nr,publn_kind,publn_date
            20,1,US,111,B1,2024-01-01
            """
        ),
    )
    _write(
        settings.raw_patstat_dir / "tls230_appln_techn_field.csv",
        textwrap.dedent(
            """\
            appln_id,techn_field
            1,COMPUTER_TECHNOLOGY
            """
        ),
    )
    _write(
        settings.raw_refs_dir / "wipo_techn_field_ipc.csv",
        textwrap.dedent(
            """\
            ipc_subclass,techn_field
            G06F,COMPUTER_TECHNOLOGY
            """
        ),
    )

    zip_payload = textwrap.dedent(
        """\
        <?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE us-patent-application SYSTEM "us-patent-application-v46-2022-02-17.dtd">
        <us-patent-application dtd-version="v4.6 2022-02-17">
          <publication-reference><document-id><country>US</country><doc-number>111</doc-number><kind>B1</kind><date>20240101</date></document-id></publication-reference>
          <application-reference appl-type="utility"><document-id><doc-number>111</doc-number><date>20230101</date></document-id></application-reference>
          <abstract><p>Sample abstract.</p></abstract>
          <claims><claim id="CLM-1" num="1"><claim-text>Sample claim.</claim-text></claim></claims>
        </us-patent-application>
        <?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE us-patent-application SYSTEM "us-patent-application-v46-2022-02-17.dtd">
        <us-patent-application dtd-version="v4.6 2022-02-17">
          <publication-reference><document-id><country>US</country><doc-number>999</doc-number><kind>A1</kind><date>20240101</date></document-id></publication-reference>
        </us-patent-application>
        """
    ).encode("utf-8")
    source_zip = tmp_path / "source.zip"
    with zipfile.ZipFile(source_zip, "w") as archive:
        archive.writestr("ipa240104.xml", zip_payload)

    def _fake_manifest(*_args, **_kwargs):
        return [
            {
                "file_name": "ipa240104.zip",
                "file_size": source_zip.stat().st_size,
                "file_data_from_date": "2024-01-01",
                "file_data_to_date": "2024-01-07",
                "file_release_date": "2024-01-04",
                "base_week": "ipa240104",
                "selected_revision": 0,
            }
        ]

    def _fake_download(_url, _headers, out_path, _timeout):
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(source_zip.read_bytes())
        return out_path.stat().st_size

    monkeypatch.setattr("patentiq_etl.prebronze.uspto_odp._download_manifest", _fake_manifest)
    monkeypatch.setattr("patentiq_etl.prebronze.uspto_odp._download_to_path", _fake_download)

    result = extract_bounded_raw(settings).finish()

    assert result.status == "success"
    assert parquet_row_count(settings.bronze_dir / "bronze_uspto_ft_document.parquet") == 1
    assert parquet_row_count(settings.bronze_dir / "bronze_uspto_ft_claims.parquet") == 1


def test_tip_seed_builder_reuses_existing_seed_files_individually(tmp_path: Path, monkeypatch) -> None:
    settings = _settings(tmp_path)
    settings = dataclasses.replace(settings, patstat_source_mode="tip")
    seed_dir = settings.bounded_seed_dir
    seed_dir.mkdir(parents=True, exist_ok=True)
    existing_publn = seed_dir / "seed_publn_ids.parquet"
    existing_ep = seed_dir / "seed_ep_publication_numbers.parquet"
    existing_us = seed_dir / "seed_us_publication_numbers.parquet"
    write_pylist_parquet(
        [
            {
                "pat_publn_id": 20,
                "appln_id": 2,
                "publn_auth": "US",
                "publication_number": "111",
                "publication_kind": "B1",
                "publication_date": "2024-01-01",
                "publication_number_full": "US111B1",
            }
        ],
        existing_publn,
    )
    write_pylist_parquet(
        [
            {
                "pat_publn_id": 10,
                "appln_id": 1,
                "publn_auth": "EP",
                "publication_number": "123",
                "publication_kind": "A1",
                "publication_date": "2024-01-01",
                "publication_number_full": "EP123A1",
            }
        ],
        existing_ep,
    )
    write_pylist_parquet(
        [
            {
                "pat_publn_id": 20,
                "appln_id": 2,
                "publn_auth": "US",
                "publication_number": "111",
                "publication_kind": "B1",
                "publication_date": "2024-01-01",
                "publication_number_full": "US111B1",
            }
        ],
        existing_us,
    )

    class FakeColumn:
        def __init__(self, name: str) -> None:
            self.name = name

        def label(self, name: str):
            return FakeColumn(name)

        def isnot(self, value):
            return self

        def in_(self, values):
            return self

        def __eq__(self, other):
            return self

    class FakeModel:
        appln_id = FakeColumn("appln_id")
        techn_field_nr = FakeColumn("techn_field_nr")
        techn_field = FakeColumn("techn_field")
        docdb_family_id = FakeColumn("docdb_family_id")
        pat_publn_id = FakeColumn("pat_publn_id")
        publn_auth = FakeColumn("publn_auth")
        publn_nr = FakeColumn("publication_number")
        publn_kind = FakeColumn("publication_kind")
        publn_date = FakeColumn("publication_date")
        person_id = FakeColumn("person_id")
        appln_auth = FakeColumn("appln_auth")
        appln_filing_date = FakeColumn("appln_filing_date")

    class FakeSubquery:
        class C:
            appln_id = FakeColumn("appln_id")
            wipo_field = FakeColumn("wipo_field")

        c = C()

    class FakeQuery:
        def __init__(self, key: str) -> None:
            self.key = key

        def join(self, *args, **kwargs):
            return self

        def filter(self, *args, **kwargs):
            return self

        def distinct(self):
            return self

        def group_by(self, *args, **kwargs):
            return self

        def subquery(self):
            return FakeSubquery()

    class FakeDB:
        def query(self, *columns):
            names = [getattr(column, "name", str(column)) for column in columns]
            if "family_count" in names:
                return FakeQuery("field_family")
            if "person_id" in names:
                return FakeQuery("seed_person")
            if "docdb_family_id" in names and len(names) == 1:
                return FakeQuery("seed_family")
            if "pat_publn_id" in names:
                return FakeQuery("seed_publn")
            if "appln_id" in names and len(names) == 1:
                return FakeQuery("seed_ep_appln")
            if "wipo_field" in names:
                return FakeQuery("seed_appln")
            return FakeQuery("other")

    class FakePatstat:
        pass

    fake_patstat = FakePatstat()
    fake_db = FakeDB()

    monkeypatch.setattr("patentiq_etl.prebronze.extract.get_patstat_client", lambda env: (fake_patstat, fake_db))
    monkeypatch.setattr("patentiq_etl.prebronze.extract.get_patstat_database_module", lambda: object())
    monkeypatch.setattr(
        "patentiq_etl.prebronze.extract.resolve_patstat_model",
        lambda module, logical_name: FakeModel,
    )
    monkeypatch.setattr(
        "patentiq_etl.prebronze.extract.apply_year_window_filter",
        lambda query, model, start, end: query,
    )
    monkeypatch.setattr(
        "patentiq_etl.prebronze.extract.write_dataframe_parquet",
        lambda df, out_path: write_pylist_parquet(df.to_dict(orient="records"), out_path),
    )

    calls: list[str] = []

    def fake_query_to_dataframe(client, query):
        calls.append(query.key)
        if query.key == "seed_appln":
            import pandas as pd

            return pd.DataFrame(
                [
                    {"appln_id": 1, "wipo_field": "COMPUTER_TECHNOLOGY"},
                    {"appln_id": 2, "wipo_field": "DIGITAL_COMMUNICATION"},
                ]
            )
        if query.key == "seed_family":
            import pandas as pd

            return pd.DataFrame([{"docdb_family_id": 100}, {"docdb_family_id": 200}])
        if query.key == "seed_person":
            import pandas as pd

            return pd.DataFrame([{"person_id": 9001}, {"person_id": 9002}])
        if query.key == "seed_ep_appln":
            import pandas as pd

            return pd.DataFrame([{"appln_id": 1}])
        if query.key == "field_family":
            import pandas as pd

            return pd.DataFrame(
                [
                    {"wipo_field": "COMPUTER_TECHNOLOGY", "family_count": 1},
                    {"wipo_field": "DIGITAL_COMMUNICATION", "family_count": 1},
                ]
            )
        raise AssertionError(f"unexpected query materialization for {query.key}")

    monkeypatch.setattr("patentiq_etl.prebronze.extract.query_to_dataframe", fake_query_to_dataframe)

    result = StageResult(stage="seed-test", status="success", summary="seed")
    seeds = _seed_patstat_scope_tip(settings, result)

    assert seeds["seed_publn_ids"] == existing_publn
    assert seeds["seed_us_publication_numbers"] == existing_us
    assert result.metrics["seed_publn_count"] == 1
    assert result.metrics["seed_us_publication_count"] == 1
    assert "seed_publn" not in calls
    assert result.metrics["seed_family_count__COMPUTER_TECHNOLOGY"] == 1
    assert result.metrics["seed_family_count__DIGITAL_COMMUNICATION"] == 1


def test_bronze_uspto_odp_mode_does_not_degrade_when_outputs_are_deferred(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    settings = dataclasses.replace(settings, uspto_source_mode="odp_api")

    bronze_result = ingest_uspto_fulltext(settings).finish()

    assert bronze_result.status == "success"
    assert bronze_result.metrics["uspto_odp_outputs_present"] == 0
    assert "deferred" in bronze_result.summary
