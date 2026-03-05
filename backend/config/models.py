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

# Models for each market research sub-task
MARKET_RESEARCH_MODELS = {
    "market_sizing": "anthropic",           # Web search for market size data
    "segmentation": "anthropic",            # Web search for segment data
    "competition": "anthropic",             # Web search for competitor data
    "trends_pestel": env("MODEL_MARKET_TRENDS", "google/gemini-2.5-pro-preview"),
    "porters_value_chain": "anthropic",     # Web search for industry structure
    "buy_and_build": "anthropic",           # Web search for fragmentation data
    "merge": env("MODEL_MARKET_MERGE", "anthropic/claude-opus-4"),
    "verify_final": env("MODEL_MARKET_VERIFY", "openai/gpt-4.1"),
}

# Per-step recheck: use different model family than the step itself
RECHECK_MODELS = {
    "anthropic": "openai/gpt-4.1",
    "openrouter": "openai/gpt-4.1",
    "google": "anthropic/claude-sonnet-4",
    "openai": "anthropic/claude-sonnet-4",
}
