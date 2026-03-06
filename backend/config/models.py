"""
Model configuration for all research pipelines.

Each step has a recommended model and metadata about required capabilities.
Users can override models per step at runtime via the API, but they see
warnings if the chosen model lacks required capabilities (e.g. web search).
"""

import os
from typing import Optional

from pydantic import BaseModel, ConfigDict


def env(key: str, default: str) -> str:
    return os.environ.get(key, default)


class ModelCapabilities(BaseModel):
    """Describes what a model can and cannot do."""
    web_search: bool = False        # Native web search (Anthropic API only)
    tool_calling: bool = True       # Function/tool calling support
    long_context: bool = True       # >32k context window
    structured_output: bool = True  # Reliable JSON output
    provider: str = "openrouter"    # "anthropic" | "openrouter"
    notes: str = ""                 # Caveats / notes for the user


class StepModelConfig(BaseModel):
    """Configuration for a single pipeline step's model."""
    model_config = ConfigDict(protected_namespaces=())

    model_id: str                   # e.g. "anthropic/claude-opus-4" or "anthropic" (direct API)
    recommended: bool = True        # Is this the recommended model for this step?
    requires_web_search: bool = False
    requires_tool_calling: bool = False
    description: str = ""           # What this step does
    why_recommended: str = ""       # Why this model is best for this step


# ─── Known model capabilities ──────────────────────────────────────────────

KNOWN_MODELS: dict[str, ModelCapabilities] = {
    # Anthropic direct API (web search available)
    "anthropic": ModelCapabilities(
        web_search=True,
        tool_calling=True,
        long_context=True,
        structured_output=True,
        provider="anthropic",
        notes="Uses Claude Sonnet 4 via Anthropic API with native web search.",
    ),
    # Google native API (Google Search grounding)
    "google": ModelCapabilities(
        web_search=True,
        tool_calling=True,
        long_context=True,
        structured_output=True,
        provider="google",
        notes="Uses Gemini 2.5 Pro via Google API with Google Search grounding. Cheapest option with web search.",
    ),
    # OpenRouter models
    "anthropic/claude-opus-4": ModelCapabilities(
        web_search=False,
        tool_calling=True,
        long_context=True,
        structured_output=True,
        provider="openrouter",
        notes="Claude Opus 4 via OpenRouter. No web search. Best for synthesis/merge tasks.",
    ),
    "anthropic/claude-sonnet-4": ModelCapabilities(
        web_search=False,
        tool_calling=True,
        long_context=True,
        structured_output=True,
        provider="openrouter",
        notes="Claude Sonnet 4 via OpenRouter. Fast, cheaper. Good for verification.",
    ),
    "google/gemini-2.5-pro-preview": ModelCapabilities(
        web_search=False,
        tool_calling=True,
        long_context=True,
        structured_output=True,
        provider="openrouter",
        notes="Gemini 2.5 Pro via OpenRouter. Strong reasoning, large context. No web search via OpenRouter.",
    ),
    "openai/gpt-5.4": ModelCapabilities(
        web_search=False,
        tool_calling=True,
        long_context=True,
        structured_output=True,
        provider="openrouter",
        notes="GPT-5.4 via OpenRouter. Latest frontier model, 1M+ context, excellent JSON. $2.50/M input.",
    ),
    "openai/o3": ModelCapabilities(
        web_search=False,
        tool_calling=True,
        long_context=True,
        structured_output=True,
        provider="openrouter",
        notes="o3 via OpenRouter. Reasoning model, thinks before answering. Best for verification. $2/M input.",
    ),
    "openai/gpt-5.2": ModelCapabilities(
        web_search=False,
        tool_calling=True,
        long_context=True,
        structured_output=True,
        provider="openrouter",
        notes="GPT-5.2 via OpenRouter. Strong reasoning, good for synthesis. $1.75/M input.",
    ),
    "openai/gpt-5.1": ModelCapabilities(
        web_search=False,
        tool_calling=True,
        long_context=True,
        structured_output=True,
        provider="openrouter",
        notes="GPT-5.1 via OpenRouter. Cheapest GPT-5 family model. $1.25/M input.",
    ),
    "openai/gpt-4.1": ModelCapabilities(
        web_search=False,
        tool_calling=True,
        long_context=True,
        structured_output=True,
        provider="openrouter",
        notes="GPT-4.1 via OpenRouter. Legacy model, good for cross-verification.",
    ),
    "openai/gpt-4.1-mini": ModelCapabilities(
        web_search=False,
        tool_calling=True,
        long_context=True,
        structured_output=True,
        provider="openrouter",
        notes="GPT-4.1 Mini via OpenRouter. Cheapest option for verification/recheck.",
    ),
    "anthropic/claude-haiku-4": ModelCapabilities(
        web_search=False,
        tool_calling=True,
        long_context=True,
        structured_output=True,
        provider="openrouter",
        notes="Claude Haiku 4 via OpenRouter. Fastest and cheapest Anthropic model.",
    ),
}


