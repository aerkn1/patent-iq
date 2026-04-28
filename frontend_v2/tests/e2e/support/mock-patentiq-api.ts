import type { Page, Route } from "@playwright/test";

export const MOCK_PORTFOLIO_OWNER_ID = "ACME_HOLDINGS";
export const MOCK_FAMILY_ID = "57400072";
export const MOCK_PUBLICATION_ID = "EP2606406A1";

const marketSegments = [
  {
    segment_id: "Computer technology",
    wipo_industry_code: "Computer technology",
    market_state: "cooling",
    total_family_count: 64000,
    latest_year: 2025,
    latest_comparable_year: 2023,
    latest_year_incomplete: true,
    latest_market_year: 2023,
    snapshot_date: "2026-03-15",
    segment_heat_state_asof: "provisional",
    segment_market_state_ui_safe_asof: false,
    segment_priority_year_incomplete_asof: true,
    segment_latest_comparable_year: 2023,
    segment_family_count_stock_asof: 32000,
    segment_priority_year_family_count_asof: 18000,
    segment_prior_priority_year_family_count_asof: 22000,
    segment_growth_index_asof: -0.18,
    segment_owner_count_hist_proxy_asof: 220000,
    segment_blocking_density_asof: 31.5,
    segment_field_balance_asof: 0.82,
    segment_active_family_count_asof: 27000,
    segment_active_weight_asof: 0.81,
    segment_active_jurisdiction_share_asof: 0.73,
    segment_enforceability_density_asof: 0.61,
    segment_top_owner_share_hist_proxy: 0.031,
    historical_compare_safe: true,
    historical_owner_truth_supported: false,
    current_owner_bridge_replayed_to_history: true,
    historical_oecd_supported: false,
    momentum_delta_pct: -0.182,
    crowding_label: "crowded",
    concentration_role: "fragmented",
    whitespace_candidate: false,
    sparkline: [
      { year: 2021, family_count: 26000, prior_family_count: 24000, market_state: "stable", growth_rate: 0.0833 },
      { year: 2022, family_count: 24000, prior_family_count: 26000, market_state: "cooling", growth_rate: -0.0769 },
      { year: 2023, family_count: 22000, prior_family_count: 24000, market_state: "cooling", growth_rate: -0.0833, market_median_family_count: 14800, year_over_year_delta_pct: -0.0833 },
      { year: 2024, family_count: 20500, prior_family_count: 22000, market_state: "cooling", growth_rate: -0.0682, market_median_family_count: 15000, year_over_year_delta_pct: -0.0682 },
      { year: 2025, family_count: 18000, prior_family_count: 20500, market_state: "cooling", growth_rate: -0.122, market_median_family_count: 15500, year_over_year_delta_pct: -0.122 },
    ],
  },
  {
    segment_id: "Digital communication",
    wipo_industry_code: "Digital communication",
    market_state: "rising",
    total_family_count: 52000,
    latest_year: 2025,
    latest_comparable_year: 2023,
    latest_year_incomplete: true,
    latest_market_year: 2023,
    snapshot_date: "2026-03-15",
    segment_heat_state_asof: "provisional",
    segment_market_state_ui_safe_asof: false,
    segment_priority_year_incomplete_asof: true,
    segment_latest_comparable_year: 2023,
    segment_family_count_stock_asof: 36000,
    segment_priority_year_family_count_asof: 21000,
    segment_prior_priority_year_family_count_asof: 17000,
    segment_growth_index_asof: 0.24,
    segment_owner_count_hist_proxy_asof: 128000,
    segment_blocking_density_asof: 44.5,
    segment_field_balance_asof: 0.76,
    segment_active_family_count_asof: 31000,
    segment_active_weight_asof: 0.88,
    segment_active_jurisdiction_share_asof: 0.79,
    segment_enforceability_density_asof: 0.69,
    segment_top_owner_share_hist_proxy: 0.047,
    historical_compare_safe: true,
    historical_owner_truth_supported: false,
    current_owner_bridge_replayed_to_history: true,
    historical_oecd_supported: false,
    momentum_delta_pct: 0.235,
    crowding_label: "concentrated",
    concentration_role: "contender",
    whitespace_candidate: false,
    sparkline: [
      { year: 2021, family_count: 11000, prior_family_count: 9800, market_state: "stable", growth_rate: 0.1224 },
      { year: 2022, family_count: 13500, prior_family_count: 11000, market_state: "rising", growth_rate: 0.2273 },
      { year: 2023, family_count: 16000, prior_family_count: 13500, market_state: "rising", growth_rate: 0.1852, market_median_family_count: 14800, year_over_year_delta_pct: 0.1852 },
      { year: 2024, family_count: 19000, prior_family_count: 16000, market_state: "rising", growth_rate: 0.1875, market_median_family_count: 15000, year_over_year_delta_pct: 0.1875 },
      { year: 2025, family_count: 21000, prior_family_count: 19000, market_state: "rising", growth_rate: 0.1053, market_median_family_count: 15500, year_over_year_delta_pct: 0.1053 },
    ],
  },
  {
    segment_id: "Semiconductors",
    wipo_industry_code: "Semiconductors",
    market_state: "stable",
    total_family_count: 40000,
    latest_year: 2025,
    latest_comparable_year: 2023,
    latest_year_incomplete: true,
    latest_market_year: 2023,
    snapshot_date: "2026-03-15",
    segment_heat_state_asof: "provisional",
    segment_market_state_ui_safe_asof: false,
    segment_priority_year_incomplete_asof: true,
    segment_latest_comparable_year: 2023,
    segment_family_count_stock_asof: 28000,
    segment_priority_year_family_count_asof: 15500,
    segment_prior_priority_year_family_count_asof: 15000,
    segment_growth_index_asof: 0.033,
    segment_owner_count_hist_proxy_asof: 86000,
    segment_blocking_density_asof: 37.2,
    segment_field_balance_asof: 0.81,
    segment_active_family_count_asof: 24000,
    segment_active_weight_asof: 0.84,
    segment_active_jurisdiction_share_asof: 0.77,
    segment_enforceability_density_asof: 0.74,
    segment_top_owner_share_hist_proxy: 0.028,
    historical_compare_safe: true,
    historical_owner_truth_supported: false,
    current_owner_bridge_replayed_to_history: true,
    historical_oecd_supported: false,
    momentum_delta_pct: 0.033,
    crowding_label: "balanced",
    concentration_role: "present",
    whitespace_candidate: true,
    sparkline: [
      { year: 2021, family_count: 14000, prior_family_count: 13800, market_state: "stable", growth_rate: 0.0145 },
      { year: 2022, family_count: 14500, prior_family_count: 14000, market_state: "stable", growth_rate: 0.0357 },
      { year: 2023, family_count: 14800, prior_family_count: 14500, market_state: "stable", growth_rate: 0.0207, market_median_family_count: 14800, year_over_year_delta_pct: 0.0207 },
      { year: 2024, family_count: 15000, prior_family_count: 14800, market_state: "stable", growth_rate: 0.0135, market_median_family_count: 15000, year_over_year_delta_pct: 0.0135 },
      { year: 2025, family_count: 15500, prior_family_count: 15000, market_state: "stable", growth_rate: 0.0333, market_median_family_count: 15500, year_over_year_delta_pct: 0.0333 },
    ],
  },
];

