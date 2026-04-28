from pydantic import BaseModel, Field

from domain.schemas.common import CoverageMetadata, PageIdentity, ResponseMeta


class PortfolioSummaryCard(BaseModel):
    key: str
    label: str
    value: str
    tone: str = "neutral"
    tooltip: str | None = None
    caveat: str | None = None
    band_code: str | None = None
    band_label: str | None = None
    peer_bucket: str | None = None
    peer_bucket_label: str | None = None
    peer_percentile: float | None = None


class PortfolioOwnerSearchResult(BaseModel):
    owner_id: str
    label: str
    family_count: int | None = None


class PortfolioOwnerSearchResponse(BaseModel):
    query: str
    rows: list[PortfolioOwnerSearchResult] = Field(default_factory=list)
    meta: ResponseMeta


class PortfolioCountScopes(BaseModel):
    in_scope_family_count: int | None = None
    primary_owner_family_count: int | None = None
    active_grant_family_count: int | None = None
    semantic_candidate_family_count: int | None = None
    pending_family_count: int | None = None
    unclassified_family_count: int | None = None


class PortfolioStatusSlice(BaseModel):
    key: str
    label: str
    count: int
    share: float


class PortfolioOverviewResponse(BaseModel):
    identity: PageIdentity
    summary_cards: list[PortfolioSummaryCard] = Field(default_factory=list)
    status_mix: list[PortfolioStatusSlice] = Field(default_factory=list)
    family_count: int | None = None
    count_scopes: PortfolioCountScopes | None = None
    active_grant_family_count: int | None = None
    semantic_candidate_count: int | None = None
    top_family_preview: list[dict[str, str | int | float | None]] = Field(default_factory=list)
    meta: ResponseMeta


class PortfolioFamiliesResponse(BaseModel):
    owner_id: str
    rows: list[dict[str, str | int | float | None]] = Field(default_factory=list)
    meta: ResponseMeta


class PortfolioFieldsResponse(BaseModel):
    owner_id: str
    rows: list[dict[str, str | int | float | None]] = Field(default_factory=list)
    meta: ResponseMeta


class PortfolioSectionResponse(BaseModel):
    owner_id: str
    rows: list[dict[str, object]] = Field(default_factory=list)
    meta: ResponseMeta


class PortfolioForecastResponse(BaseModel):
    owner_id: str
    coverage: CoverageMetadata | None = None
    sections: list[dict[str, object]] = Field(default_factory=list)
    meta: ResponseMeta


class PortfolioThreatResponse(BaseModel):
    owner_id: str
    rows: list[dict[str, str | int | float | None]] = Field(default_factory=list)
    meta: ResponseMeta


class PortfolioClassificationRow(BaseModel):
    segment: str
    classification_type: str = "CPC_MAIN_GROUP"
    wipo_field: str
    family_share: float
    trajectory: float
    top_change: str


class PortfolioClassificationTimeseriesPoint(BaseModel):
    year: int
    share: float
    portfolio: float | None = None


class PortfolioClassificationTimeseries(BaseModel):
    field: str
    points: list[PortfolioClassificationTimeseriesPoint] = Field(default_factory=list)


class PortfolioClassificationResponse(BaseModel):
    owner_id: str
    rows: list[PortfolioClassificationRow] = Field(default_factory=list)
    timeseries: list[PortfolioClassificationTimeseries] = Field(default_factory=list)
    meta: ResponseMeta
