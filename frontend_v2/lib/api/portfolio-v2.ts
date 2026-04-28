import { fetchJson } from "@/lib/api/core";
import { getApiBaseUrl } from "@/lib/config";
import type {
  PortfolioCitationAttackersQuery,
  PortfolioCitationAttackersResponse,
  PortfolioCitationCpcGroupsQuery,
  PortfolioCitationCpcGroupsResponse,
  PortfolioCitationFamiliesQuery,
  PortfolioCitationFamiliesResponse,
  PortfolioCitationFieldsQuery,
  PortfolioCitationFieldsResponse,
  PortfolioCitationJurisdictionsQuery,
  PortfolioCitationJurisdictionsResponse,
  PortfolioCitationSummaryQuery,
  PortfolioCitationSummaryResponse,
  PortfolioCitationTimeseriesQuery,
  PortfolioCitationTimeseriesResponse,
  PortfolioClassificationQuery,
  PortfolioCompareTimesliceQuery,
  PortfolioCompareTimesliceResponse,
  PortfolioFilingTimeseriesPoint,
  PortfolioFilingTimeseriesQuery,
  PortfolioFilingTimeseriesResponse,
  PortfolioJurisdictionUnlockHistoryResponse,
  PortfolioFieldTimeseriesQuery,
  PortfolioFieldTimeseriesResponse,
  PortfolioForecastPayload,
  PortfolioForecastContributorsQuery,
  PortfolioForecastContributorsResponse,
  PortfolioFieldRowsResponse,
  PortfolioIdentity,
  PortfolioDashboardPayload,
  PortfolioFamiliesQuery,
  PortfolioFamiliesResponse,
  PortfolioMarketContextQuery,
  PortfolioMarketContextResponse,
  PortfolioPagination,
  PortfolioPendingGrantResponse,
  PortfolioPendingGrantsQuery,
  PortfolioStatusTimeseriesResponse,
  PortfolioThreatQuery,
  PortfolioThreatsResponse,
  PortfolioClassificationResponse,
  PortfolioOverviewPayload,
  PortfolioOwnerSearchPayload,
  PortfolioOwnerSuggestion,
  PortfolioSummaryCard,
  PortfolioHistoryAudit,
} from "@/lib/types/portfolio-v2";
import type { SupportLevel } from "@/lib/types/common";

type BackendIdentity = {
  id?: string;
  label?: string;
  page_kind?: string;
  selected_year?: number | null;
};

type BackendOverview = {
  identity?: BackendIdentity;
  count_scopes?: {
    in_scope_family_count?: number;
    primary_owner_family_count?: number;
    active_grant_family_count?: number;
    semantic_candidate_family_count?: number;
    pending_family_count?: number;
    unclassified_family_count?: number;
  };
  status_mix?: Array<{
    key?: string;
    label?: string;
    count?: number;
    share?: number;
  }>;
  summary_cards?: Array<{
    key?: string;
    label?: string;
    value?: string;
    tone?: string;
    delta?: number;
    delta_label?: string;
    tooltip?: string;
    caveat?: string;
  }>;
  top_family_preview?: Array<{
    family_id?: string;
    owner_weight?: number;
    blocking_score?: number;
    status?: string;
    heritage?: string;
    primary_field?: string;
    forecast_contributor?: number;
  }>;
  meta?: {
    artifact_sources?: string[];
    support_level?: "strong" | "high" | "moderate" | "limited" | "candidate_only";
    coverage?: {
      status?: "high" | "medium" | "low" | "unknown";
      pct?: number;
      covered_count?: number;
      denominator_count?: number;
      caveat_text?: string;
    };
    caveats?: Array<{
      code?: string;
      title?: string;
      detail?: string;
    }>;
  };
};

type BackendRows = Array<Record<string, unknown>>;

type BackendPagination = {
  limit?: number;
  offset?: number;
  returned_count?: number;
  total_count?: number | null;
};

type BackendMeta = {
  pagination?: BackendPagination;
  support_level?: "strong" | "high" | "moderate" | "limited" | "candidate_only";
  coverage?: {
    status?: "high" | "medium" | "low" | "unknown";
    pct?: number;
    covered_count?: number;
    denominator_count?: number;
    caveat_text?: string;
  };
};

type BackendFamiliesPayload = {
  owner_id?: string;
  rows?: BackendRows;
  meta?: BackendMeta;
};

type BackendFieldsPayload = {
  owner_id?: string;
  rows?: BackendRows;
  meta?: BackendMeta;
};

type BackendForecast = {
  owner_id?: string;
  coverage?: {
    status?: "high" | "partial" | "low";
    caveat_text?: string;
    phase03_family_coverage_pct?: number;
    phase04_family_coverage_pct?: number;
    phase06_family_coverage_pct?: number;
    contribution_method?: string;
  };
  sections?: Array<{
    horizon?: string;
    total?: number;
    low?: number;
    high?: number;
    per_effective_family?: number;
    top_contributor_dependence_pct?: number;
    coverage_pct?: number;
    top_segments?: Array<{
      field?: string;
      active_families?: number;
      active_share?: number;
      hotspot_direction?: "gains" | "losses";
      change_12m?: number;
        confidence?: "strong" | "high" | "moderate" | "limited";
    }>;
    risk12m?: Array<{
      risk_band?: string;
      share?: number;
      family_count?: number;
    }>;
    risk24m?: Array<{
      risk_band?: string;
      share?: number;
      family_count?: number;
    }>;
  }>;
};

type BackendForecastSection = NonNullable<BackendForecast["sections"]>[number];
type BackendRiskRow = NonNullable<BackendForecastSection["risk12m"]>[number];

type BackendThreat = {
  owner_id?: string;
  citing_assignee_name?: string;
  citing_assignee?: string;
  wipo_field?: string;
  citation_lethality?: number;
  citation_lethality_sum?: number;
  collided_family_count?: number;
};

type BackendThreatPayload = {
  owner_id?: string;
  rows?: BackendThreat[];
  meta?: BackendMeta;
};

type BackendClassificationRow = {
  segment?: string;
  classification_type?: string;
  wipo_field?: string;
  family_share?: number;
  trajectory?: number;
  top_change?: "gain" | "loss" | "flat";
};

type BackendClassificationPoint = {
  year?: number;
  share?: number;
  portfolio?: number;
};

type BackendClassificationSeries = {
  field?: string;
  points?: BackendClassificationPoint[];
};

type BackendClassification = {
  owner_id?: string;
  rows?: BackendClassificationRow[];
  timeseries?: BackendClassificationSeries[];
  meta?: BackendMeta;
};

type BackendClassificationPayload = BackendClassification;

type BackendSectionPayload = {
  owner_id?: string;
  rows?: BackendRows;
  meta?: BackendMeta;
};

type BackendOwnerSearchPayload = {
  query?: string;
  rows?: Array<{
    owner_id?: string;
    label?: string;
    family_count?: number;
  }>;
};

const toNumber = (value: unknown, fallback = 0): number => {
  const candidate = Number(value);
  return Number.isFinite(candidate) ? candidate : fallback;
};

const parseSupportLevel = (value: unknown): SupportLevel => {
  if (value === "strong" || value === "high") {
    return "strong";
  }

  if (value === "moderate") {
    return "moderate";
  }

  if (value === "candidate_only") {
    return "candidate_only";
  }

  return "limited";
};

const parseMomentumDirection = (value: unknown): PortfolioFilingTimeseriesPoint["momentumDirection"] => {
  if (value === "accelerating" || value === "cooling" || value === "stable") {
    return value;
  }
  return "stable";
};

