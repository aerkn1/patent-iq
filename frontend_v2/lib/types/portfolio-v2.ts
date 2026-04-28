import type { CoverageStatus, SupportLevel } from "./common";

export type ForecastHorizon = "3y" | "5y";

export type SortDirection = "asc" | "desc";

export type PortfolioTab = "families" | "forecast" | "fields" | "threats" | "tables";

export type PortfolioViewMode = "overview" | "timeseries";

export interface PortfolioIdentity {
  id: string;
  label: string;
  pageKind: string;
  selectedYear?: number | null;
}

export interface PortfolioOwnerSuggestion {
  ownerId: string;
  label: string;
  familyCount?: number;
}

export interface PortfolioPagination {
  limit: number;
  offset: number;
  returnedCount: number;
  totalCount?: number;
}

export interface PortfolioSummaryCard {
  key: string;
  label: string;
  value: string;
  tone?: "neutral" | "positive" | "warning" | "critical";
  delta?: number;
  deltaLabel?: string;
  tooltip?: string;
  caveat?: string;
  bandCode?: string;
  bandLabel?: string;
  peerBucket?: string;
  peerBucketLabel?: string;
  peerPercentile?: number;
}

export interface PortfolioCoveragePayload {
  predictionCoverageStatus: CoverageStatus;
  phase03FamilyCoveragePct: number;
  phase04FamilyCoveragePct?: number | null;
  phase06FamilyCoveragePct?: number | null;
  coveredCount?: number;
  denominatorCount?: number;
  coverageCaveatText?: string;
  contributionMethod?: string;
  supportLevel?: SupportLevel;
}

export interface PortfolioCountScopes {
  inScopeFamilyCount: number;
  primaryOwnerFamilyCount: number;
  activeGrantFamilyCount: number;
  semanticCandidateFamilyCount: number;
  pendingFamilyCount: number;
  unclassifiedFamilyCount: number;
}

export interface PortfolioStatusSlice {
  key: string;
  label: string;
  count: number;
  share: number;
}

export interface PortfolioOverviewPayload {
  identity: PortfolioIdentity;
  summaryCards: PortfolioSummaryCard[];
  statusMix: PortfolioStatusSlice[];
  coverage: PortfolioCoveragePayload;
  familyCount: number;
  countScopes: PortfolioCountScopes;
  activeGrantFamilyCount: number;
  semanticCandidateCount: number;
  topFamilyPreview: PortfolioTopFamilyRow[];
}

export interface PortfolioTopFamilyRow {
  familyId: string;
  ownerWeight: number;
  blockingScore: number;
  status: string;
  priorityYear: string;
  title?: string;
  primaryField: string;
  forecastContributor?: number;
}

export interface PortfolioForecastInterval {
  total: number;
  low: number;
  high: number;
  perEffectiveFamily: number;
  topConcentrationPct: number;
  coveragePct: number;
}

export interface PortfolioForecastRiskBand {
  label: string;
  share: number;
  families: number;
}

export interface PortfolioForecastPayload {
  horizon: ForecastHorizon;
  interval3y: PortfolioForecastInterval;
  interval5y: PortfolioForecastInterval;
  risk12m: PortfolioForecastRiskBand[];
  risk24m: PortfolioForecastRiskBand[];
  topSegments: PortfolioFieldSegmentRow[];
}

export interface PortfolioFieldSegmentRow {
  field: string;
  activeFamilies: number;
  activeShare: number;
  hotspotDirection: "gains" | "losses" | "heating" | "cooling" | "stable" | "flat";
  change12m: number;
  confidence: SupportLevel;
}

export interface PortfolioThreatRow {
  citingAssignee: string;
  wipoField: string;
  citationLethality: number;
  collidedFamilyCount: number;
}

export interface PortfolioClassificationCpcRow {
  segment: string;
  classificationType: string;
  wipoField: string;
  familyShare: number;
  trajectory: number;
  topChange: "gain" | "loss" | "flat";
}

export interface PortfolioFieldTimeseriesPoint {
  year: number;
  share: number;
  portfolio: number;
}

export interface PortfolioFieldTimeseries {
  field: string;
  points: PortfolioFieldTimeseriesPoint[];
}

export interface PortfolioFieldTimeseriesSnapshot {
  snapshotDate: string;
  activeFamilyCount: number;
  activeShare: number;
  enforceabilityScore: number;
  heritageScore: number;
}

export interface PortfolioFieldTimeseriesResponse {
  ownerId: string;
  rows: PortfolioFieldTimeseries[];
}

export interface PortfolioFamiliesResponse {
  ownerId: string;
  rows: PortfolioTopFamilyRow[];
  pagination?: PortfolioPagination;
}

