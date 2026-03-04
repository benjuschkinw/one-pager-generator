"""
AI Research Pipeline: uses Claude API or OpenRouter to research a company
and fill the One-Pager data schema.

Supports:
- Anthropic provider: Claude with web search + domain filtering
- OpenRouter provider: Any model via OpenAI-compatible API (no web search)
- PDF extraction from Information Memorandums
- Multi-turn tool use with pause_turn handling (Anthropic only)
- Citation tracking for audit trails (Anthropic only)
- Robust JSON extraction with fallback parsing
"""

import json
import logging
import os
from typing import Optional

import anthropic
from openai import OpenAI

from models.one_pager import OnePagerData
from services.prompt_manager import get_prompt_template

logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

# Default models per provider — Opus for best extraction quality
DEFAULT_MODELS = {
    "anthropic": "claude-opus-4-20250514",
    "openrouter": "anthropic/claude-opus-4",
}

# Authoritative financial/business domains for M&A research
ALLOWED_DOMAINS = [
    "bloomberg.com",
    "reuters.com",
    "crunchbase.com",
    "linkedin.com",
    "macrotrends.net",
    "finance.yahoo.com",
    "handelsregister.de",
    "northdata.de",
    "unternehmensregister.de",
    "bundesanzeiger.de",
]


# Prompts are now managed via prompt_manager.py and editable at runtime.
# Access them via get_prompt_template("research_system"), etc.


def _build_json_schema() -> str:
    """Build the JSON schema description for the AI prompt."""
    return json.dumps(OnePagerData.model_json_schema(), indent=2)


def _build_user_prompt(company_name: str, im_text: Optional[str] = None) -> str:
    """Build the user prompt for research using editable prompt templates."""
    json_schema = _build_json_schema()

    if im_text:
        truncated = im_text[:50000] if len(im_text) > 50000 else im_text
        template = get_prompt_template("research_user_with_im")
        return template.format(
            company_name=company_name,
            im_text=truncated,
            json_schema=json_schema,
        )
    else:
        template = get_prompt_template("research_user_no_im")
        return template.format(
            company_name=company_name,
            json_schema=json_schema,
        )


def _build_web_search_tool() -> dict:
    """Build the web search tool definition with domain filtering."""
    tool = {
        "type": "web_search_20250305",
        "name": "web_search",
        "max_uses": 10,
    }

    # Add domain filtering for higher quality results
    if ALLOWED_DOMAINS:
        tool["allowed_domains"] = ALLOWED_DOMAINS

    return tool


def get_available_providers() -> list[dict]:
    """Return list of configured providers with their available models."""
    providers = []

    if ANTHROPIC_API_KEY:
        providers.append({
            "id": "anthropic",
            "name": "Anthropic (Claude)",
            "has_web_search": True,
            "default_model": DEFAULT_MODELS["anthropic"],
            "models": [
                {"id": "claude-opus-4-20250514", "name": "Claude Opus 4 (Recommended)"},
                {"id": "claude-sonnet-4-20250514", "name": "Claude Sonnet 4"},
                {"id": "claude-haiku-4-20250514", "name": "Claude Haiku 4"},
            ],
        })

    if OPENROUTER_API_KEY:
        providers.append({
            "id": "openrouter",
            "name": "OpenRouter",
            "has_web_search": False,
            "default_model": DEFAULT_MODELS["openrouter"],
            "models": [
                {"id": "anthropic/claude-opus-4", "name": "Claude Opus 4 (Recommended)"},
                {"id": "anthropic/claude-sonnet-4", "name": "Claude Sonnet 4"},
                {"id": "openai/gpt-4o", "name": "GPT-4o"},
                {"id": "openai/gpt-4.1", "name": "GPT-4.1"},
                {"id": "google/gemini-2.5-pro-preview", "name": "Gemini 2.5 Pro"},
                {"id": "deepseek/deepseek-r1", "name": "DeepSeek R1"},
            ],
        })

    return providers


def research_company(
    company_name: str,
    im_text: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> OnePagerData:
    """
    Use AI to research a company and fill the One-Pager schema.

    Args:
        company_name: Name of the target company
        im_text: Optional extracted text from an Information Memorandum PDF
        provider: "anthropic" or "openrouter" (auto-detected if None)
        model: Model ID override (uses provider default if None)

    Returns:
        Populated OnePagerData object
    """
    # Auto-detect provider
    if provider is None:
        if ANTHROPIC_API_KEY:
            provider = "anthropic"
        elif OPENROUTER_API_KEY:
            provider = "openrouter"
        else:
            raise ValueError(
                "No API key configured. Set ANTHROPIC_API_KEY or OPENROUTER_API_KEY."
            )

    if provider == "anthropic":
        return _research_via_anthropic(company_name, im_text, model)
    elif provider == "openrouter":
        return _research_via_openrouter(company_name, im_text, model)
    else:
        raise ValueError(f"Unknown provider: {provider}. Use 'anthropic' or 'openrouter'.")


def _research_via_anthropic(
    company_name: str,
    im_text: Optional[str],
    model: Optional[str],
) -> OnePagerData:
    """Research using Anthropic's Claude API with web search."""
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY not set.")

    resolved_model = model or DEFAULT_MODELS["anthropic"]
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    messages = [
        {
            "role": "user",
            "content": _build_user_prompt(company_name, im_text),
        }
    ]

    web_search_tool = _build_web_search_tool()
    citations: list[dict] = []

    # Multi-turn loop: Claude may use web_search multiple times
    max_turns = 15
    response = None

    for turn in range(max_turns):
        logger.info(
            "Research turn %d/%d for %s (anthropic/%s)",
            turn + 1, max_turns, company_name, resolved_model,
        )

        response = client.messages.create(
            model=resolved_model,
            max_tokens=8000,
            system=get_prompt_template("research_system"),
            messages=messages,
            tools=[web_search_tool],
        )

        # Collect citations from response
        _collect_citations(response, citations)

        # If stop reason is "end_turn", Claude is done
        if response.stop_reason == "end_turn":
            logger.info("Research complete after %d turns", turn + 1)
            break

        # Handle pause_turn: Claude paused mid-research, pass response back
        if response.stop_reason == "pause_turn":
            logger.info("Research paused, continuing...")
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": "Please continue."})
            continue

        # If stop reason is "tool_use", web search was triggered server-side
        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": "Search completed. Please continue with the results.",
                    })

            if tool_results:
                messages.append({"role": "user", "content": tool_results})
            continue

        # Any other stop reason (max_tokens, etc.), break out
        logger.warning("Unexpected stop_reason: %s", response.stop_reason)
        break

    if response is None:
        raise RuntimeError("No response from Claude API")

    # Extract the JSON from the final response
    json_text = _extract_json_from_response(response)
    data = _parse_response_json(json_text, company_name)

    if not data.header.company_name:
        data.header.company_name = company_name

    if citations:
        logger.info(
            "Research for %s used %d citations: %s",
            company_name,
            len(citations),
            ", ".join(c.get("url", "?")[:60] for c in citations[:5]),
        )

    return data


