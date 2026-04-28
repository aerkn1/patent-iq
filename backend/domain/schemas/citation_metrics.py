from pydantic import BaseModel
from typing import Optional

class CitationMetricsResponse(BaseModel):
    early_cites: int
    mid_cites: int
    late_cites: int
    trajectory_score: float
    durability_score: float
    sustainability_score_ui: float
    timing_score: float
    timing_class: str
    early_signal: float
    is_sustaining: bool
    citation_span_years: int
    peak_age: int
    trajectory_score_pct: float
    durability_score_pct: float
    sustainability_score_pct: float
    timing_score_pct: float

class TimeSeriesPoint(BaseModel):
    age_year: int
    new_forward_cites: int
    cum_forward_cites: int

class CitationTimeSeriesResponse(BaseModel):
    appln_id: int
    filing_date: int
    series: list[TimeSeriesPoint]
