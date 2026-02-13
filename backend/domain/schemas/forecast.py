"""
Pydantic schemas for citation forecast API responses.
"""

from pydantic import BaseModel
from typing import Literal, Optional


# ── Shared ──────────────────────────────────────────────────────────────────

class Interval80(BaseModel):
    low: float
    high: float


class ForecastMeta(BaseModel):
    model_version: str
    calibration: str = "bucketed_conformal_80"
    as_of_definition: str = "filing_plus_2y"


# ── Patent-level ────────────────────────────────────────────────────────────

class PatentPrediction(BaseModel):
    expected_citations: float
    interval_80: Interval80
    difficulty_bucket: Literal["LOW", "MID", "HIGH"]


class PatentForecastResponse(BaseModel):
    appln_id: int
    horizon: str
    filing_date: str
    as_of_date: str
    prediction: PatentPrediction
    features_used: dict
    meta: ForecastMeta


# ── Portfolio-level ─────────────────────────────────────────────────────────

class DifficultyMix(BaseModel):
    LOW: float
    MID: float
    HIGH: float


class TopContributor(BaseModel):
    appln_id: int
    owner_share: float
    expected: float
    interval_80: Interval80
    contribution: float
    difficulty_bucket: str


class PortfolioPrediction(BaseModel):
    expected_citations_total: float
    interval_80_total: Interval80
    n_patents_effective: float
    expected_per_effective_patent: float


class SegmentItem(BaseModel):
    key: str
    expected: float
    interval_80: Interval80
    share: float


class SegmentsMeta(BaseModel):
    top_k: int
    cpc_top_n_per_patent: int
    allocation: str
    other_bucket_label: str = "OTHER"


class PortfolioForecastSegments(BaseModel):
    meta: SegmentsMeta
    by_cpc_subclass: list[SegmentItem] = []
    by_jurisdiction_coverage_bucket: list[SegmentItem] = []
    by_major_office_grant_bucket: list[SegmentItem] = []
    by_as_of_year_bucket: list[SegmentItem] = []


class PortfolioForecastResponse(BaseModel):
    owner_id: int
    horizon: str
    as_of_date: str
    portfolio_prediction: PortfolioPrediction
    difficulty_mix: DifficultyMix
    top_contributors: list[TopContributor]
    segments: Optional[PortfolioForecastSegments] = None
    meta: ForecastMeta


class CitationForecastTimeSeriesItem(BaseModel):
    year: int
    cum_cites: float
    low: Optional[float] = None
    high: Optional[float] = None


class ForecastPredictionSummary(BaseModel):
    expected_additional: float
    interval_80: Interval80
    difficulty_bucket: str


class CitationForecastTimeSeriesResponse(BaseModel):
    appln_id: int
    filing_year: int
    horizon: str
    last_observed_year: int
    historical: list[CitationForecastTimeSeriesItem]
    forecast: list[CitationForecastTimeSeriesItem]
    prediction_summary: ForecastPredictionSummary
