"""
Models API: view and configure AI models per pipeline step.

Provides information about which models are used for each step,
their capabilities, and allows runtime overrides.
"""

import os

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, ConfigDict

from config.models import (
    DEEP_RESEARCH_STEP_CONFIGS,
    KNOWN_MODELS,
    MARKET_RESEARCH_STEP_CONFIGS,
    ModelCapabilities,
    StepModelConfig,
    get_deep_model,
    get_market_model,
    reset_all_models,
    reset_deep_model,
    reset_market_model,
    set_deep_model,
    set_market_model,
    validate_model_for_step,
)

router = APIRouter()

ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY", "")


def _require_admin(x_admin_key: str | None):
    if not ADMIN_API_KEY:
        raise HTTPException(403, "Model editing is disabled. Set ADMIN_API_KEY env var.")
    if x_admin_key != ADMIN_API_KEY:
        raise HTTPException(401, "Invalid or missing X-Admin-Key header")


class StepModelInfo(BaseModel):
    """Full info about a step's model configuration."""
    model_config = ConfigDict(protected_namespaces=())

    step: str
    pipeline: str
    current_model: str
    default_model: str
    is_override: bool
    description: str
    why_recommended: str
    requires_web_search: bool
    requires_tool_calling: bool
    model_capabilities: ModelCapabilities | None
    warnings: list[str]


class ModelOverrideRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_id: str


@router.get("/models/known")
async def list_known_models():
    """List all known models with their capabilities."""
    return {
        model_id: caps.model_dump()
        for model_id, caps in KNOWN_MODELS.items()
    }


@router.get("/models/steps/{pipeline}")
async def list_step_configs(pipeline: str):
    """List all step model configurations for a pipeline (deep or market)."""
    if pipeline not in ("deep", "market"):
        raise HTTPException(400, "Pipeline must be 'deep' or 'market'")

    configs = DEEP_RESEARCH_STEP_CONFIGS if pipeline == "deep" else MARKET_RESEARCH_STEP_CONFIGS
    getter = get_deep_model if pipeline == "deep" else get_market_model

    result: list[dict] = []
    for step, cfg in configs.items():
        current = getter(step)
        is_override = current != cfg.model_id
        caps = KNOWN_MODELS.get(current)
        warnings = validate_model_for_step(step, current, pipeline)

        result.append(StepModelInfo(
            step=step,
            pipeline=pipeline,
            current_model=current,
            default_model=cfg.model_id,
            is_override=is_override,
            description=cfg.description,
            why_recommended=cfg.why_recommended,
            requires_web_search=cfg.requires_web_search,
            requires_tool_calling=cfg.requires_tool_calling,
            model_capabilities=caps,
            warnings=warnings,
        ).model_dump())

    return result


@router.put("/models/steps/{pipeline}/{step}")
async def override_step_model(
    pipeline: str,
    step: str,
    body: ModelOverrideRequest,
    x_admin_key: str | None = Header(None),
):
    """Override the model for a specific pipeline step. Returns warnings if any."""
    _require_admin(x_admin_key)

    if pipeline not in ("deep", "market"):
        raise HTTPException(400, "Pipeline must be 'deep' or 'market'")

    configs = DEEP_RESEARCH_STEP_CONFIGS if pipeline == "deep" else MARKET_RESEARCH_STEP_CONFIGS
    if step not in configs:
        raise HTTPException(404, f"Step '{step}' not found in {pipeline} pipeline")

    warnings = validate_model_for_step(step, body.model_id, pipeline)

    if pipeline == "deep":
        set_deep_model(step, body.model_id)
    else:
        set_market_model(step, body.model_id)

    current = get_deep_model(step) if pipeline == "deep" else get_market_model(step)
    return {
        "step": step,
        "pipeline": pipeline,
        "model_id": current,
        "warnings": warnings,
    }


@router.delete("/models/steps/{pipeline}/{step}")
async def reset_step_model(
    pipeline: str,
    step: str,
    x_admin_key: str | None = Header(None),
):
    """Reset a step's model to the default."""
    _require_admin(x_admin_key)

    if pipeline not in ("deep", "market"):
        raise HTTPException(400, "Pipeline must be 'deep' or 'market'")

    configs = DEEP_RESEARCH_STEP_CONFIGS if pipeline == "deep" else MARKET_RESEARCH_STEP_CONFIGS
    if step not in configs:
        raise HTTPException(404, f"Step '{step}' not found in {pipeline} pipeline")

    if pipeline == "deep":
        reset_deep_model(step)
    else:
        reset_market_model(step)

    current = get_deep_model(step) if pipeline == "deep" else get_market_model(step)
    return {"step": step, "pipeline": pipeline, "model_id": current, "reset": True}


@router.post("/models/reset")
async def reset_all(x_admin_key: str | None = Header(None)):
    """Reset all model overrides to defaults."""
    _require_admin(x_admin_key)
    reset_all_models()
    return {"ok": True, "message": "All model overrides reset to defaults"}
