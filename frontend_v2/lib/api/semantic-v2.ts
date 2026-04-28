import { fetchJson } from "@/lib/api/core";
import type {
  SemanticComparePayload,
  SemanticCompareEntitySummary,
  SemanticCompareRow,
  SemanticCoverage,
  SemanticDetailPanel,
  SemanticFamilySuggestion,
  SemanticIdentity,
  SemanticMeta,
  SemanticPagination,
  SemanticQueryContextItem,
  SemanticSearchPayload,
  SemanticSearchResultRow,
  SemanticSummaryCard,
  SemanticVectorSpace,
} from "@/lib/types/semantic-v2";
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
  support_level?: SupportLevel;
  artifact_sources?: string[];
  caveats?: BackendCaveat[];
  coverage?: BackendCoverage | null;
  pagination?: BackendPagination | null;
};

type BackendSemanticSearchPayload = {
  query_mode?: string;
  vector_space?: SemanticVectorSpace;
  anchor_entity?: BackendIdentity | null;
  selected_entity?: BackendIdentity | null;
  summary?: Record<string, unknown> | null;
  summary_cards?: Array<Record<string, unknown>>;
  query_context?: Array<Record<string, unknown>>;
  result_rows?: Array<Record<string, unknown>>;
  meta?: BackendMeta;
};

type BackendSemanticComparePayload = {
  compare_kind?: string;
  left_entity?: BackendIdentity | null;
  right_entity?: BackendIdentity | null;
  entity_summaries?: Array<Record<string, unknown>>;
  summary_cards?: Array<Record<string, unknown>>;
  compare_rows?: Array<Record<string, unknown>>;
  detail_panels?: Array<Record<string, unknown>>;
  meta?: BackendMeta;
};