const marketSelectedDetails = {
  "Computer technology": {
    top_owners: [
      {
        as_of_year: 2025,
        leaderboard_rank: 1,
        owner_name: "Acme Holdings",
        in_segment_family_count_hist_proxy: 420,
        in_segment_family_share_hist_proxy: 0.031,
        avg_blocking_score_asof: 88.4,
        total_blocking_score_asof: 37128,
        field_presence_weight_asof: 0.92,
        family_composite_status_asof: "fully_active",
      },
      {
        as_of_year: 2025,
        leaderboard_rank: 2,
        owner_name: "Northwind Systems",
        in_segment_family_count_hist_proxy: 310,
        in_segment_family_share_hist_proxy: 0.024,
        avg_blocking_score_asof: 71.2,
        total_blocking_score_asof: 22072,
        field_presence_weight_asof: 0.81,
        family_composite_status_asof: "mixed_active",
      },
    ],
    top_jurisdictions: [
      {
        as_of_year: 2025,
        wipo_field: "Computer technology",
        jurisdiction_code: "US",
        citation_event_count: 128,
        distinct_citing_assignee_count: 44,
        citation_count: 111.3,
        citation_lethality_sum: 93.2,
        citation_pressure_index: 82.1,
      },
      {
        as_of_year: 2025,
        wipo_field: "Computer technology",
        jurisdiction_code: "CN",
        citation_event_count: 102,
        distinct_citing_assignee_count: 36,
        citation_count: 96.4,
        citation_lethality_sum: 81.5,
        citation_pressure_index: 74.3,
      },
    ],
    citation_trend: [
      {
        as_of_year: 2021,
        wipo_field: "Computer technology",
        citation_event_count: 92,
        citation_count: 80.1,
        citation_lethality_sum: 62.2,
        distinct_citing_assignee_count: 26,
        distinct_citing_jurisdiction_count: 6,
        citation_pressure_index: 61.2,
        market_citation_state: "stable",
        market_state_reference: "stable",
      },
      {
        as_of_year: 2023,
        wipo_field: "Computer technology",
        citation_event_count: 108,
        citation_count: 95.5,
        citation_lethality_sum: 75.4,
        distinct_citing_assignee_count: 34,
        distinct_citing_jurisdiction_count: 8,
        citation_pressure_index: 70.5,
        market_citation_state: "heating",
        market_state_reference: "cooling",
      },
      {
        as_of_year: 2025,
        wipo_field: "Computer technology",
        citation_event_count: 128,
        citation_count: 111.3,
        citation_lethality_sum: 93.2,
        distinct_citing_assignee_count: 44,
        distinct_citing_jurisdiction_count: 9,
        citation_pressure_index: 82.1,
        market_citation_state: "heating",
        market_state_reference: "cooling",
      },
    ],
    top_attackers: [
      {
        as_of_year: 2025,
        wipo_field: "Computer technology",
        citing_assignee: "Qualcomm",
        citation_event_count: 21,
        distinct_citing_jurisdiction_count: 5,
        citation_count: 18.2,
        citation_lethality_sum: 14.8,
        attacker_pressure_index: 91.4,
      },
      {
        as_of_year: 2025,
        wipo_field: "Computer technology",
        citing_assignee: "Samsung Electronics",
        citation_event_count: 18,
        distinct_citing_jurisdiction_count: 4,
        citation_count: 15.7,
        citation_lethality_sum: 12.9,
        attacker_pressure_index: 84.3,
      },
    ],
    top_cpcs: [
      {
        as_of_year: 2026,
        current_snapshot_date: "2026-03-15",
        wipo_field: "Computer technology",
        cpc_main_group: "G06F17/00",
        cpc_main_group_label: "G06F17/00",
        cpc_family_count_asof: 1200,
        cpc_active_family_count_asof: 880,
        cpc_family_share_within_segment_asof: 0.082,
        cpc_active_family_share_within_segment_asof: 0.091,
        cpc_blocking_density_asof: 57,
        cpc_enforceability_density_asof: 0.71,
        cpc_pre_asof_forward_citations_clean_avg_asof: 0.52,
        cpc_avg_rcf_score_asof: 1.83,
        cpc_prior_family_count_asof: 950,
        cpc_growth_index_asof: 0.263,
        cpc_heat_state_asof: "heating",
        cpc_rank_within_segment_year: 1,
      },
      {
        as_of_year: 2026,
        current_snapshot_date: "2026-03-15",
        wipo_field: "Computer technology",
        cpc_main_group: "G06N20/00",
        cpc_main_group_label: "G06N20/00",
        cpc_family_count_asof: 920,
        cpc_active_family_count_asof: 690,
        cpc_family_share_within_segment_asof: 0.061,
        cpc_active_family_share_within_segment_asof: 0.072,
        cpc_blocking_density_asof: 49.2,
        cpc_enforceability_density_asof: 0.66,
        cpc_pre_asof_forward_citations_clean_avg_asof: 0.41,
        cpc_avg_rcf_score_asof: 1.52,
        cpc_prior_family_count_asof: 870,
        cpc_growth_index_asof: 0.057,
        cpc_heat_state_asof: "stable",
        cpc_rank_within_segment_year: 2,
      },
    ],
  },
  "Digital communication": {
    top_owners: [
      {
        as_of_year: 2025,
        leaderboard_rank: 1,
        owner_name: "Acme Holdings",
        in_segment_family_count_hist_proxy: 510,
        in_segment_family_share_hist_proxy: 0.047,
        avg_blocking_score_asof: 91.3,
        total_blocking_score_asof: 46563,
        field_presence_weight_asof: 0.94,
        family_composite_status_asof: "fully_active",
      },
      {
        as_of_year: 2025,
        leaderboard_rank: 2,
        owner_name: "Contoso Networks",
        in_segment_family_count_hist_proxy: 404,
        in_segment_family_share_hist_proxy: 0.039,
        avg_blocking_score_asof: 84.1,
        total_blocking_score_asof: 33976,
        field_presence_weight_asof: 0.87,
        family_composite_status_asof: "growth_active",
      },
    ],
    top_jurisdictions: [
      {
        as_of_year: 2025,
        wipo_field: "Digital communication",
        jurisdiction_code: "US",
        citation_event_count: 141,
        distinct_citing_assignee_count: 51,
        citation_count: 122.4,
        citation_lethality_sum: 97.3,
        citation_pressure_index: 89.4,
      },
      {
        as_of_year: 2025,
        wipo_field: "Digital communication",
        jurisdiction_code: "EP",
        citation_event_count: 110,
        distinct_citing_assignee_count: 38,
        citation_count: 98.8,
        citation_lethality_sum: 79.1,
        citation_pressure_index: 77.1,
      },
    ],
    citation_trend: [
      {
        as_of_year: 2021,
        wipo_field: "Digital communication",
        citation_event_count: 64,
        citation_count: 58.2,
        citation_lethality_sum: 40.5,
        distinct_citing_assignee_count: 19,
        distinct_citing_jurisdiction_count: 4,
        citation_pressure_index: 42.4,
        market_citation_state: "stable",
        market_state_reference: "rising",
      },
      {
        as_of_year: 2023,
        wipo_field: "Digital communication",
        citation_event_count: 99,
        citation_count: 84.7,
        citation_lethality_sum: 63.1,
        distinct_citing_assignee_count: 31,
        distinct_citing_jurisdiction_count: 7,
        citation_pressure_index: 68.2,
        market_citation_state: "heating",
        market_state_reference: "rising",
      },
      {
        as_of_year: 2025,
        wipo_field: "Digital communication",
        citation_event_count: 141,
        citation_count: 122.4,
        citation_lethality_sum: 97.3,
        distinct_citing_assignee_count: 51,
        distinct_citing_jurisdiction_count: 10,
        citation_pressure_index: 89.4,
        market_citation_state: "heating",
        market_state_reference: "rising",
      },
    ],
    top_attackers: [
      {
        as_of_year: 2025,
        wipo_field: "Digital communication",
        citing_assignee: "Ericsson",
        citation_event_count: 24,
        distinct_citing_jurisdiction_count: 6,
        citation_count: 19.8,
        citation_lethality_sum: 16.4,
        attacker_pressure_index: 88.7,
      },
      {
        as_of_year: 2025,
        wipo_field: "Digital communication",
        citing_assignee: "Nokia",
        citation_event_count: 20,
        distinct_citing_jurisdiction_count: 5,
        citation_count: 17.1,
        citation_lethality_sum: 13.2,
        attacker_pressure_index: 79.5,
      },
    ],
    top_cpcs: [
      {
        as_of_year: 2026,
        current_snapshot_date: "2026-03-15",
        wipo_field: "Digital communication",
        cpc_main_group: "H04L29/00",
        cpc_main_group_label: "H04L29/00",
        cpc_family_count_asof: 1480,
        cpc_active_family_count_asof: 1090,
        cpc_family_share_within_segment_asof: 0.094,
        cpc_active_family_share_within_segment_asof: 0.104,
        cpc_blocking_density_asof: 63.1,
        cpc_enforceability_density_asof: 0.75,
        cpc_pre_asof_forward_citations_clean_avg_asof: 0.68,
        cpc_avg_rcf_score_asof: 2.14,
        cpc_prior_family_count_asof: 1150,
        cpc_growth_index_asof: 0.287,
        cpc_heat_state_asof: "heating",
        cpc_rank_within_segment_year: 1,
      },
      {
        as_of_year: 2026,
        current_snapshot_date: "2026-03-15",
        wipo_field: "Digital communication",
        cpc_main_group: "H04W72/00",
        cpc_main_group_label: "H04W72/00",
        cpc_family_count_asof: 960,
        cpc_active_family_count_asof: 720,
        cpc_family_share_within_segment_asof: 0.061,
        cpc_active_family_share_within_segment_asof: 0.069,
        cpc_blocking_density_asof: 54.8,
        cpc_enforceability_density_asof: 0.71,
        cpc_pre_asof_forward_citations_clean_avg_asof: 0.57,
        cpc_avg_rcf_score_asof: 1.91,
        cpc_prior_family_count_asof: 890,
        cpc_growth_index_asof: 0.079,
        cpc_heat_state_asof: "stable",
        cpc_rank_within_segment_year: 2,
      },
    ],
  },
  Semiconductors: {
    top_owners: [
      {
        as_of_year: 2025,
        leaderboard_rank: 1,
        owner_name: "Acme Holdings",
        in_segment_family_count_hist_proxy: 285,
        in_segment_family_share_hist_proxy: 0.028,
        avg_blocking_score_asof: 79.2,
        total_blocking_score_asof: 22572,
        field_presence_weight_asof: 0.89,
        family_composite_status_asof: "mixed_active",
      },
    ],
    top_jurisdictions: [
      {
        as_of_year: 2025,
        wipo_field: "Semiconductors",
        jurisdiction_code: "US",
        citation_event_count: 90,
        distinct_citing_assignee_count: 30,
        citation_count: 76.1,
        citation_lethality_sum: 60.4,
        citation_pressure_index: 69.2,
      },
    ],
    citation_trend: [
      {
        as_of_year: 2023,
        wipo_field: "Semiconductors",
        citation_event_count: 71,
        citation_count: 62.2,
        citation_lethality_sum: 49.3,
        distinct_citing_assignee_count: 22,
        distinct_citing_jurisdiction_count: 5,
        citation_pressure_index: 58.1,
        market_citation_state: "stable",
        market_state_reference: "stable",
      },
      {
        as_of_year: 2025,
        wipo_field: "Semiconductors",
        citation_event_count: 90,
        citation_count: 76.1,
        citation_lethality_sum: 60.4,
        distinct_citing_assignee_count: 30,
        distinct_citing_jurisdiction_count: 7,
        citation_pressure_index: 69.2,
        market_citation_state: "stable",
        market_state_reference: "stable",
      },
    ],
    top_attackers: [
      {
        as_of_year: 2025,
        wipo_field: "Semiconductors",
        citing_assignee: "TSMC",
        citation_event_count: 16,
        distinct_citing_jurisdiction_count: 3,
        citation_count: 13.7,
        citation_lethality_sum: 10.2,
        attacker_pressure_index: 74.8,
      },
    ],
    top_cpcs: [
      {
        as_of_year: 2026,
        current_snapshot_date: "2026-03-15",
        wipo_field: "Semiconductors",
        cpc_main_group: "H01L21/00",
        cpc_main_group_label: "H01L21/00",
        cpc_family_count_asof: 1040,
        cpc_active_family_count_asof: 790,
        cpc_family_share_within_segment_asof: 0.071,
        cpc_active_family_share_within_segment_asof: 0.078,
        cpc_blocking_density_asof: 58.2,
        cpc_enforceability_density_asof: 0.82,
        cpc_pre_asof_forward_citations_clean_avg_asof: 0.48,
        cpc_avg_rcf_score_asof: 2.02,
        cpc_prior_family_count_asof: 980,
        cpc_growth_index_asof: 0.061,
        cpc_heat_state_asof: "stable",
        cpc_rank_within_segment_year: 1,
      },
    ],
  },
} as const;

