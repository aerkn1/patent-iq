from __future__ import annotations

from collections import Counter
from pathlib import Path
from threading import Lock
import json
import sys
import time

from patentiq_etl.bronze.source_registry import PATSTAT_TABLES
from patentiq_etl.common.io import ensure_dir, parquet_row_count, write_pylist_parquet
from patentiq_etl.common.types import BuildSettings
from patentiq_etl.prebronze.chunked import (
    _citation_npl_column,
    _get_container_client,
    _upload_paths,
    backfill_tip_derived_seeds,
    recover_tip_blob_uploads,
    run_tip_chunked_export,
)
from patentiq_etl.prebronze.extract import _citation_npl_column_from_parquet


def _settings(tmp_path: Path) -> BuildSettings:
    root = tmp_path / "repo"
    return BuildSettings(
        repo_root=root,
        release_id="test-release",
        snapshot_date="2026-03-17",
        year_window_start=2018,
        year_window_end=2023,
        heritage_backfill_start=1996,
        heritage_backfill_end=2006,
        azure_publish_enabled=False,
        vector_sample_pct=0.1,
        active_grant_only_for_semantic=True,
        method_version="test",
        semantic_embedding_method="hash",
        semantic_ann_method="placeholder",
        patstat_source_mode="tip",
        register_source_mode="tip",
        epab_source_mode="tip",
        uspto_source_mode="odp_api",
        refs_source_mode="disabled",
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
        azure={"container": "patentiq-data"},
        execution={
            "tip_chunked_export_enabled": True,
            "blob_intermediate_enabled": False,
            "upload_after_chunk": False,
            "cleanup_after_upload": True,
            "chunk_year_span": 3,
            "table_families": ["core", "citations"],
            "max_workers": {"core": 1, "citations": 1},
            "tip_max_parallel_chunks": 2,
            "realtime_chunk_logging": True,
        },
    )


