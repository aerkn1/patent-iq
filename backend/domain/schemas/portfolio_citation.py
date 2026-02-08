from pydantic import BaseModel
from typing import List, Optional

class PortfolioSize(BaseModel):
    n_patents_effective: float

class CitationVolume(BaseModel):
    early_cites_total: float
    mid_cites_total: float
    late_cites_total: float
    early_cites_per_patent: float
    mid_cites_per_patent: float
    late_cites_per_patent: float
    cites_per_patent: float

class CitationQualityRaw(BaseModel):
    trajectory_score_avg: float
    durability_score_avg: float
    sustainability_score_avg: float
    timing_score_avg: float

class CitationQualityPercentile(BaseModel):
    trajectory_score_pct: float
    durability_score_pct: float
    sustainability_score_pct: float
    timing_score_pct: float

class PortfolioBehavior(BaseModel):
    timing_class_mode: str
    early_signal_share: float
    sustaining_share: float

class PortfolioCitationMetricsResponse(BaseModel):
    owner_id: int
    portfolio_size: PortfolioSize
    citation_volume: CitationVolume
    citation_quality_raw: CitationQualityRaw
    citation_quality_percentile: CitationQualityPercentile
    portfolio_behavior: PortfolioBehavior

class PortfolioTimeSeriesPoint(BaseModel):
    year: int
    citations_total: float
    early_cites: float
    mid_cites: float
    late_cites: float
    citations_per_patent: float
    early_cites_per_patent: float
    mid_cites_per_patent: float
    late_cites_per_patent: float
    citations_yoy_delta: Optional[float] = None
    citations_yoy_pct: Optional[float] = None
    citations_cum_total: float
    citation_phase: str

class PortfolioCitationTimeSeriesResponse(BaseModel):
    owner_id: int
    series: List[PortfolioTimeSeriesPoint]
