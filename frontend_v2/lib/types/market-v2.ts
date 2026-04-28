import type { SupportLevel } from "./common";

export interface MarketIdentity {
  id: string;
  label: string;
  page_kind: string;
  selected_year?: number | null;
}

export interface MarketScope {
  scope_type: string;
  covered_field_count: number;
  coverage_year_range: {
    start_year: number;
    end_year: number;
  };
  snapshot_date?: string | null;
  latest_market_year: number;
  latest_comparable_market_year: number;
  latest_cpc_year: number;
}

export interface MarketOverview {
  segment_count: number;
  rising_segment_count: number;
  cooling_segment_count: number;
  total_family_count: number;
  avg_segment_family_count: number;
  market_overview_history?: MarketOverviewHistoryRow[];
  latest_market_summary?: MarketOverviewHistoryRow | null;
}

export interface MarketOverviewHistoryRow {
  as_of_year: number;
  current_snapshot_date?: string | null;
  market_family_count_asof: number;
  pending_family_count_asof: number;
  fully_active_family_count_asof: number;
  partially_lapsed_family_count_asof: number;
  dead_family_count_asof: number;
  owner_count_asof: number;
  avg_blocking_power_score_asof: number;
  avg_enforceability_score_asof: number;
  avg_forward_citations_clean_asof: number;
  total_forward_citations_clean_asof: number;
  top_owner_share_asof: number;
  crowding_label: string;
}

export interface MarketStateOption {
  value: string;
  label: string;
  count: number;
}

export interface MarketSegmentOption {
  value: string;
  label: string;
  market_state: string;
  total_family_count: number;
}

export interface MarketSparklinePoint {
  year: number;
  family_count: number;
  prior_family_count: number;
  market_state: string;
  market_state_ui_safe: boolean;
  is_recent_priority_year_incomplete: boolean;
  latest_comparable_year: number;
  growth_rate: number;
  market_median_family_count?: number;
  delta_from_market_median?: number;
  year_over_year_delta_pct?: number;
}

export interface MarketSegmentRow {
  segment_id: string;
  wipo_industry_code: string;
  market_state: string;
  total_family_count: number;
  latest_year: number;
  latest_comparable_year: number;
  latest_year_incomplete: boolean;
  latest_market_year: number;
  snapshot_date?: string | null;
  segment_heat_state_asof: string;
  segment_market_state_ui_safe_asof: boolean;
  segment_priority_year_incomplete_asof: boolean;
  segment_latest_comparable_year: number;
  segment_family_count_stock_asof: number;
  segment_priority_year_family_count_asof: number;
  segment_prior_priority_year_family_count_asof: number;
  segment_growth_index_asof: number;
  segment_owner_count_hist_proxy_asof: number;
  segment_blocking_density_asof: number;
  segment_field_balance_asof: number;
  segment_active_family_count_asof: number;
  segment_active_weight_asof: number;
  segment_active_jurisdiction_share_asof: number;
  segment_enforceability_density_asof: number;
  segment_top_owner_share_hist_proxy: number;
  historical_compare_safe: boolean;
  historical_owner_truth_supported: boolean;
  current_owner_bridge_replayed_to_history: boolean;
  historical_oecd_supported: boolean;
  momentum_delta_pct: number;
  crowding_label: string;
  concentration_role: string;
  whitespace_candidate: boolean;
  sparkline: MarketSparklinePoint[];
}

export interface MarketTopOwnerRow {
  as_of_year: number;
  leaderboard_rank: number;
  owner_name: string;
  owner_id?: string | null;
  in_segment_family_count_hist_proxy: number;
  in_segment_family_share_hist_proxy: number;
  avg_blocking_score_asof: number;
  total_blocking_score_asof: number;
  field_presence_weight_asof: number;
  family_composite_status_asof: string;
  concentration_role?: string;
}

export interface MarketTopFamilyRow {
  as_of_year: number;
  leaderboard_rank: number;
  docdb_family_id: number;
  owner_name: string;
  owner_id?: string | null;
  avg_blocking_score_asof: number;
  total_blocking_score_asof: number;
  field_presence_weight_asof: number;
  family_composite_status_asof: string;
}

export interface MarketJurisdictionRow {
  as_of_year: number;
  wipo_field: string;
  jurisdiction_code: string;
  citation_event_count: number;
  distinct_citing_assignee_count: number;
  citation_count: number;
  citation_lethality_sum: number;
  citation_pressure_index: number;
}

export interface MarketFieldJurisdictionRow {
  as_of_year: number;
  wipo_field: string;
  jurisdiction_code: string;
  jurisdiction_family_count_asof: number;
  jurisdiction_active_family_count_asof: number;
  jurisdiction_family_share_within_segment_asof: number;
  jurisdiction_active_family_share_within_segment_asof: number;
  cpc_group_count: number;
}

export interface MarketCitationTrendRow {
  as_of_year: number;
  wipo_field: string;
  citation_event_count: number;
  citation_count: number;
  citation_lethality_sum: number;
  distinct_citing_assignee_count: number;
  distinct_citing_jurisdiction_count: number;
  citation_pressure_index: number;
  market_citation_state: string;
  market_state_reference: string;
}

export interface MarketAttackerRow {
  as_of_year: number;
  wipo_field: string;
  citing_assignee: string;
  citation_event_count: number;
  distinct_citing_jurisdiction_count: number;
  citation_count: number;
  citation_lethality_sum: number;
  attacker_pressure_index: number;
}

