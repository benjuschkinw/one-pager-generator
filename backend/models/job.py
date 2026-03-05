"""Pydantic models for persistent job storage."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from models.market_study import MarketStudyData
from models.one_pager import FieldFlag, OnePagerData, VerificationResult


class StepVerification(BaseModel):
    """Per-step 2nd AI recheck result."""
    verifier_model: str
    confidence: float  # 0.0 - 1.0
    flags: list[FieldFlag] = Field(default_factory=list)
    hallucination_risk: Literal["low", "medium", "high"]


class DeepResearchStep(BaseModel):
    """Result of a single deep research pipeline step."""
    model_config = ConfigDict(protected_namespaces=())

    step_name: str  # e.g. "im_extraction", "web_research"
    label: str  # Human-readable: "IM Extraction"
    model_used: str  # e.g. "anthropic/claude-opus-4"
    status: Literal["pending", "running", "done", "error", "verified"] = "pending"
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result_json: Optional[dict] = None
    verification: Optional[StepVerification] = None
    error_message: Optional[str] = None
    sources: list[str] = Field(default_factory=list)


class Job(BaseModel):
    """Full job model with all fields."""
    id: str
    company_name: str
    created_at: str
    updated_at: str
    status: Literal["pending", "researching", "completed", "failed"] = "pending"

    # Inputs
    im_filename: Optional[str] = None
    im_file_path: Optional[str] = None
    im_text: Optional[str] = None

    # Research config
    provider: Optional[str] = None
    model: Optional[str] = None
    research_mode: Literal["standard", "deep", "market"] = "standard"

    # Outputs
    research_data: Optional[OnePagerData] = None
    verification: Optional[VerificationResult] = None
    deep_research_steps: Optional[list[DeepResearchStep]] = None
    edited_data: Optional[OnePagerData] = None
    pptx_file_path: Optional[str] = None

    # Market study outputs
    market_study_data: Optional[MarketStudyData] = None
    edited_market_data: Optional[MarketStudyData] = None


class JobSummary(BaseModel):
    """Compact job info for list endpoint."""
    id: str
    company_name: str
    created_at: str
    updated_at: str
    status: Literal["pending", "researching", "completed", "failed"]
    im_filename: Optional[str] = None
    research_mode: Literal["standard", "deep", "market"] = "standard"
    has_pptx: bool = False
