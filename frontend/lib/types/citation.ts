export interface CitationMetricsResponse {
    early_cites: number
    mid_cites: number
    late_cites: number
    trajectory_score: number
    durability_score: number
    sustainability_score_ui: number
    timing_score: number
    timing_class: string
    early_signal: number
    is_sustaining: boolean
    citation_span_years: number
    peak_age: number
}

export interface TimeSeriesPoint {
    age_year: number
    new_forward_cites: number
    cum_forward_cites: number
}

export interface CitationTimeSeriesResponse {
    appln_id: number
    filing_date: number
    series: TimeSeriesPoint[]
}
