from __future__ import annotations

from enum import Enum
from typing import List

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

    executive_summary: PortfolioExecutiveSummary
    strengths: List[PortfolioStrengthWeaknessItem] = Field(default_factory=list)
    weaknesses: List[PortfolioStrengthWeaknessItem] = Field(default_factory=list)
    licensing_readiness: PortfolioLicensingReadiness
    competitive_positioning: PortfolioCompetitivePositioning
    strategic_recommendations: List[PortfolioStrategicRecommendation] = Field(default_factory=list)
    risk_flags: List[PortfolioRiskFlag] = Field(default_factory=list)
    confidence: PortfolioConfidence


class PatentRole(str, Enum):
    CORE = "CORE"
    SUPPORTING = "SUPPORTING"
    OPTIONAL = "OPTIONAL"


class PatentLifecycleStage(str, Enum):
    EARLY = "EARLY"
    PEAK = "PEAK"
    DECLINING = "DECLINING"


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

    patent_role: PatentRole
    lifecycle_stage: PatentLifecycleStage
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    strategic_value: str
    risk_assessment: PatentRiskAssessment
    confidence: PatentConfidence


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
