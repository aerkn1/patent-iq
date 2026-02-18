/**
 * Patent Page API Contract Types v1
 * Matches backend API response structure
 */

export type OwnerDTO = {
  owner_id: number;
  name: string;
  country: string;
};

export type ScoreTier = string;

export type ScoreBlock = {
  raw: number;
  percentile: number;
  tier: ScoreTier;
};

export type TechnologyAxis = {
  axis_score: number;
  percentile_global: number;
  tier: string;
};

export type MarketAxis = {
  axis_score: number;
  percentile_global: number;
  tier: string;
};

export type CitationsDTO = {
  backward: { count: number; x_normalized: number };
  forward: { count: number; x_normalized: number };
  family_citations: number;
};

export type CPCItem = { code: string; weight: number };

export type IndustryItem = { code: string; weight: number };

export type PatentCoreDTO = {
  appln_id: number;
  title: string;
  application_date: string;
  publication_date: string;
  grant_date: string;
  patent_age_years: number;
  jurisdiction: string;
  family_id: number;
  status: string;
  owners: OwnerDTO[];
  patent_category?: string;
};

export type SimilarityDTO = {
  similar_patents_available: boolean;
  similarity_vector_id: string;
};

export type MetadataDTO = {
  contract_version: string;
  data_snapshot: string;
  confidence: string;
};

export type LegalStrengthScore = {
  raw: number;
  percentile: number;
};

export type RelativePositioning = {
  blocking_power: {
    percentile_global: number;
    tier: string;
  };
  licensing_readiness: {
    percentile_global: number;
    tier: string;
  };
};

export type FamilyData = {
  family_members_count: number;
  family_jurisdiction_count: number;
  major_office_grant_auths: string[];
  family_cpc_subclass_count: number;
};

export type PatentPageResponse = {
  patent: PatentCoreDTO;
  family: FamilyData;
  scores: {
    blocking_power: ScoreBlock;
    licensing_readiness: ScoreBlock;
    legal_strength: LegalStrengthScore;
  };
  technology: TechnologyAxis;
  market: MarketAxis;
  citations: CitationsDTO;
  relative_positioning: RelativePositioning;
  similarity: SimilarityDTO;
  metadata: MetadataDTO;
};

// Advanced Analysis Types (Updated to match actual API response)
export type TechnologyDistribution = {
  cpc_subclasses: CPCItem[];
};

export type TechnologyDiversification = {
  entropy: number;
  normalized: number;
  interpretation: string;
};

export type TechnologyAnalysis = {
  distribution: TechnologyDistribution;
  diversification: TechnologyDiversification;
};

export type MarketDistribution = {
  industries: IndustryItem[];
};

export type MarketDiversification = {
  entropy: number;
  normalized: number;
  interpretation: string;
};

export type MarketAnalysis = {
  distribution: MarketDistribution;
  diversification: MarketDiversification;
};

export type BackwardCitations = {
  total: number;
  x_patent: number;
  y_patent: number;
  x_npl: number;
  y_npl: number;
};

export type ForwardCitations = {
  total: number;
  x_patent: number;
  y_patent: number;
};

export type SelfCitations = {
  forward: number;
  backward: number;
  self_forward_rate: number;
  self_blocking_rate: number;
};

export type CitationsAnalysis = {
  backward: BackwardCitations;
  forward: ForwardCitations;
  self_citations: SelfCitations;
};

export type BlockingPowerBreakdown = {
  dimensions: {
    technology: {
      axis_score: number;
    };
    market: {
      axis_score: number;
    };
    legal: {
      legal_strength_score: number;
    };
  };
  diagnostics: {
    forward_impact_score: number;
    family_breadth_normalized: number;
    tech_breadth_penalty: number;
    self_blocking_rate: number;
  };
};

export type LegalAnalysis = {
  opposition_count: number;
  lapse_count: number;
  renewal_payment_count: number;
  legal_uncertainty: boolean;
};

export type InnovationAnalysis = {
  innovation_score: number;
  tech_field_influence: number;
  field_attention: number;
};

export type Ranking = {
  rank_global: number;
  percentile_global: number;
};

export type Rankings = {
  blocking_power: Ranking;
  technology_axis: Ranking;
  market_axis: Ranking;
};

export type AdvancedMetadata = {
  contract_version: string;
  confidence: string;
};

export type PatentAnalysisResponse = {
  technology: TechnologyAnalysis;
  market: MarketAnalysis;
  citations: CitationsAnalysis;
  blocking_power_breakdown: BlockingPowerBreakdown;
  legal: LegalAnalysis;
  innovation: InnovationAnalysis;
  rankings: Rankings;
  metadata: AdvancedMetadata;
};