function buildMarketWorkspacePayload(searchParams: URLSearchParams) {
  const marketState = searchParams.get("market_state") ?? "all";
  const filteredSegments =
    marketState === "all" ? marketSegments : marketSegments.filter((segment) => segment.market_state === marketState);
  const selectedSegmentCode =
    searchParams.get("segment_id") && filteredSegments.some((segment) => segment.wipo_industry_code === searchParams.get("segment_id"))
      ? (searchParams.get("segment_id") as keyof typeof marketSelectedDetails)
      : (filteredSegments[0]?.wipo_industry_code as keyof typeof marketSelectedDetails | undefined);
  const selectedSegment = selectedSegmentCode
    ? {
        segment_id: selectedSegmentCode,
        wipo_industry_code: selectedSegmentCode,
        market_state: filteredSegments.find((segment) => segment.wipo_industry_code === selectedSegmentCode)?.market_state ?? "stable",
        summary: {
          ...filteredSegments.find((segment) => segment.wipo_industry_code === selectedSegmentCode),
          sparkline: undefined,
        },
        timeseries:
          filteredSegments.find((segment) => segment.wipo_industry_code === selectedSegmentCode)?.sparkline ?? [],
        ...marketSelectedDetails[selectedSegmentCode],
      }
    : null;

  if (selectedSegment && "sparkline" in selectedSegment.summary) {
    delete (selectedSegment.summary as Record<string, unknown>).sparkline;
  }

  return {
    identity: {
      id: "market-intelligence",
      label: "Market Intelligence",
      page_kind: "market_intelligence",
      selected_year: 2023,
    },
    scope: {
      scope_type: "mega_cluster_bounded",
      covered_field_count: 3,
      coverage_year_range: {
        start_year: 2021,
        end_year: 2025,
      },
      snapshot_date: "2026-03-15",
      latest_market_year: 2025,
      latest_comparable_market_year: 2023,
      latest_cpc_year: 2026,
    },
    overview: {
      segment_count: 3,
      rising_segment_count: 1,
      cooling_segment_count: 1,
      total_family_count: 156000,
      avg_segment_family_count: 52000,
    },
    filters: {
      market_state: marketState,
      state_options: [
        { value: "all", label: "All segments", count: marketSegments.length },
        { value: "rising", label: "Rising", count: marketSegments.filter((segment) => segment.market_state === "rising").length },
        { value: "cooling", label: "Cooling", count: marketSegments.filter((segment) => segment.market_state === "cooling").length },
        { value: "stable", label: "Stable", count: marketSegments.filter((segment) => segment.market_state === "stable").length },
      ],
      segment_options: filteredSegments.map((segment) => ({
        value: segment.wipo_industry_code,
        label: segment.wipo_industry_code,
        market_state: segment.market_state,
        total_family_count: segment.total_family_count,
      })),
      selected_segment: selectedSegmentCode ?? null,
    },
    segments: filteredSegments,
    selected_segment: selectedSegment,
    methodology: [
      {
        code: "bounded_scope",
        title: "Bounded mega-cluster scope",
        detail: "All market surfaces are restricted to the approved PatentIQ mega-cluster family universe rather than whole-world patent totals.",
      },
      {
        code: "pit_current_state",
        title: "Current-state PIT serving",
        detail: "Density, ownership, and CPC panels use latest point-in-time slices. Historical trend lines remain separate from current-state overlays.",
      },
    ],
    meta: {
      page: "market_intelligence.workspace",
      support_level: "moderate",
      caveats: [
        {
          code: "state_vs_history",
          title: "Current state versus replay",
          detail: "Read the latest state labels separately from historical chronology.",
        },
      ],
    },
  };
}

const portfolioOverviewPayload = {
  identity: {
    id: MOCK_PORTFOLIO_OWNER_ID,
    label: "Acme Holdings",
    page_kind: "portfolio",
    selected_year: 2025,
  },
  family_count: 128,
  active_grant_family_count: 81,
  semantic_candidate_count: 97,
  count_scopes: {
    in_scope_family_count: 128,
    primary_owner_family_count: 104,
    active_grant_family_count: 81,
    semantic_candidate_family_count: 97,
    pending_family_count: 28,
    unclassified_family_count: 0,
  },
  status_mix: [
    { key: "pending_emerging", label: "Pending / filing", count: 28, share: 0.2188 },
    { key: "fully_active", label: "Fully active", count: 58, share: 0.4531 },
    { key: "under_fire", label: "Under fire", count: 18, share: 0.1406 },
    { key: "partially_lapsed", label: "Partially lapsed", count: 13, share: 0.1016 },
    { key: "dead", label: "Dead", count: 11, share: 0.0859 },
  ],
  summary_cards: [
    {
      key: "primary_owner_family_count",
      label: "Primary-owner families",
      value: "104",
      tone: "neutral",
      tooltip: "Distinct families where Acme is the current primary owner.",
      band_label: "Core scale",
      peer_bucket_label: "Upper quartile",
      peer_percentile: 82,
    },
    {
      key: "active_grant_family_share",
      label: "Active grant share",
      value: "78%",
      tone: "positive",
      delta: 14,
      delta_label: "vs cohort",
      tooltip: "Share of analytics-scope families currently in active grant status.",
    },
    {
      key: "forecast_ready_share",
      label: "Forecast-ready coverage",
      value: "92%",
      tone: "positive",
      caveat: "Forecast remains bounded to model-ready families only.",
    },
    {
      key: "citation_pressure_index",
      label: "Citation pressure index",
      value: "67",
      tone: "warning",
      delta: -4,
      delta_label: "vs last quarter",
    },
  ],
  top_family_preview: [
    {
      family_id: MOCK_FAMILY_ID,
      owner_weight: 0.88,
      blocking_score: 87,
      status: "Active grant",
      heritage: "Established",
      primary_field: "Digital communications",
      forecast_contributor: 0.24,
    },
    {
      family_id: "57400091",
      owner_weight: 0.72,
      blocking_score: 74,
      status: "Pending mix",
      heritage: "Growing",
      primary_field: "Signal routing",
      forecast_contributor: 0.17,
    },
  ],
  meta: {
    support_level: "strong",
    coverage: {
      status: "high",
      pct: 0.92,
      covered_count: 96,
      denominator_count: 104,
      caveat_text: "Forecast coverage is bounded to modeled primary-owner families.",
    },
    caveats: [
      {
        code: "FC01",
        title: "Forecast bounded",
        detail: "Forecast intervals apply only to families served by the current model stack.",
      },
    ],
  },
};

