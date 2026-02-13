from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class OverallCondition(str, Enum):
    EMERGING = "EMERGING"
    PEAK = "PEAK"
    DECLINING = "DECLINING"


class MetricKey(str, Enum):
    trajectory = "trajectory"
    durability = "durability"
    sustainability = "sustainability"
    timing = "timing"
    blocking = "blocking"
    innovation = "innovation"
    legal = "legal"
    market = "market"
    technology = "technology"


class Level3(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class TimeHorizon(str, Enum):
    SHORT = "SHORT"
    MID = "MID"
    LONG = "LONG"


class RiskType(str, Enum):
    AGING = "AGING"
    CROWDING = "CROWDING"
    DECLINE = "DECLINE"


class Coverage(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class PortfolioExecutiveSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    overall_condition: OverallCondition
    one_sentence_takeaway: str


class PortfolioStrengthWeaknessItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metric: MetricKey
    evidence: str
    interpretation: str


class PortfolioLicensingReadiness(BaseModel):
    model_config = ConfigDict(extra="forbid")

    level: Level3
    justification: str


class PortfolioCompetitivePositioning(BaseModel):
    model_config = ConfigDict(extra="forbid")

    relative_strength: Level3
    explanation: str


class PortfolioStrategicRecommendation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: str
    time_horizon: TimeHorizon
    rationale: str


class PortfolioRiskFlag(BaseModel):
    model_config = ConfigDict(extra="forbid")

    risk_type: RiskType
    severity: Level3
    reason: str


class PortfolioConfidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data_coverage: Coverage
    limitations: str


class PortfolioAdvisoryOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    executive_summary: Optional[PortfolioExecutiveSummary] = None
    strengths: List[PortfolioStrengthWeaknessItem] = Field(default_factory=list)
    weaknesses: List[PortfolioStrengthWeaknessItem] = Field(default_factory=list)
    licensing_readiness: Optional[PortfolioLicensingReadiness] = None
    competitive_positioning: Optional[PortfolioCompetitivePositioning] = None
    blocking_analysis: str = ""
    innovation_assessment: str = ""
    legal_health_interpretation: str = ""
    citation_dynamics_note: str = ""
    strategic_recommendations: List[PortfolioStrategicRecommendation] = Field(default_factory=list)
    risk_flags: List[PortfolioRiskFlag] = Field(default_factory=list)
    confidence: Optional[PortfolioConfidence] = None


class PatentRole(str, Enum):
    CORE = "CORE"
    SUPPORTING = "SUPPORTING"
    OPTIONAL = "OPTIONAL"


class PatentLifecycleStage(str, Enum):
    EARLY = "EARLY"
    PEAK = "PEAK"
    DECLINING = "DECLINING"


class PatentInsightItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    area: str
    evidence: str
    interpretation: str


class PatentRiskAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    risk_level: Level3
    explanation: str


class PatentConfidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data_coverage: Coverage
    limitations: str


class PatentAdvisoryOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patent_role: Optional[PatentRole] = None
    lifecycle_stage: Optional[PatentLifecycleStage] = None
    strategic_value: Optional[str] = None
    strengths: List[PatentInsightItem] = Field(default_factory=list)
    weaknesses: List[PatentInsightItem] = Field(default_factory=list)
    technology_insight: str = ""
    market_insight: str = ""
    legal_health_note: str = ""
    innovation_insight: str = ""
    blocking_insight: str = ""
    actionable_recommendations: List[str] = Field(default_factory=list)
    risk_assessment: Optional[PatentRiskAssessment] = None
    confidence: Optional[PatentConfidence] = None


# -------- Portfolio evolution advisory (separate endpoint) --------

class EvolutionTrendDirection(str, Enum):
    ACCELERATING = "ACCELERATING"
    STABILIZING = "STABILIZING"
    DECELERATING = "DECELERATING"


class PortfolioEvolutionExecutiveSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trend_direction: EvolutionTrendDirection
    one_sentence_takeaway: str


class PortfolioEvolutionYearlyItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    year: int = Field(ge=0)
    phase: OverallCondition
    yoy_growth_pct: float
    interpretation: str
    evidence: str


class PortfolioEvolutionAdvisoryOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    executive_summary: PortfolioEvolutionExecutiveSummary
    yearly: List[PortfolioEvolutionYearlyItem] = Field(default_factory=list)
    risk_flags: List[PortfolioRiskFlag] = Field(default_factory=list)
    confidence: PortfolioConfidence