// Portfolio Overview Types
export type PortfolioSize = {
  n_patents: number;
  n_unique_patents: number;
  size_bucket: string;
};

export type PortfolioInfo = {
  owner_id: number;
  owner_name: string;
  owner_type: string;
  country: string;
  size: PortfolioSize;
  status_counts: {
    total: number;
    active: number;
    abandoned: number;
  };
};

export type PortfolioRadar = {
  technology: number;
  market: number;
  blocking: number;
  legal: number;
  licensing: number;
};

export type PortfolioStrength = {
  blocking_power: {
    raw: number;
    percentile: number;
  };
  licensing_readiness: {
    raw: number;
    percentile: number;
  };
  legal_strength: {
    raw: number;
  };
  portfolio_general: {
    power_score: number;
  };
};

export type PortfolioRanking = {
  portfolio_power_score: number;
  percentile_global: number;
  rank_global: number;
  tier: string;
};

export type PortfolioHealth = {
  abandoned_ratio: number;
  legal_unknown_ratio: number;
};

export type GlobalPositioning = {
  portfolio_percentile: number;
  portfolio_rank: number;
  portfolio_tier: string;
};

export type PeerPositioning = {
  peer_group_id: string;
  peer_percentile: number;
  peer_class: string;
  peer_zscore: number;
  n_peers: number;
};

export type PortfolioTechnologyDiversification = {
  entropy_norm: number;
  top_k_share: number;
  long_tail_share: number;
  interpretation: string;
};

export type CPCCode = {
  code: string;
  weight: number;
};

export type TechnologyProfile = {
  axis_score: number;
  diversification: PortfolioTechnologyDiversification;
  top_cpc_classes: CPCCode[];
};

export type PortfolioMarketDiversification = {
  entropy_norm: number;
  top_k_share: number;
  long_tail_share: number;
  interpretation: string;
};

export type IndustryCode = {
  code: string;
  weight: number;
};

export type MarketProfile = {
  axis_score: number;
  diversification: PortfolioMarketDiversification;
  top_industries: IndustryCode[];
};

export type PortfolioFamilyMetrics = {
  active_patent_families: number;
  effective_patents: number;
  avg_family_size: number;
  avg_jurisdiction_reach: number;
  major_office_coverage: number;
};

export type PortfolioGrantCoverage = {
  EP: number;
  US: number;
  CN: number;
  JP: number;
  KR: number;
};
export type PortfolioGrantMixItem = {
  publn_auth: string;
  granted_share: number;
};

export type PortfolioOverviewResponse = {
  portfolio: PortfolioInfo;
  radar: PortfolioRadar;
  strength: PortfolioStrength;
  ranking: PortfolioRanking;
  health: PortfolioHealth;
  global_positioning: GlobalPositioning;
  peer_positioning: PeerPositioning;
  technology_profile: TechnologyProfile;
  market_profile: MarketProfile;
  family_metrics: PortfolioFamilyMetrics;
  grant_coverage: PortfolioGrantCoverage;
  grant_mix: PortfolioGrantMixItem[];
  metadata: {
    contract_version: string;
    confidence: string;
  };
};

// Portfolio Analytics Types
export type PortfolioAnalyticsPortfolio = {
  owner_id: number;
};

export type CategoryCounts = {
  [key: string]: number;
};

export type CategoryShares = {
  [key: string]: number;
};

export type Categories = {
  counts: CategoryCounts;
  shares: CategoryShares;
  portfolio_category: string;
};

export type CitationBucket = {
  bucket: string;
  count: number;
};

export type CitationDistribution = {
  forward_buckets: CitationBucket[];
  backward_buckets: CitationBucket[];
};

export type PortfolioSelfCitations = {
  forward_total: number;
  backward_total: number;
  self_forward_rate: number;
  self_backward_rate: number;
  avg_self_forward_rate: number;
  avg_self_blocking_rate: number;
};

export type Citations = {
  forward_total: number;
  backward_total: number;
  backward_npl_total: number;
  self_citations: PortfolioSelfCitations;
  distribution: CitationDistribution;
};

export type Legal = {
  n_patents: number;
  abandoned_ratio: number;
  legal_unknown_ratio: number;
  legal_strength_avg: number;
  maintenance_profile: string;
};

export type BlockingPowerDriver = {
  forward_impact_score: number;
  family_breadth_normalized: number;
  tech_breadth_penalty: number;
  self_blocking_rate: number;
};

export type TopPatent = {
  appln_id: number;
  blocking_power_pct?: number;
  innovation_score?: number;
};

