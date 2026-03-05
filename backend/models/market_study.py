"""Pydantic models for structured market study data (10-slide format)."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class MarketStudyMeta(BaseModel):
    """Metadata for the market study."""
    market_name: str = ""
    region: str = "DACH"
    research_date: str = ""
    sources: list[str] = Field(default_factory=list)


class ExecutiveSummary(BaseModel):
    """Slide 1: Management Summary."""
    title: str = ""  # Action Title, e.g. "Dental-Labore: Konsolidierung treibt Margen"
    key_findings: list[str] = Field(default_factory=list)  # 3-5 key findings
    market_verdict: str = ""  # Overall assessment (1-2 sentences)


class MarketDataPoint(BaseModel):
    """A single historical or projected data point for market sizing."""
    year: str  # "2023", "2025E", "2030P"
    value: Optional[float] = None  # In bn EUR
    label: str = ""  # e.g. "TAM Global"


class MarketSizing(BaseModel):
    """Slide 2: TAM/SAM/SOM and growth projections."""
    tam: str = ""  # "EUR X.Xbn"
    tam_year: str = ""
    sam: str = ""
    sam_year: str = ""
    som: str = ""
    cagr: Optional[float] = None  # e.g. 0.068 = 6.8%
    cagr_period: str = ""  # "2025-2033"
    methodology: str = ""  # "Top-Down" / "Bottom-Up"
    assumptions: list[str] = Field(default_factory=list)
    data_points: list[MarketDataPoint] = Field(default_factory=list)


class MarketSegment(BaseModel):
    """A single market segment."""
    name: str
    size: str = ""  # "EUR X.Xm"
    share_pct: Optional[float] = None  # 0-100
    growth_rate: str = ""
    description: str = ""


class CompetitorProfile(BaseModel):
    """Profile for a single competitor."""
    name: str
    market_share: str = ""
    revenue: str = ""
    hq: str = ""
    strengths: list[str] = Field(default_factory=list)


class CompetitiveLandscape(BaseModel):
    """Slide 4: Competitive landscape and benchmarking."""
    fragmentation: str = "medium"  # "high" / "medium" / "low"
    top_players: list[CompetitorProfile] = Field(default_factory=list)
    hhi_index: Optional[float] = None
    consolidation_trend: str = ""
    avg_company_revenue: str = ""


class TrendsDrivers(BaseModel):
    """Slide 5: Market trends and drivers."""
    growth_drivers: list[str] = Field(default_factory=list)
    headwinds: list[str] = Field(default_factory=list)
    technological_shifts: list[str] = Field(default_factory=list)
    regulatory_changes: list[str] = Field(default_factory=list)


class PestelFactor(BaseModel):
    """A single PESTEL dimension."""
    rating: str = "neutral"  # "positive" / "neutral" / "negative"
    points: list[str] = Field(default_factory=list)


class PestelAnalysis(BaseModel):
    """Slide 6: PESTEL analysis."""
    political: PestelFactor = Field(default_factory=PestelFactor)
    economic: PestelFactor = Field(default_factory=PestelFactor)
    social: PestelFactor = Field(default_factory=PestelFactor)
    technological: PestelFactor = Field(default_factory=PestelFactor)
    environmental: PestelFactor = Field(default_factory=PestelFactor)
    legal: PestelFactor = Field(default_factory=PestelFactor)


class ForceAssessment(BaseModel):
    """A single Porter's Five Forces dimension."""
    rating: str = "medium"  # "low" / "medium" / "high"
    explanation: str = ""


class PortersFiveForces(BaseModel):
    """Slide 7: Porter's Five Forces."""
    rivalry: ForceAssessment = Field(default_factory=ForceAssessment)
    buyer_power: ForceAssessment = Field(default_factory=ForceAssessment)
    supplier_power: ForceAssessment = Field(default_factory=ForceAssessment)
    threat_new_entrants: ForceAssessment = Field(default_factory=ForceAssessment)
    threat_substitutes: ForceAssessment = Field(default_factory=ForceAssessment)


class ValueChainStage(BaseModel):
    """A single value chain stage."""
    name: str
    description: str = ""
    typical_margin: str = ""


class ValueChain(BaseModel):
    """Slide 8: Value chain and business models."""
    stages: list[ValueChainStage] = Field(default_factory=list)
    dominant_business_models: list[str] = Field(default_factory=list)
    margin_distribution: str = ""


class BuyAndBuild(BaseModel):
    """Slide 9: Buy & Build potential assessment."""
    fragmentation_score: Optional[float] = None  # 1-10 scale
    platform_candidates: list[str] = Field(default_factory=list)
    add_on_profile: str = ""
    consolidation_rationale: str = ""
    estimated_targets_dach: str = ""


class StrategicRecommendation(BaseModel):
    """A single strategic recommendation."""
    title: str  # Action Title
    description: str = ""
    risk_benefit: str = ""  # "high reward / low risk"


class StrategicImplications(BaseModel):
    """Slide 10: Strategic implications and recommendations."""
    recommendations: list[StrategicRecommendation] = Field(default_factory=list)
    investment_attractiveness: str = ""  # "high" / "medium" / "low"
    key_risks: list[str] = Field(default_factory=list)


class MarketStudyData(BaseModel):
    """Complete market study data model (maps to 10 PPTX slides)."""
    meta: MarketStudyMeta = Field(default_factory=MarketStudyMeta)
    executive_summary: ExecutiveSummary = Field(default_factory=ExecutiveSummary)
    market_sizing: MarketSizing = Field(default_factory=MarketSizing)
    market_segments: list[MarketSegment] = Field(default_factory=list)
    competitive_landscape: CompetitiveLandscape = Field(default_factory=CompetitiveLandscape)
    trends_drivers: TrendsDrivers = Field(default_factory=TrendsDrivers)
    pestel: PestelAnalysis = Field(default_factory=PestelAnalysis)
    porters_five_forces: PortersFiveForces = Field(default_factory=PortersFiveForces)
    value_chain: ValueChain = Field(default_factory=ValueChain)
    buy_and_build: BuyAndBuild = Field(default_factory=BuyAndBuild)
    strategic_implications: StrategicImplications = Field(default_factory=StrategicImplications)
