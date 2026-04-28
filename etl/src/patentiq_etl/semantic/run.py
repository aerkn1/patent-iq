from __future__ import annotations

import json
import hashlib
import logging
import os
import re
import gc
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import duckdb
import numpy as np

from patentiq_etl.common.io import ensure_dir, parquet_row_count, sanitize_semantic_text, write_pylist_parquet, write_text_json
from patentiq_etl.common.types import BuildSettings, StageResult


DEFAULT_SEMANTIC_BUCKETS = 16
FALLBACK_DIMS = 32
BGE_M3_MODEL_ID = "BAAI/bge-m3"
PATENT_SBERTA_MODEL_ID = "AI-Growth-Lab/PatentSBERTa"
DEFAULT_BATCH_SIZE = 64
DEFAULT_FETCH_CHUNK_ROWS = 2048
DEFAULT_ANN_AUDIT_TOP_K = 10
DEFAULT_ANN_AUDIT_BATCH_SIZE = 32
DEFAULT_ANN_AUDIT_MAX_QUERIES = 64
DEFAULT_ANN_CORPUS_SAMPLE_QUERIES = 128

logger = logging.getLogger("patentiq_etl.semantic")


@dataclass
class SemanticEncoderBundle:
    abstract_model_id: str
    abstract_model_version: str
    claim_model_id: str
    claim_model_version: str
    embedding_runtime: str
    uses_local_fallback: bool


def _resolve_embedding_device(bundle: SemanticEncoderBundle) -> str:
    if bundle.uses_local_fallback:
        return "cpu"
    requested = os.getenv("SEMANTIC_DEVICE", "").strip().lower()
    if requested:
        return requested
    try:
        import torch

        if getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
            return "mps"
    except Exception:
        pass
    return "cpu"


def _bool_env(name: str) -> bool:
    value = os.getenv(name, "").strip().lower()
    return value in {"1", "true", "yes", "y"}


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return int(raw)


def _optional_limit_clause(name: str) -> str:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return ""
    limit = int(raw)
    if limit <= 0:
        return ""
    return f" limit {limit}"


def _semantic_bucket_count() -> int:
    return _int_env("SEMANTIC_BUCKET_COUNT", DEFAULT_SEMANTIC_BUCKETS)


def _bucket_order_clause(bucket_row_limit_sql: str) -> str:
    if bucket_row_limit_sql:
        return """
        order by
            case
                when representative_claim_1_en is not null and trim(representative_claim_1_en) <> '' then 0
                else 1
            end,
            docdb_family_id
        """
    return "order by docdb_family_id"


def _sanitize_batch(texts: list[str | None]) -> list[str]:
    return [sanitize_semantic_text(text) or "" for text in texts]


def _hash_slot(token: str, seed: str = "") -> tuple[int, float]:
    digest = hashlib.sha256(f"{seed}{token}".encode("utf-8")).digest()
    slot = int.from_bytes(digest[:4], "little") % FALLBACK_DIMS
    sign = 1.0 if digest[4] % 2 == 0 else -1.0
    return slot, sign


def _lexical_hash_embedding(text: str) -> list[float]:
    vector = np.zeros(FALLBACK_DIMS, dtype=np.float64)
    tokens = re.findall(r"[A-Za-z0-9_]+", text.lower())
    for token in tokens:
        slot, sign = _hash_slot(token)
        vector[slot] += sign * (1.0 + min(len(token), 20) / 20.0)
        if len(token) >= 4:
            for trigram_idx in range(min(len(token) - 2, 3)):
                trigram = token[trigram_idx : trigram_idx + 3]
                tri_slot, tri_sign = _hash_slot(trigram, "tri:")
                vector[tri_slot] += tri_sign * 0.2
    norm = np.linalg.norm(vector)
    if norm == 0.0:
        return [0.0] * FALLBACK_DIMS
    normalized = vector / norm
    return [round(float(value), 6) for value in normalized]


def _fallback_encode(texts: list[str]) -> list[list[float]]:
    return [_lexical_hash_embedding(text) for text in texts]


def _build_encoder_bundle(settings: BuildSettings) -> SemanticEncoderBundle:
    if settings.semantic_embedding_method == "promoted_dual_runtime_v1":
        return SemanticEncoderBundle(
            abstract_model_id=BGE_M3_MODEL_ID,
            abstract_model_version=settings.method_version,
            claim_model_id=PATENT_SBERTA_MODEL_ID,
            claim_model_version=settings.method_version,
            embedding_runtime="promoted_dual_runtime_dense_only_v1",
            uses_local_fallback=False,
        )
    return SemanticEncoderBundle(
        abstract_model_id="lexical_hash_embedding_v1",
        abstract_model_version=settings.method_version,
        claim_model_id="lexical_hash_embedding_v1",
        claim_model_version=settings.method_version,
        embedding_runtime="lexical_hash_exact_scan_v1",
        uses_local_fallback=True,
    )


