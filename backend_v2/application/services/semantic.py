from __future__ import annotations

import logging

from fastapi import HTTPException

from domain.schemas.common import Caveat, CoverageMetadata, PageIdentity, PaginationMetadata, ResponseMeta, SupportLevel
from domain.schemas.semantic import SemanticCompareResponse, SemanticFamilySuggestion, SemanticFamilySuggestionResponse, SemanticSearchResponse
from infrastructure.repositories.semantic_repository import SemanticRepository
from infrastructure.semantic_query_encoder import SemanticQueryEncoder, get_semantic_query_encoder

logger = logging.getLogger("uvicorn.error")


class SemanticService:
    def __init__(
        self,
        repository: SemanticRepository | None = None,
        query_encoder: SemanticQueryEncoder | None = None,
    ) -> None:
        self.repository = repository or SemanticRepository()
        self.query_encoder = query_encoder or get_semantic_query_encoder()

    def get_family_anchor_search(
        self,
        family_id: str,
        *,
        vector_space: str = "abstract",
        limit: int = 12,
        offset: int = 0,
        same_field_only: bool = False,
        exclude_same_owner: bool = False,
        selected_family_id: str | None = None,
    ) -> SemanticSearchResponse:
        normalized_space = self._normalize_vector_space(vector_space)
        support = self.repository.get_family_vector_support(family_id)
        available_spaces = [space for space, available in support.items() if available]
        if not available_spaces:
            raise HTTPException(status_code=404, detail=f"Family {family_id} is not available in the semantic vector payloads.")
        if not support[normalized_space]:
            available_label = ", ".join(available_spaces)
            raise HTTPException(
                status_code=400,
                detail=f"Family {family_id} is not available in {normalized_space} space. Available spaces: {available_label}.",
            )

        safe_limit = min(max(limit, 1), 40)
        safe_offset = max(offset, 0)
        anchor = self.repository.get_anchor_row(family_id, normalized_space)
        if not anchor:
            raise HTTPException(status_code=404, detail=f"Family {family_id} was not found in {normalized_space} semantic space.")

        summary = self.repository.get_space_summary(normalized_space)
        result_rows, total_count = self.repository.get_anchor_search_results(
            family_id,
            normalized_space,
            limit=safe_limit,
            offset=safe_offset,
            same_field_only=same_field_only,
            exclude_same_owner=exclude_same_owner,
        )

        selected_entity = None
        if selected_family_id:
            selected_row = next((row for row in result_rows if str(row.get("docdb_family_id")) == str(selected_family_id)), None)
            if selected_row is not None:
                selected_entity = PageIdentity(
                    id=str(selected_row.get("docdb_family_id")),
                    label=str(selected_row.get("docdb_family_id")),
                    page_kind="family",
                )

        searchable_count = self._to_int(summary.get("searchable_family_count"))
        total_context_count = self._to_int(summary.get("total_context_family_count"))
        vector_coverage_pct = self._to_float(summary.get("vector_coverage_pct"))
        abstract_fallback_count = self._to_int(summary.get("abstract_fallback_count"))
        claim_backed_count = self._to_int(summary.get("claim_backed_count"))

        summary_cards = [
            {
                "key": "searchable_families",
                "label": "Searchable families",
                "value": searchable_count,
                "display_kind": "count",
                "note": f"{self._vector_space_label(normalized_space)} exact-search payload size.",
            },
            {
                "key": "coverage_pct",
                "label": "Context coverage",
                "value": vector_coverage_pct,
                "display_kind": "percent",
                "note": "Share of one-row-per-family semantic context currently searchable through the vector payload.",
            },
            {
                "key": "claim_backed_count" if normalized_space == "claims" else "abstract_fallback_count",
                "label": "Claim-backed families" if normalized_space == "claims" else "Abstract-fallback families",
                "value": claim_backed_count if normalized_space == "claims" else abstract_fallback_count,
                "display_kind": "count",
                "note": (
                    "EPAB claim-backed rows in the current claim-search payload."
                    if normalized_space == "claims"
                    else "Abstract rows depend on PATSTAT English abstract fallback in the current abstract-search payload."
                ),
            },
            {
                "key": "retrieval_mode",
                "label": "Retrieval mode",
                "value": "Exact vector ranking",
                "display_kind": "text",
                "note": "ANN indexes exist in ETL artifacts, but backend_v2 is currently using exact cosine ranking for determinism.",
            },
        ]

        query_context = [
            {
                "key": "anchor_family",
                "label": "Anchor family",
                "value": str(anchor.get("docdb_family_id")),
            },
            {
                "key": "vector_space",
                "label": "Vector space",
                "value": self._vector_space_label(normalized_space),
            },
            {
                "key": "anchor_field",
                "label": "Primary field",
                "value": self._to_text(anchor.get("primary_wipo_field")) or "Unknown",
            },
            {
                "key": "anchor_owner",
                "label": "Owner",
                "value": self._to_text(anchor.get("owner_name_harmonized")) or "Unassigned",
            },
        ]

        caveats = [
            Caveat(
                code="semantic_sample_scope",
                title="Search runs on the current vector payload, not the full semantic context universe",
                detail=(
                    f"The active {self._vector_space_label(normalized_space).lower()} payload currently covers "
                    f"{searchable_count or 0} searchable families out of {total_context_count or 0} semantic-context families."
                ),
            ),
            Caveat(
                code="semantic_exact_runtime",
                title="Exact ranking is active in backend_v2",
                detail="ANN snapshot artifacts are present locally, but backend_v2 currently serves exact cosine ranking for the live semantic workspace.",
            ),
            Caveat(
                code="semantic_text_query_scope",
                title="Free-text discovery is narrower than family-anchor search",
                detail="Free-text semantic search is exposed only as abstract-first discovery. Claim-space retrieval still uses family anchors or family-to-family compare.",
            ),
        ]
        if normalized_space == "abstract":
            caveats.append(
                Caveat(
                    code="abstract_fallback_semantics",
                    title="Abstract discovery is fallback-heavy",
                    detail="Most abstract-space rows are PATSTAT abstract fallback rather than claim-grade text, so abstract search is discovery-oriented rather than claim-faithful.",
                )
            )

        return SemanticSearchResponse(
            query_mode="family_anchor",
            vector_space=normalized_space,
            anchor_entity=PageIdentity(
                id=str(anchor.get("docdb_family_id")),
                label=str(anchor.get("docdb_family_id")),
                page_kind="family",
            ),
            selected_entity=selected_entity,
            summary={
                "anchor_family_id": str(anchor.get("docdb_family_id")),
                "anchor_owner": self._to_text(anchor.get("owner_name_harmonized")),
                "anchor_primary_field": self._to_text(anchor.get("primary_wipo_field")),
                "anchor_status": self._to_text(anchor.get("family_composite_status")),
                "anchor_text_excerpt": self._excerpt(anchor.get("queryable_text")),
                "anchor_text_provenance": self._to_text(anchor.get("text_provenance")),
                "same_field_only": same_field_only,
                "exclude_same_owner": exclude_same_owner,
            },
            summary_cards=summary_cards,
            query_context=query_context,
            result_rows=[self._serialize_search_row(row) for row in result_rows],
            meta=ResponseMeta(
                page="semantic.family_anchor_search",
                artifact_sources=[str(path) for path in self.repository.artifacts()],
                support_level=SupportLevel.candidate_only,
                coverage=CoverageMetadata(
                    status=self._coverage_status(vector_coverage_pct),
                    pct=vector_coverage_pct,
                    covered_count=searchable_count,
                    denominator_count=total_context_count,
                    caveat_text="Vector-search coverage reflects the current payload, not the full semantic context universe.",
                ),
                pagination=PaginationMetadata(
                    limit=safe_limit,
                    offset=safe_offset,
                    returned_count=len(result_rows),
                    total_count=total_count,
                ),
                caveats=caveats,
            ),
        )

    def get_family_anchor_suggestions(
        self,
        query: str,
        *,
        vector_space: str = "abstract",
        limit: int = 8,
    ) -> SemanticFamilySuggestionResponse:
        normalized_space = self._normalize_vector_space(vector_space)
        safe_limit = min(max(limit, 1), 20)
        rows = self.repository.get_family_anchor_suggestions(query, normalized_space, limit=safe_limit)
        return SemanticFamilySuggestionResponse(
            query=str(query).strip(),
            vector_space=normalized_space,
            rows=[
                SemanticFamilySuggestion(
                    family_id=str(row.get("family_id")),
                    label=str(row.get("label") or row.get("family_id")),
                    owner_name_harmonized=self._to_text(row.get("owner_name_harmonized")),
                    primary_wipo_field=self._to_text(row.get("primary_wipo_field")),
                    family_composite_status=self._to_text(row.get("family_composite_status")),
                )
                for row in rows
                if row.get("family_id") is not None
            ],
        )

    def get_text_discovery_search(
        self,
        query_text: str,
        *,
        vector_space: str = "abstract",
        limit: int = 12,
        offset: int = 0,
    ) -> SemanticSearchResponse:
        normalized_space = self._normalize_vector_space(vector_space)
        if normalized_space != "abstract":
            raise HTTPException(
                status_code=400,
                detail="Free-text semantic discovery is currently limited to abstract scope.",
            )

        normalized_query = self._normalize_query_text(query_text)
        if not self._query_text_is_usable(normalized_query):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Use a short English technical description with at least three words. "
                    "Free-text semantic discovery is not designed for ids, owner names, or legal claim language."
                ),
            )

        safe_limit = min(max(limit, 1), 40)
        safe_offset = max(offset, 0)
        logger.info(
            "semantic text search accepted space=%s limit=%s offset=%s query_chars=%s",
            normalized_space,
            safe_limit,
            safe_offset,
            len(normalized_query),
        )
        summary = self.repository.get_space_summary(normalized_space)
        try:
            logger.info("semantic text search encoding started space=%s", normalized_space)
            query_embedding = self.query_encoder.encode_text(normalized_query, normalized_space)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(
                status_code=503,
                detail="Semantic query encoding is not available in the current runtime.",
            ) from exc
        logger.info("semantic text search encoding finished space=%s dims=%s", normalized_space, len(query_embedding))

        logger.info("semantic text search ranking started space=%s", normalized_space)
        result_rows, total_count = self.repository.get_text_query_search_results(
            query_embedding,
            normalized_space,
            limit=safe_limit,
            offset=safe_offset,
        )
        logger.info(
            "semantic text search ranking finished space=%s returned=%s total=%s",
            normalized_space,
            len(result_rows),
            total_count,
        )

        searchable_count = self._to_int(summary.get("searchable_family_count"))
        total_context_count = self._to_int(summary.get("total_context_family_count"))
        vector_coverage_pct = self._to_float(summary.get("vector_coverage_pct"))
        abstract_fallback_count = self._to_int(summary.get("abstract_fallback_count"))

        summary_cards = [
            {
                "key": "searchable_families",
                "label": "Searchable families",
                "value": searchable_count,
                "display_kind": "count",
                "note": "Abstract discovery payload size currently searchable by free-text query.",
            },
            {
                "key": "abstract_fallback_count",
                "label": "Abstract-backed families",
                "value": abstract_fallback_count,
                "display_kind": "count",
                "note": "Free-text discovery currently runs only over the abstract-space payload.",
            },
        ]

        query_context = [
            {
                "key": "query_text",
                "label": "Search text",
                "value": self._excerpt(normalized_query, limit=120) or normalized_query,
            },
            {
                "key": "vector_space",
                "label": "Vector space",
                "value": self._vector_space_label(normalized_space),
            },
            {
                "key": "query_profile",
                "label": "Healthy query profile",
                "value": "Short English technical descriptions similar to patent abstracts.",
            },
            {
                "key": "safe_use",
                "label": "Safe use",
                "value": "Exploratory discovery of covered families, not infringement or whitespace proof.",
            },
        ]

        caveats = [
            Caveat(
                code="semantic_sample_scope",
                title="Search runs on the current vector payload, not the full semantic context universe",
                detail=(
                    f"The active abstract payload currently covers {searchable_count or 0} searchable families "
                    f"out of {total_context_count or 0} semantic-context families."
                ),
            ),
            Caveat(
                code="semantic_exact_runtime",
                title="Exact ranking is active in backend_v2",
                detail="ANN snapshot artifacts are present locally, but backend_v2 currently serves exact cosine ranking for the live semantic workspace.",
            ),
            Caveat(
                code="semantic_text_discovery_only",
                title="Free-text search is discovery-oriented",
                detail=(
                    "Free-text semantic search is intended for abstract-first discovery of covered families. "
                    "It should not be interpreted as legal-grade threat, infringement, or whitespace evidence."
                ),
            ),
            Caveat(
                code="abstract_fallback_semantics",
                title="Free-text discovery currently runs only in abstract space",
                detail=(
                    "The current free-text query path is intentionally limited to the broader PATSTAT-abstract-backed discovery payload. "
                    "Claim-space free-text search is deferred because the claim corpus is narrower and EPAB-backed rather than global."
                ),
            ),
        ]

        return SemanticSearchResponse(
            query_mode="free_text",
            vector_space=normalized_space,
            anchor_entity=None,
            selected_entity=None,
            summary={
                "query_text_excerpt": self._excerpt(normalized_query),
            },
            summary_cards=summary_cards,
            query_context=query_context,
            result_rows=[self._serialize_search_row(row) for row in result_rows],
            meta=ResponseMeta(
                page="semantic.text_discovery_search",
                artifact_sources=[str(path) for path in self.repository.artifacts()],
                support_level=SupportLevel.candidate_only,
                coverage=CoverageMetadata(
                    status=self._coverage_status(vector_coverage_pct),
                    pct=vector_coverage_pct,
                    covered_count=searchable_count,
                    denominator_count=total_context_count,
                    caveat_text="Free-text search covers the current abstract-space payload, not the full semantic context universe.",
                ),
                pagination=PaginationMetadata(
                    limit=safe_limit,
                    offset=safe_offset,
                    returned_count=len(result_rows),
                    total_count=total_count,
                ),
                caveats=caveats,
            ),
        )

    def get_family_semantic_compare(self, left_family_id: str, right_family_id: str) -> SemanticCompareResponse:
        left_context = self.repository.get_family_compare_context(left_family_id)
        right_context = self.repository.get_family_compare_context(right_family_id)
        if not left_context:
            raise HTTPException(status_code=404, detail=f"Family {left_family_id} is not available in the semantic vector payloads.")
        if not right_context:
            raise HTTPException(status_code=404, detail=f"Family {right_family_id} is not available in the semantic vector payloads.")

        abstract_similarity = self.repository.get_pair_similarity(left_family_id, right_family_id, "abstract")
        claims_similarity = self.repository.get_pair_similarity(left_family_id, right_family_id, "claims")
        same_field = self._to_text(left_context.get("primary_wipo_field")) == self._to_text(right_context.get("primary_wipo_field"))
        same_owner = self._to_text(left_context.get("owner_name_harmonized")) == self._to_text(right_context.get("owner_name_harmonized"))

        summary_cards = [
            self._metric_card(
                key="abstract_similarity",
                label="Abstract similarity",
                value=abstract_similarity,
                note="PATSTAT abstract discovery space.",
                supported=abstract_similarity is not None,
            ),
            self._metric_card(
                key="claims_similarity",
                label="Claim similarity",
                value=claims_similarity,
                note="EPAB claim-backed similarity space.",
                supported=claims_similarity is not None,
            ),
            {
                "key": "field_relationship",
                "label": "Primary field relation",
                "value": "Shared field" if same_field else "Different primary fields",
                "display_kind": "text",
                "note": self._to_text(left_context.get("primary_wipo_field")) or "No primary field available",
            },
            {
                "key": "owner_relationship",
                "label": "Owner relation",
                "value": "Same owner" if same_owner else "Different owners",
                "display_kind": "text",
                "note": "Owner identity is harmonized-name metadata, not legal proof of common control.",
            },
        ]

        compare_rows = [
            {
                "key": "abstract_similarity",
                "label": "Abstract discovery overlap",
                "value": abstract_similarity,
                "display_kind": "decimal",
                "supported": abstract_similarity is not None,
                "note": "Use this as discovery overlap, not legal proof.",
            },
            {
                "key": "claims_similarity",
                "label": "Claim-space overlap",
                "value": claims_similarity,
                "display_kind": "decimal",
                "supported": claims_similarity is not None,
                "note": "Unsupported when either family lacks claim-backed EPAB text in the current payload.",
            },
        ]

        entity_summaries = [
            self._entity_summary("anchor", left_context),
            self._entity_summary("selected", right_context),
        ]

        detail_panels = [
            self._detail_panel("left", left_context),
            self._detail_panel("right", right_context),
        ]

        caveats = [
            Caveat(
                code="semantic_compare_space_split",
                title="Semantic compare stays space-specific",
                detail="Claim and abstract similarities are shown separately on purpose. The workspace never blends them into one unlabeled semantic score.",
            ),
            Caveat(
                code="semantic_compare_sample_scope",
                title="Semantic compare reflects the current vector payload",
                detail="Similarity is computed only where both families are present in the current abstract or claim vector payloads.",
            ),
            Caveat(
                code="semantic_compare_not_legal_proof",
                title="Similarity is a discovery signal, not legal proof",
                detail="Semantic overlap should be read together with field, status, and provenance context before drawing strategic conclusions.",
            ),
        ]

        return SemanticCompareResponse(
            left_entity=PageIdentity(id=str(left_context.get("docdb_family_id")), label=str(left_context.get("label")), page_kind="family"),
            right_entity=PageIdentity(id=str(right_context.get("docdb_family_id")), label=str(right_context.get("label")), page_kind="family"),
            entity_summaries=entity_summaries,
            summary_cards=summary_cards,
            compare_rows=compare_rows,
            detail_panels=detail_panels,
            meta=ResponseMeta(
                page="semantic.family_compare",
                artifact_sources=[str(path) for path in self.repository.artifacts()],
                support_level=SupportLevel.candidate_only,
                caveats=caveats,
            ),
        )

    def _serialize_search_row(self, row: dict[str, object]) -> dict[str, object]:
        return {
            "family_id": str(row.get("docdb_family_id")),
            "family_title": self._to_text(row.get("family_title")),
            "owner_name_harmonized": self._to_text(row.get("owner_name_harmonized")),
            "primary_wipo_field": self._to_text(row.get("primary_wipo_field")),
            "semantic_similarity": self._to_float(row.get("semantic_similarity")),
            "family_composite_status": self._to_text(row.get("family_composite_status")),
            "family_ui_blocking_power_score": self._to_float(row.get("family_ui_blocking_power_score")),
            "oecd_quality_percentile": self._to_float(row.get("oecd_quality_percentile")),
            "representative_stage": self._to_text(row.get("representative_stage")),
            "text_provenance": self._to_text(row.get("text_provenance")),
            "text_source_type": self._to_text(row.get("text_source_type")),
            "is_abstract_fallback": bool(row.get("is_abstract_fallback")),
            "family_earliest_priority_date": self._to_text(row.get("family_earliest_priority_date")),
            "text_excerpt": self._to_text(row.get("text_excerpt")),
        }

    def _metric_card(
        self,
        *,
        key: str,
        label: str,
        value: float | None,
        note: str,
        supported: bool,
    ) -> dict[str, object]:
        return {
            "key": key,
            "label": label,
            "value": value if supported else "Unsupported",
            "display_kind": "decimal" if supported else "text",
            "note": note,
        }

    def _entity_summary(self, role: str, context: dict[str, object]) -> dict[str, object]:
        family_id = str(context.get("docdb_family_id"))
        return {
            "role": role,
            "family_id": family_id,
            "entity_label": f"Family {family_id}",
            "owner_name_harmonized": self._to_text(context.get("owner_name_harmonized")),
            "primary_wipo_field": self._to_text(context.get("primary_wipo_field")),
            "family_composite_status": self._to_text(context.get("family_composite_status")),
            "representative_stage": self._to_text(context.get("representative_stage")),
            "text_provenance": self._to_text(context.get("text_provenance")),
            "family_earliest_priority_date": self._to_text(context.get("family_earliest_priority_date")),
            "family_ui_blocking_power_score": self._to_float(context.get("family_ui_blocking_power_score")),
            "oecd_quality_percentile": self._to_float(context.get("oecd_quality_percentile")),
            "supported_spaces": self._supported_spaces(context),
            "support_note": self._space_support_note(context),
        }

    def _detail_panel(self, side: str, context: dict[str, object]) -> dict[str, object]:
        family_id = str(context.get("docdb_family_id"))
        return {
            "side": side,
            "family_id": family_id,
            "entity_label": f"Family {family_id}",
            "owner_name_harmonized": self._to_text(context.get("owner_name_harmonized")),
            "primary_wipo_field": self._to_text(context.get("primary_wipo_field")),
            "family_composite_status": self._to_text(context.get("family_composite_status")),
            "family_ui_blocking_power_score": self._to_float(context.get("family_ui_blocking_power_score")),
            "oecd_quality_percentile": self._to_float(context.get("oecd_quality_percentile")),
            "representative_stage": self._to_text(context.get("representative_stage")),
            "text_provenance": self._to_text(context.get("text_provenance")),
            "family_earliest_priority_date": self._to_text(context.get("family_earliest_priority_date")),
            "supported_spaces": self._supported_spaces(context),
            "text_excerpt": self._to_text(context.get("text_excerpt")),
        }

    def _supported_spaces(self, context: dict[str, object]) -> list[str]:
        badges = []
        if bool(context.get("abstract_supported")):
            badges.append("Abstract space")
        if bool(context.get("claims_supported")):
            badges.append("Claim space")
        return badges

    def _space_support_note(self, context: dict[str, object]) -> str:
        supports = []
        if bool(context.get("abstract_supported")):
            supports.append("abstract")
        if bool(context.get("claims_supported")):
            supports.append("claims")
        if not supports:
            return "No vector support"
        return f"Available spaces: {', '.join(supports)}"

    def _normalize_vector_space(self, vector_space: str | None) -> str:
        normalized = str(vector_space or "abstract").strip().lower()
        return "claims" if normalized in {"claims", "claim", "vector_claims"} else "abstract"

    def _normalize_query_text(self, query_text: str | None) -> str:
        return " ".join(str(query_text or "").split()).strip()

    def _query_text_is_usable(self, query_text: str) -> bool:
        if len(query_text) < 12:
            return False
        tokens = [token for token in query_text.split(" ") if token]
        alpha_tokens = [token for token in tokens if any(character.isalpha() for character in token)]
        return len(alpha_tokens) >= 3

    def _vector_space_label(self, vector_space: str) -> str:
        return "Claim Similarity" if vector_space == "claims" else "Abstract Discovery"

    def _coverage_status(self, coverage_pct: float | None) -> str:
        if coverage_pct is None:
            return "unknown"
        if coverage_pct >= 0.5:
            return "high"
        if coverage_pct >= 0.15:
            return "medium"
        return "low"

    def _to_int(self, value: object | None) -> int | None:
        try:
            if value is None:
                return None
            return int(value)
        except (TypeError, ValueError):
            return None

    def _to_float(self, value: object | None) -> float | None:
        try:
            if value is None:
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    def _to_text(self, value: object | None) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    def _excerpt(self, value: object | None, limit: int = 520) -> str | None:
        text = self._to_text(value)
        if not text:
            return None
        if len(text) <= limit:
            return text
        return f"{text[: limit - 1].rstrip()}…"