def test_chunked_runtime_respects_parallel_limits_and_emits_live_events(tmp_path: Path, monkeypatch) -> None:
    settings = _settings(tmp_path)
    settings.execution["table_families"] = ["core", "publications"]
    settings.execution["max_workers"] = {"core": 1, "publications": 1}
    active_total = 0
    max_active_total = 0
    family_active = Counter()
    family_max = Counter()
    lock = Lock()

    def fake_scope(*args, **kwargs):
        return {
            "patstat": None,
            "db": None,
            "database_module": None,
            "appln_sq": None,
            "family_sq": None,
            "publn_sq": None,
            "person_sq": None,
            "ep_appln_q": None,
            "ep_publn_df": __import__("pandas").DataFrame(),
            "us_publn_df": __import__("pandas").DataFrame(),
            "counts": {"appln_count": 10, "family_count": 5, "publn_count": 7},
        }

    def fake_extract(scope, family_name: str, out_dir: Path):
        nonlocal active_total, max_active_total
        with lock:
            active_total += 1
            family_active[family_name] += 1
            max_active_total = max(max_active_total, active_total)
            family_max[family_name] = max(family_max[family_name], family_active[family_name])
        try:
            time.sleep(0.05)
            if family_name == "core":
                out_path = ensure_dir(out_dir) / f"{PATSTAT_TABLES['bronze_patstat_pers_appln'][0]}.parquet"
                write_pylist_parquet([{"appln_id": 10, "person_id": 99}], out_path)
            elif family_name == "publications":
                out_path = ensure_dir(out_dir) / f"{PATSTAT_TABLES['bronze_patstat_pat_publn'][0]}.parquet"
                write_pylist_parquet(
                    [
                        {
                            "pat_publn_id": 1,
                            "appln_id": 10,
                            "publn_auth": "EP",
                            "publn_nr": "123",
                            "publn_kind": "A1",
                            "publn_date": "2024-01-01",
                        },
                        {
                            "pat_publn_id": 2,
                            "appln_id": 11,
                            "publn_auth": "US",
                            "publn_nr": "456",
                            "publn_kind": "B1",
                            "publn_date": "2024-01-02",
                        },
                    ],
                    out_path,
                )
            else:
                out_path = ensure_dir(out_dir) / f"{family_name}.parquet"
                write_pylist_parquet([{"family_name": family_name}], out_path)
            return [out_path]
        finally:
            with lock:
                active_total -= 1
                family_active[family_name] -= 1

    def fake_seed(settings, result, *, seed_dir=None, requested_seed_keys=None):
        actual_seed_dir = ensure_dir(seed_dir or settings.bounded_seed_dir)
        outputs = {
            "seed_appln_ids": actual_seed_dir / "seed_appln_ids.parquet",
            "seed_family_ids": actual_seed_dir / "seed_family_ids.parquet",
            "seed_publn_ids": actual_seed_dir / "seed_publn_ids.parquet",
            "seed_person_ids": actual_seed_dir / "seed_person_ids.parquet",
            "seed_ep_appln_ids": actual_seed_dir / "seed_ep_appln_ids.parquet",
            "seed_us_publication_numbers": actual_seed_dir / "seed_us_publication_numbers.parquet",
            "seed_ep_publication_numbers": actual_seed_dir / "seed_ep_publication_numbers.parquet",
            "seed_family_field_counts": actual_seed_dir / "seed_family_field_counts.parquet",
        }
        requested = set(requested_seed_keys or outputs.keys())
        for key, path in outputs.items():
            if key not in requested:
                continue
            path.write_text("seed", encoding="utf-8")
            result.outputs.append(str(path))
        return {key: path for key, path in outputs.items() if key in requested}

    monkeypatch.setattr("patentiq_etl.prebronze.chunked._chunk_scope_tip", fake_scope)
    monkeypatch.setattr("patentiq_etl.prebronze.chunked._extract_patstat_family", fake_extract)
    monkeypatch.setattr("patentiq_etl.prebronze.chunked._seed_patstat_scope_tip", fake_seed)

    result = run_tip_chunked_export(settings).finish()

    assert result.status == "success"
    assert result.metrics["chunk_scheduler_parallel_limit"] == 2
    assert result.metrics["global_seed_initial_file_count"] == 4
    assert result.metrics["global_seed_file_count"] == 8
    assert max_active_total <= 2
    assert family_max["core"] <= 1
    assert family_max["publications"] <= 1
    assert (settings.bounded_seed_dir / "seed_publn_ids.parquet").exists()
    assert (settings.bounded_seed_dir / "seed_person_ids.parquet").exists()
    assert (settings.bounded_seed_dir / "seed_ep_publication_numbers.parquet").exists()
    assert (settings.bounded_seed_dir / "seed_us_publication_numbers.parquet").exists()

    event_log_path = Path(result.artifacts["live_event_log"])
    assert event_log_path.exists()
    events = event_log_path.read_text(encoding="utf-8").splitlines()
    assert any('"event": "chunk_submitted"' in line for line in events)
    assert any('"event": "chunk_finished"' in line for line in events)
    assert any('"event": "global_seeds_finished"' in line for line in events)
    assert any('"event": "derived_seed_consolidated"' in line for line in events)


def test_chunked_runtime_reuses_existing_seeds_and_skips_successful_chunks(tmp_path: Path, monkeypatch) -> None:
    settings = _settings(tmp_path)
    seed_dir = settings.bounded_seed_dir
    for name in (
        "seed_appln_ids.parquet",
        "seed_family_ids.parquet",
        "seed_publn_ids.parquet",
        "seed_person_ids.parquet",
        "seed_ep_appln_ids.parquet",
        "seed_us_publication_numbers.parquet",
        "seed_ep_publication_numbers.parquet",
        "seed_family_field_counts.parquet",
    ):
        path = ensure_dir(seed_dir) / name
        path.write_text("seed", encoding="utf-8")

    chunk_manifest = ensure_dir(settings.manifests_dir / "chunks") / "computer-technology__2018_2020__core.json"
    chunk_manifest.write_text(
        json.dumps(
            {
                "chunk_id": "computer-technology__2018_2020__core",
                "status": "success",
            }
        ),
        encoding="utf-8",
    )

    def fail_if_called(*args, **kwargs):
        raise AssertionError("seed regeneration should not run when all seed files already exist")

    def fake_scope(*args, **kwargs):
        return {
            "patstat": None,
            "db": None,
            "database_module": None,
            "appln_sq": None,
            "family_sq": None,
            "publn_sq": None,
            "person_sq": None,
            "ep_appln_q": None,
            "ep_publn_df": __import__("pandas").DataFrame(),
            "us_publn_df": __import__("pandas").DataFrame(),
            "counts": {"appln_count": 1, "family_count": 1, "publn_count": 1},
        }

    def fake_extract(scope, family_name: str, out_dir: Path):
        out_path = ensure_dir(out_dir) / f"{family_name}.parquet"
        out_path.write_text(family_name, encoding="utf-8")
        return [out_path]

    monkeypatch.setattr("patentiq_etl.prebronze.chunked._seed_patstat_scope_tip", fail_if_called)
    monkeypatch.setattr("patentiq_etl.prebronze.chunked._chunk_scope_tip", fake_scope)
    monkeypatch.setattr("patentiq_etl.prebronze.chunked._extract_patstat_family", fake_extract)

    result = run_tip_chunked_export(settings).finish()

    assert result.status == "success"
    assert result.metrics["chunk_skipped_count"] >= 1
    event_log_path = Path(result.artifacts["live_event_log"])
    events = event_log_path.read_text(encoding="utf-8").splitlines()
    assert any('"event": "global_seeds_reused"' in line for line in events)
    assert any('"event": "chunk_skipped"' in line for line in events)


