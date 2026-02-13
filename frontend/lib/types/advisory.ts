export type Coverage = "HIGH" | "MEDIUM" | "LOW"
export type Level3 = "LOW" | "MEDIUM" | "HIGH"

export type PortfolioOverallCondition = "EMERGING" | "PEAK" | "DECLINING"
export type PortfolioMetricKey = "trajectory" | "durability" | "sustainability" | "timing" | "blocking" | "innovation" | "legal" | "market" | "technology"
export type TimeHorizon = "SHORT" | "MID" | "LONG"
export type RiskType = "AGING" | "CROWDING" | "DECLINE"

export type PortfolioAdvisoryOutput = {
  executive_summary: {
    overall_condition: PortfolioOverallCondition
    one_sentence_takeaway: string
  }
  strengths: Array<{
    metric: PortfolioMetricKey
    evidence: string
    interpretation: string
  }>
  weaknesses: Array<{
    metric: PortfolioMetricKey
    evidence: string
    interpretation: string
  }>
  licensing_readiness: {
    level: Level3
    justification: string
  }
  competitive_positioning: {
    relative_strength: Level3
    explanation: string
  }
  blocking_analysis: string
  innovation_assessment: string
  legal_health_interpretation: string
  citation_dynamics_note: string
  strategic_recommendations: Array<{
    action: string
    time_horizon: TimeHorizon
    rationale: string
  }>
  risk_flags: Array<{
    risk_type: RiskType
    severity: Level3
    reason: string
  }>
  confidence: {
    data_coverage: Coverage
    limitations: string
  }
}

export type PatentRole = "CORE" | "SUPPORTING" | "OPTIONAL"
export type PatentLifecycleStage = "EARLY" | "PEAK" | "DECLINING"

export type PatentInsightItem = {
  area: string
  evidence: string
  interpretation: string
}

export type PatentAdvisoryOutput = {
  patent_role?: PatentRole
  lifecycle_stage?: PatentLifecycleStage
  strategic_value?: string
  strengths?: PatentInsightItem[]
  weaknesses?: PatentInsightItem[]
  technology_insight?: string
  market_insight?: string
  legal_health_note?: string
  innovation_insight?: string
  blocking_insight?: string
  actionable_recommendations?: string[]
  risk_assessment?: {
    risk_level: Level3
    explanation: string
  }
  confidence?: {
    data_coverage: Coverage
    limitations: string
  }
}

export type EvolutionTrendDirection = "ACCELERATING" | "STABILIZING" | "DECELERATING"

export type PortfolioEvolutionAdvisoryOutput = {
  executive_summary: {
    trend_direction: EvolutionTrendDirection
    one_sentence_takeaway: string
  }
  yearly: Array<{
    year: number
    phase: PortfolioOverallCondition
    yoy_growth_pct: number
    interpretation: string
    evidence: string
  }>
  risk_flags: Array<{
    risk_type: RiskType
    severity: Level3
    reason: string
  }>
  confidence: {
    data_coverage: Coverage
    limitations: string
  }
}