export interface PortfolioFieldRowsResponse {
  ownerId: string;
  rows: PortfolioFieldSegmentRow[];
}

export interface PortfolioCitationSummary {
  asOfYear: number;
  familyCount: number;
  forwardCitationsCleanTotal: number;
  forwardCitationsWeightedTotal: number;
  backwardCitationsCleanTotal: number;
  backwardNplCitationTotal: number;
  distinctCitingFamilyCount: number;
  distinctCitedFamilyCount: number;
  avgScienceGroundingScore: number;
  avgGeneralityPercentile: number;
  avgOriginalityPercentile: number;
  avgUniqueCitingFamilyCount: number;
  avgCitingAssigneeDiversity: number;
  avgAttackerDensityScore: number;
  avgOutOfBoundsCitationShare: number;
}

export interface PortfolioCitationSummaryResponse {
  ownerId: string;
  summary: PortfolioCitationSummary | null;
}

export interface PortfolioCitationTimeseriesPoint {
  year: number;
  familyCount: number;
  forwardCitationsCleanTotal: number;
  forwardCitationsWeightedTotal: number;
  avgUniqueCitingFamilyCount: number;
  avgCitingAssigneeDiversity: number;
  avgAttackerDensityScore: number;
}

export interface PortfolioCitationTimeseriesResponse {
  ownerId: string;
  rows: PortfolioCitationTimeseriesPoint[];
}

export interface PortfolioCitationFamilyRow {
  familyId: string;
  familyPriorityYear: number;
  primaryField: string;
  status: string;
  forwardCitationsClean: number;
  forwardCitationsWeighted: number;
  earlyCitations5y: number;
  earlyCitations7y: number;
  uniqueCitingFamilyCount: number;
  citingAssigneeDiversity: number;
  blockingScore: number;
}

export interface PortfolioCitationFamiliesResponse {
  ownerId: string;
  rows: PortfolioCitationFamilyRow[];
  pagination?: PortfolioPagination;
}

export interface PortfolioCitationAttackerRow {
  citingAssignee: string;
  wipoField: string;
  jurisdictionCode: string;
  latestCitationYear: number;
  citationEventCount: number;
  cleanCitationCount: number;
  citationLethalitySum: number;
}

export interface PortfolioCitationAttackersResponse {
  ownerId: string;
  rows: PortfolioCitationAttackerRow[];
  pagination?: PortfolioPagination;
}

export interface PortfolioCitationFieldRow {
  wipoField: string;
  latestCitationYear: number;
  citationEventCount: number;
  citingAssigneeCount: number;
  cleanCitationCount: number;
  citationLethalitySum: number;
}

export interface PortfolioCitationFieldsResponse {
  ownerId: string;
  rows: PortfolioCitationFieldRow[];
  pagination?: PortfolioPagination;
}

export interface PortfolioCitationJurisdictionRow {
  jurisdictionCode: string;
  latestCitationYear: number;
  citationEventCount: number;
  citingAssigneeCount: number;
  wipoFieldCount: number;
  cleanCitationCount: number;
  citationLethalitySum: number;
}

export interface PortfolioCitationJurisdictionsResponse {
  ownerId: string;
  rows: PortfolioCitationJurisdictionRow[];
  pagination?: PortfolioPagination;
}

export interface PortfolioCitationCpcGroupRow {
  cpcMainGroup: string;
  latestCitationYear: number;
  citationEventCount: number;
  cleanCitationCount: number;
  citationLethalitySum: number;
  citedFamilyCount: number;
}

export interface PortfolioCitationCpcGroupsResponse {
  ownerId: string;
  rows: PortfolioCitationCpcGroupRow[];
  pagination?: PortfolioPagination;
}

export interface PortfolioFilingTimeseriesPoint {
  year: number;
  familyFilingCount: number;
  cumulativeFamilyCount: number;
  rolling3yFamilyFilingCount: number;
  prior3yFamilyFilingCount: number;
  rolling3yChangePct: number;
  momentumDirection: "accelerating" | "stable" | "cooling";
}

export interface PortfolioFilingTimeseriesResponse {
  ownerId: string;
  rows: PortfolioFilingTimeseriesPoint[];
}

export interface PortfolioHistoryAudit {
  coverageStatus: CoverageStatus;
  coveragePct: number;
  coveredCount?: number;
  denominatorCount?: number;
  coverageCaveatText?: string;
  supportLevel: SupportLevel;
}

