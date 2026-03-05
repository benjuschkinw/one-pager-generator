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
        notes="Uses Claude Opus 4 via Anthropic API. Only provider with native web search.",
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
    "openai/gpt-4.1": ModelCapabilities(
        web_search=False,
        tool_calling=True,
        long_context=True,
        structured_output=True,
        provider="openrouter",
        notes="GPT-4.1 via OpenRouter. Good for cross-verification (different model family).",
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
        model_id=env("MODEL_IM_EXTRACTION", "anthropic/claude-opus-4"),
        requires_web_search=False,
        description="Extract structured data from IM PDF text",
        why_recommended="Opus 4 has the best document comprehension for extracting complex financial data from PDFs.",
    ),
    "web_research": StepModelConfig(
        model_id="anthropic",
        requires_web_search=True,
        description="Web research for company basics (founding, HQ, industry, etc.)",
        why_recommended="Requires native web search — only available via Anthropic API.",
    ),
    "financials": StepModelConfig(
        model_id="anthropic",
        requires_web_search=True,
        description="Financial deep-dive (Bundesanzeiger, North Data, company filings)",
        why_recommended="Requires native web search to find public financial filings.",
    ),
    "management": StepModelConfig(
        model_id="anthropic",
        requires_web_search=True,
        description="Management team & org structure research",
        why_recommended="Requires native web search for LinkedIn, Handelsregister lookups.",
    ),
    "market": StepModelConfig(
        model_id=env("MODEL_MARKET", "google/gemini-2.5-pro-preview"),
        requires_web_search=False,
        description="Market landscape & competitive positioning analysis",
        why_recommended="Gemini 2.5 Pro has strong reasoning for market analysis. Uses different model family for diversity.",
    ),
    "merge": StepModelConfig(
        model_id=env("MODEL_MERGE", "anthropic/claude-opus-4"),
        requires_web_search=False,
        description="Merge all sub-results into a single OnePagerData JSON",
        why_recommended="Opus 4 excels at synthesizing multiple data sources into structured output.",
    ),
    "verify_final": StepModelConfig(
        model_id=env("MODEL_VERIFY", "openai/gpt-4.1"),
        requires_web_search=False,
        description="Cross-verify merged output for consistency and hallucinations",
        why_recommended="GPT-4.1 provides independent verification from a different model family.",
    ),
}

MARKET_RESEARCH_STEP_CONFIGS: dict[str, StepModelConfig] = {
    "market_sizing": StepModelConfig(
        model_id="anthropic",
        requires_web_search=True,
        description="Research TAM/SAM/SOM, CAGR, and market size data points",
        why_recommended="Requires web search to find market reports and size estimates.",
    ),
    "segmentation": StepModelConfig(
        model_id="anthropic",
        requires_web_search=True,
        description="Identify market segments, sizes, shares, and growth rates",
        why_recommended="Requires web search for segment-level data from industry reports.",
    ),
    "competition": StepModelConfig(
        model_id="anthropic",
        requires_web_search=True,
        description="Competitive landscape: top players, HHI, fragmentation, consolidation",
        why_recommended="Requires web search for competitor data and market share info.",
    ),
    "trends_pestel": StepModelConfig(
        model_id=env("MODEL_MARKET_TRENDS", "google/gemini-2.5-pro-preview"),
        requires_web_search=False,
        description="Market trends, growth drivers, headwinds, and PESTEL analysis",
        why_recommended="Gemini 2.5 Pro has strong analytical reasoning. Different model family for diversity.",
    ),
    "porters_value_chain": StepModelConfig(
        model_id="anthropic",
        requires_web_search=True,
        description="Porter's Five Forces and industry value chain mapping",
        why_recommended="Requires web search for industry structure data.",
    ),
    "buy_and_build": StepModelConfig(
        model_id="anthropic",
        requires_web_search=True,
        description="Buy & Build potential: fragmentation score, platform candidates, add-on profiles",
        why_recommended="Requires web search for fragmentation and M&A data.",
    ),
    "merge": StepModelConfig(
        model_id=env("MODEL_MARKET_MERGE", "anthropic/claude-opus-4"),
        requires_web_search=False,
        description="Merge all sub-results into a single MarketStudyData JSON",
        why_recommended="Opus 4 excels at synthesizing research into structured output.",
    ),
    "verify_final": StepModelConfig(
        model_id=env("MODEL_MARKET_VERIFY", "openai/gpt-4.1"),
        requires_web_search=False,
        description="Cross-verify merged output for consistency and hallucinations",
        why_recommended="GPT-4.1 provides independent verification from a different model family.",
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
    "anthropic": "openai/gpt-4.1",
    "openrouter": "openai/gpt-4.1",
    "google": "anthropic/claude-sonnet-4",
    "openai": "anthropic/claude-sonnet-4",
}
