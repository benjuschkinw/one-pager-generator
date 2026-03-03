"""
AI Research Pipeline: uses Claude API with web search to research a company
and fill the One-Pager data schema.

Supports:
- Web search with domain filtering for authoritative financial sources
- PDF extraction from Information Memorandums
- Multi-turn tool use with pause_turn handling
- Citation tracking for audit trails
- Robust JSON extraction with fallback parsing
"""

import json
import logging
import os

import anthropic

from models.one_pager import OnePagerData

logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

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

RESEARCH_SYSTEM_PROMPT = """You are an M&A analyst assistant for Constellation Capital AG, a private equity fund focused on DACH-region SMEs.

Your job is to research a target company and fill a structured One-Pager data object with all available information.

Constellation Capital's investment criteria:
- EBITDA minimum: EUR 1.0m
- Geography: DACH (Germany, Austria, Switzerland)
- EBITDA margin minimum: 10%
- Structure: Majority stake preferred
- Focus: Asset-light, digitizable businesses with buy & build potential

When researching, use web search to find:
- Company website, LinkedIn, Crunchbase, Handelsregister
- Revenue and EBITDA figures (last 3 years if available)
- Business description and product/service portfolio
- Management team and founders
- Market position and competitive landscape
- Any M&A activity or investment rounds

For investment_criteria, evaluate each criterion based on available data:
- "fulfilled": criterion is clearly met
- "questions": insufficient data or partially met
- "not_interest": clearly not relevant/met

Before outputting the final JSON, verify your financial figures against multiple sources and flag any discrepancies.

Return ONLY valid JSON matching the provided schema. No markdown, no explanation, no code fences."""


def _build_json_schema() -> str:
    """Build the JSON schema description for the AI prompt."""
    return json.dumps(OnePagerData.model_json_schema(), indent=2)


def _build_user_prompt(company_name: str, im_text: str | None = None) -> str:
    """Build the user prompt for research."""
    context = ""
    if im_text:
        truncated = im_text[:50000] if len(im_text) > 50000 else im_text
        context = f"\n\nInformation Memorandum text:\n{truncated}"

    return f"""Research this company and fill the One-Pager JSON schema with all available information.
Search the web for the latest revenue, EBITDA, and company information.

Company: {company_name}{context}

JSON Schema to fill:
{_build_json_schema()}

Important:
- Fill ALL fields you can find data for
- Use "EUR X.Xm" format for monetary values
- Years should be like "23A" (actual) or "26P" (projected)
- For management, include names and roles as separate list items
- For revenue_split segments, estimate percentages if exact data unavailable
- Leave null for truly unknown numeric values
- Evaluate each investment criterion honestly based on the data you found

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


def research_company(
    company_name: str,
    im_text: str | None = None,
) -> OnePagerData:
    """
    Use Claude API with web search to research a company.

    Handles multi-turn tool use and pause_turn — Claude may call
    web_search several times before returning the final JSON response.

    Args:
        company_name: Name of the target company
        im_text: Optional extracted text from an Information Memorandum PDF

    Returns:
        Populated OnePagerData object with sources list
    """
    if not ANTHROPIC_API_KEY:
        raise ValueError(
            "ANTHROPIC_API_KEY not set. Set the environment variable to use AI research."
        )

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
        logger.info("Research turn %d/%d for %s", turn + 1, max_turns, company_name)

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8000,
            system=RESEARCH_SYSTEM_PROMPT,
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
        # The web_search tool is handled by Anthropic's servers —
        # results are returned inline in the response content blocks.
        # We just continue the conversation to let Claude process results.
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

    # Parse and validate
    data = _parse_response_json(json_text, company_name)

    # Ensure company name is set
    if not data.header.company_name:
        data.header.company_name = company_name

    # Log sources for audit trail
    if citations:
        logger.info(
            "Research for %s used %d citations: %s",
            company_name,
            len(citations),
            ", ".join(c.get("url", "?")[:60] for c in citations[:5]),
        )

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
    """Extract JSON string from Claude's response, handling tool use blocks."""
    text_parts = []
    for block in response.content:
        if hasattr(block, "text") and block.text:
            text_parts.append(block.text)

    full_text = "\n".join(text_parts).strip()

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
