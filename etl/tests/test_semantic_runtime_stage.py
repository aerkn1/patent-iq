from __future__ import annotations

import json
import sys
import types
from pathlib import Path

import duckdb
import numpy as np

from patentiq_etl.common.io import ensure_dir, write_pylist_parquet
from patentiq_etl.common.types import BuildSettings
from patentiq_etl.semantic.run import run_semantic, run_semantic_ann


def _settings(tmp_path: Path) -> BuildSettings:
    root = tmp_path / "repo"
    return BuildSettings(
        repo_root=root,
        release_id="test-release",
        snapshot_date="2026-03-15",
        year_window_start=2007,
        year_window_end=2026,
        heritage_backfill_start=1996,
        heritage_backfill_end=2006,
        azure_publish_enabled=False,
        vector_sample_pct=1.0,
        active_grant_only_for_semantic=True,
        method_version="test_method_v1",
        semantic_embedding_method="stable_hash_embedding_mvp",
        semantic_ann_method="manifest_only_placeholder",
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


def test_run_semantic_materializes_phase01_runtime_outputs(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    ensure_dir(settings.silver_dir)
    ensure_dir(settings.gold_dir)
    ensure_dir(settings.ml_dir)

    write_pylist_parquet(
        [
            {
                "docdb_family_id": 101,
                "representative_appln_id": 1,
                "representative_publn_id": 11,
                "representative_stage": "STANDARD_GRANT",
                "representative_claim_1_en": "wireless packet scheduler",
                "representative_abstract_en": "A wireless packet scheduling method.",
                "representative_source_type": "EPAB_CLAIM",
                "text_provenance": "EPAB_EP1B1",
                "is_abstract_fallback": False,
            },
            {
                "docdb_family_id": 202,
                "representative_appln_id": 2,
                "representative_publn_id": 22,
                "representative_stage": "PATSTAT_ABSTRACT_FALLBACK",
                "representative_claim_1_en": None,
                "representative_abstract_en": "A battery control system for electric vehicles.",
                "representative_source_type": "PATSTAT_ABSTRACT",
                "text_provenance": "PATSTAT_ABSTRACT",
                "is_abstract_fallback": True,
            },
        ],
        settings.silver_dir / "silver_family_text_representative.parquet",
    )
    write_pylist_parquet(
        [
            {"docdb_family_id": 101, "is_semantic_candidate": True, "is_in_vector_sample": True},
            {"docdb_family_id": 202, "is_semantic_candidate": True, "is_in_vector_sample": True},
        ],
        settings.silver_dir / "silver_semantic_sampling_eligibility.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 101,
                "owner_name_harmonized": "ACME",
                "covered_wipo_fields": ["Computer technology"],
                "family_ui_blocking_power_score": 81.0,
                "oecd_quality_percentile": 0.93,
            },
            {
                "docdb_family_id": 202,
                "owner_name_harmonized": "BETA",
                "covered_wipo_fields": ["Electrical machinery, apparatus, energy"],
                "family_ui_blocking_power_score": 40.0,
                "oecd_quality_percentile": 0.44,
            },
        ],
        settings.gold_dir / "gold_semantic_match_context.parquet",
    )
    write_pylist_parquet(
        [
            {"docdb_family_id": 101, "family_composite_status": "fully_active"},
            {"docdb_family_id": 202, "family_composite_status": "dead"},
        ],
        settings.silver_dir / "silver_family_status_pt.parquet",
    )
    write_pylist_parquet(
        [
            {"docdb_family_id": 101, "family_earliest_priority_date": "2012-02-01"},
            {"docdb_family_id": 202, "family_earliest_priority_date": "2015-04-10"},
        ],
        settings.gold_dir / "gold_family_summary.parquet",
    )
    write_pylist_parquet(
        [
            {"docdb_family_id": 101, "family_ui_blocking_power_score": 81.0},
            {"docdb_family_id": 202, "family_ui_blocking_power_score": 40.0},
        ],
        settings.gold_dir / "gold_family_blocking_power.parquet",
    )
    write_pylist_parquet(
        [
            {
                "fixture_id": "claim_0001",
                "fixture_group": "claim_active_discovery",
                "workflow_type": "text_to_family_semantic_search",
                "docdb_family_id": 101,
                "vector_space": "vector_claims",
                "query_text": "wireless packet scheduler",
                "expected_behavior": "allow_current_strategic_display",
                "expected_current_threat_allowed": True,
                "primary_wipo_field": "Computer technology",
                "family_composite_status": "fully_active",
            },
            {
                "fixture_id": "abstract_0001",
                "fixture_group": "dead_family_suppression",
                "workflow_type": "semantic_current_threat_gating",
                "docdb_family_id": 202,
                "vector_space": "vector_abstract",
                "query_text": "battery control system electric vehicles",
                "expected_behavior": "suppress_current_threat_display",
                "expected_current_threat_allowed": False,
                "primary_wipo_field": "Electrical machinery, apparatus, energy",
                "family_composite_status": "dead",
            },
        ],
        settings.ml_dir / "semantic_eval_fixture_registry.parquet",
    )

    result = run_semantic(settings)[0].finish()
    assert result.status == "success"

    claims = settings.vectors_dir / "vec_family_embeddings_claims.parquet"
    abstracts = settings.vectors_dir / "vec_family_embeddings_abstracts.parquet"
    query_registry = settings.vectors_dir / "vec_query_registry.parquet"
    manifest = settings.vectors_dir / "vec_embedding_manifest.json"
    ann_manifest = settings.vectors_dir / "vec_ann_index_manifest.json"

    assert claims.exists()
    assert abstracts.exists()
    assert query_registry.exists()
    assert manifest.exists()
    assert ann_manifest.exists()

    con = duckdb.connect()
    assert con.execute(f"select count(*) from read_parquet('{claims}')").fetchone()[0] == 1
    assert con.execute(f"select count(*) from read_parquet('{abstracts}')").fetchone()[0] == 2
    assert con.execute(f"select count(*) from read_parquet('{query_registry}')").fetchone()[0] == 2
    assert (
        con.execute(f"select count(*) from read_parquet('{query_registry}') where vector_space = 'vector_claims'").fetchone()[0]
        == 1
    )
    assert (
        con.execute(f"select count(*) from read_parquet('{claims}') where family_composite_status is null").fetchone()[0]
        == 0
    )

    manifest_payload = json.loads(manifest.read_text())
    ann_payload = json.loads(ann_manifest.read_text())
    assert manifest_payload["embedding_runtime"] == "lexical_hash_exact_scan_v1"
    assert manifest_payload["query_registry_count"] == 2
    assert ann_payload["index_status"] == "not_built_exact_scan_only"


