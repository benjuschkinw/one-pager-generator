"""
AI Research Pipeline: uses Claude API, Google Gemini, or OpenRouter to research
a company and fill the One-Pager data schema.

Supports:
- Anthropic provider: Claude with web search + domain filtering
- Google provider: Gemini with Google Search grounding (cheapest option)
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
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")

# Default models per provider
DEFAULT_MODELS = {
    "anthropic": "claude-opus-4-20250514",
    "openrouter": "anthropic/claude-opus-4",
    "google": "gemini-2.5-pro",
}

# Fallback models for Google (in order of preference)
# Note: gemini-3.1-pro-preview is a thinking model that truncates JSON output,
# so we default to 2.5-pro which produces reliable structured output.
_GOOGLE_FALLBACK_MODELS = [
    "gemini-2.5-pro",
    "gemini-2.5-flash",
]

# Domain filtering disabled — Anthropic's web search blocks some domains
# (reuters.com, linkedin.com, etc.) causing 400 errors.
ALLOWED_DOMAINS = []


# Prompts are now managed via prompt_manager.py and editable at runtime.
# Access them via get_prompt_template("research_system"), etc.


def _build_json_schema() -> str:
    """Build the JSON schema description for the AI prompt."""
    return json.dumps(OnePagerData.model_json_schema(), indent=2)


def _safe_format(template: str, **kwargs) -> str:
    """Format a prompt template, gracefully handling missing or extra placeholders."""
    try:
        return template.format(**kwargs)
    except KeyError as e:
        logger.warning("Prompt template has unrecognized placeholder: %s", e)
        # Fall back to partial formatting using str.format_map with a default dict
        class SafeDict(dict):
            def __missing__(self, key: str) -> str:
                return "{" + key + "}"
        return template.format_map(SafeDict(**kwargs))


def _sanitize_company_name(name: str) -> str:
    """Sanitize company name to prevent prompt injection via user input."""
    import re
    # Strip control characters
    sanitized = re.sub(r'[\x00-\x1f\x7f]', '', name)
    # Cap length to prevent abuse
    sanitized = sanitized[:200].strip()
    return sanitized or "Unknown Company"


def _build_user_prompt(company_name: str, im_text: Optional[str] = None) -> str:
    """Build the user prompt for research using editable prompt templates."""
    json_schema = _build_json_schema()
    safe_company = _sanitize_company_name(company_name)

    if im_text:
        truncated = im_text[:50000] if len(im_text) > 50000 else im_text
        template = get_prompt_template("research_user_with_im")
        return _safe_format(
            template,
            company_name=safe_company,
            im_text=truncated,
            json_schema=json_schema,
        )
    else:
        template = get_prompt_template("research_user_no_im")
        return _safe_format(
            template,
            company_name=safe_company,
            json_schema=json_schema,
        )


def _build_web_search_tool() -> dict:
    """Build the web search tool definition with domain filtering."""
    tool = {
        "type": "web_search_20250305",
        "name": "web_search",
        "max_uses": 20,
    }

    # Add domain filtering for higher quality results
    if ALLOWED_DOMAINS:
        tool["allowed_domains"] = ALLOWED_DOMAINS

    return tool


def get_available_providers() -> list[dict]:
    """Return list of configured providers with their available models."""
    providers = []

    if GOOGLE_API_KEY:
        providers.append({
            "id": "google",
            "name": "Google (Gemini)",
            "has_web_search": True,
            "default_model": DEFAULT_MODELS["google"],
            "models": [
                {"id": "gemini-3.1-pro-preview", "name": "Gemini 3.1 Pro (Recommended)"},
                {"id": "gemini-2.5-pro", "name": "Gemini 2.5 Pro"},
                {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash (Fastest)"},
            ],
        })

    if ANTHROPIC_API_KEY:
        providers.append({
            "id": "anthropic",
            "name": "Anthropic (Claude)",
            "has_web_search": True,
            "default_model": DEFAULT_MODELS["anthropic"],
            "models": [
                {"id": "claude-opus-4-20250514", "name": "Claude Opus 4"},
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
    # Auto-detect provider — prefer Google (cheapest + web search), then Anthropic, then OpenRouter
    if provider is None:
        if GOOGLE_API_KEY:
            provider = "google"
        elif ANTHROPIC_API_KEY:
            provider = "anthropic"
        elif OPENROUTER_API_KEY:
            provider = "openrouter"
        else:
            raise ValueError(
                "No API key configured. Set GOOGLE_API_KEY, ANTHROPIC_API_KEY, or OPENROUTER_API_KEY."
            )

    if provider == "google":
        data = _research_via_google(company_name, im_text, model)
    elif provider == "anthropic":
        data = _research_via_anthropic(company_name, im_text, model)
    elif provider == "openrouter":
        data = _research_via_openrouter(company_name, im_text, model)
    else:
        raise ValueError(f"Unknown provider: {provider}. Use 'google', 'anthropic', or 'openrouter'.")

    # Cross-check key facts against the company's actual website
    data = _website_cross_check(data, company_name)
    return data


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


def _research_via_google(
    company_name: str,
    im_text: Optional[str],
    model: Optional[str],
) -> OnePagerData:
    """Research using Google Gemini API with Google Search grounding."""
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY not set.")

    from google import genai
    from google.genai import types

    # Try requested model, then fallbacks
    resolved_model = model or DEFAULT_MODELS["google"]
    models_to_try = [resolved_model] if model else _GOOGLE_FALLBACK_MODELS

    client = genai.Client(api_key=GOOGLE_API_KEY)

    system_prompt = get_prompt_template("research_system")
    user_prompt = _build_user_prompt(company_name, im_text)

    last_error = None
    for try_model in models_to_try:
        try:
            logger.info("Researching %s via google/%s", company_name, try_model)

            response = client.models.generate_content(
                model=try_model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                    max_output_tokens=16000,
                    temperature=0.2,
                ),
            )

            # Extract text from all parts (Gemini 3.1 has thought_signature parts)
            text_parts = []
            if response.candidates and response.candidates[0].content:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, "text") and part.text:
                        text_parts.append(part.text)
            raw_text = "\n".join(text_parts)
            logger.info(
                "Google response: model=%s, length=%d chars",
                try_model, len(raw_text),
            )

            json_text = _extract_json_from_text(raw_text)
            data = _parse_response_json(json_text, company_name)

            if not data.header.company_name:
                data.header.company_name = company_name

            return data

        except Exception as e:
            last_error = e
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                logger.warning("Google model %s rate-limited, trying next fallback", try_model)
                continue
            elif "404" in error_str or "NOT_FOUND" in error_str:
                logger.warning("Google model %s not found, trying next fallback", try_model)
                continue
            else:
                raise

    raise RuntimeError(f"All Google models failed. Last error: {last_error}")


def _website_cross_check(
    data: OnePagerData,
    company_name: str,
) -> OnePagerData:
    """
    Cross-check research output against the company's actual website.

    Uses Claude with web search to visit the company website (and impressum/about pages)
    and correct any factual errors in the research data.
    """
    if not ANTHROPIC_API_KEY:
        return data

    website = data.key_facts.website
    if not website:
        logger.info("No website in research data, skipping website cross-check")
        return data

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    data_json = data.model_dump_json(indent=2)

    prompt = f"""You are a fact-checker for M&A research. You have been given research data about "{company_name}".

