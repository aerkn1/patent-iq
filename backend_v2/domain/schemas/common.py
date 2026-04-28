from enum import Enum

from pydantic import BaseModel, Field


class SupportLevel(str, Enum):
    strong = "strong"
    moderate = "moderate"
    limited = "limited"
    candidate_only = "candidate_only"


class Caveat(BaseModel):
    code: str
    title: str
    detail: str


class CoverageMetadata(BaseModel):
    status: str = "unknown"
    pct: float | None = None
    covered_count: int | None = None
    denominator_count: int | None = None
    caveat_text: str | None = None


class PaginationMetadata(BaseModel):
    limit: int
    offset: int
    returned_count: int
    total_count: int | None = None


class PageIdentity(BaseModel):
    id: str
    label: str
    page_kind: str
    selected_year: int | None = None


class ResponseMeta(BaseModel):
    page: str
    artifact_sources: list[str] = Field(default_factory=list)
    support_level: SupportLevel = SupportLevel.moderate
    caveats: list[Caveat] = Field(default_factory=list)
    coverage: CoverageMetadata | None = None
    pagination: PaginationMetadata | None = None
