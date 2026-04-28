import { fetchJson } from "@/lib/api/core";
import type {
  CompareFieldOverlapRow,
  CompareIdentity,
  CompareIdentityContext,
  CompareMeta,
  CompareMetricRow,
  CompareForecastRow,
  FamilyCompareSuggestion,
  CompareSupportRow,
  CompareScopeLookup,
  CompareTimesliceOptions,
  FamilyCompareLensRow,
  FamilyComparePayload,
  PortfolioCompareLensRow,
  PortfolioComparePayload,
  PortfolioCompareTopFamilyRow,
} from "@/lib/types/compare-v2";
import type { SupportLevel } from "@/lib/types/common";

type BackendIdentity = {
  id?: string;
  label?: string;
  page_kind?: string;
};

type BackendCaveat = {
  code?: string;
  title?: string;
  detail?: string;
};

type BackendMeta = {
  page?: string;
  support_level?: "strong" | "moderate" | "limited" | "candidate_only";
  artifact_sources?: string[];
  caveats?: BackendCaveat[];
};

type BackendComparePayload = {
  compare_kind?: string;
  compare_mode?: "entity" | "timeslice";
  left_entity?: BackendIdentity | null;
  right_entity?: BackendIdentity | null;
  rows?: Array<Record<string, unknown>>;
  identity_context?: Array<Record<string, unknown>>;
  summary_cards?: Array<Record<string, unknown>>;
  contrast_rows?: Array<Record<string, unknown>>;
  field_overlap_rows?: Array<Record<string, unknown>>;
  forecast_rows?: Array<Record<string, unknown>>;
  support_rows?: Array<Record<string, unknown>>;
  meta?: BackendMeta;
};

type BackendTimesliceOptionsPayload = {
  entity_id?: string;
  available_years?: unknown[];
  compare_safe_years?: unknown[];
  default_base_year?: unknown;
  default_compare_year?: unknown;
};

type BackendScopeLookupPayload = {
  compare_kind?: string;
  entity_id?: string;
  label?: unknown;
  in_scope?: unknown;
  primary_field?: unknown;
  status?: unknown;
  family_count?: unknown;
  timeslice_available?: unknown;
  default_base_year?: unknown;
  default_compare_year?: unknown;
  note?: unknown;
};

type BackendFamilySuggestionsPayload = {
  query?: string;
  rows?: Array<Record<string, unknown>>;
};

const toNumber = (value: unknown, fallback = 0): number => {
  const candidate = Number(value);
  return Number.isFinite(candidate) ? candidate : fallback;
};

const toStringValue = (value: unknown, fallback = ""): string => {
  if (typeof value !== "string") {
    return fallback;
  }
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : fallback;
};

const toNullableString = (value: unknown): string | null => {
  const result = toStringValue(value, "");
  return result.length > 0 ? result : null;
};

const toNullableNumber = (value: unknown): number | null => {
  if (value == null) {
    return null;
  }
  const candidate = Number(value);
  return Number.isFinite(candidate) ? candidate : null;
};