export type BlockingPower = {
  drivers: BlockingPowerDriver;
  dominant_driver: string;
  top_patents: TopPatent[];
};

export type Innovation = {
  innovation_score_avg: number;
  innovation_score_median: number;
  h_index_proxy_avg: number;
  field_normalized_citations_avg: number;
  top_patents: TopPatent[];
};

export type PortfolioAnalyticsResponse = {
  portfolio: PortfolioAnalyticsPortfolio;
  categories: Categories;
  citations: Citations;
  legal: Legal;
  blocking_power: BlockingPower;
  innovation: Innovation;
  metadata: {
    contract_version: string;
    data_snapshot: string;
    confidence: string;
  };
};

// Portfolio Discover Types
export type PortfolioDiscoverResult = {
  rank: number;
  owner_id: number;
  owner_name: string;
  n_patents: number;
  portfolio_power_pct: number;
  adjusted_power_score: number;
  portfolio_tier: string;
  peer_class: string | null;
};

export type PortfolioDiscoverResponse = {
  query: {
    dimension: "CPC" | "INDUSTRY" | "COUNTRY";
    value: string;
    limit: number;
  };
  results: PortfolioDiscoverResult[];
  metadata: {
    contract_version: string;
    data_snapshot: string;
  };
};

// Portfolio Patents Types
export type PortfolioPatent = {
  appln_id: number;
  appln_title: string;
  patent_category: "CROWN_JEWEL" | "FORTRESS" | "HIDDEN_GEM" | "CORE_ASSET" | "DEADWOOD";
  blocking_power_pct: number | null;
  innovation_score: number | null;
  legal_strength: number | null;
  forward_patent_citation_count: number;
  is_abandoned: boolean;
  publn_auth: string; // e.g., "US", "EP", "WO"
  filing_date: string;
};

export type PortfolioPatentsResponse = {
  portfolio: {
    owner_id: number;
  };
  pagination: {
    total: number;
    limit: number;
    offset: number;
  };
  patents: PortfolioPatent[];
  metadata: {
    contract_version: string;
    data_snapshot: string;
  };
};

export type PortfolioCategoryCounts = {
  CROWN_JEWEL: number;
  FORTRESS: number;
  HIDDEN_GEM: number;
  CORE_ASSET: number;
  DEADWOOD: number;
};

// Portfolio Licensing Types
export type OverlapType = "CPC" | "INDUSTRY" | "CITATION" | "MIXED";
export type OverlapStrength = "HIGH" | "MEDIUM" | "LOW";
export type RelativeIPStrength = "WEAKER" | "SIMILAR" | "STRONGER";
export type StrategicRole = "LIKELY_LICENSEE" | "COMPETITOR" | "NEUTRAL";
export type LeverageProfile = "STRONG" | "BALANCED" | "WEAK";
export type ConfidenceLevel = "HIGH" | "MEDIUM" | "LOW";

export type CPCOverlap = {
  code: string;
  weight: number;
  percentage: number;
};

export type IndustryOverlap = {
  code: string;
  weight: number;
  percentage: number;
};

export type LicenseeCandidate = {
  rank: number;
  owner_id: number;
  owner_name: string;
  overlap_type: OverlapType;
  overlap_strength: OverlapStrength;
  relative_ip_strength: RelativeIPStrength;
  strategic_role: StrategicRole;
  evidence: {
    why_appears: string[];
    cpc_overlap: CPCOverlap[];
    industry_overlap: IndustryOverlap[];
    risk_note: string;
  };
};

export type PortfolioLicensingResponse = {
  portfolio: {
    owner_id: number;
  };
  summary: {
    potential_licensee_count: number;
    primary_overlap_type: OverlapType;
    portfolio_leverage_profile: LeverageProfile;
    confidence_level: ConfidenceLevel;
  };
  candidates: LicenseeCandidate[];
  metadata: {
    contract_version: string;
    data_snapshot: string;
  };
};


// Licensing Candidates Types
export type CandidateProfile = {
  owner_id: number;
  owner_name: string;
  country: string;
  peer_class: string;
  portfolio_size: number;
};

export type OverlapMetrics = {
  industry_overlap_score: number;
  cpc_overlap_score: number;
  shared_industry_codes: string[];
  shared_cpc_codes: string[];
};

export type LicensingCandidateResult = {
  rank: number;
  candidate: CandidateProfile;
  overlap: OverlapMetrics;
};

export type PortfolioLicensingCandidatesResponse = {
  portfolio: {
    owner_id: number;
  };
  pagination: {
    limit: number;
    offset: number;
    returned: number;
  };
  results: LicensingCandidateResult[];
  metadata: {
    contract_version: string;
    data_snapshot: string;
  };
};