const mapHistoryAudit = (meta?: BackendMeta): PortfolioHistoryAudit => ({
  coverageStatus:
    meta?.coverage?.status === "high" || meta?.coverage?.status === "medium" || meta?.coverage?.status === "low"
      ? meta.coverage.status
      : "low",
  coveragePct: toNumber(meta?.coverage?.pct, 0),
  coveredCount: meta?.coverage?.covered_count == null ? undefined : toNumber(meta.coverage.covered_count, 0),
  denominatorCount: meta?.coverage?.denominator_count == null ? undefined : toNumber(meta.coverage.denominator_count, 0),
  coverageCaveatText: meta?.coverage?.caveat_text,
  supportLevel: parseSupportLevel(meta?.support_level),
});

const ownerLabelFromId = (ownerId: string): string =>
  ownerId
    .replace(/[_-]+/g, " ")
    .trim()
    .replace(/\s+/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());

const mapSummaryCard = (row: {
  key?: string;
  label?: string;
  value?: string;
  tone?: string;
  delta?: number;
  delta_label?: string;
  tooltip?: string;
  caveat?: string;
  band_code?: string;
  band_label?: string;
  peer_bucket?: string;
  peer_bucket_label?: string;
  peer_percentile?: number;
}): PortfolioSummaryCard => ({
  key: row.key ?? "metric",
  label: row.label ?? "metric",
  value: row.value ?? "0",
  tone:
    row.tone === "positive" || row.tone === "warning" || row.tone === "critical" ? row.tone : "neutral",
  delta: row.delta,
  deltaLabel: row.delta_label,
  tooltip: row.tooltip,
  caveat: row.caveat,
  bandCode: row.band_code,
  bandLabel: row.band_label,
  peerBucket: row.peer_bucket,
  peerBucketLabel: row.peer_bucket_label,
  peerPercentile: row.peer_percentile == null ? undefined : toNumber(row.peer_percentile, 0),
});

const mapPagination = (meta?: BackendMeta): PortfolioPagination | undefined => {
  if (!meta?.pagination) {
    return undefined;
  }

  return {
    limit: toNumber(meta.pagination.limit, 10),
    offset: toNumber(meta.pagination.offset, 0),
    returnedCount: toNumber(meta.pagination.returned_count, 0),
    totalCount:
      meta.pagination.total_count == null
        ? undefined
        : toNumber(meta.pagination.total_count, 0),
  };
};

const mapFamilyRows = (payload: BackendFamiliesPayload = {}): PortfolioFamiliesResponse => ({
  ownerId: payload.owner_id ?? "",
  rows: (payload.rows ?? [])
    .filter((row): row is Record<string, unknown> => Boolean(row))
    .map((row) => ({
      familyId: String((row.family_id as string) ?? ""),
      ownerWeight: toNumber(row.owner_weight ?? row.ownerWeight, 0),
      blockingScore: toNumber(row.blocking_score ?? row.blockingScore, 0),
      status: String(row.status ?? "unknown"),
      priorityYear: String(row.priority_year ?? row.heritage ?? "unknown"),
      title: row.title == null ? undefined : String(row.title),
      primaryField: String(row.primary_field ?? row.primaryField ?? "unknown"),
      forecastContributor: row.forecast_contributor == null ? undefined : toNumber(row.forecast_contributor),
    })),
  pagination: mapPagination(payload.meta),
});

const mapFieldRows = (payload: BackendFieldsPayload = {}): PortfolioFieldRowsResponse => ({
  ownerId: payload.owner_id ?? "",
  rows: (payload.rows ?? [])
    .filter((row): row is Record<string, unknown> => Boolean(row))
    .map((row) => ({
      field: String(row.field ?? "unknown"),
      activeFamilies: toNumber(row.active_families ?? row.activeFamilies, 0),
      activeShare: toNumber(row.active_share ?? row.activeShare, 0),
      hotspotDirection:
        row.hotspot_direction === "gains" ||
        row.hotspot_direction === "losses" ||
        row.hotspot_direction === "heating" ||
        row.hotspot_direction === "cooling" ||
        row.hotspot_direction === "stable" ||
        row.hotspot_direction === "flat"
          ? row.hotspot_direction
          : toNumber(row.change_12m ?? row.change12m, 0) >= 0
            ? "gains"
            : "losses",
      change12m: toNumber(row.change_12m ?? row.change12m, 0),
      confidence: parseSupportLevel(row.confidence),
    })),
});

const mapThreatRows = (payload: BackendThreatPayload = {}): PortfolioThreatsResponse => ({
  ownerId: payload.owner_id ?? "",
  rows: (payload.rows ?? [])
    .filter((row): row is BackendThreat => Boolean(row))
    .map((row) => ({
      citingAssignee: String(row.citing_assignee ?? row.citing_assignee_name ?? "unknown"),
      wipoField: String(row.wipo_field ?? "unknown"),
      citationLethality: toNumber(row.citation_lethality_sum ?? row.citation_lethality, 0),
      collidedFamilyCount: toNumber(row.collided_family_count, 0),
    })),
  pagination: mapPagination(payload.meta),
});

const mapTopChange = (value: number): "gain" | "loss" | "flat" => {
  if (value > 0) {
    return "gain";
  }

  if (value < 0) {
    return "loss";
  }

  return "flat";
};

const mapClassificationRows = (payload: BackendClassification = {}): PortfolioClassificationResponse => ({
  ownerId: payload.owner_id ?? "",
  rows: (payload.rows ?? []).map((row) => ({
    segment: String(row.segment ?? ""),
    classificationType: String(row.classification_type ?? "CPC_MAIN_GROUP"),
    wipoField: String(row.wipo_field ?? row.segment ?? "unknown"),
    familyShare: toNumber(row.family_share, 0),
    trajectory: toNumber(row.trajectory, 0),
    topChange: row.top_change ?? mapTopChange(toNumber(row.trajectory, 0)),
  })),
  timeseries: (payload.timeseries ?? []).map((series) => ({
    field: String(series.field ?? "unknown"),
    points: (series.points ?? [])
      .map((point) => ({
        year: toNumber(point?.year, 0),
        share: toNumber(point?.share, 0),
        portfolio: toNumber(point?.portfolio, 0),
      }))
      .filter((point) => point.year > 0),
  })),
  pagination: mapPagination(payload.meta),
});

const emptyClassificationResponse = (ownerId: string): PortfolioClassificationResponse => ({
  ownerId,
  rows: [],
  timeseries: [],
});

const mapForecastFromSections = (
  sections: BackendForecast["sections"] = [],
): PortfolioForecastPayload => {
  if ((sections ?? []).length === 0) {
    return {
      horizon: "3y",
      interval3y: {
        total: Number.NaN,
        low: Number.NaN,
        high: Number.NaN,
        perEffectiveFamily: Number.NaN,
        topConcentrationPct: Number.NaN,
        coveragePct: Number.NaN,
      },
      interval5y: {
        total: Number.NaN,
        low: Number.NaN,
        high: Number.NaN,
        perEffectiveFamily: Number.NaN,
        topConcentrationPct: Number.NaN,
        coveragePct: Number.NaN,
      },
      risk12m: [],
      risk24m: [],
      topSegments: [],
    };
  }

  const byHorizon: Record<string, BackendForecastSection> = {};
  for (const section of sections) {
    const horizon = String(section.horizon ?? "3y");
    byHorizon[horizon] = section;
  }

  const by3y = byHorizon["3y"] ?? {};
  const by5y = byHorizon["5y"] ?? byHorizon["3"] ?? by3y;

  const asSegment = (segment: BackendForecastSection["risk12m"] = []): Array<{
    label: string;
    share: number;
    families: number;
  }> =>
    (segment ?? []).map((item: BackendRiskRow) => ({
      label: String(item.risk_band ?? "medium"),
      share: toNumber(item.share, 0),
      families: toNumber(item.family_count, 0),
    }));

  return {
    horizon: "3y",
    interval3y: {
      total: toNumber(by3y.total, 0),
      low: toNumber(by3y.low, 0),
      high: toNumber(by3y.high, 0),
      perEffectiveFamily: toNumber(by3y.per_effective_family, 0),
      topConcentrationPct: toNumber(by3y.top_contributor_dependence_pct, 0),
      coveragePct: toNumber(by3y.coverage_pct, 0),
    },
    interval5y: {
      total: toNumber(by5y.total, 0),
      low: toNumber(by5y.low, 0),
      high: toNumber(by5y.high, 0),
      perEffectiveFamily: toNumber(by5y.per_effective_family, 0),
      topConcentrationPct: toNumber(by5y.top_contributor_dependence_pct, 0),
      coveragePct: toNumber(by5y.coverage_pct, 0),
    },
    risk12m: asSegment(by3y.risk12m ?? []),
    risk24m: asSegment((by5y.risk24m ?? by3y.risk24m) ?? []),
    topSegments: mapFieldRows({ rows: (by3y.top_segments as BackendRows) ?? [] }).rows,
  };
};