def test_upload_paths_apply_azure_tuning_options(tmp_path: Path) -> None:
    path = tmp_path / "sample.parquet"
    path.write_bytes(b"payload")
    calls: list[tuple[str, dict, dict]] = []

    class FakeBlobClient:
        def __init__(self, blob_name: str, kwargs: dict) -> None:
            self.blob_name = blob_name
            self.kwargs = kwargs

        def upload_blob(self, handle, **kwargs) -> None:
            calls.append((self.blob_name, self.kwargs, {"payload": handle.read(), **kwargs}))

    class FakeContainer:
        def get_blob_client(self, blob_name: str, **kwargs):
            return FakeBlobClient(blob_name, kwargs)

    uploaded = _upload_paths(
        FakeContainer(),
        [path],
        "raw-bounded/patstat/field=computer-technology/year=2018-2020/family=core",
        {"max_concurrency": 3, "max_block_size": 8 * 1024 * 1024, "max_single_put_size": 16 * 1024 * 1024},
        chunk_id="chunk-1",
    )

    assert uploaded == [
        "raw-bounded/patstat/field=computer-technology/year=2018-2020/family=core/sample.parquet"
    ]
    assert calls[0][1]["max_block_size"] == 8 * 1024 * 1024
    assert calls[0][1]["max_single_put_size"] == 16 * 1024 * 1024
    assert calls[0][2]["max_concurrency"] == 3
    assert calls[0][2]["max_block_size"] == 8 * 1024 * 1024
    assert calls[0][2]["max_single_put_size"] == 16 * 1024 * 1024
    assert calls[0][2]["length"] == len(b"payload")
    assert calls[0][2]["overwrite"] is True
    assert calls[0][2]["payload"] == b"payload"


def test_upload_paths_fall_back_for_older_azure_blob_clients(tmp_path: Path) -> None:
    path = tmp_path / "sample.parquet"
    path.write_bytes(b"payload")
    calls: list[tuple[str, dict]] = []

    class FakeBlobClient:
        def upload_blob(self, handle, **kwargs) -> None:
            if "max_concurrency" in kwargs or "max_block_size" in kwargs or "max_single_put_size" in kwargs:
                raise TypeError("older sdk")
            calls.append((handle.read().decode("utf-8"), kwargs))

    class OldContainer:
        def get_blob_client(self, blob_name: str, **kwargs):
            if kwargs:
                raise TypeError("older sdk")
            return FakeBlobClient()

    uploaded = _upload_paths(
        OldContainer(),
        [path],
        "raw-bounded/patstat/field=computer-technology/year=2018-2020/family=core",
        {"max_concurrency": 3, "max_block_size": 8 * 1024 * 1024, "max_single_put_size": 16 * 1024 * 1024},
        chunk_id="chunk-1",
    )

    assert uploaded == [
        "raw-bounded/patstat/field=computer-technology/year=2018-2020/family=core/sample.parquet"
    ]
    assert calls == [("payload", {"overwrite": True})]