Your task: Visit the company's website ({website}), their /impressum, /about, /ueber-uns, and /team pages to verify the research data. Then search for the company on the web.

Here is the current research data:
{data_json}

CHECK THESE SPECIFIC FACTS against what you find on their actual website:
1. **Company name** — exact legal entity name (check impressum)
2. **Website URL** — is it correct? Does it resolve?
3. **Founded year** — when was the company actually founded?
4. **HQ / Address** — check impressum for registered address
5. **Management** — who are the actual Geschäftsführer/managing directors? (check impressum)
6. **Industry / Niche** — what does the company ACTUALLY do? Match their self-description.
7. **Description** — does it match what the company says about itself?
8. **Product portfolio** — what products/services do they actually list?
9. **Employees** — any team page or indication of size?
10. **Tagline** — does it accurately describe the business?

IMPORTANT RULES:
- Only correct fields where you find CONCRETE evidence of an error
- If the website confirms the data, keep it as-is
- If you find the data is wrong, replace it with what the website says
- If the website doesn't mention something, keep the original (don't delete data)
- For management: the impressum Geschäftsführer are the ground truth

Return the COMPLETE corrected JSON object (same schema as input). If you made corrections, that's fine. If everything checks out, return the data unchanged.
Return ONLY the JSON, no commentary."""

    try:
        logger.info("Website cross-check for %s against %s", company_name, website)

        messages = [{"role": "user", "content": prompt}]
        web_search_tool = _build_web_search_tool()
        response = None

        for turn in range(10):
            response = client.messages.create(
                model="claude-sonnet-4-20250514",  # Sonnet is fine for fact-checking
                max_tokens=8000,
                system="You are a meticulous fact-checker. Visit the company website and verify every claim. Return corrected JSON.",
                messages=messages,
                tools=[web_search_tool],
            )

            if response.stop_reason == "end_turn":
                break
            elif response.stop_reason == "pause_turn":
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": "Please continue."})
            elif response.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": response.content})
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": "Search completed. Please continue.",
                        })
                if tool_results:
                    messages.append({"role": "user", "content": tool_results})
            else:
                break

        if response is None:
            return data

        json_text = _extract_json_from_response(response)
        corrected = _parse_response_json(json_text, company_name)

        # Log what changed
        changes = []
        if corrected.key_facts.website != data.key_facts.website:
            changes.append(f"website: {data.key_facts.website} -> {corrected.key_facts.website}")
        if corrected.key_facts.founded != data.key_facts.founded:
            changes.append(f"founded: {data.key_facts.founded} -> {corrected.key_facts.founded}")
        if corrected.key_facts.management != data.key_facts.management:
            changes.append(f"management changed")
        if corrected.header.tagline != data.header.tagline:
            changes.append(f"tagline changed")

        if changes:
            logger.info("Website cross-check corrected %d fields: %s", len(changes), "; ".join(changes))
        else:
            logger.info("Website cross-check found no corrections needed")

        return corrected

    except Exception as e:
        logger.error("Website cross-check failed: %s", str(e))
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
