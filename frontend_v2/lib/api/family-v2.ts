import { fetchJson } from "@/lib/api/core";

import type {
  FamilyCoverage,
  FamilyIdentity,
  FamilyMeta,
  FamilyOverviewMetric,
  FamilyOverviewPayload,
  FamilySectionPayload,
  FamilySuggestion,
  FamilySummaryCard,
} from "@/lib/types/family-v2";
import type { PortfolioPagination } from "@/lib/types/portfolio-v2";
import type { SupportLevel } from "@/lib/types/common";

type BackendIdentity = {
  id?: string;
  label?: string;
  page_kind?: string;
  selected_year?: number | null;
};

type BackendCaveat = {
  code?: string;
  title?: string;
  detail?: string;
};

type BackendCoverage = {
  status?: string;
  pct?: number | null;
  covered_count?: number | null;
  denominator_count?: number | null;
  caveat_text?: string | null;
};

type BackendPagination = {
  limit?: number;
  offset?: number;
  returned_count?: number;
  total_count?: number | null;
};

type BackendMeta = {
  page?: string;
  support_level?: "strong" | "moderate" | "limited" | "candidate_only";
  caveats?: BackendCaveat[];
  coverage?: BackendCoverage | null;
  pagination?: BackendPagination | null;
};

type BackendOverviewPayload = {
  identity?: BackendIdentity;
  summary_cards?: Array<{
    key?: string;
    label?: string;
    value?: string | number;
    tooltip?: string;
    band_code?: string;
    band_label?: string;
    peer_percentile?: number;
    peer_cohort_label?: string;
  }>;
  overview_metrics?: Array<{
    group?: string;
    label?: string;
    value?: unknown;
  }>;
  meta?: BackendMeta;
};

type BackendSectionPayload = {
  family_id?: string;
  summary?: Record<string, unknown> | null;
  rows?: Array<Record<string, unknown>>;
  series?: Array<Record<string, unknown>>;
  meta?: BackendMeta;
};

type BackendFamilySuggestionsPayload = {
  query?: string;
  rows?: Array<{
    family_id?: string;
    label?: string;
    owner_label?: string | null;
    primary_field?: string | null;
    status?: string | null;
  }>;
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

function mapIdentity(payload?: BackendIdentity): FamilyIdentity {
  return {
    id: String(payload?.id ?? ""),
    label: String(payload?.label ?? ""),
    pageKind: String(payload?.page_kind ?? "family"),
    selectedYear: payload?.selected_year ?? null,
  };
}

function mapCoverage(payload?: BackendCoverage | null): FamilyCoverage | null {
  if (!payload) {
    return null;
  }
  return {
    status: (payload.status as FamilyCoverage["status"]) ?? "unknown",
    pct: payload.pct ?? null,
    coveredCount: payload.covered_count ?? null,
    denominatorCount: payload.denominator_count ?? null,
    caveatText: payload.caveat_text ?? null,
  };
}

function mapPagination(payload?: BackendPagination | null): PortfolioPagination | null {
  if (!payload) {
    return null;
  }
  return {
    limit: Number(payload.limit ?? 0),
    offset: Number(payload.offset ?? 0),
    returnedCount: Number(payload.returned_count ?? 0),
    totalCount: payload.total_count == null ? undefined : Number(payload.total_count),
  };
}

function mapMeta(payload?: BackendMeta): FamilyMeta {
  return {
    page: String(payload?.page ?? "family"),
    supportLevel: parseSupportLevel(payload?.support_level),
    caveats: (payload?.caveats ?? []).map((caveat) => ({
      code: String(caveat.code ?? "unknown"),
      title: String(caveat.title ?? "Caveat"),
      detail: String(caveat.detail ?? ""),
    })),
    coverage: mapCoverage(payload?.coverage),
    pagination: mapPagination(payload?.pagination),
  };
}

function mapSummaryCards(payload?: BackendOverviewPayload["summary_cards"]): FamilySummaryCard[] {
  return (payload ?? []).map((card) => ({
    key: String(card.key ?? "metric"),
    label: String(card.label ?? "Metric"),
    value: typeof card.value === "number" || typeof card.value === "string" ? card.value : "—",
    tooltip: card.tooltip ? String(card.tooltip) : undefined,
    bandCode: card.band_code ? String(card.band_code) : undefined,
    bandLabel: card.band_label ? String(card.band_label) : undefined,
    peerPercentile: card.peer_percentile == null ? undefined : Number(card.peer_percentile),
    peerCohortLabel: card.peer_cohort_label ? String(card.peer_cohort_label) : undefined,
  }));
}

function mapOverviewMetrics(payload?: BackendOverviewPayload["overview_metrics"]): FamilyOverviewMetric[] {
  return (payload ?? []).map((metric) => ({
    group: String(metric.group ?? "general"),
    label: String(metric.label ?? "Metric"),
    value: metric.value,
  }));
}

const toNullableString = (value: unknown): string | null => {
  if (value == null) {
    return null;
  }
  const next = String(value).trim();
  return next ? next : null;
};

export async function fetchFamilyOverview(familyId: string): Promise<FamilyOverviewPayload> {
  const payload = await fetchJson<BackendOverviewPayload>(`/api/v1/families/${encodeURIComponent(familyId)}/overview`);
  return {
    identity: mapIdentity(payload.identity),
    summaryCards: mapSummaryCards(payload.summary_cards),
    overviewMetrics: mapOverviewMetrics(payload.overview_metrics),
    meta: mapMeta(payload.meta),
  };
}

export async function fetchFamilySection(
  familyId: string,
  section: string,
  params?: Record<string, string | number | undefined>,
): Promise<FamilySectionPayload> {
  const search = new URLSearchParams();
  Object.entries(params ?? {}).forEach(([key, value]) => {
    if (value == null || value === "") {
      return;
    }
    search.set(key, String(value));
  });
  const suffix = search.toString() ? `?${search.toString()}` : "";
  const payload = await fetchJson<BackendSectionPayload>(
    `/api/v1/families/${encodeURIComponent(familyId)}/${section}${suffix}`,
  );
  return {
    familyId: String(payload.family_id ?? familyId),
    summary: payload.summary ?? null,
    rows: payload.rows ?? [],
    series: payload.series ?? [],
    meta: mapMeta(payload.meta),
  };
}

export async function fetchFamilySuggestions(query: string, limit = 8, signal?: AbortSignal): Promise<FamilySuggestion[]> {
  const search = new URLSearchParams({ q: query, limit: String(limit) });
  const payload = await fetchJson<BackendFamilySuggestionsPayload>(`/api/v1/families/suggestions?${search.toString()}`, { signal });
  return (payload.rows ?? []).map((row) => ({
    familyId: String(row.family_id ?? ""),
    label: String(row.label ?? row.family_id ?? ""),
    ownerLabel: toNullableString(row.owner_label),
    primaryField: toNullableString(row.primary_field),
    status: toNullableString(row.status),
  }));
}