const portfolioFamiliesPayload = {
  owner_id: MOCK_PORTFOLIO_OWNER_ID,
  rows: portfolioOverviewPayload.top_family_preview,
  meta: {
    pagination: {
      limit: 10,
      offset: 0,
      returned_count: 2,
      total_count: 2,
    },
  },
};

const portfolioFieldsPayload = {
  owner_id: MOCK_PORTFOLIO_OWNER_ID,
  rows: [
    {
      field: "Digital communications",
      active_families: 41,
      active_share: 0.39,
      hotspot_direction: "heating",
      change_12m: 0.12,
      confidence: "strong",
    },
    {
      field: "Signal routing",
      active_families: 27,
      active_share: 0.26,
      hotspot_direction: "stable",
      change_12m: 0.03,
      confidence: "moderate",
    },
    {
      field: "Edge compute control",
      active_families: 18,
      active_share: 0.17,
      hotspot_direction: "cooling",
      change_12m: -0.04,
      confidence: "limited",
    },
  ],
};

const portfolioThreatsPayload = {
  owner_id: MOCK_PORTFOLIO_OWNER_ID,
  rows: [
    {
      citing_assignee: "Contoso Networks",
      wipo_field: "Digital communications",
      citation_lethality_sum: 48,
      collided_family_count: 12,
    },
    {
      citing_assignee: "Northwind Devices",
      wipo_field: "Signal routing",
      citation_lethality_sum: 36,
      collided_family_count: 9,
    },
  ],
  meta: {
    pagination: {
      limit: 10,
      offset: 0,
      returned_count: 2,
      total_count: 2,
    },
  },
};

const portfolioClassificationPayload = {
  owner_id: MOCK_PORTFOLIO_OWNER_ID,
  rows: [
    {
      segment: "H04L",
      classification_type: "CPC_MAIN_GROUP",
      wipo_field: "Digital communications",
      family_share: 0.42,
      trajectory: 0.08,
      top_change: "gain",
    },
    {
      segment: "H04W",
      classification_type: "CPC_MAIN_GROUP",
      wipo_field: "Signal routing",
      family_share: 0.26,
      trajectory: 0.02,
      top_change: "flat",
    },
  ],
  timeseries: [
    {
      field: "Digital communications",
      points: [
        { year: 2021, share: 0.34, portfolio: 26 },
        { year: 2022, share: 0.37, portfolio: 31 },
        { year: 2023, share: 0.39, portfolio: 36 },
        { year: 2024, share: 0.42, portfolio: 41 },
      ],
    },
  ],
  meta: {
    pagination: {
      limit: 10,
      offset: 0,
      returned_count: 2,
      total_count: 2,
    },
  },
};

const portfolioForecastByHorizon = {
  "3y": {
    owner_id: MOCK_PORTFOLIO_OWNER_ID,
    sections: [
      {
        horizon: "3y",
        total: 28,
        low: 22,
        high: 35,
        per_effective_family: 0.27,
        top_contributor_dependence_pct: 0.31,
        coverage_pct: 0.92,
        top_segments: [
          {
            field: "Digital communications",
            active_families: 41,
            active_share: 0.39,
            hotspot_direction: "heating",
            change_12m: 0.12,
            confidence: "strong",
          },
          {
            field: "Signal routing",
            active_families: 27,
            active_share: 0.26,
            hotspot_direction: "stable",
            change_12m: 0.03,
            confidence: "moderate",
          },
        ],
        risk12m: [
          { risk_band: "low", share: 0.52, family_count: 54 },
          { risk_band: "medium", share: 0.33, family_count: 34 },
          { risk_band: "high", share: 0.15, family_count: 16 },
        ],
      },
    ],
  },
  "5y": {
    owner_id: MOCK_PORTFOLIO_OWNER_ID,
    sections: [
      {
        horizon: "5y",
        total: 44,
        low: 36,
        high: 51,
        per_effective_family: 0.42,
        top_contributor_dependence_pct: 0.35,
        coverage_pct: 0.88,
        risk24m: [
          { risk_band: "low", share: 0.48, family_count: 50 },
          { risk_band: "medium", share: 0.34, family_count: 35 },
          { risk_band: "high", share: 0.18, family_count: 19 },
        ],
      },
    ],
  },
} as const;

const portfolioCitationSummaryPayload = {
  owner_id: MOCK_PORTFOLIO_OWNER_ID,
  rows: [
    {
      as_of_year: 2025,
      family_count: 104,
      forward_citations_clean_total: 312,
      forward_citations_weighted_total: 441.2,
      backward_citations_clean_total: 201,
      backward_npl_citation_total: 37,
      distinct_citing_family_count: 248,
      distinct_cited_family_count: 173,
      avg_science_grounding_score: 0.61,
      avg_generality_percentile: 0.58,
      avg_originality_percentile: 0.71,
      avg_unique_citing_family_count: 3.2,
      avg_citing_assignee_diversity: 2.4,
      avg_attacker_density_score: 0.44,
      avg_out_of_bounds_citation_share: 0.18,
    },
  ],
};

const portfolioCitationTimeseriesPayload = {
  owner_id: MOCK_PORTFOLIO_OWNER_ID,
  rows: [
    {
      as_of_year: 2021,
      family_count: 88,
      forward_citations_clean_total: 180,
      forward_citations_weighted_total: 254.6,
      avg_unique_citing_family_count: 2.1,
      avg_citing_assignee_diversity: 1.8,
      avg_attacker_density_score: 0.32,
    },
    {
      as_of_year: 2022,
      family_count: 93,
      forward_citations_clean_total: 214,
      forward_citations_weighted_total: 302.1,
      avg_unique_citing_family_count: 2.5,
      avg_citing_assignee_diversity: 2.0,
      avg_attacker_density_score: 0.36,
    },
    {
      as_of_year: 2023,
      family_count: 97,
      forward_citations_clean_total: 246,
      forward_citations_weighted_total: 351.8,
      avg_unique_citing_family_count: 2.8,
      avg_citing_assignee_diversity: 2.1,
      avg_attacker_density_score: 0.39,
    },
    {
      as_of_year: 2024,
      family_count: 101,
      forward_citations_clean_total: 281,
      forward_citations_weighted_total: 402.4,
      avg_unique_citing_family_count: 3.0,
      avg_citing_assignee_diversity: 2.3,
      avg_attacker_density_score: 0.42,
    },
    {
      as_of_year: 2025,
      family_count: 104,
      forward_citations_clean_total: 312,
      forward_citations_weighted_total: 441.2,
      avg_unique_citing_family_count: 3.2,
      avg_citing_assignee_diversity: 2.4,
      avg_attacker_density_score: 0.44,
    },
  ],
};

const portfolioCitationAttackersPayload = {
  owner_id: MOCK_PORTFOLIO_OWNER_ID,
  rows: [
    {
      citing_assignee: "Contoso Networks",
      wipo_field: "Digital communications",
      jurisdiction_code: "US",
      latest_citation_year: 2025,
      citation_event_count: 28,
      clean_citation_count: 19,
      citation_lethality_sum: 61.4,
    },
    {
      citing_assignee: "Northwind Devices",
      wipo_field: "Signal routing",
      jurisdiction_code: "EP",
      latest_citation_year: 2024,
      citation_event_count: 18,
      clean_citation_count: 12,
      citation_lethality_sum: 39.8,
    },
  ],
  meta: {
    pagination: {
      limit: 10,
      offset: 0,
      returned_count: 2,
      total_count: 2,
    },
  },
};

const portfolioCitationFieldsPayload = {
  owner_id: MOCK_PORTFOLIO_OWNER_ID,
  rows: [
    {
      wipo_field: "Digital communications",
      latest_citation_year: 2025,
      citation_event_count: 34,
      citing_assignee_count: 9,
      clean_citation_count: 22,
      citation_lethality_sum: 68.2,
    },
    {
      wipo_field: "Signal routing",
      latest_citation_year: 2024,
      citation_event_count: 21,
      citing_assignee_count: 7,
      clean_citation_count: 14,
      citation_lethality_sum: 44.6,
    },
  ],
  meta: {
    pagination: {
      limit: 10,
      offset: 0,
      returned_count: 2,
      total_count: 2,
    },
  },
};