const mapOverview = (raw: BackendOverview): PortfolioOverviewPayload => {
  const coverage = raw.meta?.caveats ?? [];

  const identity: PortfolioIdentity = {
    id: raw.identity?.id ?? "",
    label: raw.identity?.label ?? "Portfolio",
    pageKind: raw.identity?.page_kind ?? "portfolio",
    selectedYear: raw.identity?.selected_year,
  };

  const safeCards = (raw.summary_cards ?? []).map(mapSummaryCard);

  const topFamilyPreview = (raw.top_family_preview ?? []).map((row) => ({
    familyId: String(row.family_id ?? ""),
    ownerWeight: toNumber(row.owner_weight, 0),
    blockingScore: toNumber(row.blocking_score, 0),
    status: String(row.status ?? "unknown"),
    priorityYear: String((row as { priority_year?: string }).priority_year ?? row.heritage ?? "unknown"),
    primaryField: String(row.primary_field ?? "unknown"),
    forecastContributor: row.forecast_contributor == null ? undefined : toNumber(row.forecast_contributor),
  }));

  return {
    identity,
    summaryCards: safeCards,
    statusMix: (raw.status_mix ?? []).map((row) => ({
      key: String(row.key ?? ""),
      label: String(row.label ?? ""),
      count: toNumber(row.count, 0),
      share: toNumber(row.share, 0),
    })),
    familyCount: toNumber((raw as { family_count?: number }).family_count, 0),
    countScopes: {
      inScopeFamilyCount: toNumber(raw.count_scopes?.in_scope_family_count ?? (raw as { family_count?: number }).family_count, 0),
      primaryOwnerFamilyCount: toNumber(raw.count_scopes?.primary_owner_family_count, 0),
      activeGrantFamilyCount: toNumber(
        raw.count_scopes?.active_grant_family_count ?? (raw as { active_grant_family_count?: number }).active_grant_family_count,
        0,
      ),
      semanticCandidateFamilyCount: toNumber(
        raw.count_scopes?.semantic_candidate_family_count ?? (raw as { semantic_candidate_count?: number }).semantic_candidate_count,
        0,
      ),
      pendingFamilyCount: toNumber(raw.count_scopes?.pending_family_count, 0),
      unclassifiedFamilyCount: toNumber(raw.count_scopes?.unclassified_family_count, 0),
    },
    activeGrantFamilyCount: toNumber((raw as { active_grant_family_count?: number }).active_grant_family_count, 0),
    semanticCandidateCount: toNumber((raw as { semantic_candidate_count?: number }).semantic_candidate_count, 0),
    topFamilyPreview,
    coverage: {
      predictionCoverageStatus:
        raw.meta?.coverage?.status === "high" || raw.meta?.coverage?.status === "medium" || raw.meta?.coverage?.status === "low"
          ? raw.meta.coverage.status
          : parseSupportLevel(raw.meta?.support_level) === "strong"
            ? "high"
            : parseSupportLevel(raw.meta?.support_level) === "moderate"
              ? "medium"
              : "low",
      phase03FamilyCoveragePct: toNumber(raw.meta?.coverage?.pct, 0),
      phase04FamilyCoveragePct: null,
      phase06FamilyCoveragePct: null,
      coveredCount: raw.meta?.coverage?.covered_count == null ? undefined : toNumber(raw.meta.coverage.covered_count, 0),
      denominatorCount: raw.meta?.coverage?.denominator_count == null ? undefined : toNumber(raw.meta.coverage.denominator_count, 0),
      coverageCaveatText:
        raw.meta?.coverage?.caveat_text ??
        coverage[0]?.detail ??
        "Coverage depends on portfolio rollup availability and should not be presented as exact legal truth for unmodeled years.",
      supportLevel: parseSupportLevel(raw.meta?.support_level),
    },
  };
};

const mapOwnerSuggestions = (payload: BackendOwnerSearchPayload): PortfolioOwnerSearchPayload => ({
  query: payload.query ?? "",
  rows: (payload.rows ?? [])
    .map(
      (row): PortfolioOwnerSuggestion => ({
        ownerId: String(row.owner_id ?? "").trim(),
        label: String(row.label ?? row.owner_id ?? "").trim(),
        familyCount: row.family_count == null ? undefined : toNumber(row.family_count, 0),
      }),
    )
    .filter((row) => row.ownerId.length > 0),
});

const groupSectionRowsByField = (rows: BackendRows = []): PortfolioFieldTimeseriesResponse["rows"] => {
  const buckets = new Map<string, Array<{ year: number; share: number; portfolio: number }>>();

  rows.forEach((row) => {
    const field = String(row.wipo_field ?? "unknown");
    const snapshotDate = String(row.snapshot_date ?? "");
    const year = Number(snapshotDate.slice(0, 4));
    if (!Number.isFinite(year)) {
      return;
    }
    const points = buckets.get(field) ?? [];
    points.push({
      year,
      share: toNumber(row.active_share, 0),
      portfolio: toNumber(row.active_family_count, 0),
    });
    buckets.set(field, points);
  });

  return Array.from(buckets.entries()).map(([field, points]) => ({
    field,
    points: points.sort((left, right) => left.year - right.year),
  }));
};

const mapFieldTimeseriesRows = (payload: BackendSectionPayload = {}): PortfolioFieldTimeseriesResponse => ({
  ownerId: payload.owner_id ?? "",
  rows: groupSectionRowsByField(payload.rows ?? []),
});

const mapCitationSummaryRows = (payload: BackendSectionPayload = {}): PortfolioCitationSummaryResponse => {
  const row = payload.rows?.[0];
  const hasSummary =
    row != null &&
    (toNumber(row.as_of_year, 0) > 0 || toNumber(row.family_count, 0) > 0);
  return {
    ownerId: payload.owner_id ?? "",
    summary: hasSummary
      ? {
          asOfYear: toNumber(row.as_of_year, 0),
          familyCount: toNumber(row.family_count, 0),
          forwardCitationsCleanTotal: toNumber(row.forward_citations_clean_total, 0),
          forwardCitationsWeightedTotal: toNumber(row.forward_citations_weighted_total, 0),
          backwardCitationsCleanTotal: toNumber(row.backward_citations_clean_total, 0),
          backwardNplCitationTotal: toNumber(row.backward_npl_citation_total, 0),
          distinctCitingFamilyCount: toNumber(row.distinct_citing_family_count, 0),
          distinctCitedFamilyCount: toNumber(row.distinct_cited_family_count, 0),
          avgScienceGroundingScore: toNumber(row.avg_science_grounding_score, 0),
          avgGeneralityPercentile: toNumber(row.avg_generality_percentile, 0),
          avgOriginalityPercentile: toNumber(row.avg_originality_percentile, 0),
          avgUniqueCitingFamilyCount: toNumber(row.avg_unique_citing_family_count, 0),
          avgCitingAssigneeDiversity: toNumber(row.avg_citing_assignee_diversity, 0),
          avgAttackerDensityScore: toNumber(row.avg_attacker_density_score, 0),
          avgOutOfBoundsCitationShare: toNumber(row.avg_out_of_bounds_citation_share, 0),
        }
      : null,
  };
};