export interface MarketCpcTrendRow {
  as_of_year: number;
  current_snapshot_date?: string | null;
  wipo_field: string;
  cpc_main_group: string;
  cpc_main_group_label: string;
  cpc_family_count_asof: number;
  cpc_active_family_count_asof: number;
  cpc_family_share_within_segment_asof: number;
  cpc_active_family_share_within_segment_asof: number;
  cpc_blocking_density_asof: number;
  cpc_enforceability_density_asof: number;
  cpc_pre_asof_forward_citations_clean_avg_asof: number;
  cpc_avg_rcf_score_asof: number;
  cpc_prior_family_count_asof: number;
  cpc_growth_index_asof: number;
  cpc_heat_state_asof: string;
  cpc_rank_within_segment_year: number;
  classification_jurisdiction_support_level?: string;
}

export interface MarketCpcJurisdictionRow {
  as_of_year: number;
  current_snapshot_date?: string | null;
  wipo_field: string;
  cpc_main_group: string;
  jurisdiction_code: string;
  family_count_asof: number;
  active_family_count_asof: number;
  family_share_within_slice_asof: number;
  citation_pressure_index_asof: number;
  growth_index_asof: number;
  blocking_density_asof: number;
  enforceability_density_asof: number;
  slice_rank_within_year: number;
}

export interface MarketCpcOwnerRow {
  as_of_year: number;
  wipo_field: string;
  cpc_main_group: string;
  leaderboard_rank: number;
  owner_name: string;
  owner_id?: string | null;
  owner_family_count_in_cpc_asof: number;
  owner_active_family_count_in_cpc_asof: number;
  owner_family_share_within_cpc_asof: number;
  owner_active_family_share_within_cpc_asof: number;
  avg_blocking_score_asof: number;
  avg_enforceability_score_asof: number;
}

export interface MarketCpcCitingOwnerRow {
  as_of_year: number;
  wipo_field: string;
  cpc_main_group: string;
  leaderboard_rank: number;
  citing_owner_name: string;
  citing_owner_id?: string | null;
  latest_citation_year: number;
  citation_event_count: number;
  clean_citation_count: number;
  citation_lethality_sum: number;
  distinct_citing_jurisdiction_count: number;
  cited_family_count: number;
  citation_event_share_within_cpc_asof: number;
}

export interface MarketForecastOverlay {
  horizon: number;
  as_of_year: number;
  predicted_direction_band: string;
  trend_strength_band: string;
  support_level: SupportLevel;
  predicted_direction_probability: number;
  predicted_growth_rate_reference: number;
  jurisdiction_count: number;
}

export interface MarketStateRationale {
  headline: string;
  detail: string;
  evidence: string[];
}

export interface MarketPortfolioLink {
  owner_id: string;
  owner_name: string;
}

export interface MarketSelectedSegment {
  segment_id: string;
  wipo_industry_code: string;
  market_state: string;
  summary: Omit<MarketSegmentRow, "sparkline">;
  timeseries: MarketSparklinePoint[];
  top_owners: MarketTopOwnerRow[];
  top_families: MarketTopFamilyRow[];
  top_jurisdictions: MarketJurisdictionRow[];
  citation_trend: MarketCitationTrendRow[];
  top_attackers: MarketAttackerRow[];
  top_cpcs: MarketCpcTrendRow[];
  field_jurisdictions: MarketFieldJurisdictionRow[];
  cpc_jurisdictions: MarketCpcJurisdictionRow[];
  forecast?: MarketForecastOverlay[];
  state_rationale?: MarketStateRationale;
  linked_portfolios?: MarketPortfolioLink[];
}

export interface MarketMethodologyItem {
  code: string;
  title: string;
  detail: string;
}

export interface MarketLeadingJurisdictionRow {
  as_of_year: number;
  wipo_field: string;
  field_rank_within_year: number;
  jurisdiction_code: string;
  jurisdiction_family_count_asof: number;
  jurisdiction_active_family_count_asof: number;
  jurisdiction_family_share_within_field_asof: number;
}

export interface MarketApplicationGrantRow {
  as_of_year: number;
  wipo_field: string;
  jurisdiction_code: string;
  application_count: number;
  grant_count: number;
  total_event_count: number;
}

export interface MarketGrantMixRow {
  as_of_year: number;
  wipo_field: string;
  jurisdiction_code: string;
  application_count: number;
  grant_count: number;
  total_event_count: number;
  grant_share_of_events: number;
}

export interface MarketUnitaryPatentRow {
  row_kind: "summary" | "year" | "jurisdiction";
  wipo_field: string;
  as_of_year: number;
  jurisdiction_code?: string | null;
  register_confirmed_family_count: number;
  heuristic_family_count: number;
  unrolled_member_state_count: number;
  jurisdiction_family_count: number;
  ep_grant_event_count: number;
  ep_grant_event_count_on_heuristic_up: number;
}

export interface MarketMeta {
  page: string;
  support_level: SupportLevel;
  release_id?: string | null;
  reduced_context_mode?: boolean;
  methodology_path?: string | null;
  state_label_methodology_path?: string | null;
  forecast_overlay_available?: boolean;
  caveats: MarketMethodologyItem[];
}

export interface MarketSectionResponse<Row> {
  segment_id?: string | null;
  section_key?: string | null;
  metric_basis?: string | null;
  scope_basis?: string | null;
  sum_safe?: boolean | null;
  overlap_policy?: string | null;
  rows: Row[];
  meta: MarketMeta;
}

export interface MarketWorkspaceResponse {
  identity: MarketIdentity;
  scope: MarketScope;
  overview: MarketOverview;
  filters: {
    market_state: string;
    state_options: MarketStateOption[];
    segment_options: MarketSegmentOption[];
    selected_segment?: string | null;
  };
  segments: MarketSegmentRow[];
  selected_segment: MarketSelectedSegment | null;
  methodology: MarketMethodologyItem[];
  meta: MarketMeta;
}