const portfolioCitationJurisdictionsPayload = {
  owner_id: MOCK_PORTFOLIO_OWNER_ID,
  rows: [
    {
      jurisdiction_code: "US",
      latest_citation_year: 2025,
      citation_event_count: 31,
      citing_assignee_count: 8,
      wipo_field_count: 3,
      clean_citation_count: 20,
      citation_lethality_sum: 63.1,
    },
    {
      jurisdiction_code: "EP",
      latest_citation_year: 2024,
      citation_event_count: 17,
      citing_assignee_count: 5,
      wipo_field_count: 2,
      clean_citation_count: 11,
      citation_lethality_sum: 35.7,
    },
  ],
  meta: {
    pagination: {
      limit: 10,
      offset: 0,
      returned_count: 2,
      total_count: 2,
    },
  },
};

const portfolioFieldTimeseriesPayload = {
  owner_id: MOCK_PORTFOLIO_OWNER_ID,
  rows: [
    {
      wipo_field: "Digital communications",
      snapshot_date: "2021-12-31",
      active_share: 0.31,
      active_family_count: 24,
    },
    {
      wipo_field: "Digital communications",
      snapshot_date: "2022-12-31",
      active_share: 0.34,
      active_family_count: 29,
    },
    {
      wipo_field: "Digital communications",
      snapshot_date: "2023-12-31",
      active_share: 0.37,
      active_family_count: 34,
    },
    {
      wipo_field: "Digital communications",
      snapshot_date: "2024-12-31",
      active_share: 0.39,
      active_family_count: 41,
    },
    {
      wipo_field: "Signal routing",
      snapshot_date: "2021-12-31",
      active_share: 0.22,
      active_family_count: 17,
    },
    {
      wipo_field: "Signal routing",
      snapshot_date: "2022-12-31",
      active_share: 0.24,
      active_family_count: 20,
    },
    {
      wipo_field: "Signal routing",
      snapshot_date: "2023-12-31",
      active_share: 0.25,
      active_family_count: 23,
    },
    {
      wipo_field: "Signal routing",
      snapshot_date: "2024-12-31",
      active_share: 0.26,
      active_family_count: 27,
    },
  ],
};

const portfolioMarketContextPayload = {
  owner_id: MOCK_PORTFOLIO_OWNER_ID,
  rows: [
    {
      kind: "summary",
      horizon: "3y",
      heating_market_exposure_count: 44,
      cooling_market_exposure_count: 12,
      hotspot_coverage_pct: 0.67,
    },
    {
      kind: "segment",
      horizon: "3y",
      wipo_field: "Digital communications",
      predicted_direction_band: "heating",
      support_level: "strong",
      predicted_growth_rate_reference: 0.12,
      predicted_count_reference: 44,
      portfolio_active_family_count_in_field: 41,
    },
    {
      kind: "segment",
      horizon: "3y",
      wipo_field: "Signal routing",
      predicted_direction_band: "stable",
      support_level: "moderate",
      predicted_growth_rate_reference: 0.03,
      predicted_count_reference: 27,
      portfolio_active_family_count_in_field: 27,
    },
    {
      kind: "segment",
      horizon: "3y",
      wipo_field: "Edge compute control",
      predicted_direction_band: "cooling",
      support_level: "limited",
      predicted_growth_rate_reference: -0.04,
      predicted_count_reference: 18,
      portfolio_active_family_count_in_field: 18,
    },
  ],
};

const portfolioFilingTimeseriesPayload = {
  owner_id: MOCK_PORTFOLIO_OWNER_ID,
  rows: [
    {
      year: 2019,
      family_filing_count: 11,
      cumulative_family_count: 11,
      rolling_3y_family_filing_count: 11,
      prior_3y_family_filing_count: 0,
      rolling_3y_change_pct: 1,
      momentum_direction: "accelerating",
    },
    {
      year: 2020,
      family_filing_count: 14,
      cumulative_family_count: 25,
      rolling_3y_family_filing_count: 25,
      prior_3y_family_filing_count: 0,
      rolling_3y_change_pct: 1,
      momentum_direction: "accelerating",
    },
    {
      year: 2021,
      family_filing_count: 18,
      cumulative_family_count: 43,
      rolling_3y_family_filing_count: 43,
      prior_3y_family_filing_count: 0,
      rolling_3y_change_pct: 1,
      momentum_direction: "accelerating",
    },
    {
      year: 2022,
      family_filing_count: 16,
      cumulative_family_count: 59,
      rolling_3y_family_filing_count: 48,
      prior_3y_family_filing_count: 11,
      rolling_3y_change_pct: 3.3636,
      momentum_direction: "accelerating",
    },
    {
      year: 2023,
      family_filing_count: 12,
      cumulative_family_count: 71,
      rolling_3y_family_filing_count: 46,
      prior_3y_family_filing_count: 25,
      rolling_3y_change_pct: 0.84,
      momentum_direction: "accelerating",
    },
    {
      year: 2024,
      family_filing_count: 9,
      cumulative_family_count: 80,
      rolling_3y_family_filing_count: 37,
      prior_3y_family_filing_count: 43,
      rolling_3y_change_pct: -0.1395,
      momentum_direction: "stable",
    },
  ],
};

const portfolioStatusTimeseriesPayload = {
  owner_id: MOCK_PORTFOLIO_OWNER_ID,
  rows: [
    {
      as_of_year: 2021,
      family_count: 88,
      pending_family_count: 19,
      fully_active_family_count: 42,
      under_fire_family_count: 11,
      partially_lapsed_family_count: 9,
      dead_family_count: 7,
      pending_share: 0.2159,
      fully_active_share: 0.4773,
      under_fire_share: 0.125,
      partially_lapsed_share: 0.1023,
      dead_share: 0.0795,
      status_coverage_pct: 1,
      historical_owner_truth_supported_pct: 0,
      current_owner_metadata_only_pct: 1,
      avg_data_completeness_pct_asof: 0.88,
    },
    {
      as_of_year: 2022,
      family_count: 93,
      pending_family_count: 21,
      fully_active_family_count: 45,
      under_fire_family_count: 12,
      partially_lapsed_family_count: 9,
      dead_family_count: 6,
      pending_share: 0.2258,
      fully_active_share: 0.4839,
      under_fire_share: 0.129,
      partially_lapsed_share: 0.0968,
      dead_share: 0.0645,
      status_coverage_pct: 1,
      historical_owner_truth_supported_pct: 0,
      current_owner_metadata_only_pct: 1,
      avg_data_completeness_pct_asof: 0.9,
    },
    {
      as_of_year: 2023,
      family_count: 97,
      pending_family_count: 24,
      fully_active_family_count: 47,
      under_fire_family_count: 12,
      partially_lapsed_family_count: 8,
      dead_family_count: 6,
      pending_share: 0.2474,
      fully_active_share: 0.4845,
      under_fire_share: 0.1237,
      partially_lapsed_share: 0.0825,
      dead_share: 0.0619,
      status_coverage_pct: 1,
      historical_owner_truth_supported_pct: 0,
      current_owner_metadata_only_pct: 1,
      avg_data_completeness_pct_asof: 0.92,
    },
    {
      as_of_year: 2024,
      family_count: 101,
      pending_family_count: 26,
      fully_active_family_count: 49,
      under_fire_family_count: 13,
      partially_lapsed_family_count: 7,
      dead_family_count: 6,
      pending_share: 0.2574,
      fully_active_share: 0.4851,
      under_fire_share: 0.1287,
      partially_lapsed_share: 0.0693,
      dead_share: 0.0594,
      status_coverage_pct: 1,
      historical_owner_truth_supported_pct: 0,
      current_owner_metadata_only_pct: 1,
      avg_data_completeness_pct_asof: 0.93,
    },
    {
      as_of_year: 2025,
      family_count: 104,
      pending_family_count: 28,
      fully_active_family_count: 50,
      under_fire_family_count: 12,
      partially_lapsed_family_count: 8,
      dead_family_count: 6,
      pending_share: 0.2692,
      fully_active_share: 0.4808,
      under_fire_share: 0.1154,
      partially_lapsed_share: 0.0769,
      dead_share: 0.0577,
      status_coverage_pct: 1,
      historical_owner_truth_supported_pct: 0,
      current_owner_metadata_only_pct: 1,
      avg_data_completeness_pct_asof: 0.94,
    },
  ],
  meta: {
    support_level: "moderate",
    coverage: {
      status: "high",
      pct: 1,
      covered_count: 5,
      denominator_count: 5,
      caveat_text: "Status chronology is replayed through current owner membership in mocked data.",
    },
  },
};