def test_upload_paths_retry_transient_timeout_then_succeed(tmp_path: Path) -> None:
    path = tmp_path / "sample.parquet"
    path.write_bytes(b"payload")
    calls: list[int] = []

    class FakeBlobClient:
        def upload_blob(self, handle, **kwargs) -> None:
            calls.append(1)
            if len(calls) == 1:
                raise TimeoutError("The write operation timed out")

    class FakeContainer:
        def get_blob_client(self, blob_name: str, **kwargs):
            return FakeBlobClient()

    uploaded = _upload_paths(
        FakeContainer(),
        [path],
        "raw-bounded/patstat/field=computer-technology/year=2018-2020/family=core",
        {
            "max_concurrency": 1,
            "max_block_size": 4 * 1024 * 1024,
            "max_single_put_size": 8 * 1024 * 1024,
            "retry_max_attempts": 2,
            "retry_backoff_seconds": 1,
        },
        chunk_id="chunk-1",
    )

    assert uploaded == [
        "raw-bounded/patstat/field=computer-technology/year=2018-2020/family=core/sample.parquet"
    ]
    assert len(calls) == 2


def test_get_container_client_applies_blob_transport_timeouts(tmp_path: Path, monkeypatch) -> None:
    settings = _settings(tmp_path)
    settings.execution["blob_intermediate_enabled"] = True
    settings.execution["upload_connection_timeout_seconds"] = 45
    settings.execution["upload_read_timeout_seconds"] = 900
    settings.azure["connection_string_env"] = "AZURE_STORAGE_CONNECTION_STRING"
    monkeypatch.setenv("AZURE_STORAGE_CONNECTION_STRING", "UseDevelopmentStorage=true")
    captured: dict[str, object] = {}

    class FakeService:
        def get_container_client(self, container_name: str):
            captured["container_name"] = container_name
            return {"container": container_name}

    class FakeBlobServiceClient:
        @classmethod
        def from_connection_string(cls, connection_string: str, **kwargs):
            captured["connection_string"] = connection_string
            captured["kwargs"] = kwargs
            return FakeService()

    fake_blob_module = type(sys)("azure.storage.blob")
    fake_blob_module.BlobServiceClient = FakeBlobServiceClient
    monkeypatch.setitem(sys.modules, "azure.storage.blob", fake_blob_module)

    container = _get_container_client(settings)

    assert container == {"container": settings.azure["container"]}
    assert captured["connection_string"] == "UseDevelopmentStorage=true"
    assert captured["kwargs"] == {"connection_timeout": 45, "read_timeout": 900}
    assert captured["container_name"] == settings.azure["container"]


def test_citation_npl_column_detection_supports_tip_column_shape(tmp_path: Path) -> None:
    citation_path = tmp_path / "tls212_citation.parquet"
    write_pylist_parquet(
        [{"pat_publn_id": 1, "cited_npl_publn_id": 9001}],
        citation_path,
    )

    assert _citation_npl_column(citation_path) == "cited_npl_publn_id"
    assert _citation_npl_column_from_parquet(citation_path) == "cited_npl_publn_id"


def test_recover_tip_blob_uploads_updates_manifest_and_cleans_temp(tmp_path: Path, monkeypatch) -> None:
    settings = _settings(tmp_path)
    settings.execution["blob_intermediate_enabled"] = True
    settings.execution["upload_after_chunk"] = True
    settings.azure["connection_string_env"] = "AZURE_STORAGE_CONNECTION_STRING"
    chunk_id = "computer-technology__2018_2020__citations"
    temp_dir = settings.repo_root / "etl" / "data" / "temp" / "chunks" / chunk_id / "patstat"
    output_path = ensure_dir(temp_dir) / "tls212_citation.parquet"
    output_path.write_bytes(b"payload")
    manifest_path = ensure_dir(settings.manifests_dir / "chunks") / f"{chunk_id}.json"
    manifest_path.write_text(
        json.dumps(
            {
                "chunk_id": chunk_id,
                "field": "Computer technology",
                "year_start": 2018,
                "year_end": 2020,
                "table_family": "citations",
                "status": "success",
                "local_outputs": [str(output_path)],
                "uploaded_blobs": [],
                "metrics": {},
                "warnings": [],
            }
        ),
        encoding="utf-8",
    )

    class FakeContainer:
        pass

    monkeypatch.setattr("patentiq_etl.prebronze.chunked._get_container_client", lambda settings: FakeContainer())

    uploaded: list[tuple[list[str], str]] = []

    def fake_upload(container, files, blob_prefix, upload_options, **kwargs):
        uploaded.append(([path.name for path in files], blob_prefix))
        return [f"{blob_prefix}/{path.name}" for path in files]

    monkeypatch.setattr("patentiq_etl.prebronze.chunked._upload_paths", fake_upload)

    result = recover_tip_blob_uploads(settings).finish()

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert result.status == "success"
    assert result.metrics["recovery_recovered_chunk_count"] == 1
    assert payload["uploaded_blobs"] == [
        "raw-bounded/patstat/field=computer-technology/year=2018-2020/family=citations/tls212_citation.parquet"
    ]
    assert "recovered_at" in payload
    assert uploaded == [
        (
            ["tls212_citation.parquet"],
            "raw-bounded/patstat/field=computer-technology/year=2018-2020/family=citations",
        )
    ]
    assert not output_path.exists()


