import type { CoverageStatus, SupportLevel } from "@/lib/types/common";

export type SemanticVectorSpace = "abstract" | "claims";

export type SemanticCaveat = {
  code: string;
  title: string;
  detail: string;
};

export type SemanticCoverage = {
  status: CoverageStatus | "unknown";
  pct: number | null;
  coveredCount: number | null;
  denominatorCount: number | null;
  caveatText: string | null;
};

export type SemanticPagination = {
  limit: number;
  offset: number;
  returnedCount: number;
  totalCount: number | null;
};

export type SemanticMeta = {
  page: string;
  supportLevel: SupportLevel;
  artifactSources: string[];
  caveats: SemanticCaveat[];
  coverage: SemanticCoverage | null;
  pagination: SemanticPagination | null;
};

export type SemanticIdentity = {
  id: string;
  label: string;
  pageKind: string;
};

export type SemanticFamilySuggestion = {
  familyId: string;
  label: string;
  ownerNameHarmonized: string | null;
  primaryWipoField: string | null;
  familyCompositeStatus: string | null;
};

export type SemanticSummaryCard = {
  key: string;
  label: string;
  value: number | string | null;
  displayKind: "count" | "percent" | "decimal" | "text";
  note: string | null;
};

export type SemanticQueryContextItem = {
  key: string;
  label: string;
  value: string;
};

export type SemanticSearchResultRow = {
  familyId: string;
  familyTitle: string | null;
  ownerNameHarmonized: string | null;
  primaryWipoField: string | null;
  semanticSimilarity: number | null;
  familyCompositeStatus: string | null;
  familyUiBlockingPowerScore: number | null;
  oecdQualityPercentile: number | null;
  representativeStage: string | null;
  textProvenance: string | null;
  textSourceType: string | null;
  isAbstractFallback: boolean;
  familyEarliestPriorityDate: string | null;
  textExcerpt: string | null;
};

export type SemanticSearchPayload = {
  queryMode: string;
  vectorSpace: SemanticVectorSpace;
  anchorEntity: SemanticIdentity | null;
  selectedEntity: SemanticIdentity | null;
  summary: {
    anchorFamilyId?: string | null;
    anchorOwner?: string | null;
    anchorPrimaryField?: string | null;
    anchorStatus?: string | null;
    anchorTextExcerpt?: string | null;
    anchorTextProvenance?: string | null;
    queryTextExcerpt?: string | null;
    sameFieldOnly?: boolean;
    excludeSameOwner?: boolean;
  } | null;
  summaryCards: SemanticSummaryCard[];
  queryContext: SemanticQueryContextItem[];
  resultRows: SemanticSearchResultRow[];
  meta: SemanticMeta;
};

export type SemanticCompareRow = {
  key: string;
  label: string;
  value: number | string | null;
  displayKind: "count" | "percent" | "decimal" | "text";
  supported: boolean;
  note: string | null;
};

export type SemanticCompareEntitySummary = {
  role: "anchor" | "selected";
  familyId: string;
  entityLabel: string;
  ownerNameHarmonized: string | null;
  primaryWipoField: string | null;
  familyCompositeStatus: string | null;
  representativeStage: string | null;
  textProvenance: string | null;
  familyEarliestPriorityDate: string | null;
  familyUiBlockingPowerScore: number | null;
  oecdQualityPercentile: number | null;
  supportedSpaces: string[];
  supportNote: string | null;
};

export type SemanticDetailPanel = {
  side: "left" | "right";
  familyId: string;
  entityLabel: string;
  ownerNameHarmonized: string | null;
  primaryWipoField: string | null;
  familyCompositeStatus: string | null;
  familyUiBlockingPowerScore: number | null;
  oecdQualityPercentile: number | null;
  representativeStage: string | null;
  textProvenance: string | null;
  familyEarliestPriorityDate: string | null;
  supportedSpaces: string[];
  textExcerpt: string | null;
};

export type SemanticComparePayload = {
  compareKind: string;
  leftEntity: SemanticIdentity | null;
  rightEntity: SemanticIdentity | null;
  entitySummaries: SemanticCompareEntitySummary[];
  summaryCards: SemanticSummaryCard[];
  compareRows: SemanticCompareRow[];
  detailPanels: SemanticDetailPanel[];
  meta: SemanticMeta;
};
