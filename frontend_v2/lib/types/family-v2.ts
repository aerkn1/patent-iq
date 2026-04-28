import type { CoverageStatus, SupportLevel } from "./common";
import type { PortfolioPagination } from "./portfolio-v2";

export interface FamilyIdentity {
  id: string;
  label: string;
  pageKind: string;
  selectedYear?: number | null;
}

export interface FamilyCaveat {
  code: string;
  title: string;
  detail: string;
}

export interface FamilyCoverage {
  status: CoverageStatus | "unknown";
  pct?: number | null;
  coveredCount?: number | null;
  denominatorCount?: number | null;
  caveatText?: string | null;
}

export interface FamilyMeta {
  page: string;
  supportLevel: SupportLevel;
  caveats: FamilyCaveat[];
  coverage?: FamilyCoverage | null;
  pagination?: PortfolioPagination | null;
}

export interface FamilySummaryCard {
  key: string;
  label: string;
  value: string | number;
  tooltip?: string;
  bandCode?: string;
  bandLabel?: string;
  peerPercentile?: number;
  peerCohortLabel?: string;
}

export interface FamilyOverviewMetric {
  group: string;
  label: string;
  value: unknown;
}

export interface FamilyOverviewPayload {
  identity: FamilyIdentity;
  summaryCards: FamilySummaryCard[];
  overviewMetrics: FamilyOverviewMetric[];
  meta: FamilyMeta;
}

export interface FamilySuggestion {
  familyId: string;
  label: string;
  ownerLabel?: string | null;
  primaryField?: string | null;
  status?: string | null;
}

export interface FamilySectionPayload {
  familyId: string;
  summary?: Record<string, unknown> | null;
  rows: Array<Record<string, unknown>>;
  series: Array<Record<string, unknown>>;
  meta: FamilyMeta;
}

export type FamilyWorkspaceTab = "publications" | "legal" | "fields" | "evidence";
