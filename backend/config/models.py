import os


def env(key: str, default: str) -> str:
    return os.environ.get(key, default)


# Models for each deep research sub-task
DEEP_RESEARCH_MODELS = {
    "im_extraction": env("MODEL_IM_EXTRACTION", "anthropic/claude-opus-4"),
    "web_research": "anthropic",        # Must use Anthropic API for web search
    "financials": "anthropic",           # Must use Anthropic API for web search
    "management": "anthropic",           # Must use Anthropic API for web search
    "market": env("MODEL_MARKET", "google/gemini-2.5-pro-preview"),
    "merge": env("MODEL_MERGE", "anthropic/claude-opus-4"),
    "verify_final": env("MODEL_VERIFY", "openai/gpt-4.1"),
}

# Per-step recheck: use different model family than the step itself
RECHECK_MODELS = {
    "anthropic": "openai/gpt-4.1",
    "openrouter": "openai/gpt-4.1",
    "google": "anthropic/claude-sonnet-4",
    "openai": "anthropic/claude-sonnet-4",
}
