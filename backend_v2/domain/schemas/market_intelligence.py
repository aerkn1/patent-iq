from typing import Any

from pydantic import BaseModel, Field

from domain.schemas.common import PageIdentity, ResponseMeta


class MarketOverviewResponse(BaseModel):
    identity: PageIdentity
    summary_cards: list[dict[str, str | int | float | None]] = Field(default_factory=list)
    featured_segments: list[dict[str, str | int | float | None]] = Field(default_factory=list)
    meta: ResponseMeta


class MarketSectionResponse(BaseModel):
    segment_id: str | None = None
    section_key: str | None = None
    metric_basis: str | None = None
    scope_basis: str | None = None
    sum_safe: bool | None = None
    overlap_policy: str | None = None
    rows: list[dict[str, str | int | float | bool | None]] = Field(default_factory=list)
    meta: ResponseMeta


class MarketWorkspaceResponse(BaseModel):
    identity: PageIdentity
    scope: dict[str, Any] = Field(default_factory=dict)
    overview: dict[str, Any] = Field(default_factory=dict)
    filters: dict[str, Any] = Field(default_factory=dict)
    segments: list[dict[str, Any]] = Field(default_factory=list)
    selected_segment: dict[str, Any] | None = None
    methodology: list[dict[str, Any]] = Field(default_factory=list)
    meta: ResponseMeta