const mapCitationTimeseriesRows = (payload: BackendSectionPayload = {}): PortfolioCitationTimeseriesResponse => ({
  ownerId: payload.owner_id ?? "",
  rows: (payload.rows ?? [])
    .map((row) => ({
      year: toNumber(row.as_of_year, 0),
      familyCount: toNumber(row.family_count, 0),
      forwardCitationsCleanTotal: toNumber(row.forward_citations_clean_total, 0),
      forwardCitationsWeightedTotal: toNumber(row.forward_citations_weighted_total, 0),
      avgUniqueCitingFamilyCount: toNumber(row.avg_unique_citing_family_count, 0),
      avgCitingAssigneeDiversity: toNumber(row.avg_citing_assignee_diversity, 0),
      avgAttackerDensityScore: toNumber(row.avg_attacker_density_score, 0),
    }))
    .filter((row) => row.year > 0)
    .sort((left, right) => left.year - right.year),
});

const mapCitationFamilyRows = (payload: BackendSectionPayload = {}): PortfolioCitationFamiliesResponse => ({
  ownerId: payload.owner_id ?? "",
  rows: (payload.rows ?? []).map((row) => ({
    familyId: String(row.family_id ?? ""),
    familyPriorityYear: toNumber(row.family_priority_year, 0),
    primaryField: String(row.primary_field ?? "unknown"),
    status: String(row.status ?? "unknown"),
    forwardCitationsClean: toNumber(row.forward_citations_clean, 0),
    forwardCitationsWeighted: toNumber(row.forward_citations_weighted, 0),
    earlyCitations5y: toNumber(row.early_citations_5y, 0),
    earlyCitations7y: toNumber(row.early_citations_7y, 0),
    uniqueCitingFamilyCount: toNumber(row.unique_citing_family_count, 0),
    citingAssigneeDiversity: toNumber(row.citing_assignee_diversity, 0),
    blockingScore: toNumber(row.blocking_score, 0),
  })),
  pagination: mapPagination(payload.meta),
});

const mapCitationAttackerRows = (payload: BackendSectionPayload = {}): PortfolioCitationAttackersResponse => ({
  ownerId: payload.owner_id ?? "",
  rows: (payload.rows ?? []).map((row) => ({
    citingAssignee: String(row.citing_assignee ?? ""),
    wipoField: String(row.wipo_field ?? ""),
    jurisdictionCode: String(row.jurisdiction_code ?? ""),
    latestCitationYear: toNumber(row.latest_citation_year, 0),
    citationEventCount: toNumber(row.citation_event_count, 0),
    cleanCitationCount: toNumber(row.clean_citation_count, 0),
    citationLethalitySum: toNumber(row.citation_lethality_sum, 0),
  })),
  pagination: mapPagination(payload.meta),
});

const mapCitationFieldRows = (payload: BackendSectionPayload = {}): PortfolioCitationFieldsResponse => ({
  ownerId: payload.owner_id ?? "",
  rows: (payload.rows ?? []).map((row) => ({
    wipoField: String(row.wipo_field ?? ""),
    latestCitationYear: toNumber(row.latest_citation_year, 0),
    citationEventCount: toNumber(row.citation_event_count, 0),
    citingAssigneeCount: toNumber(row.citing_assignee_count, 0),
    cleanCitationCount: toNumber(row.clean_citation_count, 0),
    citationLethalitySum: toNumber(row.citation_lethality_sum, 0),
  })),
  pagination: mapPagination(payload.meta),
});

const mapCitationJurisdictionRows = (payload: BackendSectionPayload = {}): PortfolioCitationJurisdictionsResponse => ({
  ownerId: payload.owner_id ?? "",
  rows: (payload.rows ?? []).map((row) => ({
    jurisdictionCode: String(row.jurisdiction_code ?? ""),
    latestCitationYear: toNumber(row.latest_citation_year, 0),
    citationEventCount: toNumber(row.citation_event_count, 0),
    citingAssigneeCount: toNumber(row.citing_assignee_count, 0),
    wipoFieldCount: toNumber(row.wipo_field_count, 0),
    cleanCitationCount: toNumber(row.clean_citation_count, 0),
    citationLethalitySum: toNumber(row.citation_lethality_sum, 0),
  })),
  pagination: mapPagination(payload.meta),
});

const mapCitationCpcGroupRows = (payload: BackendSectionPayload = {}): PortfolioCitationCpcGroupsResponse => ({
  ownerId: payload.owner_id ?? "",
  rows: (payload.rows ?? []).map((row) => ({
    cpcMainGroup: String(row.cpc_main_group ?? ""),
    latestCitationYear: toNumber(row.latest_citation_year, 0),
    citationEventCount: toNumber(row.citation_event_count, 0),
    cleanCitationCount: toNumber(row.clean_citation_count, 0),
    citationLethalitySum: toNumber(row.citation_lethality_sum, 0),
    citedFamilyCount: toNumber(row.cited_family_count, 0),
  })),
  pagination: mapPagination(payload.meta),
});

const mapFilingTimeseriesRows = (payload: BackendSectionPayload = {}): PortfolioFilingTimeseriesResponse => ({
  ownerId: payload.owner_id ?? "",
  rows: (payload.rows ?? [])
    .map<PortfolioFilingTimeseriesPoint>((row) => ({
      year: toNumber(row.year, 0),
      familyFilingCount: toNumber(row.family_filing_count, 0),
      cumulativeFamilyCount: toNumber(row.cumulative_family_count, 0),
      rolling3yFamilyFilingCount: toNumber(row.rolling_3y_family_filing_count, 0),
      prior3yFamilyFilingCount: toNumber(row.prior_3y_family_filing_count, 0),
      rolling3yChangePct: toNumber(row.rolling_3y_change_pct, 0),
      momentumDirection: parseMomentumDirection(row.momentum_direction),
    }))
    .filter((row) => row.year > 0)
    .sort((left, right) => left.year - right.year),
});

const mapStatusTimeseriesRows = (payload: BackendSectionPayload = {}): PortfolioStatusTimeseriesResponse => ({
  ownerId: payload.owner_id ?? "",
  rows: (payload.rows ?? [])
    .map((row) => ({
      year: toNumber(row.as_of_year, 0),
      familyCount: toNumber(row.family_count, 0),
      pendingFamilyCount: toNumber(row.pending_family_count, 0),
      fullyActiveFamilyCount: toNumber(row.fully_active_family_count, 0),
      underFireFamilyCount: toNumber(row.under_fire_family_count, 0),
      partiallyLapsedFamilyCount: toNumber(row.partially_lapsed_family_count, 0),
      deadFamilyCount: toNumber(row.dead_family_count, 0),
      pendingShare: toNumber(row.pending_share, 0),
      fullyActiveShare: toNumber(row.fully_active_share, 0),
      underFireShare: toNumber(row.under_fire_share, 0),
      partiallyLapsedShare: toNumber(row.partially_lapsed_share, 0),
      deadShare: toNumber(row.dead_share, 0),
      statusCoveragePct: toNumber(row.status_coverage_pct, 0),
      historicalOwnerTruthSupportedPct: toNumber(row.historical_owner_truth_supported_pct, 0),
      currentOwnerMetadataOnlyPct: toNumber(row.current_owner_metadata_only_pct, 0),
      avgDataCompletenessPctAsOf: toNumber(row.avg_data_completeness_pct_asof, 0),
    }))
    .filter((row) => row.year > 0)
    .sort((left, right) => left.year - right.year),
  audit: mapHistoryAudit(payload.meta),
});