class _FakeHnswIndex:
    _saved: dict[str, tuple[np.ndarray, np.ndarray]] = {}

    def __init__(self, space: str, dim: int) -> None:
        self.space = space
        self.dim = dim
        self.items = np.empty((0, dim), dtype=np.float32)
        self.ids = np.empty(0, dtype=np.uint32)

    def init_index(self, max_elements: int, ef_construction: int, M: int) -> None:  # noqa: N803
        self.max_elements = max_elements
        self.ef_construction = ef_construction
        self.m = M

    def add_items(self, items: np.ndarray, ids: np.ndarray) -> None:
        self.items = np.asarray(items, dtype=np.float32)
        self.ids = np.asarray(ids, dtype=np.uint32)

    def set_ef(self, ef: int) -> None:
        self.ef = ef

    def save_index(self, path: str) -> None:
        _FakeHnswIndex._saved[path] = (self.items.copy(), self.ids.copy())
        Path(path).write_bytes(b"fake-hnsw-index")

    def load_index(self, path: str, max_elements: int | None = None) -> None:
        self.items, self.ids = _FakeHnswIndex._saved[path]
        self.max_elements = max_elements

    def knn_query(self, queries: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]:
        query_array = np.asarray(queries, dtype=np.float32)
        sims = np.matmul(query_array, self.items.T)
        top_idx = np.argsort(-sims, axis=1)[:, :k]
        top_scores = np.take_along_axis(sims, top_idx, axis=1)
        return self.ids[top_idx], 1.0 - top_scores


