import type { SupportLevel } from "./common";

export type CompareMode = "entity" | "timeslice";

export interface CompareIdentity {
  id: string;
  label: string;
  pageKind: string;
}

export interface CompareCaveat {
  code: string;
  title: string;
  detail: string;
}

export interface CompareIdentityContext {
  side: "left" | "right";
  title: string;
  subtitle?: string | null;
  badges: string[];
  href?: string | null;
}

export interface CompareMetricRow {
  key: string;
  label: string;
  displayKind: "count" | "decimal" | "percent" | "text";
  leftValue: number | string | null;
  rightValue: number | string | null;
  deltaValue?: number | null;
  leftNote?: string | null;
  rightNote?: string | null;
  note?: string | null;
  winner?: "left" | "right" | "tie" | null;
  winnerBasis?: string | null;
}

export interface CompareFieldOverlapRow {
  key: string;
  label: string;
  leftShare: number;
  rightShare: number;
  overlapShare: number;
  leftRank?: number | null;
  rightRank?: number | null;
  presence: "shared" | "left_only" | "right_only" | "empty";
  leftNote?: string | null;
  rightNote?: string | null;
}

export interface CompareForecastRow {
  key: string;
  label: string;
  displayKind: "decimal" | "count" | "percent";
  leftValue: number | null;
  rightValue: number | null;
  leftRangeLow?: number | null;
  leftRangeHigh?: number | null;
  rightRangeLow?: number | null;
  rightRangeHigh?: number | null;
  leftNote?: string | null;
  rightNote?: string | null;
  overlapState?: string | null;
  note?: string | null;
}

export interface CompareSupportRow {
  kind: string;
  side: "left" | "right";
  title: string;
  subtitle?: string | null;
  badge?: string | null;
  primaryMetricLabel?: string | null;
  primaryMetricValue?: number | string | null;
  secondaryMetricLabel?: string | null;
  secondaryMetricValue?: number | string | null;
  href?: string | null;
}

export interface CompareMeta {
  page: string;
  supportLevel: SupportLevel;
  artifactSources: string[];
  caveats: CompareCaveat[];
}

export interface CompareTimesliceOptions {
  entityId: string;
  availableYears: number[];
  compareSafeYears: number[];
  defaultBaseYear: number | null;
  defaultCompareYear: number | null;
}

export interface CompareScopeLookup {
  compareKind: string;
  entityId: string;
  label: string | null;
  inScope: boolean;
  primaryField: string | null;
  status: string | null;
  familyCount: number | null;
  timesliceAvailable: boolean;
  defaultBaseYear: number | null;
  defaultCompareYear: number | null;
  note: string | null;
}

export interface FamilyCompareSuggestion {
  familyId: string;
  label: string;
  ownerLabel: string | null;
  primaryField: string | null;
  status: string | null;
}

export interface FamilyCompareLensRow {
  kind: "lens";
  lens: string;
  label: string;
  metricKey: string;
  metricLabel: string;
  leftFamilyId: string;
  leftFamilyLabel: string;
  leftRawValue: number;
  leftBandCode?: string | null;
  leftBandLabel?: string | null;
  leftPeerPercentile?: number | null;
  leftPeerCohort?: string | null;
  leftPeerCohortLabel?: string | null;
  rightFamilyId: string;
  rightFamilyLabel: string;
  rightRawValue: number;
  rightBandCode?: string | null;
  rightBandLabel?: string | null;
  rightPeerPercentile?: number | null;
  rightPeerCohort?: string | null;
  rightPeerCohortLabel?: string | null;
  sameCohort: boolean;
  comparisonMode: string;
  winner?: "left" | "right" | "tie" | null;
  winnerBasis?: string | null;
}

export interface FamilyComparePayload {
  compareKind: string;
  compareMode: CompareMode;
  leftEntity: CompareIdentity | null;
  rightEntity: CompareIdentity | null;
  identityContext: CompareIdentityContext[];
  summaryCards: CompareMetricRow[];
  contrastRows: CompareMetricRow[];
  fieldOverlapRows: CompareFieldOverlapRow[];
  forecastRows: CompareForecastRow[];
  supportRows: CompareSupportRow[];
  lensRows: FamilyCompareLensRow[];
  meta: CompareMeta;
}

export interface PortfolioCompareLensRow {
  kind: "lens";
  lens: string;
  label: string;
  metricKey: string;
  metricLabel: string;
  leftOwnerId: string;
  leftOwnerLabel: string;
  leftRawValue: number;
  leftBandCode?: string | null;
  leftBandLabel?: string | null;
  leftPeerPercentile?: number | null;
  leftPeerBucket?: string | null;
  leftPeerBucketLabel?: string | null;
  rightOwnerId: string;
  rightOwnerLabel: string;
  rightRawValue: number;
  rightBandCode?: string | null;
  rightBandLabel?: string | null;
  rightPeerPercentile?: number | null;
  rightPeerBucket?: string | null;
  rightPeerBucketLabel?: string | null;
  samePeerBucket: boolean;
  comparisonMode: string;
  suppressed: boolean;
  suppressionReason?: string | null;
  winner?: "left" | "right" | "tie" | null;
  winnerBasis?: string | null;
}

export interface PortfolioCompareTopFamilyRow {
  kind: "top_family_preview";
  side: "left" | "right";
  ownerId: string;
  ownerLabel: string;
  rank: number;
  familyId: string;
  blockingScore: number;
  forecastContributor: number;
  primaryField: string;
  status: string;
}

export interface PortfolioComparePayload {
  compareKind: string;
  compareMode: CompareMode;
  leftEntity: CompareIdentity | null;
  rightEntity: CompareIdentity | null;
  identityContext: CompareIdentityContext[];
  summaryCards: CompareMetricRow[];
  contrastRows: CompareMetricRow[];
  fieldOverlapRows: CompareFieldOverlapRow[];
  forecastRows: CompareForecastRow[];
  supportRows: CompareSupportRow[];
  lensRows: PortfolioCompareLensRow[];
  topFamilyRows: PortfolioCompareTopFamilyRow[];
  meta: CompareMeta;
}
