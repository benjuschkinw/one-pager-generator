"""Pydantic models for the Company Sourcing feature (find similar companies)."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class CompanyProfile(BaseModel):
    """A single comparable company found by the sourcing pipeline."""
    name: str
    hq_city: str = ""
    hq_country: str = ""  # DE, AT, CH
    website: Optional[str] = None
    founded_year: Optional[int] = None
    description: str = ""

    # Industry
    industry: str = ""
    nace_code: Optional[str] = None
    sub_sector: Optional[str] = None

    # Size & scale
    revenue_eur_m: Optional[float] = None
    revenue_estimate: bool = False
    ebitda_eur_m: Optional[float] = None
    ebitda_margin_pct: Optional[float] = None
    employee_count: Optional[int] = None
    employee_estimate: bool = False

    # Business characteristics
    business_model: str = ""
    ownership_type: str = ""  # "Family-owned", "PE-backed", "Founder-led", "Public subsidiary"
    customer_segments: list[str] = Field(default_factory=list)
    key_products_services: list[str] = Field(default_factory=list)

    # Similarity
    similarity_score: float = 0.0  # 0-100
    similarity_rationale: str = ""
    similarity_dimensions: dict[str, float] = Field(default_factory=dict)

    # Data quality
    data_sources: list[str] = Field(default_factory=list)
    data_freshness: str = ""
    confidence: float = 0.0


class CompSummaryStats(BaseModel):
    """Aggregate statistics across all comparable companies."""
    count: int = 0
    avg_revenue_eur_m: Optional[float] = None
    median_revenue_eur_m: Optional[float] = None
    avg_ebitda_margin: Optional[float] = None
    avg_employees: Optional[int] = None
    country_distribution: dict[str, int] = Field(default_factory=dict)
    ownership_distribution: dict[str, int] = Field(default_factory=dict)


class CompanySourcingResult(BaseModel):
    """Full result of a company sourcing run."""
    seed_company: str
    seed_industry: str = ""
    seed_revenue_range: str = ""
    search_region: str = "DACH"
    search_criteria: dict = Field(default_factory=dict)

    companies: list[CompanyProfile] = Field(default_factory=list)
    summary: CompSummaryStats = Field(default_factory=CompSummaryStats)
    executive_summary: str = ""