def _load_abstract_encoder(bundle: SemanticEncoderBundle, device: str):
    if bundle.uses_local_fallback:
        return _fallback_encode
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(BGE_M3_MODEL_ID, device=device)
    batch_size = _int_env("SEMANTIC_BATCH_SIZE", DEFAULT_BATCH_SIZE)

    def encode(texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        dense = model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return np.asarray(dense).tolist()

    return encode


def _load_claim_encoder(bundle: SemanticEncoderBundle, device: str):
    if bundle.uses_local_fallback:
        return _fallback_encode
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(PATENT_SBERTA_MODEL_ID, device=device)
    batch_size = _int_env("SEMANTIC_BATCH_SIZE", DEFAULT_BATCH_SIZE)

    def encode(texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        dense = model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return np.asarray(dense).tolist()

    return encode


def _release_torch_device_cache() -> None:
    torch = sys.modules.get("torch")
    if torch is not None:
        try:
            if getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
                try:
                    torch.mps.empty_cache()
                except Exception:
                    pass
            if torch.cuda.is_available():
                try:
                    torch.cuda.empty_cache()
                except Exception:
                    pass
        except Exception:
            pass
    gc.collect()


def _vector_columns() -> list[str]:
    return [
        "docdb_family_id",
        "representative_appln_id",
        "representative_publn_id",
        "representative_stage",
        "vector_space",
        "queryable_text",
        "token_count",
        "text_provenance",
        "text_source_type",
        "is_abstract_fallback",
        "family_earliest_priority_date",
        "primary_wipo_field",
        "owner_name_harmonized",
        "family_ui_blocking_power_score",
        "oecd_quality_percentile",
        "family_composite_status",
        "embedding_model",
        "embedding_model_version",
        "embedding_runtime",
        "language_code",
        "is_machine_translated",
        "corpus_snapshot",
        "embedding",
    ]


def _query_columns() -> list[str]:
    return [
        "query_id",
        "query_source",
        "fixture_group",
        "workflow_type",
        "anchor_family_id",
        "vector_space",
        "query_text",
        "token_count",
        "expected_behavior",
        "expected_current_threat_allowed",
        "primary_wipo_field",
        "family_composite_status",
        "embedding_model",
        "embedding_model_version",
        "embedding_runtime",
        "corpus_snapshot",
        "embedding",
    ]


def _merge_bucket_files(con: duckdb.DuckDBPyConnection, paths: list[Path], out_path: Path, columns: list[str]) -> int:
    usable = [path for path in paths if path.exists() and path.stat().st_size > 0]
    if not usable:
        write_pylist_parquet([], out_path, columns=columns)
        return 0
    path_list_sql = "[" + ", ".join(f"'{path}'" for path in usable) + "]"
    normalized_select = f"""
        select
            cast(docdb_family_id as bigint) as docdb_family_id,
            cast(representative_appln_id as bigint) as representative_appln_id,
            cast(representative_publn_id as bigint) as representative_publn_id,
            cast(representative_stage as varchar) as representative_stage,
            cast(vector_space as varchar) as vector_space,
            cast(queryable_text as varchar) as queryable_text,
            cast(token_count as bigint) as token_count,
            cast(text_provenance as varchar) as text_provenance,
            cast(text_source_type as varchar) as text_source_type,
            cast(is_abstract_fallback as boolean) as is_abstract_fallback,
            cast(family_earliest_priority_date as varchar) as family_earliest_priority_date,
            cast(primary_wipo_field as varchar) as primary_wipo_field,
            cast(owner_name_harmonized as varchar) as owner_name_harmonized,
            cast(family_ui_blocking_power_score as double) as family_ui_blocking_power_score,
            cast(oecd_quality_percentile as double) as oecd_quality_percentile,
            cast(family_composite_status as varchar) as family_composite_status,
            cast(embedding_model as varchar) as embedding_model,
            cast(embedding_model_version as varchar) as embedding_model_version,
            cast(embedding_runtime as varchar) as embedding_runtime,
            cast(language_code as varchar) as language_code,
            cast(is_machine_translated as boolean) as is_machine_translated,
            cast(corpus_snapshot as varchar) as corpus_snapshot,
            cast(embedding as double[]) as embedding
        from read_parquet({path_list_sql}, union_by_name=true)
    """
    con.execute(f"copy ({normalized_select}) to '{out_path}' (format parquet, compression zstd)")
    return parquet_row_count(out_path)


def _chunk_bucket_files(
    con: duckdb.DuckDBPyConnection,
    tmp_base: Path,
    bucket: int,
    bucket_count: int,
    bucket_order_sql: str,
    bucket_row_limit_sql: str,
    fetch_chunk_rows: int,
    claim_chunk_dir: Path,
    abstract_chunk_dir: Path,
    claim_bucket_path: Path,
    abstract_bucket_path: Path,
    claim_encode,
    abstract_encode,
    bundle: SemanticEncoderBundle,
    settings: BuildSettings,
) -> tuple[int, int]:
    bucket_query = f"""
        select *
        from read_parquet('{tmp_base}')
        where mod(docdb_family_id, {bucket_count}) = {bucket}
        {bucket_order_sql}
        {bucket_row_limit_sql}
    """
    cursor = con.execute(bucket_query)
    claim_chunk_paths: list[Path] = []
    abstract_chunk_paths: list[Path] = []
    encoded_claim_rows = 0
    encoded_abstract_rows = 0
    chunk_index = 0

    while True:
        bucket_rows = cursor.fetchmany(fetch_chunk_rows)
        if not bucket_rows:
            break
        claim_chunk_path = claim_chunk_dir / f"claims_bucket_{bucket:02d}_part_{chunk_index:04d}.parquet"
        abstract_chunk_path = abstract_chunk_dir / f"abstracts_bucket_{bucket:02d}_part_{chunk_index:04d}.parquet"
        claim_chunk_paths.append(claim_chunk_path)
        abstract_chunk_paths.append(abstract_chunk_path)

        if claim_chunk_path.exists() and claim_chunk_path.stat().st_size > 0 and abstract_chunk_path.exists() and abstract_chunk_path.stat().st_size > 0:
            logger.info("Reusing semantic bucket chunk bucket=%s chunk=%s", bucket, chunk_index)
            chunk_index += 1
            continue

        claim_rows = _encode_rows(
            bucket_rows,
            "vector_claims",
            claim_encode,
            bundle.claim_model_id,
            bundle.claim_model_version,
            bundle.embedding_runtime,
            settings.snapshot_date,
        )
        abstract_rows = _encode_rows(
            bucket_rows,
            "vector_abstract",
            abstract_encode,
            bundle.abstract_model_id,
            bundle.abstract_model_version,
            bundle.embedding_runtime,
            settings.snapshot_date,
        )
        encoded_claim_rows += write_pylist_parquet(claim_rows, claim_chunk_path, columns=_vector_columns())
        encoded_abstract_rows += write_pylist_parquet(abstract_rows, abstract_chunk_path, columns=_vector_columns())
        logger.info(
            "Finished semantic bucket chunk bucket=%s chunk=%s claim_rows=%s abstract_rows=%s",
            bucket,
            chunk_index,
            len(claim_rows),
            len(abstract_rows),
        )
        chunk_index += 1

    claim_rows_merged = _merge_bucket_files(con, claim_chunk_paths, claim_bucket_path, _vector_columns())
    abstract_rows_merged = _merge_bucket_files(con, abstract_chunk_paths, abstract_bucket_path, _vector_columns())
    logger.info(
        "Finished semantic bucket bucket=%s merged_claim_rows=%s merged_abstract_rows=%s",
        bucket,
        claim_rows_merged,
        abstract_rows_merged,
    )
    return encoded_claim_rows, encoded_abstract_rows


def _phase_kind_name(vector_space: str) -> str:
    return "claims" if vector_space == "vector_claims" else "abstracts"


def _phase_artifact_path(settings: BuildSettings, vector_space: str, phase_id: int, phase_count: int) -> Path:
    kind = _phase_kind_name(vector_space)
    phase_dir = ensure_dir(settings.vectors_dir / "phases" / kind)
    return phase_dir / f"vec_family_embeddings_{kind}_phase_{phase_id:02d}_of_{phase_count:02d}.parquet"


def _phase_chunk_dir(settings: BuildSettings, vector_space: str, phase_id: int, phase_count: int) -> Path:
    kind = _phase_kind_name(vector_space)
    return ensure_dir(settings.vectors_dir / "phases" / kind / f"_chunks_phase_{phase_id:02d}_of_{phase_count:02d}")


def _phase_stage_name(vector_space: str, phase_id: int) -> str:
    kind = "claim" if vector_space == "vector_claims" else "abstract"
    return f"semantic-{kind}-phase-{phase_id:02d}"


def _ann_kind_name(vector_space: str) -> str:
    return "claims" if vector_space == "vector_claims" else "abstracts"


def _ann_snapshot_paths(settings: BuildSettings, vector_space: str) -> tuple[Path, Path]:
    kind = _ann_kind_name(vector_space)
    ann_dir = ensure_dir(settings.vectors_dir / "ann")
    return ann_dir / f"vec_ann_{kind}_hnsw.bin", ann_dir / f"vec_ann_{kind}_family_ids.npy"


def _resolved_ann_method(settings: BuildSettings) -> str:
    configured = os.getenv("SEMANTIC_ANN_METHOD", "").strip() or settings.semantic_ann_method
    if configured in {"", "exact_scan_runtime_v1", "manifest_only_placeholder"}:
        return "hnsw_cosine_snapshot_v1"
    return configured


def _load_hnswlib():
    try:
        import hnswlib  # type: ignore
    except Exception as exc:  # pragma: no cover - exercised in live env
        raise RuntimeError(
            "hnswlib is required to build semantic ANN snapshots. Install ETL dependencies with hnswlib enabled."
        ) from exc
    return hnswlib


def _load_payload_vectors(
    con: duckdb.DuckDBPyConnection,
    payload_path: Path,
) -> tuple[np.ndarray, np.ndarray]:
    rows = con.execute(
        f"select docdb_family_id, embedding from read_parquet('{payload_path}') order by docdb_family_id"
    ).fetchall()
    if not rows:
        return np.empty(0, dtype=np.int64), np.empty((0, 0), dtype=np.float32)
    family_ids = np.asarray([row[0] for row in rows], dtype=np.int64)
    embeddings = np.asarray([row[1] for row in rows], dtype=np.float32)
    return family_ids, embeddings


def _payload_completeness_metrics(
    con: duckdb.DuckDBPyConnection,
    payload_path: Path,
) -> tuple[float, float, float, float]:
    duplicate_rate = con.execute(
        f"""
        with payload as (
            select * from read_parquet('{payload_path}')
        )
        select round(
            coalesce(
                (
                    select count(*)
                    from (
                        select docdb_family_id, count(*) c
                        from payload
                        group by 1
                        having c > 1
                    )
                ) * 1.0 / nullif((select count(*) from payload), 0),
                0.0
            ),
            6
        )
        """
    ).fetchone()[0]
    legal_completeness = con.execute(
        f"select round(avg(case when family_composite_status is not null then 1.0 else 0.0 end), 6) from read_parquet('{payload_path}')"
    ).fetchone()[0]
    chronology_completeness = con.execute(
        f"select round(avg(case when family_earliest_priority_date is not null then 1.0 else 0.0 end), 6) from read_parquet('{payload_path}')"
    ).fetchone()[0]
    blocking_completeness = con.execute(
        f"select round(avg(case when family_ui_blocking_power_score is not null then 1.0 else 0.0 end), 6) from read_parquet('{payload_path}')"
    ).fetchone()[0]
    return duplicate_rate, legal_completeness, chronology_completeness, blocking_completeness


def _build_hnsw_snapshot(
    settings: BuildSettings,
    vector_space: str,
    family_ids: np.ndarray,
    embeddings: np.ndarray,
) -> tuple[Path, Path, int, int, int]:
    hnswlib = _load_hnswlib()
    index_path, family_ids_path = _ann_snapshot_paths(settings, vector_space)
    if embeddings.size == 0:
        raise RuntimeError(f"Cannot build ANN snapshot for empty payload: {vector_space}")
    internal_ids = np.arange(len(family_ids), dtype=np.uint32)
    dim = int(embeddings.shape[1])
    if vector_space == "vector_claims":
        ef_construction = _int_env("SEMANTIC_ANN_EF_CONSTRUCTION_CLAIMS", 300)
        m = _int_env("SEMANTIC_ANN_M_CLAIMS", 32)
        search_ef = _int_env("SEMANTIC_ANN_SEARCH_EF_CLAIMS", 120)
    else:
        ef_construction = _int_env("SEMANTIC_ANN_EF_CONSTRUCTION_ABSTRACTS", 200)
        m = _int_env("SEMANTIC_ANN_M_ABSTRACTS", 32)
        search_ef = _int_env("SEMANTIC_ANN_SEARCH_EF_ABSTRACTS", 100)
    index = hnswlib.Index(space="cosine", dim=dim)
    index.init_index(max_elements=len(family_ids), ef_construction=ef_construction, M=m)
    index.add_items(embeddings, internal_ids)
    index.set_ef(search_ef)
    index.save_index(str(index_path))
    np.save(family_ids_path, family_ids)
    return index_path, family_ids_path, dim, ef_construction, search_ef


def _load_query_audit_vectors(
    con: duckdb.DuckDBPyConnection,
    query_registry_path: Path,
    vector_space: str,
    available_family_ids: np.ndarray,
) -> tuple[np.ndarray, float | None, int]:
    if not query_registry_path.exists():
        return np.empty((0, 0), dtype=np.float32), None, 0
    rows = con.execute(
        f"""
        select anchor_family_id, embedding
        from read_parquet('{query_registry_path}')
        where vector_space = '{vector_space}'
        order by query_id
        """
    ).fetchall()
    if not rows:
        return np.empty((0, 0), dtype=np.float32), None, 0
    available = set(int(value) for value in available_family_ids.tolist())
    covered_rows = [row for row in rows if int(row[0]) in available]
    coverage = round(len(covered_rows) / len(rows), 6)
    if not covered_rows:
        return np.empty((0, 0), dtype=np.float32), coverage, 0
    max_queries = _int_env("SEMANTIC_ANN_AUDIT_MAX_QUERIES", DEFAULT_ANN_AUDIT_MAX_QUERIES)
    if max_queries > 0:
        covered_rows = covered_rows[:max_queries]
    query_vectors = np.asarray([row[1] for row in covered_rows], dtype=np.float32)
    return query_vectors, coverage, len(covered_rows)


def _sample_corpus_query_vectors(
    family_ids: np.ndarray,
    embeddings: np.ndarray,
) -> tuple[np.ndarray, int]:
    if embeddings.size == 0 or len(family_ids) == 0:
        return np.empty((0, 0), dtype=np.float32), 0
    max_queries = _int_env("SEMANTIC_ANN_CORPUS_SAMPLE_QUERIES", DEFAULT_ANN_CORPUS_SAMPLE_QUERIES)
    if max_queries <= 0:
        return np.empty((0, 0), dtype=np.float32), 0
    sample_size = min(max_queries, len(family_ids))
    if sample_size == len(family_ids):
        return embeddings, sample_size
    positions = np.linspace(0, len(family_ids) - 1, num=sample_size, dtype=int)
    unique_positions = np.unique(positions)
    return embeddings[unique_positions], int(len(unique_positions))


def _exact_topk_family_ids(
    query_embeddings: np.ndarray,
    corpus_embeddings: np.ndarray,
    corpus_family_ids: np.ndarray,
    top_k: int,
) -> np.ndarray:
    if query_embeddings.size == 0 or corpus_embeddings.size == 0:
        return np.empty((0, 0), dtype=np.int64)
    k = min(top_k, len(corpus_family_ids))
    batch_size = _int_env("SEMANTIC_ANN_AUDIT_BATCH_SIZE", DEFAULT_ANN_AUDIT_BATCH_SIZE)
    output = np.empty((len(query_embeddings), k), dtype=np.int64)
    corpus_t = corpus_embeddings.T
    for start in range(0, len(query_embeddings), batch_size):
        stop = min(start + batch_size, len(query_embeddings))
        sims = np.matmul(query_embeddings[start:stop], corpus_t)
        top_idx = np.argpartition(-sims, kth=k - 1, axis=1)[:, :k]
        top_scores = np.take_along_axis(sims, top_idx, axis=1)
        order = np.argsort(-top_scores, axis=1)
        sorted_idx = np.take_along_axis(top_idx, order, axis=1)
        output[start:stop] = corpus_family_ids[sorted_idx]
    return output


def _ann_topk_family_ids(index, family_ids: np.ndarray, query_embeddings: np.ndarray, top_k: int) -> np.ndarray:
    if query_embeddings.size == 0 or family_ids.size == 0:
        return np.empty((0, 0), dtype=np.int64)
    k = min(top_k, len(family_ids))
    labels, _ = index.knn_query(query_embeddings, k=k)
    label_array = np.asarray(labels, dtype=np.int64)
    return family_ids[label_array]


def _audit_exact_vs_ann(
    index,
    family_ids: np.ndarray,
    corpus_embeddings: np.ndarray,
    query_embeddings: np.ndarray,
    top_k: int,
) -> tuple[float | None, float | None, int]:
    if query_embeddings.size == 0:
        return None, None, 0
    exact = _exact_topk_family_ids(query_embeddings, corpus_embeddings, family_ids, top_k)
    ann = _ann_topk_family_ids(index, family_ids, query_embeddings, top_k)
    if exact.size == 0 or ann.size == 0:
        return None, None, 0
    recall_scores: list[float] = []
    top1_scores: list[float] = []
    for exact_row, ann_row in zip(exact.tolist(), ann.tolist(), strict=False):
        exact_set = set(exact_row)
        ann_set = set(ann_row)
        if not exact_set:
            continue
        recall_scores.append(len(exact_set & ann_set) / len(exact_set))
        top1_scores.append(1.0 if exact_row[0] == ann_row[0] else 0.0)
    if not recall_scores:
        return None, None, 0
    return round(float(np.mean(recall_scores)), 6), round(float(np.mean(top1_scores)), 6), len(recall_scores)


def run_semantic_ann(settings: BuildSettings) -> list[StageResult]:
    result = StageResult(
        stage="semantic-ann",
        status="success",
        summary="Built HNSW ANN snapshots for the promoted semantic payloads and audited exact-vs-ANN agreement.",
        methods=[
            "Loaded the promoted semantic payloads from the canonical vector parquet paths.",
            "Built separate cosine HNSW snapshots for abstract and claim corpora.",
            "Audited ANN recall against exact top-k search using the semantic query registry where anchor coverage exists.",
        ],
        calculations=[
            "Claims use a higher ef_construction default than abstracts to preserve legal/technical specificity during ANN approximation.",
            "Abstract query audit is evaluated only on the subset of registry anchors present in the current partial MVP abstract corpus.",
        ],
        doc_refs=[
            "docs/new-feature-ideas/semantic-and-model-development/phases/phase-01-semantic-runtime-foundation.md",
        ],
    )

    manifest_path = settings.vectors_dir / "vec_embedding_manifest.json"
    query_registry_path = settings.vectors_dir / "vec_query_registry.parquet"
    ann_manifest_path = settings.vectors_dir / "vec_ann_index_manifest.json"
    ann_audit_path = settings.vectors_dir / "vec_ann_exact_vs_ann_audit.json"
    claim_payload_path = settings.vectors_dir / "vec_family_embeddings_claims.parquet"
    abstract_payload_path = settings.vectors_dir / "vec_family_embeddings_abstracts.parquet"

    if manifest_path.exists():
        manifest_payload = json.loads(manifest_path.read_text())
        claim_payload_path = Path(manifest_payload.get("claim_payload_path", claim_payload_path))
        abstract_payload_path = Path(manifest_payload.get("abstract_payload_path", abstract_payload_path))
    else:
        manifest_payload = {}

    required = [claim_payload_path, abstract_payload_path, query_registry_path]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        result.status = "failed"
        result.warnings.append(f"Semantic ANN build requires current payloads and query registry. Missing: {missing}")
        return [result]

    con = duckdb.connect()
    ann_method = _resolved_ann_method(settings)
    top_k = _int_env("SEMANTIC_ANN_AUDIT_TOP_K", DEFAULT_ANN_AUDIT_TOP_K)

    claim_family_ids, claim_embeddings = _load_payload_vectors(con, claim_payload_path)
    abstract_family_ids, abstract_embeddings = _load_payload_vectors(con, abstract_payload_path)
    logger.info(
        "Loaded semantic payload vectors claim_rows=%s abstract_rows=%s",
        len(claim_family_ids),
        len(abstract_family_ids),
    )
    claim_duplicate_rate, claim_legal_completeness, claim_chronology_completeness, claim_blocking_completeness = _payload_completeness_metrics(
        con, claim_payload_path
    )
    (
        abstract_duplicate_rate,
        abstract_legal_completeness,
        abstract_chronology_completeness,
        abstract_blocking_completeness,
    ) = _payload_completeness_metrics(con, abstract_payload_path)

    claim_index_path, claim_ids_path, claim_dim, claim_ef_construction, claim_search_ef = _build_hnsw_snapshot(
        settings, "vector_claims", claim_family_ids, claim_embeddings
    )
    abstract_index_path, abstract_ids_path, abstract_dim, abstract_ef_construction, abstract_search_ef = _build_hnsw_snapshot(
        settings, "vector_abstract", abstract_family_ids, abstract_embeddings
    )
    logger.info(
        "Built semantic ANN snapshots claim_dim=%s abstract_dim=%s claim_path=%s abstract_path=%s",
        claim_dim,
        abstract_dim,
        claim_index_path,
        abstract_index_path,
    )

    hnswlib = _load_hnswlib()
    claim_index = hnswlib.Index(space="cosine", dim=claim_dim)
    claim_index.load_index(str(claim_index_path), max_elements=len(claim_family_ids))
    claim_index.set_ef(claim_search_ef)
    abstract_index = hnswlib.Index(space="cosine", dim=abstract_dim)
    abstract_index.load_index(str(abstract_index_path), max_elements=len(abstract_family_ids))
    abstract_index.set_ef(abstract_search_ef)

    claim_query_vectors, claim_query_coverage, claim_registry_query_count = _load_query_audit_vectors(
        con, query_registry_path, "vector_claims", claim_family_ids
    )
    abstract_query_vectors, abstract_query_coverage, abstract_registry_query_count = _load_query_audit_vectors(
        con, query_registry_path, "vector_abstract", abstract_family_ids
    )
    claim_corpus_query_vectors, claim_corpus_query_count = _sample_corpus_query_vectors(claim_family_ids, claim_embeddings)
    abstract_corpus_query_vectors, abstract_corpus_query_count = _sample_corpus_query_vectors(abstract_family_ids, abstract_embeddings)
    logger.info(
        "Loaded ANN audit queries claim_registry_queries=%s abstract_registry_queries=%s claim_corpus_queries=%s abstract_corpus_queries=%s claim_coverage=%s abstract_coverage=%s",
        claim_registry_query_count,
        abstract_registry_query_count,
        claim_corpus_query_count,
        abstract_corpus_query_count,
        claim_query_coverage,
        abstract_query_coverage,
    )
    claim_recall_at_k, claim_match_at_1, claim_audit_queries = _audit_exact_vs_ann(
        claim_index, claim_family_ids, claim_embeddings, claim_query_vectors, top_k
    )
    abstract_recall_at_k, abstract_match_at_1, abstract_audit_queries = _audit_exact_vs_ann(
        abstract_index, abstract_family_ids, abstract_embeddings, abstract_query_vectors, top_k
    )
    claim_corpus_recall_at_k, claim_corpus_match_at_1, claim_corpus_audit_queries = _audit_exact_vs_ann(
        claim_index, claim_family_ids, claim_embeddings, claim_corpus_query_vectors, top_k
    )
    abstract_corpus_recall_at_k, abstract_corpus_match_at_1, abstract_corpus_audit_queries = _audit_exact_vs_ann(
        abstract_index, abstract_family_ids, abstract_embeddings, abstract_corpus_query_vectors, top_k
    )
    logger.info(
        "Finished ANN audit top_k=%s claim_registry_recall=%s abstract_registry_recall=%s claim_corpus_recall=%s abstract_corpus_recall=%s",
        top_k,
        claim_recall_at_k,
        abstract_recall_at_k,
        claim_corpus_recall_at_k,
        abstract_corpus_recall_at_k,
    )

    audit_payload = {
        "ann_method": ann_method,
        "audit_top_k": top_k,
        "claim": {
            "query_anchor_coverage": claim_query_coverage,
            "registry_query_count": claim_registry_query_count,
            "audit_query_count": claim_audit_queries,
            "exact_vs_ann_recall_at_k": claim_recall_at_k,
            "exact_vs_ann_match_at_1": claim_match_at_1,
            "corpus_sample_query_count": claim_corpus_query_count,
            "corpus_sample_audit_query_count": claim_corpus_audit_queries,
            "corpus_sample_exact_vs_ann_recall_at_k": claim_corpus_recall_at_k,
            "corpus_sample_exact_vs_ann_match_at_1": claim_corpus_match_at_1,
        },
        "abstract": {
            "query_anchor_coverage": abstract_query_coverage,
            "registry_query_count": abstract_registry_query_count,
            "audit_query_count": abstract_audit_queries,
            "exact_vs_ann_recall_at_k": abstract_recall_at_k,
            "exact_vs_ann_match_at_1": abstract_match_at_1,
            "corpus_sample_query_count": abstract_corpus_query_count,
            "corpus_sample_audit_query_count": abstract_corpus_audit_queries,
            "corpus_sample_exact_vs_ann_recall_at_k": abstract_corpus_recall_at_k,
            "corpus_sample_exact_vs_ann_match_at_1": abstract_corpus_match_at_1,
        },
    }
    write_text_json(ann_audit_path, audit_payload)
    write_text_json(
        ann_manifest_path,
        {
            "ann_method": ann_method,
            "index_status": "built_hnsw_snapshot",
            "embedding_device": manifest_payload.get("embedding_device"),
            "claim_index_path": str(claim_index_path),
            "claim_family_ids_path": str(claim_ids_path),
            "claim_payload_count": int(len(claim_family_ids)),
            "claim_embedding_dim": claim_dim,
            "claim_ef_construction": claim_ef_construction,
            "claim_search_ef": claim_search_ef,
            "claim_index_size_bytes": claim_index_path.stat().st_size,
            "claim_duplicate_family_rate": claim_duplicate_rate,
            "claim_legal_status_join_completeness": claim_legal_completeness,
            "claim_chronology_join_completeness": claim_chronology_completeness,
            "claim_blocking_context_completeness": claim_blocking_completeness,
            "query_anchor_claim_coverage": claim_query_coverage,
            f"claim_exact_vs_ann_recall_at_{top_k}": claim_recall_at_k,
            "claim_exact_vs_ann_match_at_1": claim_match_at_1,
            "claim_audit_query_count": claim_audit_queries,
            "claim_registry_query_count": claim_registry_query_count,
            "claim_corpus_sample_query_count": claim_corpus_query_count,
            "claim_corpus_sample_audit_query_count": claim_corpus_audit_queries,
            f"claim_corpus_sample_exact_vs_ann_recall_at_{top_k}": claim_corpus_recall_at_k,
            "claim_corpus_sample_exact_vs_ann_match_at_1": claim_corpus_match_at_1,
            "abstract_index_path": str(abstract_index_path),
            "abstract_family_ids_path": str(abstract_ids_path),
            "abstract_payload_count": int(len(abstract_family_ids)),
            "abstract_embedding_dim": abstract_dim,
            "abstract_ef_construction": abstract_ef_construction,
            "abstract_search_ef": abstract_search_ef,
            "abstract_index_size_bytes": abstract_index_path.stat().st_size,
            "abstract_duplicate_family_rate": abstract_duplicate_rate,
            "abstract_legal_status_join_completeness": abstract_legal_completeness,
            "abstract_chronology_join_completeness": abstract_chronology_completeness,
            "abstract_blocking_context_completeness": abstract_blocking_completeness,
            "query_anchor_abstract_coverage": abstract_query_coverage,
            f"abstract_exact_vs_ann_recall_at_{top_k}": abstract_recall_at_k,
            "abstract_exact_vs_ann_match_at_1": abstract_match_at_1,
            "abstract_audit_query_count": abstract_audit_queries,
            "abstract_registry_query_count": abstract_registry_query_count,
            "abstract_corpus_sample_query_count": abstract_corpus_query_count,
            "abstract_corpus_sample_audit_query_count": abstract_corpus_audit_queries,
            f"abstract_corpus_sample_exact_vs_ann_recall_at_{top_k}": abstract_corpus_recall_at_k,
            "abstract_corpus_sample_exact_vs_ann_match_at_1": abstract_corpus_match_at_1,
            "audit_summary_path": str(ann_audit_path),
        },
    )

    result.inputs.extend([str(claim_payload_path), str(abstract_payload_path), str(query_registry_path)])
    result.outputs.extend(
        [
            str(claim_index_path),
            str(claim_ids_path),
            str(abstract_index_path),
            str(abstract_ids_path),
            str(ann_manifest_path),
            str(ann_audit_path),
        ]
    )
    result.metrics["claim_payload_count"] = int(len(claim_family_ids))
    result.metrics["abstract_payload_count"] = int(len(abstract_family_ids))
    result.metrics["claim_embedding_dim"] = claim_dim
    result.metrics["abstract_embedding_dim"] = abstract_dim
    result.metrics[f"claim_exact_vs_ann_recall_at_{top_k}"] = claim_recall_at_k
    result.metrics[f"abstract_exact_vs_ann_recall_at_{top_k}"] = abstract_recall_at_k
    result.metrics[f"claim_corpus_sample_exact_vs_ann_recall_at_{top_k}"] = claim_corpus_recall_at_k
    result.metrics[f"abstract_corpus_sample_exact_vs_ann_recall_at_{top_k}"] = abstract_corpus_recall_at_k
    result.metrics["query_anchor_claim_coverage"] = claim_query_coverage
    result.metrics["query_anchor_abstract_coverage"] = abstract_query_coverage
    return [result]


def _vector_space_text_predicate(vector_space: str) -> str:
    column = "representative_claim_1_en" if vector_space == "vector_claims" else "representative_abstract_en"
    return f"{column} is not null and trim({column}) <> ''"


def _run_semantic_phase(settings: BuildSettings, vector_space: str, default_phase_count: int) -> list[StageResult]:
    phase_id = _int_env("SEMANTIC_PHASE_ID", 0)
    phase_count = _int_env("SEMANTIC_PHASE_COUNT", default_phase_count)
    if phase_id < 0 or phase_id >= phase_count:
        result = StageResult(
            stage=_phase_stage_name(vector_space, phase_id),
            status="failed",
            summary="Semantic phase configuration is invalid.",
        )
        result.warnings.append(f"Invalid semantic phase id/count: phase_id={phase_id}, phase_count={phase_count}")
        return [result]

    result = StageResult(
        stage=_phase_stage_name(vector_space, phase_id),
        status="success",
        summary=f"Built {_phase_kind_name(vector_space)} semantic phase artifact {phase_id + 1}/{phase_count}.",
        methods=[
            "Materialized or reused the semantic base parquet, then encoded one deterministic phase partition.",
            "Persisted resumable chunk checkpoints before merging the finished phase artifact.",
        ],
        calculations=[
            "Phase partitions are deterministic by docdb_family_id modulo phase_count.",
            "Only rows with usable text for the requested vector space are encoded in the phase artifact.",
        ],
        doc_refs=[
            "docs/new-feature-ideas/semantic-and-model-development/phases/phase-01-semantic-runtime-foundation.md",
        ],
    )

    rep = settings.silver_dir / "silver_family_text_representative.parquet"
    elig = settings.silver_dir / "silver_semantic_sampling_eligibility.parquet"
    semantic_context = settings.gold_dir / "gold_semantic_match_context.parquet"
    family_status = settings.silver_dir / "silver_family_status_pt.parquet"
    family_summary = settings.gold_dir / "gold_family_summary.parquet"
    family_blocking = settings.gold_dir / "gold_family_blocking_power.parquet"
    required = [rep, elig, semantic_context, family_status, family_summary]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        result.status = "failed"
        result.warnings.append(f"Missing required inputs for semantic phase: {missing}")
        return [result]

    vectors_dir = ensure_dir(settings.vectors_dir)
    tmp_base = vectors_dir / "_tmp_semantic_base.parquet"
    con = duckdb.connect()
    bundle = _build_encoder_bundle(settings)
    device = _resolve_embedding_device(bundle)
    result.metrics["embedding_device"] = device

    if not tmp_base.exists():
        base_rows = _materialize_semantic_base(con, rep, elig, semantic_context, family_status, family_summary, family_blocking, tmp_base)
        result.metrics["semantic_base_rows"] = base_rows

    encode_fn = _load_claim_encoder(bundle, device) if vector_space == "vector_claims" else _load_abstract_encoder(bundle, device)
    model_id = bundle.claim_model_id if vector_space == "vector_claims" else bundle.abstract_model_id
    model_version = bundle.claim_model_version if vector_space == "vector_claims" else bundle.abstract_model_version
    fetch_chunk_rows = _int_env("SEMANTIC_FETCH_CHUNK_ROWS", DEFAULT_FETCH_CHUNK_ROWS)
    phase_row_limit_sql = _optional_limit_clause("SEMANTIC_PHASE_ROW_LIMIT")
    phase_artifact = _phase_artifact_path(settings, vector_space, phase_id, phase_count)
    phase_chunk_dir = _phase_chunk_dir(settings, vector_space, phase_id, phase_count)
    chunk_paths: list[Path] = []
    encoded_rows = 0

    query = f"""
        select *
        from read_parquet('{tmp_base}')
        where mod(docdb_family_id, {phase_count}) = {phase_id}
          and {_vector_space_text_predicate(vector_space)}
        order by docdb_family_id
        {phase_row_limit_sql}
    """
    cursor = con.execute(query)
    chunk_index = 0
    while True:
        phase_rows = cursor.fetchmany(fetch_chunk_rows)
        if not phase_rows:
            break
        chunk_path = phase_chunk_dir / f"{_phase_kind_name(vector_space)}_phase_{phase_id:02d}_part_{chunk_index:04d}.parquet"
        if chunk_path.exists() and chunk_path.stat().st_size > 0:
            chunk_paths.append(chunk_path)
            logger.info("Reusing semantic phase chunk vector_space=%s phase=%s chunk=%s", vector_space, phase_id, chunk_index)
            chunk_index += 1
            continue
        encoded = _encode_rows(
            phase_rows,
            vector_space,
            encode_fn,
            model_id,
            model_version,
            bundle.embedding_runtime,
            settings.snapshot_date,
        )
        if encoded:
            encoded_rows += write_pylist_parquet(encoded, chunk_path, columns=_vector_columns())
            chunk_paths.append(chunk_path)
            logger.info(
                "Finished semantic phase chunk vector_space=%s phase=%s chunk=%s rows=%s",
                vector_space,
                phase_id,
                chunk_index,
                len(encoded),
            )
        chunk_index += 1

    merged_rows = _merge_bucket_files(con, chunk_paths, phase_artifact, _vector_columns())
    duplicate_rows = 0
    duplicate_rate = 0.0
    dims = None
    if merged_rows:
        duplicate_rows = con.execute(
            f"select count(*) from (select docdb_family_id, count(*) c from read_parquet('{phase_artifact}') group by 1 having c > 1)"
        ).fetchone()[0]
        duplicate_rate = round(duplicate_rows / merged_rows, 6)
        dims = con.execute(
            f"select min(array_length(embedding)), max(array_length(embedding)) from read_parquet('{phase_artifact}')"
        ).fetchone()

    result.outputs.append(str(phase_artifact))
    result.metrics["phase_id"] = phase_id
    result.metrics["phase_count"] = phase_count
    result.metrics["phase_chunk_files_present"] = len(chunk_paths)
    result.metrics["encoded_rows"] = encoded_rows
    result.metrics["merged_rows"] = merged_rows
    result.metrics["duplicate_family_rows"] = duplicate_rows
    result.metrics["duplicate_family_rate"] = duplicate_rate
    if dims is not None:
        result.metrics["embedding_dim_min"] = dims[0]
        result.metrics["embedding_dim_max"] = dims[1]
    return [result]


def run_semantic_abstract_phase(settings: BuildSettings) -> list[StageResult]:
    return _run_semantic_phase(settings, "vector_abstract", default_phase_count=10)


def run_semantic_claim_phase(settings: BuildSettings) -> list[StageResult]:
    return _run_semantic_phase(settings, "vector_claims", default_phase_count=3)


def run_semantic_merge(settings: BuildSettings) -> list[StageResult]:
    result = StageResult(
        stage="semantic-merge",
        status="success",
        summary="Merged semantic phase artifacts into final corpus vector outputs and refreshed semantic metadata.",
        methods=[
            "Merged durable abstract and claim phase artifacts into the final vector payloads.",
            "Refreshed query registry and semantic manifests against the promoted model runtime.",
        ],
        calculations=[
            "Merged outputs require all expected phase artifacts to be present before final release is rewritten.",
        ],
        doc_refs=[
            "docs/new-feature-ideas/semantic-and-model-development/phases/phase-01-semantic-runtime-foundation.md",
        ],
    )
    abstract_phase_count = _int_env("SEMANTIC_ABSTRACT_PHASE_COUNT", 10)
    claim_phase_count = _int_env("SEMANTIC_CLAIM_PHASE_COUNT", 3)
    out_claims = settings.vectors_dir / "vec_family_embeddings_claims.parquet"
    out_abstracts = settings.vectors_dir / "vec_family_embeddings_abstracts.parquet"
    manifest = settings.vectors_dir / "vec_embedding_manifest.json"
    ann_meta = settings.vectors_dir / "vec_ann_index_manifest.json"
    query_registry = settings.vectors_dir / "vec_query_registry.parquet"
    query_registry_meta = settings.vectors_dir / "vec_query_registry.json"
    phase0_fixtures = settings.ml_dir / "semantic_eval_fixture_registry.parquet"

    abstract_paths = [_phase_artifact_path(settings, "vector_abstract", phase_id, abstract_phase_count) for phase_id in range(abstract_phase_count)]
    claim_paths = [_phase_artifact_path(settings, "vector_claims", phase_id, claim_phase_count) for phase_id in range(claim_phase_count)]
    missing = [str(path) for path in [*abstract_paths, *claim_paths] if not path.exists()]
    if missing:
        result.status = "failed"
        result.warnings.append(f"Missing semantic phase artifacts for merge: {missing}")
        return [result]

    con = duckdb.connect()
    bundle = _build_encoder_bundle(settings)
    device = _resolve_embedding_device(bundle)
    abstract_encode = _load_abstract_encoder(bundle, device)
    claim_encode = _load_claim_encoder(bundle, device)
    merged_claims = _merge_bucket_files(con, claim_paths, out_claims, _vector_columns())
    merged_abstracts = _merge_bucket_files(con, abstract_paths, out_abstracts, _vector_columns())
    query_registry_rows = _build_query_registry(
        phase0_fixtures,
        query_registry,
        bundle,
        abstract_encode,
        claim_encode,
        settings.snapshot_date,
    )
    write_text_json(
        manifest,
        {
            "release_id": settings.release_id,
            "embedding_runtime": bundle.embedding_runtime,
            "embedding_device": device,
            "abstract_model_id": bundle.abstract_model_id,
            "abstract_model_version": bundle.abstract_model_version,
            "claim_model_id": bundle.claim_model_id,
            "claim_model_version": bundle.claim_model_version,
            "corpus_snapshot": settings.snapshot_date,
            "vector_sample_pct": settings.vector_sample_pct,
            "claim_payload_path": str(out_claims),
            "abstract_payload_path": str(out_abstracts),
            "query_registry_path": str(query_registry),
            "claim_payload_count": merged_claims,
            "abstract_payload_count": merged_abstracts,
            "query_registry_count": query_registry_rows,
            "abstract_phase_count": abstract_phase_count,
            "claim_phase_count": claim_phase_count,
        },
    )
    write_text_json(
        ann_meta,
        {
            "ann_method": settings.semantic_ann_method,
            "index_status": "not_built_exact_scan_only",
            "embedding_device": device,
            "reason": "Dense embeddings are promoted first; ANN snapshots will be added after exact-scan quality gates are met.",
        },
    )
    write_text_json(
        query_registry_meta,
        {
            "status": "materialized",
            "query_source": "phase0_semantic_fixture",
            "query_registry_path": str(query_registry),
            "query_registry_count": query_registry_rows,
            "embedding_runtime": bundle.embedding_runtime,
            "embedding_device": device,
            "corpus_snapshot": settings.snapshot_date,
        },
    )
    result.outputs.extend([str(out_claims), str(out_abstracts), str(manifest), str(ann_meta), str(query_registry), str(query_registry_meta)])
    result.metrics["vec_family_embeddings_claims_rows"] = merged_claims
    result.metrics["vec_family_embeddings_abstracts_rows"] = merged_abstracts
    result.metrics["vec_query_registry_rows"] = query_registry_rows
    result.metrics["embedding_device"] = device
    return [result]


def _materialize_semantic_base(
    con: duckdb.DuckDBPyConnection,
    rep: Path,
    elig: Path,
    semantic_context: Path,
    family_status: Path,
    family_summary: Path,
    family_blocking: Path,
    base_path: Path,
) -> int:
    family_blocking_sql = (
        f"select docdb_family_id, family_ui_blocking_power_score from read_parquet('{family_blocking}')"
        if family_blocking.exists()
        else "select null::bigint as docdb_family_id, null::double as family_ui_blocking_power_score where false"
    )
    con.execute(
        f"""
        copy (
            with elig as (
                select
                    docdb_family_id,
                    is_semantic_candidate,
                    coalesce(is_in_vector_sample, true) as is_in_vector_sample
                from read_parquet('{elig}')
            )
            select
                r.docdb_family_id,
                r.representative_appln_id,
                r.representative_publn_id,
                r.representative_stage,
                r.representative_claim_1_en,
                r.representative_abstract_en,
                r.representative_source_type,
                r.text_provenance,
                r.is_abstract_fallback,
                fs.family_earliest_priority_date,
                list_extract(ctx.covered_wipo_fields, 1) as primary_wipo_field,
                ctx.owner_name_harmonized,
                coalesce(ctx.family_ui_blocking_power_score, bp.family_ui_blocking_power_score) as family_ui_blocking_power_score,
                ctx.oecd_quality_percentile,
                st.family_composite_status
            from read_parquet('{rep}') r
            join elig e using (docdb_family_id)
            left join read_parquet('{semantic_context}') ctx using (docdb_family_id)
            left join read_parquet('{family_status}') st using (docdb_family_id)
            left join read_parquet('{family_summary}') fs using (docdb_family_id)
            left join ({family_blocking_sql}) bp using (docdb_family_id)
            where e.is_semantic_candidate = true
              and e.is_in_vector_sample = true
        ) to '{base_path}' (format parquet, compression zstd)
        """
    )
    return parquet_row_count(base_path)


def _encode_rows(
    rows: list[tuple[Any, ...]],
    vector_space: str,
    encode_fn,
    embedding_model: str,
    embedding_model_version: str,
    embedding_runtime: str,
    snapshot_date: str,
) -> list[dict[str, Any]]:
    if not rows:
        return []
    texts = _sanitize_batch([row[4] if vector_space == "vector_claims" else row[5] for row in rows])
    valid_positions = [idx for idx, text in enumerate(texts) if text]
    if not valid_positions:
        return []
    chunk_rows = _int_env("SEMANTIC_ENCODE_CHUNK_ROWS", 2048)
    encoded_by_position: dict[int, list[float]] = {}
    for start in range(0, len(valid_positions), chunk_rows):
        chunk_positions = valid_positions[start : start + chunk_rows]
        chunk_texts = [texts[idx] for idx in chunk_positions]
        encodings = encode_fn(chunk_texts)
        for position, embedding in zip(chunk_positions, encodings):
            encoded_by_position[position] = embedding
        _release_torch_device_cache()
    materialized: list[dict[str, Any]] = []
    for idx, row in enumerate(rows):
        if idx not in encoded_by_position:
            continue
        (
            family_id,
            appln_id,
            publn_id,
            representative_stage,
            claim_text,
            abstract_text,
            representative_source_type,
            provenance,
            is_fallback,
            priority_date,
            primary_wipo_field,
            owner_name_harmonized,
            blocking_score,
            oecd_quality_percentile,
            family_composite_status,
        ) = row
        clean_text = texts[idx]
        text_source_type = representative_source_type or ("EPAB_CLAIM" if str(provenance).startswith("EPAB_") else "PATSTAT_ABSTRACT")
        materialized.append(
            {
                "docdb_family_id": family_id,
                "representative_appln_id": appln_id,
                "representative_publn_id": publn_id,
                "representative_stage": representative_stage,
                "vector_space": vector_space,
                "queryable_text": clean_text,
                "token_count": len(re.findall(r"[A-Za-z0-9_]+", clean_text)),
                "text_provenance": provenance,
                "text_source_type": text_source_type,
                "is_abstract_fallback": bool(is_fallback),
                "family_earliest_priority_date": str(priority_date) if priority_date is not None else None,
                "primary_wipo_field": primary_wipo_field,
                "owner_name_harmonized": owner_name_harmonized,
                "family_ui_blocking_power_score": blocking_score,
                "oecd_quality_percentile": oecd_quality_percentile,
                "family_composite_status": family_composite_status,
                "embedding_model": embedding_model,
                "embedding_model_version": embedding_model_version,
                "embedding_runtime": embedding_runtime,
                "language_code": "en",
                "is_machine_translated": False,
                "corpus_snapshot": snapshot_date,
                "embedding": encoded_by_position[idx],
            }
        )
    return materialized


def _build_query_registry(
    phase0_fixtures: Path,
    out_path: Path,
    bundle: SemanticEncoderBundle,
    abstract_encode,
    claim_encode,
    snapshot_date: str,
) -> int:
    if not phase0_fixtures.exists():
        write_pylist_parquet([], out_path, columns=_query_columns())
        return 0
    con = duckdb.connect()
    fixture_rows = con.execute(
        f"""
        select
            fixture_id,
            fixture_group,
            workflow_type,
            docdb_family_id,
            vector_space,
            query_text,
            expected_behavior,
            expected_current_threat_allowed,
            primary_wipo_field,
            family_composite_status
        from read_parquet('{phase0_fixtures}')
        order by fixture_id
        """
    ).fetchall()
    groups = {"vector_claims": [], "vector_abstract": []}
    for row in fixture_rows:
        groups[row[4]].append(row)
    rows: list[dict[str, Any]] = []
    for vector_space, encode_fn, model_id, model_version in [
        ("vector_claims", claim_encode, bundle.claim_model_id, bundle.claim_model_version),
        ("vector_abstract", abstract_encode, bundle.abstract_model_id, bundle.abstract_model_version),
    ]:
        group_rows = groups[vector_space]
        texts = _sanitize_batch([row[5] for row in group_rows])
        valid_positions = [idx for idx, text in enumerate(texts) if text]
        if not valid_positions:
            continue
        embeddings = encode_fn([texts[idx] for idx in valid_positions])
        encoded_by_position = {position: embedding for position, embedding in zip(valid_positions, embeddings)}
        for idx, row in enumerate(group_rows):
            if idx not in encoded_by_position:
                continue
            (
                fixture_id,
                fixture_group,
                workflow_type,
                family_id,
                _vector_space,
                _query_text,
                expected_behavior,
                expected_current_threat_allowed,
                primary_wipo_field,
                family_composite_status,
            ) = row
            rows.append(
                {
                    "query_id": fixture_id,
                    "query_source": "phase0_semantic_fixture",
                    "fixture_group": fixture_group,
                    "workflow_type": workflow_type,
                    "anchor_family_id": family_id,
                    "vector_space": vector_space,
                    "query_text": texts[idx],
                    "token_count": len(re.findall(r"[A-Za-z0-9_]+", texts[idx])),
                    "expected_behavior": expected_behavior,
                    "expected_current_threat_allowed": bool(expected_current_threat_allowed),
                    "primary_wipo_field": primary_wipo_field,
                    "family_composite_status": family_composite_status,
                    "embedding_model": model_id,
                    "embedding_model_version": model_version,
                    "embedding_runtime": bundle.embedding_runtime,
                    "corpus_snapshot": snapshot_date,
                    "embedding": encoded_by_position[idx],
                }
            )
    return write_pylist_parquet(rows, out_path, columns=_query_columns())


def run_semantic(settings: BuildSettings) -> list[StageResult]:
    """Materialize family-first semantic vectors, manifests, and query fixtures for the promoted runtime."""
    result = StageResult(
        stage="semantic",
        status="success",
        summary="Built family-first semantic vector artifacts and query fixtures for the promoted dual semantic runtime.",
        methods=[
            "Generated separate vector_claims and vector_abstract payloads from representative family text.",
            "Used BGE-M3 for abstract embeddings and PatentSBERTa for claim embeddings when the promoted dual runtime is enabled, otherwise kept the lexical fallback for local regression use.",
            "Materialized one semantic base parquet first, then encoded in bucketed slices to avoid repeated large joins.",
        ],
        calculations=[
            "Claims and abstracts remain physically separated and explicitly labeled by vector space.",
            "Only semantic candidates already marked in the Silver eligibility mart are embedded.",
            "Current runtime remains dense-only; ANN is still exact-scan compatible and recorded as such in manifests.",
        ],
        doc_refs=[
            "docs/new-feature-ideas/semantic-and-model-development/phases/phase-01-semantic-runtime-foundation.md",
            "docs/new-feature-ideas/semantic-and-model-development/semantic-embedding-model-selection-decision.md",
            "docs/new-feature-ideas/semantic-and-model-development/semantic-embedding-candidate-shortlist-and-benchmark-plan.md",
            "docs/new-feature-ideas/semantic-and-model-development/bge-m3-and-patentsberta-local-installation-storage-and-runtime-guide.md",
        ],
    )

    rep = settings.silver_dir / "silver_family_text_representative.parquet"
    elig = settings.silver_dir / "silver_semantic_sampling_eligibility.parquet"
    semantic_context = settings.gold_dir / "gold_semantic_match_context.parquet"
    family_status = settings.silver_dir / "silver_family_status_pt.parquet"
    family_summary = settings.gold_dir / "gold_family_summary.parquet"
    family_blocking = settings.gold_dir / "gold_family_blocking_power.parquet"
    phase0_fixtures = settings.ml_dir / "semantic_eval_fixture_registry.parquet"

    out_claims = settings.vectors_dir / "vec_family_embeddings_claims.parquet"
    out_abstracts = settings.vectors_dir / "vec_family_embeddings_abstracts.parquet"
    manifest = settings.vectors_dir / "vec_embedding_manifest.json"
    ann_meta = settings.vectors_dir / "vec_ann_index_manifest.json"
    query_registry = settings.vectors_dir / "vec_query_registry.parquet"
    query_registry_meta = settings.vectors_dir / "vec_query_registry.json"

    required = [rep, elig, semantic_context, family_status, family_summary]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        result.status = "failed"
        result.warnings.append(f"Representative text, eligibility, context, status, and family summary must exist before semantic runtime packaging. Missing: {missing}")
        return [result]

    vectors_dir = ensure_dir(settings.vectors_dir)
    tmp_claim_dir = ensure_dir(vectors_dir / "_tmp_claim_buckets")
    tmp_abstract_dir = ensure_dir(vectors_dir / "_tmp_abstract_buckets")
    tmp_claim_chunk_dir = ensure_dir(vectors_dir / "_tmp_claim_chunks")
    tmp_abstract_chunk_dir = ensure_dir(vectors_dir / "_tmp_abstract_chunks")
    tmp_base = vectors_dir / "_tmp_semantic_base.parquet"

    con = duckdb.connect()
    bundle = _build_encoder_bundle(settings)
    skip_metadata = _bool_env("SEMANTIC_SKIP_METADATA")
    merge_only = _bool_env("SEMANTIC_MERGE_ONLY")
    embedding_device = _resolve_embedding_device(bundle)
    if bundle.uses_local_fallback:
        result.warnings.append("Promoted semantic models are not enabled; using lexical_hash_embedding_v1 fallback.")
    result.metrics["embedding_device"] = embedding_device

    if not merge_only:
        base_rows = _materialize_semantic_base(con, rep, elig, semantic_context, family_status, family_summary, family_blocking, tmp_base)
        result.metrics["semantic_base_rows"] = base_rows
    elif not tmp_base.exists():
        result.status = "failed"
        result.warnings.append("SEMANTIC_MERGE_ONLY was requested but the semantic base parquet does not exist.")
        return [result]

    abstract_encode = _load_abstract_encoder(bundle, embedding_device)
    claim_encode = _load_claim_encoder(bundle, embedding_device)

    bucket_count = _semantic_bucket_count()
    bucket_start = _int_env("SEMANTIC_BUCKET_START", 0)
    bucket_end = _int_env("SEMANTIC_BUCKET_END", bucket_count - 1)
    bucket_row_limit_sql = _optional_limit_clause("SEMANTIC_BUCKET_ROW_LIMIT")
    bucket_order_sql = _bucket_order_clause(bucket_row_limit_sql)
    fetch_chunk_rows = _int_env("SEMANTIC_FETCH_CHUNK_ROWS", DEFAULT_FETCH_CHUNK_ROWS)
    merge_requested = not bucket_row_limit_sql and bucket_start == 0 and bucket_end == bucket_count - 1
    encode_requested = not (merge_only and merge_requested)
    if bucket_start < 0 or bucket_end >= bucket_count or bucket_start > bucket_end:
        result.status = "failed"
        result.warnings.append(f"Invalid semantic bucket range: {bucket_start}..{bucket_end}")
        return [result]

    claim_bucket_paths = [tmp_claim_dir / f"claims_bucket_{bucket:02d}.parquet" for bucket in range(bucket_count)]
    abstract_bucket_paths = [tmp_abstract_dir / f"abstracts_bucket_{bucket:02d}.parquet" for bucket in range(bucket_count)]
    encoded_claim_rows = 0
    encoded_abstract_rows = 0

    if encode_requested:
        for bucket in range(bucket_start, bucket_end + 1):
            claim_rows_written, abstract_rows_written = _chunk_bucket_files(
                con=con,
                tmp_base=tmp_base,
                bucket=bucket,
                bucket_count=bucket_count,
                bucket_order_sql=bucket_order_sql,
                bucket_row_limit_sql=bucket_row_limit_sql,
                fetch_chunk_rows=fetch_chunk_rows,
                claim_chunk_dir=tmp_claim_chunk_dir,
                abstract_chunk_dir=tmp_abstract_chunk_dir,
                claim_bucket_path=claim_bucket_paths[bucket],
                abstract_bucket_path=abstract_bucket_paths[bucket],
                claim_encode=claim_encode,
                abstract_encode=abstract_encode,
                bundle=bundle,
                settings=settings,
            )
            encoded_claim_rows += claim_rows_written
            encoded_abstract_rows += abstract_rows_written
        result.metrics["encoded_claim_bucket_rows"] = encoded_claim_rows
        result.metrics["encoded_abstract_bucket_rows"] = encoded_abstract_rows
    elif merge_only:
        result.warnings.append("Semantic run reused existing bucket files and skipped bucket encoding because merge-only mode was requested for the full bucket range.")

    complete_claim_buckets = sum(1 for path in claim_bucket_paths if path.exists() and path.stat().st_size > 0)
    complete_abstract_buckets = sum(1 for path in abstract_bucket_paths if path.exists() and path.stat().st_size > 0)
    result.metrics["claim_bucket_files_present"] = complete_claim_buckets
    result.metrics["abstract_bucket_files_present"] = complete_abstract_buckets
    if bucket_row_limit_sql:
        result.warnings.append("Semantic bucket row limiting was enabled for this run, so the outputs represent a bounded smoke sample, not a full corpus release.")

    merged_claims = 0
    merged_abstracts = 0
    if merge_requested and complete_claim_buckets == bucket_count and complete_abstract_buckets == bucket_count:
        merged_claims = _merge_bucket_files(con, claim_bucket_paths, out_claims, _vector_columns())
        merged_abstracts = _merge_bucket_files(con, abstract_bucket_paths, out_abstracts, _vector_columns())
    else:
        if merge_requested:
            result.warnings.append(
                f"Semantic bucket generation is incomplete ({complete_claim_buckets}/{bucket_count} claim buckets, {complete_abstract_buckets}/{bucket_count} abstract buckets), so final merged vector artifacts were not rewritten."
            )
        else:
            result.warnings.append("Semantic run was intentionally bounded to a subset of buckets, so final merged vector artifacts were not rewritten.")

    query_registry_rows = 0
    if not skip_metadata:
        query_registry_rows = _build_query_registry(
            phase0_fixtures,
            query_registry,
            bundle,
            abstract_encode,
            claim_encode,
            settings.snapshot_date,
        )

    claim_duplicate_rate = None
    abstract_duplicate_rate = None
    claim_legal_completeness = None
    abstract_legal_completeness = None
    claim_chronology_completeness = None
    abstract_chronology_completeness = None
    claim_blocking_completeness = None
    abstract_blocking_completeness = None
    query_anchor_claim_coverage = None
    query_anchor_abstract_coverage = None

    if merged_claims:
        duplicate_claims = con.execute(
            f"select count(*) from (select docdb_family_id, count(*) c from read_parquet('{out_claims}') group by 1 having c > 1)"
        ).fetchone()[0]
        claim_duplicate_rate = round(duplicate_claims / merged_claims, 6)
        claim_legal_completeness = con.execute(
            f"select round(avg(case when family_composite_status is not null then 1.0 else 0.0 end), 6) from read_parquet('{out_claims}')"
        ).fetchone()[0]
        claim_chronology_completeness = con.execute(
            f"select round(avg(case when family_earliest_priority_date is not null then 1.0 else 0.0 end), 6) from read_parquet('{out_claims}')"
        ).fetchone()[0]
        claim_blocking_completeness = con.execute(
            f"select round(avg(case when family_ui_blocking_power_score is not null then 1.0 else 0.0 end), 6) from read_parquet('{out_claims}')"
        ).fetchone()[0]
    if merged_abstracts:
        duplicate_abstracts = con.execute(
            f"select count(*) from (select docdb_family_id, count(*) c from read_parquet('{out_abstracts}') group by 1 having c > 1)"
        ).fetchone()[0]
        abstract_duplicate_rate = round(duplicate_abstracts / merged_abstracts, 6)
        abstract_legal_completeness = con.execute(
            f"select round(avg(case when family_composite_status is not null then 1.0 else 0.0 end), 6) from read_parquet('{out_abstracts}')"
        ).fetchone()[0]
        abstract_chronology_completeness = con.execute(
            f"select round(avg(case when family_earliest_priority_date is not null then 1.0 else 0.0 end), 6) from read_parquet('{out_abstracts}')"
        ).fetchone()[0]
        abstract_blocking_completeness = con.execute(
            f"select round(avg(case when family_ui_blocking_power_score is not null then 1.0 else 0.0 end), 6) from read_parquet('{out_abstracts}')"
        ).fetchone()[0]
    if query_registry_rows and merged_claims:
        query_anchor_claim_coverage = con.execute(
            f"""
            select round(avg(case when v.docdb_family_id is not null then 1.0 else 0.0 end), 6)
            from read_parquet('{query_registry}') q
            left join read_parquet('{out_claims}') v
              on q.anchor_family_id = v.docdb_family_id
             and q.vector_space = v.vector_space
            where q.vector_space = 'vector_claims'
            """
        ).fetchone()[0]
    if query_registry_rows and merged_abstracts:
        query_anchor_abstract_coverage = con.execute(
            f"""
            select round(avg(case when v.docdb_family_id is not null then 1.0 else 0.0 end), 6)
            from read_parquet('{query_registry}') q
            left join read_parquet('{out_abstracts}') v
              on q.anchor_family_id = v.docdb_family_id
             and q.vector_space = v.vector_space
            where q.vector_space = 'vector_abstract'
            """
        ).fetchone()[0]

    if not skip_metadata:
        write_text_json(
            manifest,
            {
                "release_id": settings.release_id,
                "embedding_runtime": bundle.embedding_runtime,
                "embedding_device": embedding_device,
                "abstract_model_id": bundle.abstract_model_id,
                "abstract_model_version": bundle.abstract_model_version,
                "claim_model_id": bundle.claim_model_id,
                "claim_model_version": bundle.claim_model_version,
                "corpus_snapshot": settings.snapshot_date,
                "vector_sample_pct": settings.vector_sample_pct,
                "claim_payload_path": str(out_claims),
                "abstract_payload_path": str(out_abstracts),
                "query_registry_path": str(query_registry),
                "claim_payload_count": merged_claims,
                "abstract_payload_count": merged_abstracts,
                "query_registry_count": query_registry_rows,
                "bucket_count": bucket_count,
                "bucket_range_built": [bucket_start, bucket_end],
            },
        )
        write_text_json(
            ann_meta,
            {
                "ann_method": settings.semantic_ann_method,
                "index_status": "not_built_exact_scan_only",
                "reason": "Dense embeddings are promoted first; ANN snapshots will be added after exact-scan quality gates are met.",
                "embedding_device": embedding_device,
                "claim_duplicate_family_rate": claim_duplicate_rate,
                "abstract_duplicate_family_rate": abstract_duplicate_rate,
                "claim_legal_status_join_completeness": claim_legal_completeness,
                "abstract_legal_status_join_completeness": abstract_legal_completeness,
                "claim_chronology_join_completeness": claim_chronology_completeness,
                "abstract_chronology_join_completeness": abstract_chronology_completeness,
                "claim_blocking_context_completeness": claim_blocking_completeness,
                "abstract_blocking_context_completeness": abstract_blocking_completeness,
                "query_anchor_claim_coverage": query_anchor_claim_coverage,
                "query_anchor_abstract_coverage": query_anchor_abstract_coverage,
            },
        )
        write_text_json(
            query_registry_meta,
            {
                "status": "materialized",
                "query_source": "phase0_semantic_fixture",
                "query_registry_path": str(query_registry),
                "query_registry_count": query_registry_rows,
                "embedding_runtime": bundle.embedding_runtime,
                "embedding_device": embedding_device,
                "corpus_snapshot": settings.snapshot_date,
            },
        )
    else:
        result.warnings.append("Semantic metadata and query registry writes were skipped for this subset worker run.")

    result.outputs.extend([str(out_claims), str(out_abstracts), str(manifest), str(ann_meta), str(query_registry), str(query_registry_meta)])
    result.metrics["vec_family_embeddings_claims_rows"] = merged_claims
    result.metrics["vec_family_embeddings_abstracts_rows"] = merged_abstracts
    result.metrics["vec_query_registry_rows"] = query_registry_rows
    result.metrics["claim_duplicate_family_rate"] = claim_duplicate_rate
    result.metrics["abstract_duplicate_family_rate"] = abstract_duplicate_rate
    result.metrics["claim_legal_status_join_completeness"] = claim_legal_completeness
    result.metrics["abstract_legal_status_join_completeness"] = abstract_legal_completeness
    result.metrics["claim_chronology_join_completeness"] = claim_chronology_completeness
    result.metrics["abstract_chronology_join_completeness"] = abstract_chronology_completeness
    result.metrics["claim_blocking_context_completeness"] = claim_blocking_completeness
    result.metrics["abstract_blocking_context_completeness"] = abstract_blocking_completeness
    result.metrics["query_anchor_claim_coverage"] = query_anchor_claim_coverage
    result.metrics["query_anchor_abstract_coverage"] = query_anchor_abstract_coverage
    return [result]
