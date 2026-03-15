from __future__ import annotations

import json

import duckdb

from patentiq_etl.common.io import parquet_row_count, stable_hash_embedding, write_pylist_parquet, write_text_json
from patentiq_etl.common.types import BuildSettings, StageResult


def run_semantic(settings: BuildSettings) -> list[StageResult]:
    """Package bounded semantic payloads, manifests, and ANN metadata for the MVP release."""
    result = StageResult(
        stage="semantic",
        status="success",
        summary="Packaged vector payloads, embedding manifests, and ANN placeholder metadata for the MVP semantic layer.",
        methods=[
            "Derived claim and abstract vector payloads from the representative family text table.",
            "Used deterministic hash embeddings as the default local MVP embedding method until a promoted external embedding model is wired in.",
        ],
        calculations=[
            "Claim and abstract vector spaces remain physically separate.",
            "Only bounded semantic candidates are embedded.",
        ],
        doc_refs=[
            "docs/new-feature-ideas/semantic-similarity-and-vector-layer-requirements.md",
            "docs/next-phase-v2/16-patentiq-v2-semantic-search-and-comparison-flow-and-guardrails.md",
            "docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md",
        ],
    )

    rep = settings.silver_dir / "silver_family_text_representative.parquet"
    elig = settings.silver_dir / "silver_semantic_sampling_eligibility.parquet"
    out_claims = settings.vectors_dir / "vec_family_embeddings_claims.parquet"
    out_abstracts = settings.vectors_dir / "vec_family_embeddings_abstracts.parquet"
    manifest = settings.vectors_dir / "vec_embedding_manifest.json"
    ann_meta = settings.vectors_dir / "vec_ann_index_manifest.json"

    if not rep.exists() or not elig.exists():
        result.status = "failed"
        result.warnings.append("Representative text and semantic eligibility must exist before vector packaging.")
        return [result]

    con = duckdb.connect()
    rep_rows = con.execute(
        f"""
        select
            r.docdb_family_id,
            r.representative_claim_1_en,
            r.representative_abstract_en,
            r.text_provenance,
            r.is_abstract_fallback
        from read_parquet('{rep}') r
        join read_parquet('{elig}') e using (docdb_family_id)
        where e.is_semantic_candidate = true
        """
    ).fetchall()

    claim_rows: list[dict] = []
    abstract_rows: list[dict] = []
    for family_id, claim_text, abstract_text, provenance, is_fallback in rep_rows:
        if claim_text:
            claim_rows.append(
                {
                    "docdb_family_id": family_id,
                    "vector_space": "vector_claims",
                    "text_provenance": provenance,
                    "is_abstract_fallback": bool(is_fallback),
                    "embedding": stable_hash_embedding(claim_text),
                }
            )
        if abstract_text:
            abstract_rows.append(
                {
                    "docdb_family_id": family_id,
                    "vector_space": "vector_abstract",
                    "text_provenance": provenance,
                    "is_abstract_fallback": bool(is_fallback),
                    "embedding": stable_hash_embedding(abstract_text),
                }
            )

    if claim_rows:
        write_pylist_parquet(claim_rows, out_claims)
    if abstract_rows:
        write_pylist_parquet(abstract_rows, out_abstracts)

    write_text_json(
        manifest,
        {
            "release_id": settings.release_id,
            "embedding_method": settings.semantic_embedding_method,
            "claim_payload_path": str(out_claims),
            "abstract_payload_path": str(out_abstracts),
            "vector_sample_pct": settings.vector_sample_pct,
            "claim_payload_count": len(claim_rows),
            "abstract_payload_count": len(abstract_rows),
        },
    )
    write_text_json(
        ann_meta,
        {
            "ann_method": settings.semantic_ann_method,
            "status": "manifest_only_placeholder",
            "reason": "ANN runtime packaging is declared, but a dedicated ANN index builder has not yet been integrated.",
        },
    )

    result.outputs.extend([str(out_claims), str(out_abstracts), str(manifest), str(ann_meta)])
    if out_claims.exists():
        result.metrics["vec_family_embeddings_claims_rows"] = parquet_row_count(out_claims)
    if out_abstracts.exists():
        result.metrics["vec_family_embeddings_abstracts_rows"] = parquet_row_count(out_abstracts)
    return [result]
