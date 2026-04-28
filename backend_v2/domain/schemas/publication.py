from typing import Any

from pydantic import BaseModel, Field

from domain.schemas.common import PageIdentity, ResponseMeta


class PublicationOverviewResponse(BaseModel):
    identity: PageIdentity
    overview: dict[str, Any] = Field(default_factory=dict)
    summary_cards: list[dict[str, Any]] = Field(default_factory=list)
    bibliography: list[dict[str, Any]] = Field(default_factory=list)
    family_context: list[dict[str, Any]] = Field(default_factory=list)
    text_availability: list[dict[str, Any]] = Field(default_factory=list)
    register_evidence: list[dict[str, Any]] = Field(default_factory=list)
    related_publications: list[dict[str, Any]] = Field(default_factory=list)
    meta: ResponseMeta


class PublicationSuggestion(BaseModel):
    publication_id: str
    label: str
    authority: str | None = None
    kind_code: str | None = None
    publication_date: str | None = None
    family_id: str | None = None


class PublicationSuggestionResponse(BaseModel):
    query: str
    rows: list[PublicationSuggestion] = Field(default_factory=list)


class PublicationSectionResponse(BaseModel):
    publication_id: str
    summary: dict[str, Any] | None = None
    rows: list[dict[str, Any]] = Field(default_factory=list)
    meta: ResponseMeta
