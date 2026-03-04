"""Pydantic models for the One-Pager data schema."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class CriterionStatus(str, Enum):
    FULFILLED = "fulfilled"
    QUESTIONS = "questions"
    NOT_INTEREST = "not_interest"


class Meta(BaseModel):
    source: str = ""
    im_received: str = ""
    loi_deadline: str = ""
    status: str = ""


class Header(BaseModel):
    label: str = "One Pager"
    company_name: str = ""
    tagline: str = ""


class KeyFacts(BaseModel):
    founded: str = ""
    hq: str = ""
    website: str = ""
    industry: str = ""
    niche: str = ""
    revenue: str = ""
    revenue_year: str = ""
    ebitda: str = ""
    ebitda_year: str = ""
    management: list[str] = Field(default_factory=list)
    employees: str = ""


class InvestmentRationale(BaseModel):
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)


class RevenueSegment(BaseModel):
    name: str
    pct: float
    growth: Optional[str] = None


class RevenueSplit(BaseModel):
    segments: list[RevenueSegment] = Field(default_factory=list)
    total: str = ""


class Financials(BaseModel):
    years: list[str] = Field(default_factory=list)
    revenue: list[Optional[float]] = Field(default_factory=list)
    ebitda: list[Optional[float]] = Field(default_factory=list)
    ebitda_margin: list[Optional[float]] = Field(default_factory=list)
    da_pct: Optional[float] = None


class InvestmentCriteria(BaseModel):
    ebitda_1m: CriterionStatus = CriterionStatus.QUESTIONS
    dach: CriterionStatus = CriterionStatus.QUESTIONS
    ebitda_margin_10: CriterionStatus = CriterionStatus.QUESTIONS
    majority_stake: CriterionStatus = CriterionStatus.QUESTIONS
    revenue_split: CriterionStatus = CriterionStatus.QUESTIONS
    digitization: CriterionStatus = CriterionStatus.QUESTIONS
    asset_light: CriterionStatus = CriterionStatus.QUESTIONS
    buy_and_build: CriterionStatus = CriterionStatus.QUESTIONS
    esg: CriterionStatus = CriterionStatus.QUESTIONS
    market_fragmentation: CriterionStatus = CriterionStatus.QUESTIONS
    acquisition_vertical: CriterionStatus = CriterionStatus.QUESTIONS
    acquisition_horizontal: CriterionStatus = CriterionStatus.QUESTIONS
    acquisition_geographical: CriterionStatus = CriterionStatus.QUESTIONS


class OnePagerData(BaseModel):
    """Complete One-Pager data model matching the slide schema."""

    meta: Meta = Field(default_factory=Meta)
    header: Header = Field(default_factory=Header)
    investment_thesis: str = ""
    key_facts: KeyFacts = Field(default_factory=KeyFacts)
    description: list[str] = Field(default_factory=list)
    product_portfolio: list[str] = Field(default_factory=list)
    investment_rationale: InvestmentRationale = Field(
        default_factory=InvestmentRationale
    )
    revenue_split: RevenueSplit = Field(default_factory=RevenueSplit)
    financials: Financials = Field(default_factory=Financials)
    investment_criteria: InvestmentCriteria = Field(
        default_factory=InvestmentCriteria
    )


class FieldFlag(BaseModel):
    """A verification flag for a specific field."""
    field: str
    severity: str = "warning"  # "warning", "error", "info"
    message: str


class VerificationResult(BaseModel):
    """Result of cross-checking the AI-generated data."""
    verified: bool = False
    confidence: float = 0.0  # 0.0 to 1.0
    flags: list[FieldFlag] = Field(default_factory=list)
    verifier_model: str = ""


class ResearchResponse(BaseModel):
    """Extended research response with verification."""
    data: OnePagerData
    verification: Optional[VerificationResult] = None
    job_id: Optional[str] = None


class ResearchRequest(BaseModel):
    company_name: str
    im_text: Optional[str] = None


class GenerateRequest(BaseModel):
    data: OnePagerData