const mapJurisdictionUnlockRows = (payload: BackendSectionPayload = {}): PortfolioJurisdictionUnlockHistoryResponse => {
  const rows = payload.rows ?? [];
  const summaryRow = rows.find((row) => row.kind === "summary");
  return {
    ownerId: payload.owner_id ?? "",
    summary: summaryRow
      ? {
          unlockedJurisdictionCount: toNumber(summaryRow.unlocked_jurisdiction_count, 0),
          firstUnlockYear: toNumber(summaryRow.first_unlock_year, 0),
          latestUnlockYear: toNumber(summaryRow.latest_unlock_year, 0),
          latestPresenceYear: toNumber(summaryRow.latest_presence_year, 0),
          latestActiveJurisdictionCount: toNumber(summaryRow.latest_active_jurisdiction_count, 0),
          latestPendingJurisdictionCount: toNumber(summaryRow.latest_pending_jurisdiction_count, 0),
          latestLapsedJurisdictionCount: toNumber(summaryRow.latest_lapsed_jurisdiction_count, 0),
          everActiveJurisdictionCount: toNumber(summaryRow.ever_active_jurisdiction_count, 0),
        }
      : null,
    years: rows
      .filter((row) => row.kind === "year")
      .map((row) => ({
        year: toNumber(row.as_of_year, 0),
        unlockedJurisdictionCount: toNumber(row.unlocked_jurisdiction_count, 0),
        cumulativeUnlockedJurisdictionCount: toNumber(row.cumulative_unlocked_jurisdiction_count, 0),
        activeUnlockCount: toNumber(row.active_unlock_count, 0),
        pendingUnlockCount: toNumber(row.pending_unlock_count, 0),
        lapsedOnlyUnlockCount: toNumber(row.lapsed_only_unlock_count, 0),
        activeJurisdictionCount: toNumber(row.active_jurisdiction_count, 0),
        pendingJurisdictionCount: toNumber(row.pending_jurisdiction_count, 0),
        lapsedJurisdictionCount: toNumber(row.lapsed_jurisdiction_count, 0),
        unlockedJurisdictions: Array.isArray(row.unlocked_jurisdictions)
          ? row.unlocked_jurisdictions.map((value) => String(value))
          : [],
      }))
      .filter((row) => row.year > 0)
      .sort((left, right) => left.year - right.year),
    jurisdictions: rows
      .filter((row) => row.kind === "jurisdiction")
      .map((row) => ({
        jurisdictionCode: String(row.jurisdiction_code ?? ""),
        firstUnlockYear: toNumber(row.first_unlock_year, 0),
        firstUnlockBasis: String(row.first_unlock_basis ?? "tracked") as "active" | "pending" | "lapsed_only" | "tracked",
        firstActiveYear: toNumber(row.first_active_year, 0),
        firstPendingYear: toNumber(row.first_pending_year, 0),
        firstLapsedYear: toNumber(row.first_lapsed_year, 0),
        trackedFamilyCount: toNumber(row.tracked_family_count, 0),
        activeFamilyCount: toNumber(row.active_family_count, 0),
        pendingFamilyCount: toNumber(row.pending_family_count, 0),
        lapsedFamilyCount: toNumber(row.lapsed_family_count, 0),
      }))
      .filter((row) => row.jurisdictionCode.length > 0),
    audit: mapHistoryAudit(payload.meta),
  };
};

const mapMarketContextRows = (payload: BackendSectionPayload = {}): PortfolioMarketContextResponse => {
  const rows = payload.rows ?? [];
  const summaryRow = rows.find((row) => row.kind === "summary");
  const segments = rows
    .filter((row) => row.kind === "segment")
    .map((row) => ({
      horizon: String(row.horizon ?? "3y") as "3y" | "5y",
      wipoField: String(row.wipo_field ?? ""),
      predictedDirectionBand: String(row.predicted_direction_band ?? "stable"),
      supportLevel: parseSupportLevel(row.support_level),
      predictedGrowthRateReference: toNumber(row.predicted_growth_rate_reference, 0),
      predictedCountReference: toNumber(row.predicted_count_reference, 0),
      activeFamilyCount: toNumber(row.portfolio_active_family_count_in_field, 0),
    }));

  return {
    ownerId: payload.owner_id ?? "",
    summary: summaryRow
      ? {
          horizon: String(summaryRow.horizon ?? "3y") as "3y" | "5y",
          heatingMarketExposureCount: toNumber(summaryRow.heating_market_exposure_count, 0),
          coolingMarketExposureCount: toNumber(summaryRow.cooling_market_exposure_count, 0),
          hotspotCoveragePct: toNumber(summaryRow.hotspot_coverage_pct, 0),
        }
      : null,
    segments,
  };
};

const mapForecastContributorsRows = (payload: BackendSectionPayload = {}): PortfolioForecastContributorsResponse => ({
  ownerId: payload.owner_id ?? "",
  rows: (payload.rows ?? []).map((row) => ({
    contributorScope: String(row.contributor_scope ?? ""),
    horizon: String(row.horizon ?? "3y") as "3y" | "5y",
    contributorEntityId: String(row.contributor_entity_id ?? ""),
    jurisdictionCode: String(row.jurisdiction_code ?? ""),
    contributionValue: toNumber(row.contribution_value, 0),
    contributionShare: toNumber(row.contribution_share, 0),
    contributorRank: toNumber(row.contributor_rank, 0),
  })),
  pagination: mapPagination(payload.meta),
});

const mapCompareTimesliceRows = (payload: BackendSectionPayload = {}): PortfolioCompareTimesliceResponse => ({
  ownerId: payload.owner_id ?? "",
  rows: (payload.rows ?? []).map((row) => ({
    metric: String(row.metric ?? ""),
    label: String(row.label ?? ""),
    currentValue: toNumber(row.current_value, 0),
    compareValue: toNumber(row.compare_value, 0),
    currentScore: toNumber(row.current_score, 0),
    compareScore: toNumber(row.compare_score, 0),
    currentYear: toNumber(row.current_year, 0),
    compareYear: toNumber(row.compare_year, 0),
    delta: toNumber(row.delta, 0),
  })),
});