# ─── Deep research step configs ─────────────────────────────────────────────

DEEP_RESEARCH_STEP_CONFIGS: dict[str, StepModelConfig] = {
    "im_extraction": StepModelConfig(
        model_id=env("MODEL_IM_EXTRACTION", "google"),
        requires_web_search=False,
        description="Extract structured data from IM PDF text",
        why_recommended="Gemini 2.5 Pro: strong document comprehension at $1.25/M input (12x cheaper than Opus).",
    ),
    "web_research": StepModelConfig(
        model_id=env("MODEL_WEB_RESEARCH", "google"),
        requires_web_search=True,
        description="Web research for company basics (founding, HQ, industry, etc.)",
        why_recommended="Gemini 2.5 Pro with Google Search grounding: cheapest web search option.",
    ),
    "financials": StepModelConfig(
        model_id=env("MODEL_FINANCIALS", "anthropic"),
        requires_web_search=True,
        description="Financial deep-dive (Bundesanzeiger, North Data, company filings)",
        why_recommended="Claude Sonnet 4 with Anthropic web search: reliable for German financial data sources.",
    ),
    "management": StepModelConfig(
        model_id=env("MODEL_MANAGEMENT", "google"),
        requires_web_search=True,
        description="Management team & org structure research",
        why_recommended="Gemini 2.5 Pro with Google Search: effective for impressum/LinkedIn lookups.",
    ),
    "market": StepModelConfig(
        model_id=env("MODEL_MARKET", "openai/gpt-5.4"),
        requires_web_search=False,
        description="Market landscape & competitive positioning analysis",
        why_recommended="GPT-5.4: latest frontier model, strong reasoning for market analysis. $2.50/M input.",
    ),
    "merge": StepModelConfig(
        model_id=env("MODEL_MERGE", "openai/gpt-5.4"),
        requires_web_search=False,
        description="Merge all sub-results into a single OnePagerData JSON",
        why_recommended="GPT-5.4: latest frontier, excellent at synthesizing structured data. $2.50/M input.",
    ),
    "verify_final": StepModelConfig(
        model_id=env("MODEL_VERIFY", "openai/o3"),
        requires_web_search=False,
        description="Cross-verify merged output for consistency and hallucinations",
        why_recommended="o3: reasoning model that thinks before answering, catches plausibility issues. $2/M input.",
    ),
}

MARKET_RESEARCH_STEP_CONFIGS: dict[str, StepModelConfig] = {
    "market_sizing": StepModelConfig(
        model_id=env("MODEL_MARKET_SIZING", "google"),
        requires_web_search=True,
        description="Research TAM/SAM/SOM, CAGR, and market size data points",
        why_recommended="Gemini 2.5 Pro with Google Search grounding: finds real market data at $1.25/M input.",
    ),
    "segmentation": StepModelConfig(
        model_id=env("MODEL_MARKET_SEGMENTATION", "google"),
        requires_web_search=True,
        description="Identify market segments, sizes, shares, and growth rates",
        why_recommended="Gemini 2.5 Pro with Google Search: reliable segment research.",
    ),
    "competition": StepModelConfig(
        model_id=env("MODEL_MARKET_COMPETITION", "google"),
        requires_web_search=True,
        description="Competitive landscape: top players, HHI, fragmentation, consolidation",
        why_recommended="Gemini 2.5 Pro with Google Search: finds real competitor data.",
    ),
    "trends_pestel": StepModelConfig(
        model_id=env("MODEL_MARKET_TRENDS", "openai/gpt-5.4"),
        requires_web_search=False,
        description="Market trends, growth drivers, headwinds, and PESTEL analysis",
        why_recommended="GPT-5.4: latest frontier, strong analytical reasoning for trend analysis. $2.50/M input.",
    ),
    "porters_value_chain": StepModelConfig(
        model_id=env("MODEL_MARKET_PORTERS", "anthropic"),
        requires_web_search=True,
        description="Sourcing dynamics, PE deal multiples, EBITDA benchmarks, trading comps, Porter's Five Forces, value chain",
        why_recommended="Claude Sonnet 4 with Anthropic web search: deep M&A/PE knowledge for multiples.",
    ),
    "buy_and_build": StepModelConfig(
        model_id=env("MODEL_MARKET_BNB", "openai/gpt-5.4"),
        requires_web_search=False,
        description="Buy & Build potential: fragmentation score, platform candidates, add-on profiles",
        why_recommended="GPT-5.4: latest frontier model, strong M&A analysis. $2.50/M input.",
    ),
    "merge": StepModelConfig(
        model_id=env("MODEL_MARKET_MERGE", "openai/gpt-5.4"),
        requires_web_search=False,
        description="Merge all sub-results into a single MarketStudyData JSON",
        why_recommended="GPT-5.4: latest frontier, excellent at synthesizing structured output. $2.50/M input.",
    ),
    "verify_final": StepModelConfig(
        model_id=env("MODEL_MARKET_VERIFY", "openai/o3"),
        requires_web_search=False,
        description="Cross-verify merged output for consistency and hallucinations",
        why_recommended="o3: reasoning model, thinks before answering, catches plausibility issues. $2/M input.",
    ),
}

