from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import duckdb

from patentiq_etl.common.io import ensure_dir, parquet_row_count, write_pylist_parquet
from patentiq_etl.common.types import BuildSettings
from patentiq_etl.prebronze.consolidate import consolidate_before_bronze


def _settings(tmp_path: Path) -> BuildSettings:
    root = tmp_path / "repo"
    return BuildSettings(
        repo_root=root,
        release_id="test-release",
        snapshot_date="2026-03-30",
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
        patstat_source_mode="tip",
        register_source_mode="tip",
        epab_source_mode="tip",
        uspto_source_mode="odp_api",
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
        azure={"container": "patentiq-data", "connection_string_env": "AZURE_STORAGE_CONNECTION_STRING"},
        execution={},
    )


@dataclass
class _BlobItem:
    name: str


class _Downloader:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    def readinto(self, handle) -> int:
        handle.write(self.payload)
        return len(self.payload)

    def readall(self) -> bytes:
        return self.payload


class _BlobClient:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    def download_blob(self, max_concurrency: int = 1) -> _Downloader:
        return _Downloader(self.payload)


class _Container:
    def __init__(self, blobs: dict[str, bytes]) -> None:
        self.blobs = blobs

    def list_blobs(self, name_starts_with: str):
        return [_BlobItem(name) for name in sorted(self.blobs) if name.startswith(name_starts_with)]

    def get_blob_client(self, blob_name: str) -> _BlobClient:
        return _BlobClient(self.blobs[blob_name])


def _parquet_bytes(tmp_path: Path, name: str, rows: list[dict]) -> bytes:
    path = ensure_dir(tmp_path / "blob-fixtures") / name
    write_pylist_parquet(rows, path)
    return path.read_bytes()


def test_consolidate_before_bronze_downloads_and_flattens_blob_chunk_outputs(tmp_path: Path, monkeypatch) -> None:
    settings = _settings(tmp_path)

    main_seed = ensure_dir(settings.bounded_seed_dir) / "seed_appln_ids.parquet"
    write_pylist_parquet([{"appln_id": 999}], main_seed)

    stale_epab = ensure_dir(settings.bounded_epab_dir) / "epab_application.parquet"
    write_pylist_parquet([{"epab_doc_id": "stale"}], stale_epab)

    blobs = {
        "raw-bounded/patstat/field=computer-technology/year=2007-2008/family=core/tls201_appln.parquet": _parquet_bytes(
            tmp_path,
            "tls201_main_a.parquet",
            [{"appln_id": 1, "docdb_family_id": 100, "appln_auth": "EP"}],
        ),
        "raw-bounded/patstat/field=computer-technology/year=2009-2010/family=core/tls201_appln.parquet": _parquet_bytes(
            tmp_path,
            "tls201_main_b.parquet",
            [{"appln_id": 1, "docdb_family_id": 100, "appln_auth": "EP"}],
        ),
        "raw-bounded/patstat/field=computer-technology/year=2007-2008/family=publications/tls211_pat_publn.parquet": _parquet_bytes(
            tmp_path,
            "tls211_main.parquet",
            [{"pat_publn_id": 11, "appln_id": 1, "publn_auth": "EP", "publn_kind": "A1"}],
        ),
        "raw-bounded/register/field=computer-technology/year=2007-2008/family=register/reg101_appln.parquet": _parquet_bytes(
            tmp_path,
            "reg101_main.parquet",
            [{"id": 7001, "appln_id": 1}],
        ),
        "raw-bounded/epab/field=computer-technology/year=2007-2008/family=epab/epab_publication.parquet": _parquet_bytes(
            tmp_path,
            "epab_publication.parquet",
            [{"epab_doc_id": "doc-1", "publication_number_full": "EP123A1"}],
        ),
        "raw-bounded/epab/field=computer-technology/year=2007-2008/family=epab/epab_abstract.parquet": _parquet_bytes(
            tmp_path,
            "epab_abstract.parquet",
            [{"epab_doc_id": "doc-1", "language_code": "EN", "abstract_text": "Example abstract"}],
        ),
        "raw-bounded/epab/field=computer-technology/year=2007-2008/family=epab/epab_claims.parquet": _parquet_bytes(
            tmp_path,
            "epab_claims.parquet",
            [{"epab_doc_id": "doc-1", "claim_id": "c1", "claim_sequence_no": 1, "language_code": "EN", "claim_text_plain": "Claim"}],
        ),
        "raw-bounded/refs/wipo_techn_field_ipc.parquet": _parquet_bytes(
            tmp_path,
            "wipo_techn_field_ipc.parquet",
            [{"techn_field": "Computer technology", "ipc_subclass": "G06F"}],
        ),
        "raw-bounded-heritage/patstat/field=computer-technology/year=1999-2000/family=core/tls201_appln.parquet": _parquet_bytes(
            tmp_path,
            "tls201_heritage.parquet",
            [{"appln_id": 2, "docdb_family_id": 200, "appln_auth": "US"}],
        ),
        "raw-bounded-heritage/seeds/seed_appln_ids.parquet": _parquet_bytes(
            tmp_path,
            "seed_appln_ids_heritage.parquet",
            [{"appln_id": 2}],
        ),
    }

    monkeypatch.setattr(
        "patentiq_etl.prebronze.consolidate._blob_container_client",
        lambda settings: (_Container(blobs), {"max_concurrency": 1, "retry_max_attempts": 1, "retry_backoff_seconds": 1}),
    )

    result = consolidate_before_bronze(settings).finish()

    assert result.status == "success"
    assert result.metrics["staged_blob_file_count"] == len(blobs)
    assert result.metrics["heritage_seed_staging_count"] == 1

    tls201_out = settings.bounded_patstat_dir / "tls201_appln.parquet"
    assert tls201_out.exists()
    assert parquet_row_count(tls201_out) == 2
    con = duckdb.connect()
    appln_ids = con.execute("select appln_id from read_parquet(?) order by appln_id", [str(tls201_out)]).fetchall()
    assert appln_ids == [(1,), (2,)]

    tls211_out = settings.bounded_patstat_dir / "tls211_pat_publn.parquet"
    assert tls211_out.exists()
    assert parquet_row_count(tls211_out) == 1

    reg101_out = settings.bounded_register_dir / "reg101_appln.parquet"
    assert reg101_out.exists()
    assert parquet_row_count(reg101_out) == 1

    ref_out = settings.bounded_refs_dir / "wipo_techn_field_ipc.parquet"
    assert ref_out.exists()
    assert parquet_row_count(ref_out) == 1

    epab_pub_out = settings.bounded_epab_dir / "epab_publication.parquet"
    epab_abs_out = settings.bounded_epab_dir / "epab_abstract.parquet"
    epab_claim_out = settings.bounded_epab_dir / "epab_claims.parquet"
    assert epab_pub_out.exists()
    assert epab_abs_out.exists()
    assert epab_claim_out.exists()
    assert not stale_epab.exists()

    heritage_seed_staged = settings.repo_root / "etl/data/imports/raw-bounded-heritage/_seeds/seed_appln_ids.parquet"
    assert heritage_seed_staged.exists()
    assert parquet_row_count(heritage_seed_staged) == 1

    main_seed_rows = con.execute("select appln_id from read_parquet(?)", [str(main_seed)]).fetchall()
    assert main_seed_rows == [(999,)]