export interface PortfolioStatusTimeseriesPoint {
  year: number;
  familyCount: number;
  pendingFamilyCount: number;
  fullyActiveFamilyCount: number;
  underFireFamilyCount: number;
  partiallyLapsedFamilyCount: number;
  deadFamilyCount: number;
  pendingShare: number;
  fullyActiveShare: number;
  underFireShare: number;
  partiallyLapsedShare: number;
  deadShare: number;
  statusCoveragePct: number;
  historicalOwnerTruthSupportedPct: number;
  currentOwnerMetadataOnlyPct: number;
  avgDataCompletenessPctAsOf: number;
}

export interface PortfolioStatusTimeseriesResponse {
  ownerId: string;
  rows: PortfolioStatusTimeseriesPoint[];
  audit: PortfolioHistoryAudit;
}

export interface PortfolioJurisdictionUnlockSummary {
  unlockedJurisdictionCount: number;
  firstUnlockYear: number;
  latestUnlockYear: number;
  latestPresenceYear: number;
  latestActiveJurisdictionCount: number;
  latestPendingJurisdictionCount: number;
  latestLapsedJurisdictionCount: number;
  everActiveJurisdictionCount: number;
}

export interface PortfolioJurisdictionUnlockYearRow {
  year: number;
  unlockedJurisdictionCount: number;
  cumulativeUnlockedJurisdictionCount: number;
  activeUnlockCount: number;
  pendingUnlockCount: number;
  lapsedOnlyUnlockCount: number;
  activeJurisdictionCount: number;
  pendingJurisdictionCount: number;
  lapsedJurisdictionCount: number;
  unlockedJurisdictions: string[];
}

export interface PortfolioJurisdictionUnlockDetailRow {
  jurisdictionCode: string;
  firstUnlockYear: number;
  firstUnlockBasis: "active" | "pending" | "lapsed_only" | "tracked";
  firstActiveYear: number;
  firstPendingYear: number;
  firstLapsedYear: number;
  trackedFamilyCount: number;
  activeFamilyCount: number;
  pendingFamilyCount: number;
  lapsedFamilyCount: number;
}

export interface PortfolioJurisdictionUnlockHistoryResponse {
  ownerId: string;
  summary: PortfolioJurisdictionUnlockSummary | null;
  years: PortfolioJurisdictionUnlockYearRow[];
  jurisdictions: PortfolioJurisdictionUnlockDetailRow[];
  audit: PortfolioHistoryAudit;
}

export interface PortfolioMarketContextSummary {
  horizon: ForecastHorizon;
  heatingMarketExposureCount: number;
  coolingMarketExposureCount: number;
  hotspotCoveragePct: number;
}

export interface PortfolioMarketContextSegment {
  horizon: ForecastHorizon;
  wipoField: string;
  predictedDirectionBand: string;
  supportLevel: SupportLevel;
  predictedGrowthRateReference: number;
  predictedCountReference: number;
  activeFamilyCount: number;
}

export interface PortfolioMarketContextResponse {
  ownerId: string;
  summary: PortfolioMarketContextSummary | null;
  segments: PortfolioMarketContextSegment[];
}

export interface PortfolioThreatsResponse {
  ownerId: string;
  rows: PortfolioThreatRow[];
  pagination?: PortfolioPagination;
}

export interface PortfolioClassificationResponse {
  ownerId: string;
  rows: PortfolioClassificationCpcRow[];
  timeseries: PortfolioFieldTimeseries[];
  pagination?: PortfolioPagination;
}

export interface PortfolioForecastContributorRow {
  contributorScope: string;
  horizon: ForecastHorizon;
  contributorEntityId: string;
  jurisdictionCode: string;
  contributionValue: number;
  contributionShare: number;
  contributorRank: number;
}

export interface PortfolioForecastContributorsResponse {
  ownerId: string;
  rows: PortfolioForecastContributorRow[];
  pagination?: PortfolioPagination;
}

export interface PortfolioCompareTimesliceRow {
  metric: string;
  label: string;
  currentValue: number;
  compareValue: number;
  currentScore: number;
  compareScore: number;
  currentYear: number;
  compareYear: number;
  delta: number;
}

export interface PortfolioCompareTimesliceResponse {
  ownerId: string;
  rows: PortfolioCompareTimesliceRow[];
}

export type PortfolioPendingGrantKind = "summary" | "jurisdiction" | "field" | "branch";