const mapPendingGrantRows = (payload: BackendSectionPayload = {}): PortfolioPendingGrantResponse => ({
  ownerId: payload.owner_id ?? "",
  rows: (payload.rows ?? []).map((row) => ({
    kind: String(row.kind ?? "summary") as "summary" | "jurisdiction" | "field" | "branch",
    featureStatus: row.feature_status != null ? String(row.feature_status) : undefined,
    servingReady: row.serving_ready != null ? Boolean(row.serving_ready) : undefined,
    horizon: row.horizon != null ? String(row.horizon) : undefined,
    recommendedOutput: row.recommended_output != null ? String(row.recommended_output) : undefined,
    probabilityHeadlineAllowed:
      row.probability_headline_allowed != null ? Boolean(row.probability_headline_allowed) : undefined,
    reason: row.reason != null ? String(row.reason) : undefined,
    observedRocAuc: row.observed_roc_auc != null ? toNumber(row.observed_roc_auc, 0) : undefined,
    observedPrAuc: row.observed_pr_auc != null ? toNumber(row.observed_pr_auc, 0) : undefined,
    pendingPipelineBranchCount:
      row.pending_pipeline_branch_count != null ? toNumber(row.pending_pipeline_branch_count, 0) : undefined,
    pendingPipelineFamilyCount:
      row.pending_pipeline_family_count != null ? toNumber(row.pending_pipeline_family_count, 0) : undefined,
    currentPendingBranchCount:
      row.current_pending_branch_count != null ? toNumber(row.current_pending_branch_count, 0) : undefined,
    currentPendingFamilyCount:
      row.current_pending_family_count != null ? toNumber(row.current_pending_family_count, 0) : undefined,
    pendingPipelineBranchCoveragePct:
      row.pending_pipeline_branch_coverage_pct != null
        ? toNumber(row.pending_pipeline_branch_coverage_pct, 0)
        : undefined,
    pendingPipelineFamilyCoveragePct:
      row.pending_pipeline_family_coverage_pct != null
        ? toNumber(row.pending_pipeline_family_coverage_pct, 0)
        : undefined,
    pendingPipelineExpectedLikelyGrants12m:
      row.pending_pipeline_expected_likely_grants_12m != null
        ? toNumber(row.pending_pipeline_expected_likely_grants_12m, 0)
        : undefined,
    pendingPipelineExpectedLikelyGrants24m:
      row.pending_pipeline_expected_likely_grants_24m != null
        ? toNumber(row.pending_pipeline_expected_likely_grants_24m, 0)
        : undefined,
    pendingPipelineAvgProbability12m:
      row.pending_pipeline_avg_probability_12m != null
        ? toNumber(row.pending_pipeline_avg_probability_12m, 0)
        : undefined,
    pendingPipelineAvgProbability24m:
      row.pending_pipeline_avg_probability_24m != null
        ? toNumber(row.pending_pipeline_avg_probability_24m, 0)
        : undefined,
    pendingPipelinePercentile:
      row.pending_pipeline_percentile != null ? toNumber(row.pending_pipeline_percentile, 0) : undefined,
    pendingPipelinePriorityTier:
      row.pending_pipeline_priority_tier != null ? String(row.pending_pipeline_priority_tier) : undefined,
    pendingPipelineSupportLevel:
      row.pending_pipeline_support_level != null ? String(row.pending_pipeline_support_level) : undefined,
    pendingPipelineTopJurisdiction:
      row.pending_pipeline_top_jurisdiction != null ? String(row.pending_pipeline_top_jurisdiction) : undefined,
    pendingPipelineTopField: row.pending_pipeline_top_field != null ? String(row.pending_pipeline_top_field) : undefined,
    topBranchFamilyId: row.top_branch_family_id != null ? String(row.top_branch_family_id) : undefined,
    topBranchJurisdiction: row.top_branch_jurisdiction != null ? String(row.top_branch_jurisdiction) : undefined,
    topBranchField: row.top_branch_field != null ? String(row.top_branch_field) : undefined,
    topBranchProbability: row.top_branch_probability != null ? toNumber(row.top_branch_probability, 0) : undefined,
    topBranchPercentile: row.top_branch_percentile != null ? toNumber(row.top_branch_percentile, 0) : undefined,
    jurisdictionCode: row.jurisdiction_code != null ? String(row.jurisdiction_code) : undefined,
    wipoField: row.wipo_field != null ? String(row.wipo_field) : undefined,
    officeSupportLevel: row.office_support_level != null ? String(row.office_support_level) : undefined,
    branchCount: row.branch_count != null ? toNumber(row.branch_count, 0) : undefined,
    familyCount: row.family_count != null ? toNumber(row.family_count, 0) : undefined,
    avgProbability12m: row.avg_probability_12m != null ? toNumber(row.avg_probability_12m, 0) : undefined,
    avgProbability24m: row.avg_probability_24m != null ? toNumber(row.avg_probability_24m, 0) : undefined,
    expectedLikelyGrants12m:
      row.expected_likely_grants_12m != null ? toNumber(row.expected_likely_grants_12m, 0) : undefined,
    expectedLikelyGrants24m:
      row.expected_likely_grants_24m != null ? toNumber(row.expected_likely_grants_24m, 0) : undefined,
    avgPercentile: row.avg_percentile != null ? toNumber(row.avg_percentile, 0) : undefined,
    docdbFamilyId: row.docdb_family_id != null ? String(row.docdb_family_id) : undefined,
    primaryWipoField: row.primary_wipo_field != null ? String(row.primary_wipo_field) : undefined,
    pendingAgeYears: row.pending_age_years != null ? toNumber(row.pending_age_years, 0) : undefined,
    familyAgeYears: row.family_age_years != null ? toNumber(row.family_age_years, 0) : undefined,
    familyBlockingPowerScore:
      row.family_blocking_power_score_asof != null ? toNumber(row.family_blocking_power_score_asof, 0) : undefined,
    familyEnforceabilityScore:
      row.family_enforceability_score_asof != null ? toNumber(row.family_enforceability_score_asof, 0) : undefined,
    familyRcfScore: row.family_rcf_score_asof != null ? toNumber(row.family_rcf_score_asof, 0) : undefined,
    dataCompletenessPct:
      row.data_completeness_pct_asof != null ? toNumber(row.data_completeness_pct_asof, 0) : undefined,
    probability12m: row.probability_12m != null ? toNumber(row.probability_12m, 0) : undefined,
    probability24m: row.probability_24m != null ? toNumber(row.probability_24m, 0) : undefined,
    selectedProbability: row.selected_probability != null ? toNumber(row.selected_probability, 0) : undefined,
    rankWithinOfficeHorizon:
      row.rank_within_office_horizon != null ? toNumber(row.rank_within_office_horizon, 0) : undefined,
    percentileWithinOfficeHorizon:
      row.percentile_within_office_horizon != null ? toNumber(row.percentile_within_office_horizon, 0) : undefined,
    priorityTier: row.priority_tier != null ? String(row.priority_tier) : undefined,
  })),
});

export async function fetchPortfolioDashboard(ownerId: string): Promise<PortfolioDashboardPayload> {
  const [
    overviewResult,
    familiesResult,
    fieldsResult,
    forecast3Result,
    forecast5Result,
    threatsResult,
  ] = await Promise.allSettled([
    fetchJson<BackendOverview>(`/api/v1/portfolios/${ownerId}/overview`),
    fetchJson<BackendFamiliesPayload>(`/api/v1/portfolios/${ownerId}/families?limit=10&offset=0`),
    fetchJson<BackendFieldsPayload>(`/api/v1/portfolios/${ownerId}/fields`),
    fetchJson<BackendForecast>(`/api/v1/portfolios/${ownerId}/forecast?horizon=3y`),
    fetchJson<BackendForecast>(`/api/v1/portfolios/${ownerId}/forecast?horizon=5y`),
    fetchJson<BackendThreatPayload>(`/api/v1/portfolios/${ownerId}/threats`),
  ]);

  if (overviewResult.status === "rejected") {
    const detail = overviewResult.reason instanceof Error ? overviewResult.reason.message : "Could not load portfolio overview.";
    throw new Error(`${detail} Frontend API base is ${getApiBaseUrl()}.`);
  }

  const overview = overviewResult.value;
  const families = familiesResult.status === "fulfilled" ? familiesResult.value : { owner_id: ownerId, rows: [] };
  const fields = fieldsResult.status === "fulfilled" ? fieldsResult.value : { owner_id: ownerId, rows: [] };
  const forecast3y = forecast3Result;
  const forecast5y = forecast5Result;
  const forecastSections: BackendForecast["sections"] = [
    ...(forecast3y.status === "fulfilled" ? forecast3y.value.sections ?? [] : []),
    ...(forecast5y.status === "fulfilled" ? forecast5y.value.sections ?? [] : []),
  ];
  const threatsPayload = threatsResult.status === "fulfilled" ? threatsResult.value : { owner_id: ownerId, rows: [] };

  const mapped = {
    overview: mapOverview(overview),
    families: mapFamilyRows(families),
    fields: mapFieldRows(fields),
    threats: mapThreatRows(threatsPayload),
    classification: emptyClassificationResponse(ownerId),
    forecast: mapForecastFromSections(forecastSections),
  };

  mapped.families.ownerId = ownerId;
  mapped.families.rows = mapped.families.rows.length ? mapped.families.rows : [];

  mapped.fields.ownerId = ownerId;
  mapped.fields.rows = mapped.fields.rows.length ? mapped.fields.rows : [];

  mapped.overview.identity.id = ownerId;
  mapped.overview.identity.label = overview.identity?.label ?? ownerLabelFromId(ownerId);

  mapped.threats.ownerId = ownerId;
  mapped.threats.rows = mapped.threats.rows.length ? mapped.threats.rows : [];

  mapped.classification.ownerId = ownerId;
  mapped.classification.rows = mapped.classification.rows.length ? mapped.classification.rows : [];
  mapped.classification.timeseries = mapped.classification.timeseries.length ? mapped.classification.timeseries : [];

  return mapped;
}