type BackendSemanticSuggestionsPayload = {
  query?: string;
  vector_space?: SemanticVectorSpace;
  rows?: Array<Record<string, unknown>>;
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

const toNumber = (value: unknown, fallback = 0): number => {
  const candidate = Number(value);
  return Number.isFinite(candidate) ? candidate : fallback;
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

const mapIdentity = (payload?: BackendIdentity | null): SemanticIdentity | null => {
  if (!payload?.id) {
    return null;
  }
  return {
    id: String(payload.id),
    label: String(payload.label ?? payload.id),
    pageKind: String(payload.page_kind ?? "family"),
  };
};

const mapCoverage = (payload?: BackendCoverage | null): SemanticCoverage | null => {
  if (!payload) {
    return null;
  }
  return {
    status:
      payload.status === "high" || payload.status === "medium" || payload.status === "low" || payload.status === "unknown"
        ? payload.status
        : "unknown",
    pct: toNullableNumber(payload.pct),
    coveredCount: toNullableNumber(payload.covered_count),
    denominatorCount: toNullableNumber(payload.denominator_count),
    caveatText: toNullableString(payload.caveat_text),
  };
};

const mapPagination = (payload?: BackendPagination | null): SemanticPagination | null => {
  if (!payload) {
    return null;
  }
  return {
    limit: toNumber(payload.limit),
    offset: toNumber(payload.offset),
    returnedCount: toNumber(payload.returned_count),
    totalCount: toNullableNumber(payload.total_count),
  };
};

const mapMeta = (payload?: BackendMeta): SemanticMeta => ({
  page: String(payload?.page ?? "semantic"),
  supportLevel: parseSupportLevel(payload?.support_level),
  artifactSources: (payload?.artifact_sources ?? []).map((source) => String(source)),
  caveats: (payload?.caveats ?? []).map((caveat) => ({
    code: String(caveat.code ?? "unknown"),
    title: String(caveat.title ?? "Caveat"),
    detail: String(caveat.detail ?? ""),
  })),
  coverage: mapCoverage(payload?.coverage),
  pagination: mapPagination(payload?.pagination),
});

const mapSummaryCard = (row: Record<string, unknown>): SemanticSummaryCard => ({
  key: String(row.key ?? "metric"),
  label: String(row.label ?? "Metric"),
  value: typeof row.value === "string" ? row.value : toNullableNumber(row.value),
  displayKind:
    row.display_kind === "count" || row.display_kind === "percent" || row.display_kind === "text"
      ? row.display_kind
      : "decimal",
  note: toNullableString(row.note),
});

const mapQueryContext = (row: Record<string, unknown>): SemanticQueryContextItem => ({
  key: String(row.key ?? "context"),
  label: String(row.label ?? "Context"),
  value: String(row.value ?? "—"),
});

const mapResultRow = (row: Record<string, unknown>): SemanticSearchResultRow => ({
  familyId: String(row.family_id ?? ""),
  familyTitle: toNullableString(row.family_title),
  ownerNameHarmonized: toNullableString(row.owner_name_harmonized),
  primaryWipoField: toNullableString(row.primary_wipo_field),
  semanticSimilarity: toNullableNumber(row.semantic_similarity),
  familyCompositeStatus: toNullableString(row.family_composite_status),
  familyUiBlockingPowerScore: toNullableNumber(row.family_ui_blocking_power_score),
  oecdQualityPercentile: toNullableNumber(row.oecd_quality_percentile),
  representativeStage: toNullableString(row.representative_stage),
  textProvenance: toNullableString(row.text_provenance),
  textSourceType: toNullableString(row.text_source_type),
  isAbstractFallback: Boolean(row.is_abstract_fallback),
  familyEarliestPriorityDate: toNullableString(row.family_earliest_priority_date),
  textExcerpt: toNullableString(row.text_excerpt),
});

const mapCompareRow = (row: Record<string, unknown>): SemanticCompareRow => ({
  key: String(row.key ?? "metric"),
  label: String(row.label ?? "Metric"),
  value: typeof row.value === "string" ? row.value : toNullableNumber(row.value),
  displayKind:
    row.display_kind === "count" || row.display_kind === "percent" || row.display_kind === "text"
      ? row.display_kind
      : "decimal",
  supported: Boolean(row.supported),
  note: toNullableString(row.note),
});

const mapEntitySummary = (row: Record<string, unknown>): SemanticCompareEntitySummary => ({
  role: row.role === "selected" ? "selected" : "anchor",
  familyId: String(row.family_id ?? ""),
  entityLabel: String(row.entity_label ?? row.family_id ?? ""),
  ownerNameHarmonized: toNullableString(row.owner_name_harmonized),
  primaryWipoField: toNullableString(row.primary_wipo_field),
  familyCompositeStatus: toNullableString(row.family_composite_status),
  representativeStage: toNullableString(row.representative_stage),
  textProvenance: toNullableString(row.text_provenance),
  familyEarliestPriorityDate: toNullableString(row.family_earliest_priority_date),
  familyUiBlockingPowerScore: toNullableNumber(row.family_ui_blocking_power_score),
  oecdQualityPercentile: toNullableNumber(row.oecd_quality_percentile),
  supportedSpaces: Array.isArray(row.supported_spaces) ? row.supported_spaces.map((value) => String(value)) : [],
  supportNote: toNullableString(row.support_note),
});

const mapDetailPanel = (row: Record<string, unknown>): SemanticDetailPanel => ({
  side: row.side === "right" ? "right" : "left",
  familyId: String(row.family_id ?? ""),
  entityLabel: String(row.entity_label ?? row.family_id ?? ""),
  ownerNameHarmonized: toNullableString(row.owner_name_harmonized),
  primaryWipoField: toNullableString(row.primary_wipo_field),
  familyCompositeStatus: toNullableString(row.family_composite_status),
  familyUiBlockingPowerScore: toNullableNumber(row.family_ui_blocking_power_score),
  oecdQualityPercentile: toNullableNumber(row.oecd_quality_percentile),
  representativeStage: toNullableString(row.representative_stage),
  textProvenance: toNullableString(row.text_provenance),
  familyEarliestPriorityDate: toNullableString(row.family_earliest_priority_date),
  supportedSpaces: Array.isArray(row.supported_spaces) ? row.supported_spaces.map((value) => String(value)) : [],
  textExcerpt: toNullableString(row.text_excerpt),
});

export async function fetchFamilyAnchorSemanticSearch(params: {
  familyId: string;
  vectorSpace: SemanticVectorSpace;
  limit?: number;
  offset?: number;
  sameFieldOnly?: boolean;
  excludeSameOwner?: boolean;
  selectedFamilyId?: string | null;
}): Promise<SemanticSearchPayload> {
  const search = new URLSearchParams({
    family_id: params.familyId,
    vector_space: params.vectorSpace,
    limit: String(params.limit ?? 12),
    offset: String(params.offset ?? 0),
    same_field_only: String(Boolean(params.sameFieldOnly)),
    exclude_same_owner: String(Boolean(params.excludeSameOwner)),
  });
  if (params.selectedFamilyId) {
    search.set("selected_family_id", params.selectedFamilyId);
  }
  const raw = await fetchJson<BackendSemanticSearchPayload>(`/api/v1/semantic/families/search?${search.toString()}`);
  return {
    queryMode: String(raw.query_mode ?? "family_anchor"),
    vectorSpace: raw.vector_space === "claims" ? "claims" : "abstract",
    anchorEntity: mapIdentity(raw.anchor_entity),
    selectedEntity: mapIdentity(raw.selected_entity),
    summary: raw.summary
        ? {
            anchorFamilyId: toNullableString(raw.summary.anchor_family_id),
            anchorOwner: toNullableString(raw.summary.anchor_owner),
            anchorPrimaryField: toNullableString(raw.summary.anchor_primary_field),
            anchorStatus: toNullableString(raw.summary.anchor_status),
            anchorTextExcerpt: toNullableString(raw.summary.anchor_text_excerpt),
            anchorTextProvenance: toNullableString(raw.summary.anchor_text_provenance),
            sameFieldOnly: Boolean(raw.summary.same_field_only),
            excludeSameOwner: Boolean(raw.summary.exclude_same_owner),
          }
      : null,
    summaryCards: (raw.summary_cards ?? []).map(mapSummaryCard),
    queryContext: (raw.query_context ?? []).map(mapQueryContext),
    resultRows: (raw.result_rows ?? []).map(mapResultRow),
    meta: mapMeta(raw.meta),
  };
}

export async function fetchTextDiscoverySemanticSearch(params: {
  queryText: string;
  vectorSpace?: SemanticVectorSpace;
  limit?: number;
  offset?: number;
}): Promise<SemanticSearchPayload> {
  const search = new URLSearchParams({
    q: params.queryText,
    vector_space: params.vectorSpace ?? "abstract",
    limit: String(params.limit ?? 12),
    offset: String(params.offset ?? 0),
  });
  const raw = await fetchJson<BackendSemanticSearchPayload>(`/api/v1/semantic/text/search?${search.toString()}`);
  return {
    queryMode: String(raw.query_mode ?? "free_text"),
    vectorSpace: raw.vector_space === "claims" ? "claims" : "abstract",
    anchorEntity: mapIdentity(raw.anchor_entity),
    selectedEntity: mapIdentity(raw.selected_entity),
    summary: raw.summary
      ? {
          anchorFamilyId: toNullableString(raw.summary.anchor_family_id),
          anchorOwner: toNullableString(raw.summary.anchor_owner),
          anchorPrimaryField: toNullableString(raw.summary.anchor_primary_field),
          anchorStatus: toNullableString(raw.summary.anchor_status),
          anchorTextExcerpt: toNullableString(raw.summary.anchor_text_excerpt),
          anchorTextProvenance: toNullableString(raw.summary.anchor_text_provenance),
          queryTextExcerpt: toNullableString(raw.summary.query_text_excerpt),
          sameFieldOnly: Boolean(raw.summary.same_field_only),
          excludeSameOwner: Boolean(raw.summary.exclude_same_owner),
        }
      : null,
    summaryCards: (raw.summary_cards ?? []).map(mapSummaryCard),
    queryContext: (raw.query_context ?? []).map(mapQueryContext),
    resultRows: (raw.result_rows ?? []).map(mapResultRow),
    meta: mapMeta(raw.meta),
  };
}

export async function fetchSemanticFamilySuggestions(params: {
  query: string;
  vectorSpace: SemanticVectorSpace;
  limit?: number;
}): Promise<SemanticFamilySuggestion[]> {
  const search = new URLSearchParams({
    q: params.query,
    vector_space: params.vectorSpace,
    limit: String(params.limit ?? 8),
  });
  const raw = await fetchJson<BackendSemanticSuggestionsPayload>(`/api/v1/semantic/families/suggestions?${search.toString()}`);
  return (raw.rows ?? []).map((row) => ({
    familyId: String(row.family_id ?? ""),
    label: String(row.label ?? row.family_id ?? ""),
    ownerNameHarmonized: toNullableString(row.owner_name_harmonized),
    primaryWipoField: toNullableString(row.primary_wipo_field),
    familyCompositeStatus: toNullableString(row.family_composite_status),
  }));
}

export async function fetchFamilySemanticCompare(params: {
  leftFamilyId: string;
  rightFamilyId: string;
}): Promise<SemanticComparePayload> {
  const search = new URLSearchParams({
    left_family_id: params.leftFamilyId,
    right_family_id: params.rightFamilyId,
  });
  const raw = await fetchJson<BackendSemanticComparePayload>(`/api/v1/semantic/families/compare?${search.toString()}`);
  return {
    compareKind: String(raw.compare_kind ?? "semantic_families"),
    leftEntity: mapIdentity(raw.left_entity),
    rightEntity: mapIdentity(raw.right_entity),
    entitySummaries: (raw.entity_summaries ?? []).map(mapEntitySummary),
    summaryCards: (raw.summary_cards ?? []).map(mapSummaryCard),
    compareRows: (raw.compare_rows ?? []).map(mapCompareRow),
    detailPanels: (raw.detail_panels ?? []).map(mapDetailPanel),
    meta: mapMeta(raw.meta),
  };
}