def test_recover_tip_blob_uploads_restores_failed_upload_timeout_chunk(tmp_path: Path, monkeypatch) -> None:
    settings = _settings(tmp_path)
    settings.execution["blob_intermediate_enabled"] = True
    settings.execution["upload_after_chunk"] = True
    settings.azure["connection_string_env"] = "AZURE_STORAGE_CONNECTION_STRING"
    chunk_id = "telecommunications__2013_2015__citations"
    temp_dir = settings.repo_root / "etl" / "data" / "temp" / "chunks" / chunk_id / "patstat"
    output_path = ensure_dir(temp_dir) / "tls212_citation.parquet"
    output_path.write_bytes(b"payload")
    manifest_path = ensure_dir(settings.manifests_dir / "chunks") / f"{chunk_id}.json"
    manifest_path.write_text(
        json.dumps(
            {
                "chunk_id": chunk_id,
                "field": "Telecommunications",
                "year_start": 2013,
                "year_end": 2015,
                "table_family": "citations",
                "status": "failed",
                "local_outputs": [str(output_path)],
                "uploaded_blobs": [],
                "metrics": {"local_output_file_count": 1},
                "warnings": ["Connection timeout while uploading blob to Azure storage."],
            }
        ),
        encoding="utf-8",
    )

    class FakeContainer:
        pass

    monkeypatch.setattr("patentiq_etl.prebronze.chunked._get_container_client", lambda settings: FakeContainer())

    uploaded: list[tuple[list[str], str]] = []

    def fake_upload(container, files, blob_prefix, upload_options, **kwargs):
        uploaded.append(([path.name for path in files], blob_prefix))
        return [f"{blob_prefix}/{path.name}" for path in files]

    monkeypatch.setattr("patentiq_etl.prebronze.chunked._upload_paths", fake_upload)

    result = recover_tip_blob_uploads(settings).finish()

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert result.status == "success"
    assert result.metrics["recovery_recovered_chunk_count"] == 1
    assert payload["status"] == "success"
    assert payload["recovered_from_status"] == "failed"
    assert payload["uploaded_blobs"] == [
        "raw-bounded/patstat/field=telecommunications/year=2013-2015/family=citations/tls212_citation.parquet"
    ]
    assert uploaded == [
        (
            ["tls212_citation.parquet"],
            "raw-bounded/patstat/field=telecommunications/year=2013-2015/family=citations",
        )
    ]
    assert not output_path.exists()