def test_run_semantic_ann_builds_snapshots_and_updates_manifest(tmp_path: Path, monkeypatch) -> None:
    settings = _settings(tmp_path)
    ensure_dir(settings.vectors_dir)

    claims = settings.vectors_dir / "vec_family_embeddings_claims.parquet"
    abstracts = settings.vectors_dir / "vec_family_embeddings_abstracts.parquet"
    query_registry = settings.vectors_dir / "vec_query_registry.parquet"
    embedding_manifest = settings.vectors_dir / "vec_embedding_manifest.json"

    write_pylist_parquet(
        [
            {
                "docdb_family_id": 11,
                "representative_appln_id": 101,
                "representative_publn_id": 1001,
                "representative_stage": "STANDARD_GRANT",
                "vector_space": "vector_claims",
                "queryable_text": "claim alpha",
                "token_count": 2,
                "text_provenance": "EPAB_EP1",
                "text_source_type": "EPAB_CLAIM",
                "is_abstract_fallback": False,
                "family_earliest_priority_date": "2011-01-01",
                "primary_wipo_field": "Computer technology",
                "owner_name_harmonized": "ACME",
                "family_ui_blocking_power_score": 81.0,
                "oecd_quality_percentile": 0.91,
                "family_composite_status": "fully_active",
                "embedding_model": "AI-Growth-Lab/PatentSBERTa",
                "embedding_model_version": "v2_mvp_local_etl",
                "embedding_runtime": "promoted_dual_runtime_dense_only_v1",
                "language_code": "en",
                "is_machine_translated": False,
                "corpus_snapshot": "2026-03-15",
                "embedding": [1.0, 0.0],
            },
            {
                "docdb_family_id": 22,
                "representative_appln_id": 202,
                "representative_publn_id": 2002,
                "representative_stage": "STANDARD_GRANT",
                "vector_space": "vector_claims",
                "queryable_text": "claim beta",
                "token_count": 2,
                "text_provenance": "EPAB_EP2",
                "text_source_type": "EPAB_CLAIM",
                "is_abstract_fallback": False,
                "family_earliest_priority_date": "2012-01-01",
                "primary_wipo_field": "Computer technology",
                "owner_name_harmonized": "BETA",
                "family_ui_blocking_power_score": 62.0,
                "oecd_quality_percentile": 0.77,
                "family_composite_status": "fully_active",
                "embedding_model": "AI-Growth-Lab/PatentSBERTa",
                "embedding_model_version": "v2_mvp_local_etl",
                "embedding_runtime": "promoted_dual_runtime_dense_only_v1",
                "language_code": "en",
                "is_machine_translated": False,
                "corpus_snapshot": "2026-03-15",
                "embedding": [0.0, 1.0],
            },
        ],
        claims,
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1011,
                "representative_appln_id": 301,
                "representative_publn_id": 3001,
                "representative_stage": "STANDARD_GRANT",
                "vector_space": "vector_abstract",
                "queryable_text": "abstract alpha",
                "token_count": 2,
                "text_provenance": "PATSTAT_ABSTRACT",
                "text_source_type": "PATSTAT_ABSTRACT",
                "is_abstract_fallback": False,
                "family_earliest_priority_date": "2010-01-01",
                "primary_wipo_field": "Computer technology",
                "owner_name_harmonized": "ACME",
                "family_ui_blocking_power_score": 51.0,
                "oecd_quality_percentile": 0.66,
                "family_composite_status": "dead",
                "embedding_model": "BAAI/bge-m3",
                "embedding_model_version": "v2_mvp_local_etl",
                "embedding_runtime": "promoted_dual_runtime_dense_only_v1",
                "language_code": "en",
                "is_machine_translated": False,
                "corpus_snapshot": "2026-03-15",
                "embedding": [1.0, 0.0],
            },
            {
                "docdb_family_id": 2022,
                "representative_appln_id": 302,
                "representative_publn_id": 3002,
                "representative_stage": "STANDARD_GRANT",
                "vector_space": "vector_abstract",
                "queryable_text": "abstract beta",
                "token_count": 2,
                "text_provenance": "PATSTAT_ABSTRACT",
                "text_source_type": "PATSTAT_ABSTRACT",
                "is_abstract_fallback": False,
                "family_earliest_priority_date": "2014-01-01",
                "primary_wipo_field": "Electrical machinery, apparatus, energy",
                "owner_name_harmonized": "BETA",
                "family_ui_blocking_power_score": 55.0,
                "oecd_quality_percentile": 0.72,
                "family_composite_status": "fully_active",
                "embedding_model": "BAAI/bge-m3",
                "embedding_model_version": "v2_mvp_local_etl",
                "embedding_runtime": "promoted_dual_runtime_dense_only_v1",
                "language_code": "en",
                "is_machine_translated": False,
                "corpus_snapshot": "2026-03-15",
                "embedding": [0.0, 1.0],
            },
        ],
        abstracts,
    )
    write_pylist_parquet(
        [
            {
                "query_id": "claim_q1",
                "query_source": "fixture",
                "fixture_group": "claims",
                "workflow_type": "search",
                "anchor_family_id": 11,
                "vector_space": "vector_claims",
                "query_text": "claim alpha",
                "token_count": 2,
                "expected_behavior": "allow",
                "expected_current_threat_allowed": True,
                "primary_wipo_field": "Computer technology",
                "family_composite_status": "fully_active",
                "embedding_model": "AI-Growth-Lab/PatentSBERTa",
                "embedding_model_version": "v2_mvp_local_etl",
                "embedding_runtime": "promoted_dual_runtime_dense_only_v1",
                "corpus_snapshot": "2026-03-15",
                "embedding": [1.0, 0.0],
            },
            {
                "query_id": "abstract_q1",
                "query_source": "fixture",
                "fixture_group": "abstracts",
                "workflow_type": "search",
                "anchor_family_id": 2022,
                "vector_space": "vector_abstract",
                "query_text": "abstract beta",
                "token_count": 2,
                "expected_behavior": "allow",
                "expected_current_threat_allowed": True,
                "primary_wipo_field": "Electrical machinery, apparatus, energy",
                "family_composite_status": "fully_active",
                "embedding_model": "BAAI/bge-m3",
                "embedding_model_version": "v2_mvp_local_etl",
                "embedding_runtime": "promoted_dual_runtime_dense_only_v1",
                "corpus_snapshot": "2026-03-15",
                "embedding": [0.0, 1.0],
            },
        ],
        query_registry,
    )
    embedding_manifest.write_text(
        json.dumps(
            {
                "embedding_device": "mps",
                "claim_payload_path": str(claims),
                "abstract_payload_path": str(abstracts),
            }
        )
    )

    monkeypatch.setitem(sys.modules, "hnswlib", types.SimpleNamespace(Index=_FakeHnswIndex))

    result = run_semantic_ann(settings)[0].finish()
    assert result.status == "success"

    ann_manifest = settings.vectors_dir / "vec_ann_index_manifest.json"
    ann_audit = settings.vectors_dir / "vec_ann_exact_vs_ann_audit.json"
    assert ann_manifest.exists()
    assert ann_audit.exists()

    ann_payload = json.loads(ann_manifest.read_text())
    audit_payload = json.loads(ann_audit.read_text())
    assert ann_payload["index_status"] == "built_hnsw_snapshot"
    assert ann_payload["claim_payload_count"] == 2
    assert ann_payload["abstract_payload_count"] == 2
    assert ann_payload["query_anchor_claim_coverage"] == 1.0
    assert ann_payload["query_anchor_abstract_coverage"] == 1.0
    assert ann_payload["claim_exact_vs_ann_recall_at_10"] == 1.0
    assert ann_payload["abstract_exact_vs_ann_recall_at_10"] == 1.0
    assert ann_payload["claim_corpus_sample_exact_vs_ann_recall_at_10"] == 1.0
    assert ann_payload["abstract_corpus_sample_exact_vs_ann_recall_at_10"] == 1.0
    assert audit_payload["claim"]["exact_vs_ann_match_at_1"] == 1.0
    assert audit_payload["abstract"]["exact_vs_ann_match_at_1"] == 1.0
    assert audit_payload["claim"]["corpus_sample_exact_vs_ann_match_at_1"] == 1.0
    assert audit_payload["abstract"]["corpus_sample_exact_vs_ann_match_at_1"] == 1.0