export interface PortfolioPendingGrantRow {
  kind: PortfolioPendingGrantKind;
  featureStatus?: string;
  servingReady?: boolean;
  horizon?: string;
  recommendedOutput?: string;
  probabilityHeadlineAllowed?: boolean;
  reason?: string;
  observedRocAuc?: number;
  observedPrAuc?: number;
  pendingPipelineBranchCount?: number;
  pendingPipelineFamilyCount?: number;
  currentPendingBranchCount?: number;
  currentPendingFamilyCount?: number;
  pendingPipelineBranchCoveragePct?: number;
  pendingPipelineFamilyCoveragePct?: number;
  pendingPipelineExpectedLikelyGrants12m?: number;
  pendingPipelineExpectedLikelyGrants24m?: number;
  pendingPipelineAvgProbability12m?: number;
  pendingPipelineAvgProbability24m?: number;
  pendingPipelinePercentile?: number;
  pendingPipelinePriorityTier?: string;
  pendingPipelineSupportLevel?: string;
  pendingPipelineTopJurisdiction?: string;
  pendingPipelineTopField?: string;
  topBranchFamilyId?: string;
  topBranchJurisdiction?: string;
  topBranchField?: string;
  topBranchProbability?: number;
  topBranchPercentile?: number;
  jurisdictionCode?: string;
  wipoField?: string;
  officeSupportLevel?: string;
  branchCount?: number;
  familyCount?: number;
  avgProbability12m?: number;
  avgProbability24m?: number;
  expectedLikelyGrants12m?: number;
  expectedLikelyGrants24m?: number;
  avgPercentile?: number;
  docdbFamilyId?: string;
  primaryWipoField?: string;
  pendingAgeYears?: number;
  familyAgeYears?: number;
  familyBlockingPowerScore?: number;
  familyEnforceabilityScore?: number;
  familyRcfScore?: number;
  dataCompletenessPct?: number;
  probability12m?: number;
  probability24m?: number;
  selectedProbability?: number;
  rankWithinOfficeHorizon?: number;
  percentileWithinOfficeHorizon?: number;
  priorityTier?: string;
}

export interface PortfolioPendingGrantResponse {
  ownerId: string;
  rows: PortfolioPendingGrantRow[];
}

export interface PortfolioPagedQuery {
  limit?: number;
  offset?: number;
  q?: string;
  status?: string;
  primaryField?: string;
}

export interface PortfolioFamiliesQuery extends PortfolioPagedQuery {
  sort?: "blocking" | "priority_year";
}

export interface PortfolioThreatQuery extends PortfolioPagedQuery {
  wipoField?: string;
}

export interface PortfolioClassificationQuery extends PortfolioPagedQuery {
  classificationType?: string;
  timeseriesFields?: number;
  wipoField?: string;
}

export interface PortfolioFieldTimeseriesQuery {
  limitFields?: number;
  asOfYear?: number;
}

export interface PortfolioCitationSummaryQuery {
  asOfYear?: number;
}

export interface PortfolioCitationTimeseriesQuery {
  yearFrom?: number;
  yearTo?: number;
}

export interface PortfolioCitationFamiliesQuery extends PortfolioPagedQuery {
  wipoField?: string;
  sort?: "forward_clean" | "forward_weighted" | "early_5y" | "early_7y" | "blocking";
}

export interface PortfolioCitationAttackersQuery extends PortfolioPagedQuery {
  wipoField?: string;
  jurisdictionCode?: string;
  yearFrom?: number;
  yearTo?: number;
}

export interface PortfolioCitationFieldsQuery extends PortfolioPagedQuery {
  jurisdictionCode?: string;
  yearFrom?: number;
  yearTo?: number;
}

export interface PortfolioCitationJurisdictionsQuery extends PortfolioPagedQuery {
  wipoField?: string;
  yearFrom?: number;
  yearTo?: number;
}

export interface PortfolioCitationCpcGroupsQuery extends PortfolioPagedQuery {
  wipoField?: string;
  jurisdictionCode?: string;
  yearFrom?: number;
  yearTo?: number;
}

export interface PortfolioMarketContextQuery {
  horizon?: ForecastHorizon;
  asOfYear?: number;
}

export interface PortfolioFilingTimeseriesQuery {
  yearFrom?: number;
  yearTo?: number;
}

export interface PortfolioForecastContributorsQuery extends PortfolioPagedQuery {
  horizon?: ForecastHorizon;
  contributorScope?: string;
}

export interface PortfolioCompareTimesliceQuery {
  baseYear?: number;
  compareYear?: number;
}

export interface PortfolioPendingGrantsQuery {
  horizon?: string;
  branchJurisdictionCode?: string;
  branchWipoField?: string;
  branchLimit?: number;
}

export interface PortfolioDashboardPayload {
  overview: PortfolioOverviewPayload;
  families: PortfolioFamiliesResponse;
  fields: PortfolioFieldRowsResponse;
  forecast: PortfolioForecastPayload;
  threats: PortfolioThreatsResponse;
  classification: PortfolioClassificationResponse;
}

export interface PortfolioOwnerSearchPayload {
  query: string;
  rows: PortfolioOwnerSuggestion[];
}