# ─── Runtime overrides (mutable, updated via API) ───────────────────────────

_deep_overrides: dict[str, str] = {}
_market_overrides: dict[str, str] = {}


def get_deep_model(step: str) -> str:
    """Get the model for a deep research step, with runtime override support."""
    return _deep_overrides.get(step, DEEP_RESEARCH_STEP_CONFIGS[step].model_id)


def get_market_model(step: str) -> str:
    """Get the model for a market research step, with runtime override support."""
    return _market_overrides.get(step, MARKET_RESEARCH_STEP_CONFIGS[step].model_id)


def set_deep_model(step: str, model_id: str) -> None:
    """Override the model for a deep research step at runtime."""
    _deep_overrides[step] = model_id


def set_market_model(step: str, model_id: str) -> None:
    """Override the model for a market research step at runtime."""
    _market_overrides[step] = model_id


def reset_deep_model(step: str) -> None:
    """Reset a deep research step to its default model."""
    _deep_overrides.pop(step, None)


def reset_market_model(step: str) -> None:
    """Reset a market research step to its default model."""
    _market_overrides.pop(step, None)


def reset_all_models() -> None:
    """Reset all model overrides to defaults."""
    _deep_overrides.clear()
    _market_overrides.clear()


def validate_model_for_step(
    step: str, model_id: str, pipeline: str = "deep"
) -> list[str]:
    """
    Validate a model choice for a step. Returns a list of warnings (empty = OK).
    """
    configs = DEEP_RESEARCH_STEP_CONFIGS if pipeline == "deep" else MARKET_RESEARCH_STEP_CONFIGS
    if step not in configs:
        return [f"Unknown step: {step}"]

    step_cfg = configs[step]
    caps = KNOWN_MODELS.get(model_id)
    warnings: list[str] = []

    if caps is None:
        warnings.append(
            f"Model '{model_id}' is not in the known models list. "
            "Capabilities cannot be verified — use at your own risk."
        )
        return warnings

    if step_cfg.requires_web_search and not caps.web_search:
        warnings.append(
            f"Step '{step}' requires web search, but '{model_id}' does not support it. "
            "Only 'anthropic' (Anthropic direct API) supports native web search. "
            "Results may be lower quality without web access."
        )

    if step_cfg.requires_tool_calling and not caps.tool_calling:
        warnings.append(
            f"Step '{step}' requires tool calling, but '{model_id}' may not support it."
        )

    return warnings


# ─── Backward-compatible dicts (used by existing pipeline code) ──────────────

# These are dynamic properties that read from overrides + defaults
def _build_deep_dict() -> dict[str, str]:
    return {step: get_deep_model(step) for step in DEEP_RESEARCH_STEP_CONFIGS}


def _build_market_dict() -> dict[str, str]:
    return {step: get_market_model(step) for step in MARKET_RESEARCH_STEP_CONFIGS}


class _DynamicModelDict(dict):
    """Dict that reads from overrides at access time."""
    def __init__(self, getter):
        self._getter = getter
        super().__init__()

    def __getitem__(self, key):
        return self._getter(key)

    def get(self, key, default=None):
        try:
            return self._getter(key)
        except KeyError:
            return default

    def __contains__(self, key):
        configs = DEEP_RESEARCH_STEP_CONFIGS if self._getter == get_deep_model else MARKET_RESEARCH_STEP_CONFIGS
        return key in configs

    def keys(self):
        configs = DEEP_RESEARCH_STEP_CONFIGS if self._getter == get_deep_model else MARKET_RESEARCH_STEP_CONFIGS
        return configs.keys()

    def values(self):
        return [self._getter(k) for k in self.keys()]

    def items(self):
        return [(k, self._getter(k)) for k in self.keys()]

    def __iter__(self):
        return iter(self.keys())

    def __len__(self):
        configs = DEEP_RESEARCH_STEP_CONFIGS if self._getter == get_deep_model else MARKET_RESEARCH_STEP_CONFIGS
        return len(configs)


DEEP_RESEARCH_MODELS = _DynamicModelDict(get_deep_model)
MARKET_RESEARCH_MODELS = _DynamicModelDict(get_market_model)

# Per-step recheck: use different model family than the step itself
RECHECK_MODELS = {
    "anthropic": "openai/gpt-5.1",
    "openrouter": "openai/gpt-5.1",
    "google": "openai/gpt-5.1",
    "openai": "anthropic/claude-sonnet-4",
}
