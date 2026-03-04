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

logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

# Default models per provider
DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-4-20250514",
    "openrouter": "anthropic/claude-sonnet-4",
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

RESEARCH_SYSTEM_PROMPT = """You are a senior M&A analyst at Constellation Capital AG, a private equity fund focused on acquiring DACH-region SMEs. You have 15 years of experience in due diligence and company evaluation.

Your task is to research a target company and populate a structured One-Pager JSON object. This One-Pager will be reviewed by the investment committee, so accuracy is critical.

## Constellation Capital Investment Criteria

| Criterion | Threshold |
|-----------|-----------|
| EBITDA | >= EUR 1.0m |
| Geography | DACH (Germany, Austria, Switzerland) |
| EBITDA Margin | >= 10% |
| Structure | Majority stake preferred |
| Business Model | Asset-light, digitizable, buy & build potential |

## Research Process

Work through these steps systematically:

1. **Identify the company**: Find the official website, legal entity name, and headquarters.
2. **Gather financials**: Look for revenue and EBITDA figures for the last 3 years. For DACH SMEs, check Bundesanzeiger, Unternehmensregister, North Data, and Handelsregister.
3. **Understand the business**: What products/services does the company offer? What is their market position?
4. **Identify management**: Who are the founders, CEO, and key executives?
5. **Evaluate investment criteria**: For each criterion, assess based ONLY on the data you actually found.

## Critical Rules to Avoid Errors

1. **NEVER invent financial figures.** Most DACH SMEs do not publish revenue or EBITDA publicly. If you cannot find a figure from a credible source, leave the field as an empty string or null. An empty field is far better than a fabricated number.

2. **Distinguish facts from inferences.** If you infer something (e.g., estimating employee count from LinkedIn), prefix the value with "~" (e.g., "~120"). If a figure comes from the IM document, use it as-is.

3. **When in doubt, use "questions".** For investment_criteria evaluation:
   - "fulfilled": You have concrete evidence the criterion is met
   - "questions": You lack sufficient data, or the data is ambiguous
   - "not_interest": You have concrete evidence the criterion is NOT met
   Default to "questions" when unsure. Never mark a criterion as "fulfilled" without supporting data in the One-Pager.

4. **Revenue split: only if known.** Do NOT estimate or guess revenue segment percentages. Only fill revenue_split if the IM or a credible source provides this breakdown. Leave segments as an empty array otherwise.

5. **Management: only verified names.** Only include management names you found on the company website, LinkedIn, Handelsregister, or in the IM. Never guess or fabricate names. If unknown, use a role description like "1 managing shareholder (operational MD)".

6. **Cross-check your output.** Before finalizing:
   - Does EBITDA margin ≈ EBITDA / Revenue? (If both are provided)
   - Do your investment criteria evaluations match the key facts? (e.g., if EBITDA is stated as EUR 2.0m, ebitda_1m should be "fulfilled")
   - Are there any contradictions between description, key_facts, and financials?

Return ONLY valid JSON matching the provided schema. No markdown, no explanation, no code fences."""

# Anthropic variant includes web search instruction
RESEARCH_SYSTEM_PROMPT_ANTHROPIC = RESEARCH_SYSTEM_PROMPT.replace(
    "Look for revenue and EBITDA figures for the last 3 years. For DACH SMEs, check Bundesanzeiger, Unternehmensregister, North Data, and Handelsregister.",
    "Use web search to find revenue and EBITDA figures for the last 3 years. Search Bundesanzeiger, Unternehmensregister, North Data, Handelsregister, and the company website.",
)


def _build_json_schema() -> str:
    """Build the JSON schema description for the AI prompt."""
    return json.dumps(OnePagerData.model_json_schema(), indent=2)