const parseSupportLevel = (value: unknown): SupportLevel => {
  if (value === "strong") {
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

const mapIdentity = (payload?: BackendIdentity | null): CompareIdentity | null => {
  if (!payload?.id) {
    return null;
  }
  return {
    id: String(payload.id),
    label: String(payload.label ?? payload.id),
    pageKind: String(payload.page_kind ?? "entity"),
  };
};

const mapMeta = (payload?: BackendMeta): CompareMeta => ({
  page: String(payload?.page ?? "compare"),
  supportLevel: parseSupportLevel(payload?.support_level),
  artifactSources: (payload?.artifact_sources ?? []).map((source) => String(source)),
  caveats: (payload?.caveats ?? []).map((caveat) => ({
    code: String(caveat.code ?? "unknown"),
    title: String(caveat.title ?? "Caveat"),
    detail: String(caveat.detail ?? ""),
  })),
});

const mapIdentityContext = (row: Record<string, unknown>): CompareIdentityContext => ({
  side: row.side === "right" ? "right" : "left",
  title: String(row.title ?? "Entity"),
  subtitle: toNullableString(row.subtitle),
  badges: Array.isArray(row.badges) ? row.badges.map((badge) => String(badge)) : [],
  href: toNullableString(row.href),
});

const mapMetricRow = (row: Record<string, unknown>): CompareMetricRow => ({
  key: String(row.key ?? "metric"),
  label: String(row.label ?? "Metric"),
  displayKind:
    row.display_kind === "count" || row.display_kind === "percent" || row.display_kind === "text"
      ? row.display_kind
      : "decimal",
  leftValue: typeof row.left_value === "string" ? row.left_value : toNullableNumber(row.left_value),
  rightValue: typeof row.right_value === "string" ? row.right_value : toNullableNumber(row.right_value),
  deltaValue: toNullableNumber(row.delta_value),
  leftNote: toNullableString(row.left_note),
  rightNote: toNullableString(row.right_note),
  note: toNullableString(row.note),
  winner:
    row.winner === "left" || row.winner === "right" || row.winner === "tie"
      ? row.winner
      : null,
  winnerBasis: toNullableString(row.winner_basis),
});

const mapFieldOverlapRow = (row: Record<string, unknown>): CompareFieldOverlapRow => ({
  key: String(row.key ?? "field"),
  label: String(row.label ?? "Field"),
  leftShare: toNumber(row.left_share),
  rightShare: toNumber(row.right_share),
  overlapShare: toNumber(row.overlap_share),
  leftRank: toNullableNumber(row.left_rank),
  rightRank: toNullableNumber(row.right_rank),
  presence:
    row.presence === "left_only" || row.presence === "right_only" || row.presence === "empty"
      ? row.presence
      : "shared",
  leftNote: toNullableString(row.left_note),
  rightNote: toNullableString(row.right_note),
});

const mapForecastRow = (row: Record<string, unknown>): CompareForecastRow => ({
  key: String(row.key ?? "forecast"),
  label: String(row.label ?? "Forecast"),
  displayKind: row.display_kind === "count" || row.display_kind === "percent" ? row.display_kind : "decimal",
  leftValue: toNullableNumber(row.left_value),
  rightValue: toNullableNumber(row.right_value),
  leftRangeLow: toNullableNumber(row.left_range_low),
  leftRangeHigh: toNullableNumber(row.left_range_high),
  rightRangeLow: toNullableNumber(row.right_range_low),
  rightRangeHigh: toNullableNumber(row.right_range_high),
  leftNote: toNullableString(row.left_note),
  rightNote: toNullableString(row.right_note),
  overlapState: toNullableString(row.overlap_state),
  note: toNullableString(row.note),
});

const mapSupportRow = (row: Record<string, unknown>): CompareSupportRow => ({
  kind: String(row.kind ?? "support"),
  side: row.side === "right" ? "right" : "left",
  title: String(row.title ?? "Evidence"),
  subtitle: toNullableString(row.subtitle),
  badge: toNullableString(row.badge),
  primaryMetricLabel: toNullableString(row.primary_metric_label),
  primaryMetricValue: typeof row.primary_metric_value === "string" ? row.primary_metric_value : toNullableNumber(row.primary_metric_value),
  secondaryMetricLabel: toNullableString(row.secondary_metric_label),
  secondaryMetricValue:
    typeof row.secondary_metric_value === "string" ? row.secondary_metric_value : toNullableNumber(row.secondary_metric_value),
  href: toNullableString(row.href),
});

const mapFamilyLensRow = (row: Record<string, unknown>): FamilyCompareLensRow => ({
  kind: "lens",
  lens: String(row.lens ?? "lens"),
  label: String(row.label ?? "Lens"),
  metricKey: String(row.metric_key ?? ""),
  metricLabel: String(row.metric_label ?? ""),
  leftFamilyId: String(row.left_family_id ?? ""),
  leftFamilyLabel: String(row.left_family_label ?? row.left_family_id ?? ""),
  leftRawValue: toNumber(row.left_raw_value),
  leftBandCode: toNullableString(row.left_band_code),
  leftBandLabel: toNullableString(row.left_band_label),
  leftPeerPercentile: row.left_peer_percentile == null ? null : toNumber(row.left_peer_percentile),
  leftPeerCohort: toNullableString(row.left_peer_cohort),
  leftPeerCohortLabel: toNullableString(row.left_peer_cohort_label),
  rightFamilyId: String(row.right_family_id ?? ""),
  rightFamilyLabel: String(row.right_family_label ?? row.right_family_id ?? ""),
  rightRawValue: toNumber(row.right_raw_value),
  rightBandCode: toNullableString(row.right_band_code),
  rightBandLabel: toNullableString(row.right_band_label),
  rightPeerPercentile: row.right_peer_percentile == null ? null : toNumber(row.right_peer_percentile),
  rightPeerCohort: toNullableString(row.right_peer_cohort),
  rightPeerCohortLabel: toNullableString(row.right_peer_cohort_label),
  sameCohort: Boolean(row.same_cohort),
  comparisonMode: String(row.comparison_mode ?? "same_cohort_percentile"),
  winner:
    row.winner === "left" || row.winner === "right" || row.winner === "tie"
      ? row.winner
      : null,
  winnerBasis: toNullableString(row.winner_basis),
});

const mapPortfolioLensRow = (row: Record<string, unknown>): PortfolioCompareLensRow => ({
  kind: "lens",
  lens: String(row.lens ?? "lens"),
  label: String(row.label ?? "Lens"),
  metricKey: String(row.metric_key ?? ""),
  metricLabel: String(row.metric_label ?? ""),
  leftOwnerId: String(row.left_owner_id ?? ""),
  leftOwnerLabel: String(row.left_owner_label ?? row.left_owner_id ?? ""),
  leftRawValue: toNumber(row.left_raw_value),
  leftBandCode: toNullableString(row.left_band_code),
  leftBandLabel: toNullableString(row.left_band_label),
  leftPeerPercentile: row.left_peer_percentile == null ? null : toNumber(row.left_peer_percentile),
  leftPeerBucket: toNullableString(row.left_peer_bucket),
  leftPeerBucketLabel: toNullableString(row.left_peer_bucket_label),
  rightOwnerId: String(row.right_owner_id ?? ""),
  rightOwnerLabel: String(row.right_owner_label ?? row.right_owner_id ?? ""),
  rightRawValue: toNumber(row.right_raw_value),
  rightBandCode: toNullableString(row.right_band_code),
  rightBandLabel: toNullableString(row.right_band_label),
  rightPeerPercentile: row.right_peer_percentile == null ? null : toNumber(row.right_peer_percentile),
  rightPeerBucket: toNullableString(row.right_peer_bucket),
  rightPeerBucketLabel: toNullableString(row.right_peer_bucket_label),
  samePeerBucket: Boolean(row.same_peer_bucket),
  comparisonMode: String(row.comparison_mode ?? "same_bucket_percentile"),
  suppressed: Boolean(row.suppressed),
  suppressionReason: toNullableString(row.suppression_reason),
  winner:
    row.winner === "left" || row.winner === "right" || row.winner === "tie"
      ? row.winner
      : null,
  winnerBasis: toNullableString(row.winner_basis),
});

const mapPortfolioTopFamilyRow = (row: Record<string, unknown>): PortfolioCompareTopFamilyRow => ({
  kind: "top_family_preview",
  side: row.side === "right" ? "right" : "left",
  ownerId: String(row.owner_id ?? ""),
  ownerLabel: String(row.owner_label ?? row.owner_id ?? ""),
  rank: toNumber(row.rank, 0),
  familyId: String(row.family_id ?? ""),
  blockingScore: toNumber(row.blocking_score),
  forecastContributor: toNumber(row.forecast_contributor),
  primaryField: toStringValue(row.primary_field, "unknown"),
  status: toStringValue(row.status, "unknown"),
});

const mapTimesliceOptions = (payload: BackendTimesliceOptionsPayload): CompareTimesliceOptions => ({
  entityId: String(payload.entity_id ?? ""),
  availableYears: (payload.available_years ?? [])
    .map((year) => toNullableNumber(year))
    .filter((year): year is number => Number.isInteger(year)),
  compareSafeYears: (payload.compare_safe_years ?? [])
    .map((year) => toNullableNumber(year))
    .filter((year): year is number => Number.isInteger(year)),
  defaultBaseYear: toNullableNumber(payload.default_base_year),
  defaultCompareYear: toNullableNumber(payload.default_compare_year),
});

const mapScopeLookup = (payload: BackendScopeLookupPayload): CompareScopeLookup => ({
  compareKind: String(payload.compare_kind ?? ""),
  entityId: String(payload.entity_id ?? ""),
  label: toNullableString(payload.label),
  inScope: Boolean(payload.in_scope),
  primaryField: toNullableString(payload.primary_field),
  status: toNullableString(payload.status),
  familyCount: toNullableNumber(payload.family_count),
  timesliceAvailable: Boolean(payload.timeslice_available),
  defaultBaseYear: toNullableNumber(payload.default_base_year),
  defaultCompareYear: toNullableNumber(payload.default_compare_year),
  note: toNullableString(payload.note),
});

export async function fetchFamilyCompare(params: {
  leftFamilyId: string;
  rightFamilyId: string;
}): Promise<FamilyComparePayload> {
  const search = new URLSearchParams({
    left_family_id: params.leftFamilyId,
    right_family_id: params.rightFamilyId,
  });
  const payload = await fetchJson<BackendComparePayload>(`/api/v1/compare/families?${search.toString()}`);
  const rows = (payload.rows ?? []).filter((row) => row.kind === "lens").map(mapFamilyLensRow);

  return {
    compareKind: String(payload.compare_kind ?? "families"),
    compareMode: payload.compare_mode === "timeslice" ? "timeslice" : "entity",
    leftEntity: mapIdentity(payload.left_entity),
    rightEntity: mapIdentity(payload.right_entity),
    identityContext: (payload.identity_context ?? []).map(mapIdentityContext),
    summaryCards: (payload.summary_cards ?? []).map(mapMetricRow),
    contrastRows: (payload.contrast_rows ?? []).map(mapMetricRow),
    fieldOverlapRows: (payload.field_overlap_rows ?? []).map(mapFieldOverlapRow),
    forecastRows: (payload.forecast_rows ?? []).map(mapForecastRow),
    supportRows: (payload.support_rows ?? []).map(mapSupportRow),
    lensRows: rows,
    meta: mapMeta(payload.meta),
  };
}

export async function fetchPortfolioCompare(params: {
  leftOwnerId: string;
  rightOwnerId: string;
  topFamilyLimit?: number;
}): Promise<PortfolioComparePayload> {
  const search = new URLSearchParams({
    left_owner_id: params.leftOwnerId,
    right_owner_id: params.rightOwnerId,
    top_family_limit: String(params.topFamilyLimit ?? 5),
  });
  const payload = await fetchJson<BackendComparePayload>(`/api/v1/compare/portfolios?${search.toString()}`);
  const rows = payload.rows ?? [];

  return {
    compareKind: String(payload.compare_kind ?? "portfolios"),
    compareMode: payload.compare_mode === "timeslice" ? "timeslice" : "entity",
    leftEntity: mapIdentity(payload.left_entity),
    rightEntity: mapIdentity(payload.right_entity),
    identityContext: (payload.identity_context ?? []).map(mapIdentityContext),
    summaryCards: (payload.summary_cards ?? []).map(mapMetricRow),
    contrastRows: (payload.contrast_rows ?? []).map(mapMetricRow),
    fieldOverlapRows: (payload.field_overlap_rows ?? []).map(mapFieldOverlapRow),
    forecastRows: (payload.forecast_rows ?? []).map(mapForecastRow),
    supportRows: (payload.support_rows ?? []).map(mapSupportRow),
    lensRows: rows.filter((row) => row.kind === "lens").map(mapPortfolioLensRow),
    topFamilyRows: rows.filter((row) => row.kind === "top_family_preview").map(mapPortfolioTopFamilyRow),
    meta: mapMeta(payload.meta),
  };
}

export async function fetchFamilyTimesliceCompare(params: {
  familyId: string;
  baseYear?: number;
  compareYear?: number;
}): Promise<FamilyComparePayload> {
  const search = new URLSearchParams({
    family_id: params.familyId,
  });
  if (params.baseYear != null) {
    search.set("base_year", String(params.baseYear));
  }
  if (params.compareYear != null) {
    search.set("compare_year", String(params.compareYear));
  }
  const payload = await fetchJson<BackendComparePayload>(`/api/v1/compare/families/timeslice?${search.toString()}`);

  return {
    compareKind: String(payload.compare_kind ?? "families"),
    compareMode: payload.compare_mode === "timeslice" ? "timeslice" : "entity",
    leftEntity: mapIdentity(payload.left_entity),
    rightEntity: mapIdentity(payload.right_entity),
    identityContext: (payload.identity_context ?? []).map(mapIdentityContext),
    summaryCards: (payload.summary_cards ?? []).map(mapMetricRow),
    contrastRows: (payload.contrast_rows ?? []).map(mapMetricRow),
    fieldOverlapRows: (payload.field_overlap_rows ?? []).map(mapFieldOverlapRow),
    forecastRows: (payload.forecast_rows ?? []).map(mapForecastRow),
    supportRows: (payload.support_rows ?? []).map(mapSupportRow),
    lensRows: [],
    meta: mapMeta(payload.meta),
  };
}

export async function fetchFamilyTimesliceOptions(familyId: string): Promise<CompareTimesliceOptions> {
  const search = new URLSearchParams({ family_id: familyId });
  const payload = await fetchJson<BackendTimesliceOptionsPayload>(`/api/v1/compare/families/timeslice/options?${search.toString()}`);
  return mapTimesliceOptions(payload);
}

export async function fetchFamilyCompareLookup(familyId: string, signal?: AbortSignal): Promise<CompareScopeLookup> {
  const search = new URLSearchParams({ family_id: familyId });
  const payload = await fetchJson<BackendScopeLookupPayload>(`/api/v1/compare/families/lookup?${search.toString()}`, { signal });
  return mapScopeLookup(payload);
}

export async function fetchFamilyCompareSuggestions(query: string, limit = 8, signal?: AbortSignal): Promise<FamilyCompareSuggestion[]> {
  const search = new URLSearchParams({ q: query, limit: String(limit) });
  const payload = await fetchJson<BackendFamilySuggestionsPayload>(`/api/v1/compare/families/suggestions?${search.toString()}`, { signal });
  return (payload.rows ?? []).map((row) => ({
    familyId: String(row.family_id ?? ""),
    label: String(row.label ?? row.family_id ?? ""),
    ownerLabel: toNullableString(row.owner_label),
    primaryField: toNullableString(row.primary_field),
    status: toNullableString(row.status),
  }));
}

export async function fetchPortfolioTimesliceOptions(ownerId: string): Promise<CompareTimesliceOptions> {
  const search = new URLSearchParams({ owner_id: ownerId });
  const payload = await fetchJson<BackendTimesliceOptionsPayload>(`/api/v1/compare/portfolios/timeslice/options?${search.toString()}`);
  return mapTimesliceOptions(payload);
}

export async function fetchPortfolioCompareLookup(ownerId: string): Promise<CompareScopeLookup> {
  const search = new URLSearchParams({ owner_id: ownerId });
  const payload = await fetchJson<BackendScopeLookupPayload>(`/api/v1/compare/portfolios/lookup?${search.toString()}`);
  return mapScopeLookup(payload);
}

export async function fetchPortfolioTimesliceCompare(params: {
  ownerId: string;
  baseYear?: number;
  compareYear?: number;
}): Promise<PortfolioComparePayload> {
  const search = new URLSearchParams({
    owner_id: params.ownerId,
  });
  if (params.baseYear != null) {
    search.set("base_year", String(params.baseYear));
  }
  if (params.compareYear != null) {
    search.set("compare_year", String(params.compareYear));
  }
  const payload = await fetchJson<BackendComparePayload>(`/api/v1/compare/portfolios/timeslice?${search.toString()}`);

  return {
    compareKind: String(payload.compare_kind ?? "portfolios"),
    compareMode: payload.compare_mode === "timeslice" ? "timeslice" : "entity",
    leftEntity: mapIdentity(payload.left_entity),
    rightEntity: mapIdentity(payload.right_entity),
    identityContext: (payload.identity_context ?? []).map(mapIdentityContext),
    summaryCards: (payload.summary_cards ?? []).map(mapMetricRow),
    contrastRows: (payload.contrast_rows ?? []).map(mapMetricRow),
    fieldOverlapRows: (payload.field_overlap_rows ?? []).map(mapFieldOverlapRow),
    forecastRows: (payload.forecast_rows ?? []).map(mapForecastRow),
    supportRows: (payload.support_rows ?? []).map(mapSupportRow),
    lensRows: [],
    topFamilyRows: [],
    meta: mapMeta(payload.meta),
  };
}
