import { fetchJson } from "@/lib/api/core";

import type {
  PublicationAvailability,
  PublicationFact,
  PublicationIdentity,
  PublicationMeta,
  PublicationOverviewPayload,
  PublicationSectionPayload,
  PublicationSuggestion,
  PublicationSummaryCard,
} from "@/lib/types/publication-v2";
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

type BackendMeta = {
  page?: string;
  support_level?: "strong" | "moderate" | "limited" | "candidate_only";
  caveats?: BackendCaveat[];
};

type BackendOverviewPayload = {
  identity?: BackendIdentity;
  overview?: Record<string, unknown>;
  summary_cards?: Array<{
    key?: string;
    label?: string;
    value?: string | number;
  }>;
  bibliography?: Array<{
    label?: string;
    value?: unknown;
    detail?: string;
  }>;
  family_context?: Array<{
    label?: string;
    value?: unknown;
    detail?: string;
  }>;
  text_availability?: Array<{
    key?: string;
    label?: string;
    status?: string;
    detail?: string;
  }>;
  register_evidence?: Array<{
    label?: string;
    value?: unknown;
    detail?: string;
  }>;
  related_publications?: Array<Record<string, unknown>>;
  meta?: BackendMeta;
};

type BackendSectionPayload = {
  publication_id?: string;
  summary?: Record<string, unknown> | null;
  rows?: Array<Record<string, unknown>>;
  meta?: BackendMeta;
};

type BackendPublicationSuggestionsPayload = {
  query?: string;
  rows?: Array<{
    publication_id?: string;
    label?: string;
    authority?: string | null;
    kind_code?: string | null;
    publication_date?: string | null;
    family_id?: string | null;
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

function mapIdentity(payload?: BackendIdentity): PublicationIdentity {
  return {
    id: String(payload?.id ?? ""),
    label: String(payload?.label ?? ""),
    pageKind: String(payload?.page_kind ?? "publication"),
    selectedYear: payload?.selected_year ?? null,
  };
}

function mapMeta(payload?: BackendMeta): PublicationMeta {
  return {
    page: String(payload?.page ?? "publication"),
    supportLevel: parseSupportLevel(payload?.support_level),
    caveats: (payload?.caveats ?? []).map((caveat) => ({
      code: String(caveat.code ?? "unknown"),
      title: String(caveat.title ?? "Caveat"),
      detail: String(caveat.detail ?? ""),
    })),
  };
}

function mapSummaryCards(payload?: BackendOverviewPayload["summary_cards"]): PublicationSummaryCard[] {
  return (payload ?? []).map((card) => ({
    key: String(card.key ?? "fact"),
    label: String(card.label ?? "Fact"),
    value: typeof card.value === "number" || typeof card.value === "string" ? card.value : "—",
  }));
}

function mapFacts(
  payload?: Array<{
    label?: string;
    value?: unknown;
    detail?: string;
  }>,
): PublicationFact[] {
  return (payload ?? []).map((fact) => ({
    label: String(fact.label ?? "Fact"),
    value: fact.value,
    detail: fact.detail ? String(fact.detail) : undefined,
  }));
}

function mapAvailability(payload?: BackendOverviewPayload["text_availability"]): PublicationAvailability[] {
  return (payload ?? []).map((item) => ({
    key: String(item.key ?? "availability"),
    label: String(item.label ?? "Availability"),
    status: String(item.status ?? "unknown"),
    detail: item.detail ? String(item.detail) : undefined,
  }));
}

const toNullableString = (value: unknown): string | null => {
  if (value == null) {
    return null;
  }
  const next = String(value).trim();
  return next ? next : null;
};

export async function fetchPublicationOverview(publicationId: string): Promise<PublicationOverviewPayload> {
  const payload = await fetchJson<BackendOverviewPayload>(
    `/api/v1/publications/${encodeURIComponent(publicationId)}/overview`,
  );
  return {
    identity: mapIdentity(payload.identity),
    overview: payload.overview ?? {},
    summaryCards: mapSummaryCards(payload.summary_cards),
    bibliography: mapFacts(payload.bibliography),
    familyContext: mapFacts(payload.family_context),
    textAvailability: mapAvailability(payload.text_availability),
    registerEvidence: mapFacts(payload.register_evidence),
    relatedPublications: payload.related_publications ?? [],
    meta: mapMeta(payload.meta),
  };
}

export async function fetchPublicationSection(
  publicationId: string,
  section: "text" | "legal-timeline" | "register-evidence",
): Promise<PublicationSectionPayload> {
  const payload = await fetchJson<BackendSectionPayload>(
    `/api/v1/publications/${encodeURIComponent(publicationId)}/${section}`,
  );
  return {
    publicationId: String(payload.publication_id ?? publicationId),
    summary: payload.summary ?? null,
    rows: payload.rows ?? [],
    meta: mapMeta(payload.meta),
  };
}

export async function fetchPublicationSuggestions(query: string, limit = 8, signal?: AbortSignal): Promise<PublicationSuggestion[]> {
  const search = new URLSearchParams({ q: query, limit: String(limit) });
  const payload = await fetchJson<BackendPublicationSuggestionsPayload>(`/api/v1/publications/suggestions?${search.toString()}`, { signal });
  return (payload.rows ?? []).map((row) => ({
    publicationId: String(row.publication_id ?? ""),
    label: String(row.label ?? row.publication_id ?? ""),
    authority: toNullableString(row.authority),
    kindCode: toNullableString(row.kind_code),
    publicationDate: toNullableString(row.publication_date),
    familyId: toNullableString(row.family_id),
  }));
}
