from typing import Any

from pydantic import BaseModel, Field

from domain.schemas.common import PageIdentity, ResponseMeta


class SemanticSearchResponse(BaseModel):
    query_mode: str = "family_anchor"
    vector_space: str
    anchor_entity: PageIdentity | None = None
    selected_entity: PageIdentity | None = None
    summary: dict[str, Any] | None = None
    summary_cards: list[dict[str, Any]] = Field(default_factory=list)
    query_context: list[dict[str, Any]] = Field(default_factory=list)
    result_rows: list[dict[str, Any]] = Field(default_factory=list)
    meta: ResponseMeta


class SemanticCompareResponse(BaseModel):
    compare_kind: str = "semantic_families"
    left_entity: PageIdentity | None = None
    right_entity: PageIdentity | None = None
    entity_summaries: list[dict[str, Any]] = Field(default_factory=list)
    summary_cards: list[dict[str, Any]] = Field(default_factory=list)
    compare_rows: list[dict[str, Any]] = Field(default_factory=list)
    detail_panels: list[dict[str, Any]] = Field(default_factory=list)
    meta: ResponseMeta


class SemanticFamilySuggestion(BaseModel):
    family_id: str
    label: str
    owner_name_harmonized: str | None = None
    primary_wipo_field: str | None = None
    family_composite_status: str | None = None


class SemanticFamilySuggestionResponse(BaseModel):
    query: str
    vector_space: str
    rows: list[SemanticFamilySuggestion] = Field(default_factory=list)