def _research_via_openrouter(
    company_name: str,
    im_text: Optional[str],
    model: Optional[str],
) -> OnePagerData:
    """Research using OpenRouter (OpenAI-compatible API)."""
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY not set.")

    resolved_model = model or DEFAULT_MODELS["openrouter"]

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )

    logger.info("Researching %s via openrouter/%s", company_name, resolved_model)

    user_prompt = _build_user_prompt(company_name, im_text)

    response = client.chat.completions.create(
        model=resolved_model,
        max_tokens=8000,
        messages=[
            {"role": "system", "content": get_prompt_template("research_system_no_search")},
            {"role": "user", "content": user_prompt},
        ],
        extra_headers={
            "HTTP-Referer": "https://constellation-capital.de",
            "X-Title": "M&A One-Pager Generator",
        },
    )

    if not response.choices:
        raise RuntimeError("No response from OpenRouter API")

    raw_text = response.choices[0].message.content or ""
    logger.info(
        "OpenRouter response: model=%s, tokens=%s",
        response.model,
        getattr(response.usage, "total_tokens", "?") if response.usage else "?",
    )

    json_text = _extract_json_from_text(raw_text)
    data = _parse_response_json(json_text, company_name)

    if not data.header.company_name:
        data.header.company_name = company_name

    return data


def _collect_citations(response, citations: list[dict]):
    """Extract citation data from response content blocks for audit trail."""
    for block in response.content:
        # Check for web search result blocks
        if hasattr(block, "type") and block.type == "web_search_tool_result":
            if hasattr(block, "search_results"):
                for result in block.search_results:
                    citations.append({
                        "url": getattr(result, "url", ""),
                        "title": getattr(result, "title", ""),
                    })


def _parse_response_json(json_text: str, company_name: str) -> OnePagerData:
    """Parse AI response JSON with multiple fallback strategies."""
    # Strategy 1: Direct Pydantic validation
    try:
        return OnePagerData.model_validate_json(json_text)
    except Exception:
        pass

    # Strategy 2: Parse as dict, then validate
    try:
        raw = json.loads(json_text)
        return OnePagerData.model_validate(raw)
    except Exception:
        pass

    # Strategy 3: Try to fix common JSON issues
    try:
        fixed = json_text.replace("'", '"')
        raw = json.loads(fixed)
        return OnePagerData.model_validate(raw)
    except Exception as e:
        logger.warning("Failed to parse AI response JSON: %s", str(e)[:200])

    # Fallback: Return empty template with error note
    data = OnePagerData()
    data.header.company_name = company_name
    data.header.label = "One Pager"
    data.investment_thesis = "AI research returned unparseable data. Please fill manually."
    return data


def _extract_json_from_response(response) -> str:
    """Extract JSON string from Anthropic's response, handling tool use blocks."""
    text_parts = []
    for block in response.content:
        if hasattr(block, "text") and block.text:
            text_parts.append(block.text)

    full_text = "\n".join(text_parts).strip()
    return _extract_json_from_text(full_text)


def _extract_json_from_text(full_text: str) -> str:
    """Extract JSON from a raw text string (handles code fences, brace matching)."""
    if not full_text:
        return "{}"

    # Handle markdown code fences
    if "```json" in full_text:
        try:
            start = full_text.index("```json") + 7
            end = full_text.index("```", start)
            return full_text[start:end].strip()
        except ValueError:
            pass
    elif "```" in full_text:
        try:
            start = full_text.index("```") + 3
            end = full_text.index("```", start)
            return full_text[start:end].strip()
        except ValueError:
            pass

    # Find raw JSON object with proper brace matching (handles strings with braces)
    brace_start = full_text.find("{")
    if brace_start >= 0:
        depth = 0
        in_string = False
        escape_next = False
        for i in range(brace_start, len(full_text)):
            c = full_text[i]
            if escape_next:
                escape_next = False
                continue
            if c == "\\":
                escape_next = True
                continue
            if c == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return full_text[brace_start : i + 1]

    return full_text