def test_backfill_tip_derived_seeds_rebuilds_canonical_seeds_from_local_success_chunks(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    settings.execution["table_families"] = ["core", "publications"]

    publications_chunk_id = "computer-technology__2018_2020__publications"
    publications_dir = settings.repo_root / "etl" / "data" / "temp" / "chunks" / publications_chunk_id / "patstat"
    publications_path = ensure_dir(publications_dir) / f"{PATSTAT_TABLES['bronze_patstat_pat_publn'][0]}.parquet"
    write_pylist_parquet(
        [
            {"pat_publn_id": 1, "appln_id": 10, "publn_auth": "EP", "publn_nr": "123", "publn_kind": "A1", "publn_date": "2024-01-01"},
            {"pat_publn_id": 2, "appln_id": 11, "publn_auth": "US", "publn_nr": "456", "publn_kind": "B1", "publn_date": "2024-01-02"},
        ],
        publications_path,
    )
    publications_manifest = ensure_dir(settings.manifests_dir / "chunks") / f"{publications_chunk_id}.json"
    publications_manifest.write_text(
        json.dumps(
            {
                "chunk_id": publications_chunk_id,
                "field": "Computer technology",
                "year_start": 2018,
                "year_end": 2020,
                "table_family": "publications",
                "status": "success",
                "local_outputs": [str(publications_path)],
                "uploaded_blobs": [],
                "metrics": {},
                "warnings": [],
            }
        ),
        encoding="utf-8",
    )

    core_chunk_id = "computer-technology__2018_2020__core"
    core_dir = settings.repo_root / "etl" / "data" / "temp" / "chunks" / core_chunk_id / "patstat"
    core_path = ensure_dir(core_dir) / f"{PATSTAT_TABLES['bronze_patstat_pers_appln'][0]}.parquet"
    write_pylist_parquet(
        [{"appln_id": 10, "person_id": 9001}, {"appln_id": 10, "person_id": 9002}],
        core_path,
    )
    core_manifest = ensure_dir(settings.manifests_dir / "chunks") / f"{core_chunk_id}.json"
    core_manifest.write_text(
        json.dumps(
            {
                "chunk_id": core_chunk_id,
                "field": "Computer technology",
                "year_start": 2018,
                "year_end": 2020,
                "table_family": "core",
                "status": "success",
                "local_outputs": [str(core_path)],
                "uploaded_blobs": [],
                "metrics": {},
                "warnings": [],
            }
        ),
        encoding="utf-8",
    )

    result = backfill_tip_derived_seeds(settings).finish()

    assert result.status == "success"
    assert result.metrics["seed_backfill_local_source_chunk_count"] == 2
    assert parquet_row_count(settings.bounded_seed_dir / "seed_publn_ids.parquet") == 2
    assert parquet_row_count(settings.bounded_seed_dir / "seed_ep_publication_numbers.parquet") == 1
    assert parquet_row_count(settings.bounded_seed_dir / "seed_us_publication_numbers.parquet") == 1
    assert parquet_row_count(settings.bounded_seed_dir / "seed_person_ids.parquet") == 2


def test_backfill_tip_derived_seeds_falls_back_to_blob_for_cleaned_success_chunks(tmp_path: Path, monkeypatch) -> None:
    settings = _settings(tmp_path)
    settings.execution["blob_intermediate_enabled"] = True
    settings.azure["connection_string_env"] = "AZURE_STORAGE_CONNECTION_STRING"
    publications_chunk_id = "telecommunications__2018_2020__publications"
    missing_local_path = settings.repo_root / "etl" / "data" / "temp" / "chunks" / publications_chunk_id / "patstat" / f"{PATSTAT_TABLES['bronze_patstat_pat_publn'][0]}.parquet"
    blob_name = "raw-bounded/patstat/field=telecommunications/year=2018-2020/family=publications/tls211_pat_publn.parquet"
    manifest_path = ensure_dir(settings.manifests_dir / "chunks") / f"{publications_chunk_id}.json"
    manifest_path.write_text(
        json.dumps(
            {
                "chunk_id": publications_chunk_id,
                "field": "Telecommunications",
                "year_start": 2018,
                "year_end": 2020,
                "table_family": "publications",
                "status": "success",
                "local_outputs": [str(missing_local_path)],
                "uploaded_blobs": [blob_name],
                "metrics": {},
                "warnings": [],
            }
        ),
        encoding="utf-8",
    )

    payload_path = tmp_path / "blob-publications.parquet"
    write_pylist_parquet(
        [{"pat_publn_id": 55, "appln_id": 77, "publn_auth": "EP", "publn_nr": "999", "publn_kind": "A1", "publn_date": "2024-01-03"}],
        payload_path,
    )

    class FakeDownloader:
        def readinto(self, handle) -> int:
            data = payload_path.read_bytes()
            handle.write(data)
            return len(data)

    class FakeBlobClient:
        def download_blob(self, **kwargs):
            return FakeDownloader()

    class FakeContainer:
        def get_blob_client(self, requested_blob_name: str, **kwargs):
            assert requested_blob_name == blob_name
            return FakeBlobClient()

    monkeypatch.setattr("patentiq_etl.prebronze.chunked._get_container_client", lambda settings: FakeContainer())
    monkeypatch.setattr(
        "patentiq_etl.prebronze.chunked._upload_paths",
        lambda container, files, blob_prefix, upload_options, **kwargs: [f"{blob_prefix}/{path.name}" for path in files],
    )

    result = backfill_tip_derived_seeds(settings).finish()

    assert result.status == "success"
    assert result.metrics["seed_backfill_blob_source_chunk_count"] == 1
    assert parquet_row_count(settings.bounded_seed_dir / "seed_publn_ids.parquet") == 1
    assert parquet_row_count(settings.bounded_seed_dir / "seed_ep_publication_numbers.parquet") == 1
