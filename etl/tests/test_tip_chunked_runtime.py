from __future__ import annotations

from collections import Counter
from pathlib import Path
from threading import Lock
import json
import time

from patentiq_etl.common.io import ensure_dir, write_pylist_parquet
from patentiq_etl.common.types import BuildSettings
from patentiq_etl.prebronze.chunked import _citation_npl_column, _upload_paths, recover_tip_blob_uploads, run_tip_chunked_export
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
            out_path = ensure_dir(out_dir) / f"{family_name}.parquet"
            out_path.write_text(family_name, encoding="utf-8")
            return [out_path]
        finally:
            with lock:
                active_total -= 1
                family_active[family_name] -= 1

    def fake_seed(settings, result, *, seed_dir=None):
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
        for path in outputs.values():
            path.write_text("seed", encoding="utf-8")
            result.outputs.append(str(path))
        return outputs

    monkeypatch.setattr("patentiq_etl.prebronze.chunked._chunk_scope_tip", fake_scope)
    monkeypatch.setattr("patentiq_etl.prebronze.chunked._extract_patstat_family", fake_extract)
    monkeypatch.setattr("patentiq_etl.prebronze.chunked._seed_patstat_scope_tip", fake_seed)

    result = run_tip_chunked_export(settings).finish()

    assert result.status == "success"
    assert result.metrics["chunk_scheduler_parallel_limit"] == 2
    assert result.metrics["global_seed_file_count"] == 8
    assert max_active_total <= 2
    assert family_max["core"] <= 1
    assert family_max["citations"] <= 1

    event_log_path = Path(result.artifacts["live_event_log"])
    assert event_log_path.exists()
    events = event_log_path.read_text(encoding="utf-8").splitlines()
    assert any('"event": "chunk_submitted"' in line for line in events)
    assert any('"event": "chunk_finished"' in line for line in events)
    assert any('"event": "global_seeds_finished"' in line for line in events)


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
