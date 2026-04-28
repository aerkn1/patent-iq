/**
 * Citation Forecast API Types
 */

export type Interval80 = {
    low: number;
    high: number;
};

export type DifficultyBucket = "LOW" | "MID" | "HIGH";

// ── Patent Forecast ──────────────────────────────────────────────────────

export type PatentForecastPrediction = {
    expected_citations: number;
    interval_80: Interval80;
    difficulty_bucket: DifficultyBucket;
};

export type ForecastMeta = {
    model_version: string;
    calibration: string;
    as_of_definition: string;
    aggregation?: string;
};

export type PatentForecastResponse = {
    appln_id: number;
    horizon: string;
    filing_date: string;
    as_of_date: string;
    prediction: PatentForecastPrediction;
    features_used: Record<string, number | boolean>;
    meta: ForecastMeta;
};

// ── Portfolio Forecast ───────────────────────────────────────────────────

export type PortfolioForecastPrediction = {
    expected_citations_total: number;
    interval_80_total: Interval80;
    n_patents_effective: number;
    expected_per_effective_patent: number;
};

export type DifficultyMix = {
    LOW: number;
    MID: number;
    HIGH: number;
};

export type TopContributor = {
    appln_id: number;
    owner_share: number;
    expected: number;
    interval_80: Interval80;
    contribution: number;
    difficulty_bucket: DifficultyBucket;
};

export type SegmentItem = {
    key: string;
    expected: number;
    interval_80: Interval80;
    share: number;
};

export type SegmentsMeta = {
    top_k: number;
    cpc_top_n_per_patent: number;
    allocation: string;
    other_bucket_label: string;
};

export type PortfolioForecastSegments = {
    meta: SegmentsMeta;
    by_cpc_subclass: SegmentItem[];
    by_jurisdiction_coverage_bucket: SegmentItem[];
    by_major_office_grant_bucket: SegmentItem[];
    by_as_of_year_bucket: SegmentItem[];
};

export type PortfolioForecastResponse = {
    owner_id: number;
    horizon: string;
    as_of_date: string;
    portfolio_prediction: PortfolioForecastPrediction;
    difficulty_mix: DifficultyMix;
    top_contributors: TopContributor[];
    segments?: PortfolioForecastSegments | null;
    meta: ForecastMeta;
};

export type CitationForecastTimeSeriesPoint = {
    year: number;
    cum_cites: number;
    low?: number;
    high?: number;
};

export type CitationForecastTimeSeriesResponse = {
    appln_id?: number;
    owner_id?: number;
    filing_year: number;
    horizon: string;
    last_observed_year: number;
    historical: CitationForecastTimeSeriesPoint[];
    forecast: CitationForecastTimeSeriesPoint[];
    prediction_summary: {
        expected_additional: number;
        interval_80: Interval80;
        difficulty_bucket: DifficultyBucket | string;
    };
};
