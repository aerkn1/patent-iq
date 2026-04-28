from typing import Any

from pydantic import BaseModel, Field

from domain.schemas.common import PageIdentity, ResponseMeta


class CompareResponse(BaseModel):
    compare_kind: str
    compare_mode: str = "entity"
    left_entity: PageIdentity | None = None
    right_entity: PageIdentity | None = None
    rows: list[dict[str, Any]] = Field(default_factory=list)
    identity_context: list[dict[str, Any]] = Field(default_factory=list)
    summary_cards: list[dict[str, Any]] = Field(default_factory=list)
    contrast_rows: list[dict[str, Any]] = Field(default_factory=list)
    field_overlap_rows: list[dict[str, Any]] = Field(default_factory=list)
    forecast_rows: list[dict[str, Any]] = Field(default_factory=list)
    support_rows: list[dict[str, Any]] = Field(default_factory=list)
    meta: ResponseMeta


class CompareTimesliceOptionsResponse(BaseModel):
    entity_id: str
    available_years: list[int] = Field(default_factory=list)
    compare_safe_years: list[int] = Field(default_factory=list)
    default_base_year: int | None = None
    default_compare_year: int | None = None


class CompareScopeLookupResponse(BaseModel):
    compare_kind: str
    entity_id: str
    label: str | None = None
    in_scope: bool
    primary_field: str | None = None
    status: str | None = None
    family_count: int | None = None
    timeslice_available: bool = False
    default_base_year: int | None = None
    default_compare_year: int | None = None
    note: str | None = None


class CompareFamilySuggestion(BaseModel):
    family_id: str
    label: str
    owner_label: str | None = None
    primary_field: str | None = None
    status: str | None = None


class CompareFamilySuggestionResponse(BaseModel):
    query: str
    rows: list[CompareFamilySuggestion] = Field(default_factory=list)
