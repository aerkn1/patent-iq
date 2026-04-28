export interface PortfolioSize {
    n_patents_effective: number;
}

export interface CitationVolume {
    early_cites_total: number;
    mid_cites_total: number;
    late_cites_total: number;
    early_cites_per_patent: number;
    mid_cites_per_patent: number;
    late_cites_per_patent: number;
    cites_per_patent: number;
}

export interface CitationQualityRaw {
    trajectory_score_avg: number;
    durability_score_avg: number;
    sustainability_score_avg: number;
    timing_score_avg: number;
}

export interface CitationQualityPercentile {
    trajectory_score_pct: number;
    durability_score_pct: number;
    sustainability_score_pct: number;
    timing_score_pct: number;
}

export interface PortfolioBehavior {
    timing_class_mode: string;
    early_signal_share: number;
    sustaining_share: number;
}

export interface PortfolioCitationMetricsResponse {
    owner_id: number;
    portfolio_size: PortfolioSize;
    citation_volume: CitationVolume;
    citation_quality_raw: CitationQualityRaw;
    citation_quality_percentile: CitationQualityPercentile;
    portfolio_behavior: PortfolioBehavior;
}

export interface PortfolioTimeSeriesPoint {
    year: number;
    citations_total: number;
    early_cites: number;
    mid_cites: number;
    late_cites: number;
    citations_per_patent: number;
    early_cites_per_patent: number;
    mid_cites_per_patent: number;
    late_cites_per_patent: number;
    citations_yoy_delta?: number;
    citations_yoy_pct?: number;
    citations_cum_total: number;
    citation_phase: string;
}

export interface PortfolioCitationTimeSeriesResponse {
    owner_id: number;
    series: PortfolioTimeSeriesPoint[];
}