const portfolioJurisdictionUnlockPayload = {
  owner_id: MOCK_PORTFOLIO_OWNER_ID,
  rows: [
    {
      kind: "summary",
      unlocked_jurisdiction_count: 8,
      first_unlock_year: 2019,
      latest_unlock_year: 2024,
      latest_presence_year: 2025,
      latest_active_jurisdiction_count: 6,
      latest_pending_jurisdiction_count: 7,
      latest_lapsed_jurisdiction_count: 2,
      ever_active_jurisdiction_count: 6,
    },
    {
      kind: "year",
      as_of_year: 2019,
      unlocked_jurisdiction_count: 2,
      cumulative_unlocked_jurisdiction_count: 2,
      active_unlock_count: 1,
      pending_unlock_count: 2,
      lapsed_only_unlock_count: 0,
      active_jurisdiction_count: 1,
      pending_jurisdiction_count: 2,
      lapsed_jurisdiction_count: 0,
      unlocked_jurisdictions: ["US", "WO"],
    },
    {
      kind: "year",
      as_of_year: 2020,
      unlocked_jurisdiction_count: 2,
      cumulative_unlocked_jurisdiction_count: 4,
      active_unlock_count: 1,
      pending_unlock_count: 2,
      lapsed_only_unlock_count: 0,
      active_jurisdiction_count: 2,
      pending_jurisdiction_count: 4,
      lapsed_jurisdiction_count: 0,
      unlocked_jurisdictions: ["CN", "EP"],
    },
    {
      kind: "year",
      as_of_year: 2022,
      unlocked_jurisdiction_count: 2,
      cumulative_unlocked_jurisdiction_count: 6,
      active_unlock_count: 1,
      pending_unlock_count: 1,
      lapsed_only_unlock_count: 0,
      active_jurisdiction_count: 4,
      pending_jurisdiction_count: 5,
      lapsed_jurisdiction_count: 1,
      unlocked_jurisdictions: ["JP", "KR"],
    },
    {
      kind: "year",
      as_of_year: 2024,
      unlocked_jurisdiction_count: 2,
      cumulative_unlocked_jurisdiction_count: 8,
      active_unlock_count: 1,
      pending_unlock_count: 1,
      lapsed_only_unlock_count: 0,
      active_jurisdiction_count: 6,
      pending_jurisdiction_count: 7,
      lapsed_jurisdiction_count: 2,
      unlocked_jurisdictions: ["CA", "GB"],
    },
    {
      kind: "year",
      as_of_year: 2025,
      unlocked_jurisdiction_count: 0,
      cumulative_unlocked_jurisdiction_count: 8,
      active_unlock_count: 0,
      pending_unlock_count: 0,
      lapsed_only_unlock_count: 0,
      active_jurisdiction_count: 6,
      pending_jurisdiction_count: 7,
      lapsed_jurisdiction_count: 2,
      unlocked_jurisdictions: [],
    },
    {
      kind: "jurisdiction",
      jurisdiction_code: "US",
      first_unlock_year: 2019,
      first_unlock_basis: "active",
      first_active_year: 2019,
      first_pending_year: 2019,
      first_lapsed_year: 0,
      tracked_family_count: 18,
      active_family_count: 12,
      pending_family_count: 14,
      lapsed_family_count: 2,
    },
    {
      kind: "jurisdiction",
      jurisdiction_code: "WO",
      first_unlock_year: 2019,
      first_unlock_basis: "pending",
      first_active_year: 2020,
      first_pending_year: 2019,
      first_lapsed_year: 0,
      tracked_family_count: 16,
      active_family_count: 9,
      pending_family_count: 16,
      lapsed_family_count: 1,
    },
    {
      kind: "jurisdiction",
      jurisdiction_code: "EP",
      first_unlock_year: 2020,
      first_unlock_basis: "pending",
      first_active_year: 2021,
      first_pending_year: 2020,
      first_lapsed_year: 0,
      tracked_family_count: 14,
      active_family_count: 8,
      pending_family_count: 13,
      lapsed_family_count: 1,
    },
    {
      kind: "jurisdiction",
      jurisdiction_code: "CN",
      first_unlock_year: 2020,
      first_unlock_basis: "active",
      first_active_year: 2020,
      first_pending_year: 2020,
      first_lapsed_year: 2024,
      tracked_family_count: 12,
      active_family_count: 7,
      pending_family_count: 10,
      lapsed_family_count: 2,
    },
  ],
  meta: {
    support_level: "moderate",
    coverage: {
      status: "high",
      pct: 1,
      covered_count: 5,
      denominator_count: 5,
      caveat_text: "Unlock chronology in mocked data uses first observed branch years under current owner replay.",
    },
  },
};

const portfolioCompareTimeslicePayload = {
  owner_id: MOCK_PORTFOLIO_OWNER_ID,
  rows: [
    {
      metric: "field_share",
      label: "Field share",
      current_value: 0.42,
      compare_value: 0.34,
      current_score: 74,
      compare_score: 61,
      current_year: 2025,
      compare_year: 2022,
      delta: 13,
    },
    {
      metric: "citation_pressure",
      label: "Citation pressure",
      current_value: 67,
      compare_value: 58,
      current_score: 69,
      compare_score: 57,
      current_year: 2025,
      compare_year: 2022,
      delta: 12,
    },
    {
      metric: "grant_density",
      label: "Grant density",
      current_value: 0.78,
      compare_value: 0.81,
      current_score: 63,
      compare_score: 68,
      current_year: 2025,
      compare_year: 2022,
      delta: -5,
    },
  ],
};

const portfolioPendingGrantsPayload = {
  owner_id: MOCK_PORTFOLIO_OWNER_ID,
  rows: [
    {
      kind: "summary",
      feature_status: "phase04_ready",
      serving_ready: true,
      horizon: "24m",
      recommended_output: "rank-first",
      probability_headline_allowed: false,
      pending_pipeline_branch_count: 54,
      pending_pipeline_family_count: 19,
      pending_pipeline_expected_likely_grants_24m: 9.6,
      pending_pipeline_avg_probability_24m: 0.41,
      pending_pipeline_percentile: 84.2,
      pending_pipeline_priority_tier: "priority",
      pending_pipeline_support_level: "strong",
      pending_pipeline_top_jurisdiction: "US",
      pending_pipeline_top_field: "Digital communications",
      top_branch_family_id: MOCK_FAMILY_ID,
      top_branch_jurisdiction: "US",
      top_branch_field: "Digital communications",
      top_branch_percentile: 96.4,
      top_branch_probability: 0.82,
    },
    {
      kind: "jurisdiction",
      jurisdiction_code: "US",
      expected_likely_grants_24m: 4.2,
      avg_percentile: 88.1,
    },
    {
      kind: "jurisdiction",
      jurisdiction_code: "EP",
      expected_likely_grants_24m: 2.8,
      avg_percentile: 75.4,
    },
    {
      kind: "field",
      wipo_field: "Digital communications",
      expected_likely_grants_24m: 5.3,
      avg_percentile: 86.3,
    },
    {
      kind: "field",
      wipo_field: "Signal routing",
      expected_likely_grants_24m: 2.1,
      avg_percentile: 72.8,
    },
    {
      kind: "branch",
      docdb_family_id: MOCK_FAMILY_ID,
      jurisdiction_code: "US",
      primary_wipo_field: "Digital communications",
      pending_age_years: 2.4,
      family_age_years: 6.1,
      family_blocking_power_score_asof: 87,
      family_enforceability_score_asof: 82,
      family_rcf_score_asof: 74,
      data_completeness_pct_asof: 0.94,
      probability_24m: 0.82,
      selected_probability: 0.82,
      percentile_within_office_horizon: 96.4,
      priority_tier: "priority",
    },
  ],
};

function buildForecastContributorsPayload({
  contributorScope,
  horizon,
}: {
  contributorScope: string;
  horizon: "3y" | "5y";
}) {
  return {
    owner_id: MOCK_PORTFOLIO_OWNER_ID,
    rows: [
      {
        contributor_scope: contributorScope,
        horizon,
        contributor_entity_id: MOCK_FAMILY_ID,
        jurisdiction_code: "US",
        contribution_value: horizon === "5y" ? 9.1 : 6.4,
        contribution_share: horizon === "5y" ? 0.28 : 0.24,
        contributor_rank: 1,
      },
      {
        contributor_scope: contributorScope,
        horizon,
        contributor_entity_id: "57400091",
        jurisdiction_code: "EP",
        contribution_value: horizon === "5y" ? 5.8 : 4.1,
        contribution_share: horizon === "5y" ? 0.19 : 0.16,
        contributor_rank: 2,
      },
      {
        contributor_scope: contributorScope,
        horizon,
        contributor_entity_id: "57400102",
        jurisdiction_code: "JP",
        contribution_value: horizon === "5y" ? 4.7 : 3.6,
        contribution_share: horizon === "5y" ? 0.14 : 0.12,
        contributor_rank: 3,
      },
    ],
    meta: {
      pagination: {
        limit: 10,
        offset: 0,
        returned_count: 3,
        total_count: 3,
      },
    },
  };
}