def _build_user_prompt(company_name: str, im_text: Optional[str] = None) -> str:
    """Build the user prompt for research."""
    if im_text:
        truncated = im_text[:50000] if len(im_text) > 50000 else im_text
        source_instructions = f"""## Source Material

An Information Memorandum (IM) has been provided below. This is your PRIMARY source.
- Extract financials, management names, and business description directly from the IM.
- Use web search only to supplement or verify IM data (e.g., confirm management names, check for recent news).
- If the IM contradicts web sources, prefer the IM data (it is more current and deal-specific).

<im_document>
{truncated}
</im_document>"""
    else:
        source_instructions = """## Source Material

No Information Memorandum was provided. Research this company using public sources only.
- Many DACH SMEs have limited public data. This is normal.
- Leave financial fields empty rather than guessing. An empty field is expected and acceptable.
- Focus on what you CAN verify: website, HQ, industry, founding year, products, management (from LinkedIn/Handelsregister)."""

    return f"""Research this company and fill the One-Pager JSON schema.

**Company: {company_name}**

{source_instructions}

## Output Format

JSON Schema to fill:
{_build_json_schema()}

### Field Format Rules (learn from these real examples):

**header.tagline** — One-line business description, max 80 chars:
- "Vertically integrated dental practice with strong margin profile"
- "Provider of premium bedding products & sleep-comfort solutions"
- "Succession Solution for Indoor E-Karting & Bowling Platform"

**investment_thesis** — Deal-type + target description, one sentence:
- "100% acquisition of profitable dual-venue leisure platform"
- "Opportunity to acquire 100% of the shares in a provider of premium bedding products"
- "100% sale of cash-generative lab component trader & developer"

**key_facts.revenue** / **key_facts.ebitda** — Currency + amount + margin for EBITDA:
- revenue: "EUR 4.3m", ebitda: "EUR 2.0m (47%)"
- revenue: "CHF 7.8m", ebitda: "CHF 1.9m (25%)"
- Use CHF for Swiss companies, EUR otherwise

**key_facts.revenue_year** / **key_facts.ebitda_year** — Year with A/P/E suffix:
- "FY24A" or "2025A" (A = actual)
- "25P" (P = projected), "25E" (E = estimated)

**key_facts.management** — Array of strings, one per person with role:
- ["Andreas Weiland, Founder & Managing Shareholder", "2nd level management for operations"]
- ["Arndt Hüsges, CEO", "Owners: Arndt Hüsges (70%) & Bernd Hüsges (30%)"]
- ["1 managing shareholder (operational MD)"] (when names are unknown)

**key_facts.employees** — Number with unit (FTEs or HC):
- "22.5 FTEs", "150 HC", "~28 FTEs", "10"

**key_facts.founded** — Year only, or "n/a" if truly unknown:
- "2008", "1957", "n/a"

**description** — 3-5 bullet points describing the business:
- "Premium 3-level indoor e-karting track (600m, RIMO karts) + 25-lane high-tech bowling center"
- "Operates own in-house lab enabling high-quality, fast-turnaround prosthetics"

**investment_rationale.pros** — Short, punchy positives (no "+" prefix):
- "Exceptional profitability"
- "Asset light business model with strong margins"
- "Stable, recurring service demand"

**investment_rationale.cons** — Short, punchy negatives (no "–" prefix):
- "Founder dependency"
- "High platform dependence on Amazon"
- "Key-person risk"

**financials** — Multi-year data. Values are in EUR millions as plain numbers:
- years: ["22A", "23A", "24A", "25P"]
- revenue: [3.2, 2.9, 3.1, 3.1]  (plain floats, NOT strings)
- ebitda: [0.9, 0.9, 1.1, 1.2]
- ebitda_margin: [0.29, 0.317, 0.37, 0.382]  (as decimals, e.g. 0.37 = 37%)

**meta.source** — Where the deal came from:
- "Alphabet Partners", "Nachfolgekontor", "Ramus & Company AG"
- "CIM received on 06.11.2025" (if no broker, just IM date)

**meta.status** — Current deal stage:
- "Internal discussion – 03.03.26"
- "NBO – 08.12.2025"

### Unknown / unavailable data:
- Unknown strings: use "" (empty string) or "n/a" for key_facts.founded/website
- Unknown numeric values: use null (not 0, not a guess)
- Unknown arrays: use [] (empty array)
- Revenue split: ONLY fill if you have actual data. Leave segments as [].
- Investment criteria: Default to "questions" unless you have clear evidence.

Return ONLY the JSON object."""


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
                {"id": "claude-sonnet-4-20250514", "name": "Claude Sonnet 4"},
                {"id": "claude-opus-4-20250514", "name": "Claude Opus 4"},
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
                {"id": "anthropic/claude-sonnet-4", "name": "Claude Sonnet 4"},
                {"id": "anthropic/claude-opus-4", "name": "Claude Opus 4"},
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
            system=RESEARCH_SYSTEM_PROMPT_ANTHROPIC,
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
            {"role": "system", "content": RESEARCH_SYSTEM_PROMPT},
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