export async function fetchPortfolioOverview(ownerId: string): Promise<PortfolioOverviewPayload> {
  const payload = await fetchJson<BackendOverview>(`/api/v1/portfolios/${ownerId}/overview`);
  return mapOverview(payload);
}

export async function fetchPortfolioFamilies(
  ownerId: string,
  query: PortfolioFamiliesQuery = {},
): Promise<PortfolioFamiliesResponse> {
  const params = new URLSearchParams();
  params.set("limit", String(query.limit ?? 10));
  params.set("offset", String(query.offset ?? 0));
  if (query.q) {
    params.set("q", query.q);
  }
  if (query.status) {
    params.set("status", query.status);
  }
  if (query.primaryField) {
    params.set("primary_field", query.primaryField);
  }
  if (query.sort) {
    params.set("sort", query.sort);
  }
  const payload = await fetchJson<BackendFamiliesPayload>(`/api/v1/portfolios/${ownerId}/families?${params.toString()}`);
  return mapFamilyRows(payload);
}

export async function fetchPortfolioFields(ownerId: string): Promise<PortfolioFieldRowsResponse> {
  const payload = await fetchJson<BackendFieldsPayload>(`/api/v1/portfolios/${ownerId}/fields`);
  return mapFieldRows(payload);
}

export async function fetchPortfolioForecast(ownerId: string): Promise<PortfolioForecastPayload> {
  const [forecast3, forecast5] = await Promise.all([
    fetchJson<BackendForecast>(`/api/v1/portfolios/${ownerId}/forecast?horizon=3y`),
    fetchJson<BackendForecast>(`/api/v1/portfolios/${ownerId}/forecast?horizon=5y`),
  ]);
  return mapForecastFromSections([...(forecast3.sections ?? []), ...(forecast5.sections ?? [])]);
}

export async function fetchPortfolioThreats(
  ownerId: string,
  query: PortfolioThreatQuery = {},
): Promise<PortfolioThreatsResponse> {
  const params = new URLSearchParams();
  params.set("limit", String(query.limit ?? 10));
  params.set("offset", String(query.offset ?? 0));
  if (query.wipoField) {
    params.set("wipo_field", query.wipoField);
  }
  const payload = await fetchJson<BackendThreatPayload>(`/api/v1/portfolios/${ownerId}/threats?${params.toString()}`);
  return mapThreatRows(payload);
}

export async function fetchPortfolioClassification(
  ownerId: string,
  query: PortfolioClassificationQuery = {},
): Promise<PortfolioClassificationResponse> {
  const params = new URLSearchParams();
  params.set("limit", String(query.limit ?? 10));
  params.set("offset", String(query.offset ?? 0));
  params.set("classification_type", query.classificationType ?? "CPC_MAIN_GROUP");
  params.set("timeseries_fields", String(query.timeseriesFields ?? 6));
  if (query.wipoField) {
    params.set("wipo_field", query.wipoField);
  }
  const payload = await fetchJson<BackendClassificationPayload>(
    `/api/v1/portfolios/${ownerId}/classification?${params.toString()}`,
  );
  return mapClassificationRows(payload);
}

export async function fetchPortfolioFieldTimeseries(
  ownerId: string,
  query: PortfolioFieldTimeseriesQuery = {},
): Promise<PortfolioFieldTimeseriesResponse> {
  const params = new URLSearchParams();
  params.set("limit_fields", String(query.limitFields ?? 8));
  if (query.asOfYear != null) {
    params.set("as_of_year", String(query.asOfYear));
  }
  const payload = await fetchJson<BackendSectionPayload>(
    `/api/v1/portfolios/${ownerId}/field-timeseries?${params.toString()}`,
  );
  return mapFieldTimeseriesRows(payload);
}

export async function fetchPortfolioCitationSummary(
  ownerId: string,
  query: PortfolioCitationSummaryQuery = {},
): Promise<PortfolioCitationSummaryResponse> {
  const params = new URLSearchParams();
  if (query.asOfYear != null) {
    params.set("as_of_year", String(query.asOfYear));
  }
  const suffix = params.toString();
  const payload = await fetchJson<BackendSectionPayload>(
    `/api/v1/portfolios/${ownerId}/citation-summary${suffix ? `?${suffix}` : ""}`,
  );
  return mapCitationSummaryRows(payload);
}

export async function fetchPortfolioCitationTimeseries(
  ownerId: string,
  query: PortfolioCitationTimeseriesQuery = {},
): Promise<PortfolioCitationTimeseriesResponse> {
  const params = new URLSearchParams();
  if (query.yearFrom != null) {
    params.set("year_from", String(query.yearFrom));
  }
  if (query.yearTo != null) {
    params.set("year_to", String(query.yearTo));
  }
  const suffix = params.toString();
  const payload = await fetchJson<BackendSectionPayload>(
    `/api/v1/portfolios/${ownerId}/citation-timeseries${suffix ? `?${suffix}` : ""}`,
  );
  return mapCitationTimeseriesRows(payload);
}

export async function fetchPortfolioCitationFamilies(
  ownerId: string,
  query: PortfolioCitationFamiliesQuery = {},
): Promise<PortfolioCitationFamiliesResponse> {
  const params = new URLSearchParams();
  params.set("limit", String(query.limit ?? 10));
  params.set("offset", String(query.offset ?? 0));
  if (query.wipoField) {
    params.set("wipo_field", query.wipoField);
  }
  if (query.status) {
    params.set("status", query.status);
  }
  if (query.sort) {
    params.set("sort", query.sort);
  }
  const payload = await fetchJson<BackendSectionPayload>(`/api/v1/portfolios/${ownerId}/citation-families?${params.toString()}`);
  return mapCitationFamilyRows(payload);
}

export async function fetchPortfolioCitationAttackers(
  ownerId: string,
  query: PortfolioCitationAttackersQuery = {},
): Promise<PortfolioCitationAttackersResponse> {
  const params = new URLSearchParams();
  params.set("limit", String(query.limit ?? 10));
  params.set("offset", String(query.offset ?? 0));
  if (query.wipoField) {
    params.set("wipo_field", query.wipoField);
  }
  if (query.jurisdictionCode) {
    params.set("jurisdiction_code", query.jurisdictionCode);
  }
  if (query.yearFrom != null) {
    params.set("year_from", String(query.yearFrom));
  }
  if (query.yearTo != null) {
    params.set("year_to", String(query.yearTo));
  }
  const payload = await fetchJson<BackendSectionPayload>(
    `/api/v1/portfolios/${ownerId}/citation-attackers?${params.toString()}`,
  );
  return mapCitationAttackerRows(payload);
}