const familyOverviewPayload = {
  identity: {
    id: MOCK_FAMILY_ID,
    label: "Acme signal routing family",
    page_kind: "family",
    selected_year: 2025,
  },
  summary_cards: [
    {
      key: "family_strength_score",
      label: "Family strength",
      value: 83,
      band_code: "strong",
      band_label: "Decision-ready",
      peer_percentile: 79,
      peer_cohort_label: "Core communications cohort",
    },
    {
      key: "jurisdiction_count",
      label: "Jurisdictions",
      value: 12,
      band_code: "neutral",
      band_label: "Global spread",
    },
    {
      key: "forward_citation_total",
      label: "Forward citations",
      value: 144,
      band_code: "neutral",
      band_label: "Sustained evidence",
    },
  ],
  overview_metrics: [
    {
      group: "positioning",
      label: "Primary WIPO field",
      value: "Digital communications",
    },
    {
      group: "positioning",
      label: "Status",
      value: "Active grant",
    },
    {
      group: "support",
      label: "Data completeness pct",
      value: 0.91,
    },
    {
      group: "support",
      label: "Enforceability score",
      value: 0.82,
    },
  ],
  meta: {
    page: "family",
    support_level: "strong",
    coverage: {
      status: "high",
      pct: 0.91,
      covered_count: 31,
      denominator_count: 34,
      caveat_text: "Forecast overlays remain bounded to modeled family members.",
    },
    caveats: [
      {
        code: "FM01",
        title: "Modeled coverage only",
        detail: "Forecast and chronology views remain limited to currently modeled family members.",
      },
    ],
  },
};

const familySectionPayloads: Record<string, object> = {
  legal: {
    family_id: MOCK_FAMILY_ID,
    summary: {
      active_jurisdiction_count: 12,
      active_grant_branch_count: 9,
      last_event_date: "2025-01-18",
      last_event_type: "grant_maintained",
    },
    rows: [],
    series: [],
    meta: {
      page: "family",
      support_level: "strong",
      caveats: [],
    },
  },
  fields: {
    family_id: MOCK_FAMILY_ID,
    summary: {
      primary_field: "Digital communications",
      concentration_score: 0.74,
    },
    rows: [],
    series: [],
    meta: {
      page: "family",
      support_level: "moderate",
      caveats: [],
    },
  },
  timeseries: {
    family_id: MOCK_FAMILY_ID,
    summary: {
      publication_count: 18,
    },
    rows: [],
    series: [],
    meta: {
      page: "family",
      support_level: "moderate",
      caveats: [],
    },
  },
  citations: {
    family_id: MOCK_FAMILY_ID,
    summary: {
      forward_citations_clean: 144,
      forward_citations_7y: 118,
      forward_citing_owner_count: 53,
      backward_citations_clean: 37,
      backward_cited_owner_count: 24,
      backward_npl_citation_count: 9,
    },
    rows: [
      {
        as_of_date: "2024-12-31",
        as_of_year: 2024,
        is_observed_as_of_snapshot: true,
        pre_asof_forward_citation_event_count: 182,
        pre_asof_forward_clean_citation_event_count: 144,
        pre_asof_forward_citations_weighted: 212.4,
        pre_asof_unique_citing_family_count: 96,
        pre_asof_unique_citing_owner_count: 53,
        pre_asof_backward_citation_event_count: 44,
        pre_asof_backward_clean_citation_event_count: 37,
        pre_asof_distinct_cited_family_count: 29,
        data_completeness_pct_asof: 0.91,
      },
    ],
    series: [
      {
        series_kind: "citing_family",
        citing_docdb_family_id: 998877,
        citing_assignee_name: "Nokia",
        distinct_cited_member_count: 2,
        distinct_citing_publication_count: 3,
        first_citation_date: "2016-03-10",
        latest_citation_date: "2024-11-09",
      },
    ],
    meta: {
      page: "family",
      support_level: "moderate",
      caveats: [],
      pagination: {
        limit: 10,
        offset: 0,
        returned_count: 1,
        total_count: 1,
      },
    },
  },
  classification: {
    family_id: MOCK_FAMILY_ID,
    summary: {
      primary_classification: "H04L",
    },
    rows: [],
    series: [],
    meta: {
      page: "family",
      support_level: "moderate",
      caveats: [],
    },
  },
  forecast: {
    family_id: MOCK_FAMILY_ID,
    summary: {
      forecast_available: true,
      forecast_interval_low: 4,
      forecast_interval_high: 7,
    },
    rows: [],
    series: [],
    meta: {
      page: "family",
      support_level: "strong",
      caveats: [],
    },
  },
  members: {
    family_id: MOCK_FAMILY_ID,
    summary: null,
    rows: [
      {
        publication_number_full: MOCK_PUBLICATION_ID,
        publn_auth: "EP",
        publn_kind: "A1",
        publn_date: "2013-07-10",
        is_application_stage: true,
        is_grant_stage: false,
      },
      {
        publication_number_full: "EP2606406B1",
        publn_auth: "EP",
        publn_kind: "B1",
        publn_date: "2018-11-14",
        is_application_stage: false,
        is_grant_stage: true,
      },
    ],
    series: [],
    meta: {
      page: "family",
      support_level: "moderate",
      pagination: {
        limit: 10,
        offset: 0,
        returned_count: 2,
        total_count: 2,
      },
      caveats: [],
    },
  },
};

const publicationOverviewPayload = {
  identity: {
    id: MOCK_PUBLICATION_ID,
    label: MOCK_PUBLICATION_ID,
    page_kind: "publication",
  },
  overview: {
    publication_id: MOCK_PUBLICATION_ID,
    authority: "EP",
    kind_code: "A1",
    stage_label: "Application",
    publication_date: "2013-07-10",
    docdb_family_id: Number(MOCK_FAMILY_ID),
    appln_id: 11223344,
    pat_publn_id: 26064061,
    scope_type: "mega_cluster_bounded",
    snapshot_date: "2026-03-15",
    title: "Signal routing for adaptive network switching",
  },
  summary_cards: [
    { key: "office", label: "Office", value: "EP" },
    { key: "kind_code", label: "Kind code", value: "A1" },
    { key: "stage", label: "Stage", value: "Application" },
    { key: "publication_date", label: "Publication date", value: "2013-07-10" },
    { key: "register_evidence", label: "Register evidence", value: "Present" },
    { key: "text_coverage", label: "Text evidence", value: "Title + abstract" },
  ],
  bibliography: [
    { label: "Publication number", value: MOCK_PUBLICATION_ID },
    { label: "Authority", value: "EP" },
    { label: "Publication number body", value: "2606406" },
    { label: "Kind code", value: "A1" },
    { label: "Publication date", value: "2013-07-10" },
    { label: "PATSTAT application id", value: 11223344 },
  ],
  family_context: [
    { label: "DOCDB family", value: Number(MOCK_FAMILY_ID) },
    { label: "Document stage", value: "Application" },
    { label: "Scope type", value: "mega_cluster_bounded" },
    { label: "Snapshot date", value: "2026-03-15" },
  ],
  text_availability: [
    {
      key: "title",
      label: "Title",
      status: "available",
      detail: "PATSTAT application title",
    },
    {
      key: "abstract",
      label: "Abstract",
      status: "available",
      detail: "PATSTAT English abstract fallback",
    },
    {
      key: "claim_1",
      label: "Claim 1",
      status: "candidate",
      detail: "EPAB English Claim 1 is checked lazily when the text panel opens.",
    },
  ],
  register_evidence: [
    {
      label: "Register record present",
      value: "Yes",
      detail: "EP Register evidence only applies to EP publications with register anchors.",
    },
    {
      label: "Display status",
      value: "pending_examination",
      detail: "REGISTER_CORE",
    },
    {
      label: "Registered license",
      value: "Yes",
      detail: "Acme Licensing GmbH",
    },
  ],
  related_publications: [
    {
      publication_number_full: "EP2606406B1",
      publn_auth: "EP",
      publn_kind: "B1",
      publn_date: "2018-11-14",
      stage_label: "Grant",
    },
    {
      publication_number_full: "WO2012131275A1",
      publn_auth: "WO",
      publn_kind: "A1",
      publn_date: "2012-10-04",
      stage_label: "Application",
    },
  ],
  meta: {
    page: "publication.overview",
    support_level: "moderate",
    caveats: [
      {
        code: "publication_evidence_first",
        title: "Publication pages stay evidence-first",
        detail: "This view is intentionally factual and document-level. It does not introduce synthetic publication strength or threat scoring.",
      },
    ],
  },
};

