import type { SupportLevel } from "./common";

export interface PublicationIdentity {
  id: string;
  label: string;
  pageKind: string;
  selectedYear?: number | null;
}

export interface PublicationCaveat {
  code: string;
  title: string;
  detail: string;
}

export interface PublicationMeta {
  page: string;
  supportLevel: SupportLevel;
  caveats: PublicationCaveat[];
}

export interface PublicationSummaryCard {
  key: string;
  label: string;
  value: string | number;
}

export interface PublicationFact {
  label: string;
  value: unknown;
  detail?: string;
}

export interface PublicationAvailability {
  key: string;
  label: string;
  status: string;
  detail?: string;
}

export interface PublicationOverviewPayload {
  identity: PublicationIdentity;
  overview: Record<string, unknown>;
  summaryCards: PublicationSummaryCard[];
  bibliography: PublicationFact[];
  familyContext: PublicationFact[];
  textAvailability: PublicationAvailability[];
  registerEvidence: PublicationFact[];
  relatedPublications: Array<Record<string, unknown>>;
  meta: PublicationMeta;
}

export interface PublicationSuggestion {
  publicationId: string;
  label: string;
  authority?: string | null;
  kindCode?: string | null;
  publicationDate?: string | null;
  familyId?: string | null;
}

export interface PublicationSectionPayload {
  publicationId: string;
  summary?: Record<string, unknown> | null;
  rows: Array<Record<string, unknown>>;
  meta: PublicationMeta;
}

export type PublicationWorkspaceTab = "text" | "timeline" | "register";