export async function fetchPortfolioCitationFields(
  ownerId: string,
  query: PortfolioCitationFieldsQuery = {},
): Promise<PortfolioCitationFieldsResponse> {
  const params = new URLSearchParams();
  params.set("limit", String(query.limit ?? 10));
  params.set("offset", String(query.offset ?? 0));
  if (query.jurisdictionCode) {
    params.set("jurisdiction_code", query.jurisdictionCode);
  }
  if (query.yearFrom != null) {
    params.set("year_from", String(query.yearFrom));
  }
  if (query.yearTo != null) {
    params.set("year_to", String(query.yearTo));
  }
  const payload = await fetchJson<BackendSectionPayload>(
    `/api/v1/portfolios/${ownerId}/citation-fields?${params.toString()}`,
  );
  return mapCitationFieldRows(payload);
}

export async function fetchPortfolioCitationJurisdictions(
  ownerId: string,
  query: PortfolioCitationJurisdictionsQuery = {},
): Promise<PortfolioCitationJurisdictionsResponse> {
  const params = new URLSearchParams();
  params.set("limit", String(query.limit ?? 10));
  params.set("offset", String(query.offset ?? 0));
  if (query.wipoField) {
    params.set("wipo_field", query.wipoField);
  }
  if (query.yearFrom != null) {
    params.set("year_from", String(query.yearFrom));
  }
  if (query.yearTo != null) {
    params.set("year_to", String(query.yearTo));
  }
  const payload = await fetchJson<BackendSectionPayload>(
    `/api/v1/portfolios/${ownerId}/citation-jurisdictions?${params.toString()}`,
  );
  return mapCitationJurisdictionRows(payload);
}

export async function fetchPortfolioCitationCpcGroups(
  ownerId: string,
  query: PortfolioCitationCpcGroupsQuery = {},
): Promise<PortfolioCitationCpcGroupsResponse> {
  const params = new URLSearchParams();
  params.set("limit", String(query.limit ?? 10));
  params.set("offset", String(query.offset ?? 0));
  if (query.wipoField) {
    params.set("wipo_field", query.wipoField);
  }
  if (query.jurisdictionCode) {
    params.set("jurisdiction_code", query.jurisdictionCode);
  }
  if (query.yearFrom != null) {
    params.set("year_from", String(query.yearFrom));
  }
  if (query.yearTo != null) {
    params.set("year_to", String(query.yearTo));
  }
  const payload = await fetchJson<BackendSectionPayload>(
    `/api/v1/portfolios/${ownerId}/citation-cpc-groups?${params.toString()}`,
  );
  return mapCitationCpcGroupRows(payload);
}

export async function fetchPortfolioMarketContext(
  ownerId: string,
  query: PortfolioMarketContextQuery = {},
): Promise<PortfolioMarketContextResponse> {
  const params = new URLSearchParams();
  params.set("horizon", String(query.horizon ?? "3y"));
  if (query.asOfYear != null) {
    params.set("as_of_year", String(query.asOfYear));
  }
  const payload = await fetchJson<BackendSectionPayload>(
    `/api/v1/portfolios/${ownerId}/market-context?${params.toString()}`,
  );
  return mapMarketContextRows(payload);
}

export async function fetchPortfolioFilingTimeseries(
  ownerId: string,
  query: PortfolioFilingTimeseriesQuery = {},
): Promise<PortfolioFilingTimeseriesResponse> {
  const params = new URLSearchParams();
  if (query.yearFrom != null) {
    params.set("year_from", String(query.yearFrom));
  }
  if (query.yearTo != null) {
    params.set("year_to", String(query.yearTo));
  }
  const suffix = params.toString();
  const payload = await fetchJson<BackendSectionPayload>(
    `/api/v1/portfolios/${ownerId}/filing-timeseries${suffix ? `?${suffix}` : ""}`,
  );
  return mapFilingTimeseriesRows(payload);
}

export async function fetchPortfolioStatusTimeseries(
  ownerId: string,
  query: { yearFrom?: number; yearTo?: number } = {},
): Promise<PortfolioStatusTimeseriesResponse> {
  const params = new URLSearchParams();
  if (query.yearFrom != null) {
    params.set("year_from", String(query.yearFrom));
  }
  if (query.yearTo != null) {
    params.set("year_to", String(query.yearTo));
  }
  const suffix = params.toString();
  const payload = await fetchJson<BackendSectionPayload>(
    `/api/v1/portfolios/${ownerId}/status-timeseries${suffix ? `?${suffix}` : ""}`,
  );
  return mapStatusTimeseriesRows(payload);
}

export async function fetchPortfolioJurisdictionUnlockHistory(
  ownerId: string,
  query: { yearFrom?: number; yearTo?: number; jurisdictionLimit?: number } = {},
): Promise<PortfolioJurisdictionUnlockHistoryResponse> {
  const params = new URLSearchParams();
  if (query.yearFrom != null) {
    params.set("year_from", String(query.yearFrom));
  }
  if (query.yearTo != null) {
    params.set("year_to", String(query.yearTo));
  }
  if (query.jurisdictionLimit != null) {
    params.set("jurisdiction_limit", String(query.jurisdictionLimit));
  }
  const suffix = params.toString();
  const payload = await fetchJson<BackendSectionPayload>(
    `/api/v1/portfolios/${ownerId}/jurisdiction-unlocks${suffix ? `?${suffix}` : ""}`,
  );
  return mapJurisdictionUnlockRows(payload);
}

export async function fetchPortfolioForecastContributors(
  ownerId: string,
  query: PortfolioForecastContributorsQuery = {},
): Promise<PortfolioForecastContributorsResponse> {
  const params = new URLSearchParams();
  params.set("horizon", String(query.horizon ?? "3y"));
  params.set("contributor_scope", String(query.contributorScope ?? "phase03_future_citations"));
  params.set("limit", String(query.limit ?? 10));
  params.set("offset", String(query.offset ?? 0));
  const payload = await fetchJson<BackendSectionPayload>(
    `/api/v1/portfolios/${ownerId}/forecast-contributors?${params.toString()}`,
  );
  return mapForecastContributorsRows(payload);
}

export async function fetchPortfolioCompareTimeslice(
  ownerId: string,
  query: PortfolioCompareTimesliceQuery = {},
): Promise<PortfolioCompareTimesliceResponse> {
  const params = new URLSearchParams();
  if (query.baseYear != null) {
    params.set("base_year", String(query.baseYear));
  }
  if (query.compareYear != null) {
    params.set("compare_year", String(query.compareYear));
  }
  const suffix = params.toString();
  const payload = await fetchJson<BackendSectionPayload>(
    `/api/v1/portfolios/${ownerId}/compare-timeslice${suffix ? `?${suffix}` : ""}`,
  );
  return mapCompareTimesliceRows(payload);
}

export async function fetchPortfolioPendingGrants(
  ownerId: string,
  query: PortfolioPendingGrantsQuery = {},
): Promise<PortfolioPendingGrantResponse> {
  const params = new URLSearchParams();
  params.set("horizon", String(query.horizon ?? "24m"));
  if (query.branchJurisdictionCode) {
    params.set("branch_jurisdiction_code", query.branchJurisdictionCode);
  }
  if (query.branchWipoField) {
    params.set("branch_wipo_field", query.branchWipoField);
  }
  if (query.branchLimit != null) {
    params.set("branch_limit", String(query.branchLimit));
  }
  const payload = await fetchJson<BackendSectionPayload>(
    `/api/v1/portfolios/${ownerId}/pending-grants?${params.toString()}`,
  );
  return mapPendingGrantRows(payload);
}

export async function fetchPortfolioOwnerSuggestions(
  query: string,
  limit = 8,
  signal?: AbortSignal,
): Promise<PortfolioOwnerSearchPayload> {
  const trimmed = query.trim();
  if (trimmed.length < 2) {
    return { query: trimmed, rows: [] };
  }

  const payload = await fetchJson<BackendOwnerSearchPayload>(
    `/api/v1/portfolios/search?query=${encodeURIComponent(trimmed)}&limit=${limit}`,
    { signal },
  );
  return mapOwnerSuggestions(payload);
}