const publicationSectionPayloads: Record<string, object> = {
  text: {
    publication_id: MOCK_PUBLICATION_ID,
    summary: {
      title_available: true,
      abstract_available: true,
      claim_1_available: true,
      claim_source_mode: "epab_claim_1",
    },
    rows: [
      {
        panel_key: "title",
        label: "Title",
        text: "Signal routing for adaptive network switching",
        language_code: "en",
        source: "PATSTAT_TITLE",
        available: true,
      },
      {
        panel_key: "abstract",
        label: "Abstract",
        text: "An adaptive routing system for network traffic.",
        language_code: "en",
        source: "PATSTAT_ABSTRACT",
        available: true,
      },
      {
        panel_key: "claim_1",
        label: "Claim 1",
        text: "A routing apparatus comprising an adaptive signal controller.",
        language_code: "en",
        source: "EPAB_CLAIM",
        available: true,
      },
    ],
    meta: {
      page: "publication.text",
      support_level: "moderate",
      caveats: [],
    },
  },
  "legal-timeline": {
    publication_id: MOCK_PUBLICATION_ID,
    summary: {
      latest_event_date: "2026-03-15",
      latest_event_type: "Register snapshot",
      event_count: 3,
      register_record_present: true,
    },
    rows: [
      {
        event_date: "2013-07-10",
        event_type: "Publication",
        detail: "EP2606406A1 published in EP.",
        source: "PATSTAT_PUBLICATION",
      },
      {
        event_date: "2014-01-12",
        event_type: "Search report mailed",
        detail: "EXAM",
        source: "EP_REGISTER_PROC",
      },
      {
        event_date: "2026-03-15",
        event_type: "Register snapshot",
        detail: "pending_examination",
        source: "REGISTER_CORE",
      },
    ],
    meta: {
      page: "publication.legal_timeline",
      support_level: "strong",
      caveats: [],
    },
  },
  "register-evidence": {
    publication_id: MOCK_PUBLICATION_ID,
    summary: {
      register_record_present: true,
      register_snapshot_date: "2026-03-15",
      license_flag: true,
      unitary_patent: false,
      opposition_active: false,
    },
    rows: [
      {
        label: "Register record present",
        value: "Yes",
        detail: "2026-03-15",
      },
      {
        label: "Display status",
        value: "pending_examination",
        detail: "REGISTER_CORE",
      },
      {
        label: "Registered license flag",
        value: "Yes",
        detail: "Acme Licensing GmbH",
      },
      {
        label: "Search report mailed",
        value: "2014-01-12",
        detail: "EXAM",
      },
      {
        label: "Latest procedure result",
        value: "PENDING",
        detail: "0.81",
      },
      {
        label: "Unitary patent status",
        value: "—",
        detail: "No UP event date recorded.",
      },
      {
        label: "Opposition status",
        value: "—",
        detail: "No opponent names observed.",
      },
      {
        label: "Lead agent",
        value: "Meyer IP",
        detail: "DE",
      },
    ],
    meta: {
      page: "publication.register_evidence",
      support_level: "strong",
      caveats: [],
    },
  },
};

async function fulfillJson(route: Route, payload: unknown) {
  await route.fulfill({
    status: 200,
    contentType: "application/json; charset=utf-8",
    body: JSON.stringify(payload),
  });
}

export async function mockPatentIqApis(page: Page) {
  await page.route("**/api/v1/**", async (route) => {
    const url = new URL(route.request().url());
    const { pathname, searchParams } = url;

    if (pathname === "/api/v1/market-intelligence/workspace") {
      await fulfillJson(route, buildMarketWorkspacePayload(searchParams));
      return;
    }

    if (pathname === `/api/v1/portfolios/${MOCK_PORTFOLIO_OWNER_ID}/overview`) {
      await fulfillJson(route, portfolioOverviewPayload);
      return;
    }

    if (pathname === `/api/v1/portfolios/${MOCK_PORTFOLIO_OWNER_ID}/families`) {
      await fulfillJson(route, portfolioFamiliesPayload);
      return;
    }

    if (pathname === `/api/v1/portfolios/${MOCK_PORTFOLIO_OWNER_ID}/fields`) {
      await fulfillJson(route, portfolioFieldsPayload);
      return;
    }

    if (pathname === `/api/v1/portfolios/${MOCK_PORTFOLIO_OWNER_ID}/forecast`) {
      const horizon = searchParams.get("horizon") === "5y" ? "5y" : "3y";
      await fulfillJson(route, portfolioForecastByHorizon[horizon]);
      return;
    }

    if (pathname === `/api/v1/portfolios/${MOCK_PORTFOLIO_OWNER_ID}/threats`) {
      await fulfillJson(route, portfolioThreatsPayload);
      return;
    }

    if (pathname === `/api/v1/portfolios/${MOCK_PORTFOLIO_OWNER_ID}/classification`) {
      await fulfillJson(route, portfolioClassificationPayload);
      return;
    }

    if (pathname === `/api/v1/portfolios/${MOCK_PORTFOLIO_OWNER_ID}/citation-summary`) {
      await fulfillJson(route, portfolioCitationSummaryPayload);
      return;
    }

    if (pathname === `/api/v1/portfolios/${MOCK_PORTFOLIO_OWNER_ID}/citation-timeseries`) {
      await fulfillJson(route, portfolioCitationTimeseriesPayload);
      return;
    }

    if (pathname === `/api/v1/portfolios/${MOCK_PORTFOLIO_OWNER_ID}/citation-attackers`) {
      await fulfillJson(route, portfolioCitationAttackersPayload);
      return;
    }

    if (pathname === `/api/v1/portfolios/${MOCK_PORTFOLIO_OWNER_ID}/citation-fields`) {
      await fulfillJson(route, portfolioCitationFieldsPayload);
      return;
    }

    if (pathname === `/api/v1/portfolios/${MOCK_PORTFOLIO_OWNER_ID}/citation-jurisdictions`) {
      await fulfillJson(route, portfolioCitationJurisdictionsPayload);
      return;
    }

    if (pathname === `/api/v1/portfolios/${MOCK_PORTFOLIO_OWNER_ID}/filing-timeseries`) {
      await fulfillJson(route, portfolioFilingTimeseriesPayload);
      return;
    }

    if (pathname === `/api/v1/portfolios/${MOCK_PORTFOLIO_OWNER_ID}/status-timeseries`) {
      await fulfillJson(route, portfolioStatusTimeseriesPayload);
      return;
    }

    if (pathname === `/api/v1/portfolios/${MOCK_PORTFOLIO_OWNER_ID}/jurisdiction-unlocks`) {
      await fulfillJson(route, portfolioJurisdictionUnlockPayload);
      return;
    }

    if (pathname === `/api/v1/portfolios/${MOCK_PORTFOLIO_OWNER_ID}/field-timeseries`) {
      await fulfillJson(route, portfolioFieldTimeseriesPayload);
      return;
    }

    if (pathname === `/api/v1/portfolios/${MOCK_PORTFOLIO_OWNER_ID}/market-context`) {
      await fulfillJson(route, portfolioMarketContextPayload);
      return;
    }

    if (pathname === `/api/v1/portfolios/${MOCK_PORTFOLIO_OWNER_ID}/compare-timeslice`) {
      await fulfillJson(route, portfolioCompareTimeslicePayload);
      return;
    }

    if (pathname === `/api/v1/portfolios/${MOCK_PORTFOLIO_OWNER_ID}/pending-grants`) {
      await fulfillJson(route, portfolioPendingGrantsPayload);
      return;
    }

    if (pathname === `/api/v1/portfolios/${MOCK_PORTFOLIO_OWNER_ID}/forecast-contributors`) {
      const contributorScope = searchParams.get("contributor_scope") ?? "phase03_future_citations";
      const horizon = searchParams.get("horizon") === "5y" ? "5y" : "3y";
      await fulfillJson(route, buildForecastContributorsPayload({ contributorScope, horizon }));
      return;
    }

    if (pathname === "/api/v1/portfolios/search") {
      await fulfillJson(route, {
        query: searchParams.get("query") ?? "",
        rows: [
          {
            owner_id: MOCK_PORTFOLIO_OWNER_ID,
            label: "Acme Holdings",
            family_count: 104,
          },
        ],
      });
      return;
    }

    if (pathname === `/api/v1/families/${MOCK_FAMILY_ID}/overview`) {
      await fulfillJson(route, familyOverviewPayload);
      return;
    }

    const familySectionMatch = pathname.match(new RegExp(`^/api/v1/families/${MOCK_FAMILY_ID}/([^/]+)$`));
    if (familySectionMatch) {
      const section = familySectionMatch[1] ?? "";
      const payload = familySectionPayloads[section];

      if (payload) {
        await fulfillJson(route, payload);
        return;
      }
    }

    if (pathname === `/api/v1/publications/${MOCK_PUBLICATION_ID}/overview`) {
      await fulfillJson(route, publicationOverviewPayload);
      return;
    }

    const publicationSectionMatch = pathname.match(new RegExp(`^/api/v1/publications/${MOCK_PUBLICATION_ID}/([^/]+)$`));
    if (publicationSectionMatch) {
      const section = publicationSectionMatch[1] ?? "";
      const payload = publicationSectionPayloads[section];

      if (payload) {
        await fulfillJson(route, payload);
        return;
      }
    }

    await route.fulfill({
      status: 404,
      contentType: "application/json; charset=utf-8",
      body: JSON.stringify({
        error: {
          code: "UNMOCKED_ROUTE",
          message: `No test fixture is configured for ${pathname}${url.search}`,
        },
      }),
    });
  });
}
