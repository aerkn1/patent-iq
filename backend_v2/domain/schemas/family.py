from typing import Any

from pydantic import BaseModel, Field

from domain.schemas.common import PageIdentity, ResponseMeta


class FamilyOverviewResponse(BaseModel):
    identity: PageIdentity
    summary_cards: list[dict[str, Any]] = Field(default_factory=list)
    overview_metrics: list[dict[str, Any]] = Field(default_factory=list)
    meta: ResponseMeta


class FamilySuggestion(BaseModel):
    family_id: str
    label: str
    owner_label: str | None = None
    primary_field: str | None = None
    status: str | None = None


class FamilySuggestionResponse(BaseModel):
    query: str
    rows: list[FamilySuggestion] = Field(default_factory=list)


class FamilySectionResponse(BaseModel):
    family_id: str
    summary: dict[str, Any] | None = None
    rows: list[dict[str, Any]] = Field(default_factory=list)
    series: list[dict[str, Any]] = Field(default_factory=list)
    meta: ResponseMeta
