"""
Verification service: cross-checks AI-generated One-Pager data using
algorithmic consistency checks and a second AI model via OpenRouter.

Uses a different model than the research step to avoid correlated errors.
"""

import json
import logging
import os
import re
from typing import Optional

from openai import OpenAI

from models.one_pager import (
    OnePagerData,
    FieldFlag,
    VerificationResult,
)
from services.prompt_manager import get_prompt_template

logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

# Use a different model family for verification to avoid correlated errors.
# If research used Claude, verify with GPT; if research used GPT, verify with Claude.
VERIFICATION_MODELS = {
    "anthropic": "openai/gpt-4.1",       # Research was Claude → verify with GPT
    "openrouter": "openai/gpt-4.1",      # Default fallback
    "openai": "anthropic/claude-sonnet-4", # Research was GPT → verify with Claude
    "google": "anthropic/claude-sonnet-4", # Research was Gemini → verify with Claude
    "deepseek": "anthropic/claude-sonnet-4",
}

# Verification prompt is now managed via prompt_manager.py


def _parse_monetary_value(value: str) -> Optional[float]:
    """Extract numeric value from monetary string like 'EUR 12.5m' or 'CHF 2.8m'."""
    if not value:
        return None
    match = re.search(r'([\d.]+)\s*m', value.lower())
    if match:
        return float(match.group(1))
    match = re.search(r'([\d,.]+)', value)
    if match:
        num_str = match.group(1).replace(',', '')
        try:
            return float(num_str)
        except ValueError:
            return None
    return None


def _algorithmic_checks(data: OnePagerData) -> list[FieldFlag]:
    """Run fast algorithmic consistency checks (no AI call needed)."""
    flags: list[FieldFlag] = []

    # Check revenue split sums to ~100%
    if data.revenue_split.segments:
        total_pct = sum(s.pct for s in data.revenue_split.segments)
        if abs(total_pct - 100.0) > 5.0:
            flags.append(FieldFlag(
                field="revenue_split.segments",
                severity="error",
                message=f"Revenue split segments sum to {total_pct}%, expected ~100%"
            ))

    # Check EBITDA margin consistency with EBITDA/revenue
    fin = data.financials
    if fin.years and fin.revenue and fin.ebitda and fin.ebitda_margin:
        for i in range(min(len(fin.years), len(fin.revenue), len(fin.ebitda), len(fin.ebitda_margin))):
            rev = fin.revenue[i]
            ebit = fin.ebitda[i]
            margin = fin.ebitda_margin[i]
            if rev and ebit and margin and rev > 0:
                calculated_margin = ebit / rev
                if abs(calculated_margin - margin) > 0.05:
                    flags.append(FieldFlag(
                        field=f"financials.ebitda_margin[{i}]",
                        severity="warning",
                        message=f"Year {fin.years[i]}: stated margin {margin:.0%} but EBITDA/Revenue = {calculated_margin:.0%}"
                    ))

    # Check criteria consistency
    kf = data.key_facts
    criteria = data.investment_criteria

    # EBITDA > 1M check
    ebitda_val = _parse_monetary_value(kf.ebitda)
    if ebitda_val is not None:
        if ebitda_val >= 1.0 and criteria.ebitda_1m.value != "fulfilled":
            flags.append(FieldFlag(
                field="investment_criteria.ebitda_1m",
                severity="warning",
                message=f"EBITDA is {kf.ebitda} (>= EUR 1.0m) but criterion is '{criteria.ebitda_1m.value}'"
            ))
        elif ebitda_val < 1.0 and criteria.ebitda_1m.value == "fulfilled":
            flags.append(FieldFlag(
                field="investment_criteria.ebitda_1m",
                severity="error",
                message=f"EBITDA is {kf.ebitda} (< EUR 1.0m) but criterion marked as 'fulfilled'"
            ))

    # DACH geography check
    dach_keywords = ["germany", "deutschland", "austria", "österreich", "switzerland", "schweiz",
                     "munich", "münchen", "berlin", "hamburg", "frankfurt", "zurich", "zürich",
                     "vienna", "wien", "cologne", "köln", "düsseldorf", "stuttgart"]
    hq_lower = kf.hq.lower()
    if any(kw in hq_lower for kw in dach_keywords) and criteria.dach.value != "fulfilled":
        flags.append(FieldFlag(
            field="investment_criteria.dach",
            severity="warning",
            message=f"HQ is '{kf.hq}' (DACH region) but criterion is '{criteria.dach.value}'"
        ))

    # Check arrays have consistent lengths
    if fin.years:
        expected_len = len(fin.years)
        for field_name, values in [("revenue", fin.revenue), ("ebitda", fin.ebitda), ("ebitda_margin", fin.ebitda_margin)]:
            if values and len(values) != expected_len:
                flags.append(FieldFlag(
                    field=f"financials.{field_name}",
                    severity="error",
                    message=f"Has {len(values)} entries but {expected_len} years defined"
                ))

    # Plausibility: founded year
    if kf.founded:
        try:
            year = int(re.search(r'\d{4}', kf.founded).group())
            if year < 1800 or year > 2026:
                flags.append(FieldFlag(
                    field="key_facts.founded",
                    severity="error",
                    message=f"Founded year {year} is implausible"
                ))
        except (AttributeError, ValueError):
            pass

    # Plausibility: negative EBITDA with "fulfilled" margin criterion
    if ebitda_val is not None and ebitda_val < 0:
        if criteria.ebitda_margin_10.value == "fulfilled":
            flags.append(FieldFlag(
                field="investment_criteria.ebitda_margin_10",
                severity="error",
                message="EBITDA is negative but margin criterion marked as 'fulfilled'"
            ))

    return flags


def _ai_verification(
    data: OnePagerData,
    company_name: str,
    im_text: Optional[str],
    research_provider: str,
) -> tuple[list[FieldFlag], float, str]:
    """
    Call a second AI model via OpenRouter to cross-verify the research data.

    Uses a different model family than the research to avoid correlated errors.

    Returns: (flags, confidence, model_used)
    """
    if not OPENROUTER_API_KEY:
        logger.warning("No OPENROUTER_API_KEY set, skipping AI verification")
        return [], 0.5, ""

    # Pick a different model family for verification
    verifier_model = VERIFICATION_MODELS.get(research_provider, "openai/gpt-4.1")

    # If the research model was already GPT, use Claude instead
    if research_provider == "openrouter":
        verifier_model = "openai/gpt-4.1"

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )

    data_json = data.model_dump_json(indent=2)
    context = ""
    if im_text:
        truncated = im_text[:20000]
        context = f"\n\nOriginal IM text (excerpt):\n{truncated}"

    user_prompt = f"""Company researched: {company_name}{context}

One-Pager data to verify:
{data_json}"""

    logger.info("Verifying research for %s with %s", company_name, verifier_model)

    try:
        response = client.chat.completions.create(
            model=verifier_model,
            max_tokens=4000,
            messages=[
                {"role": "system", "content": get_prompt_template("verification")},
                {"role": "user", "content": user_prompt},
            ],
            extra_headers={
                "HTTP-Referer": "https://constellation-capital.de",
                "X-Title": "M&A One-Pager Verification",
            },
        )

        if not response.choices:
            logger.warning("No response from verification model")
            return [], 0.5, verifier_model

        raw_text = response.choices[0].message.content or ""
        logger.info(
            "Verification response: model=%s, tokens=%s",
            response.model,
            getattr(response.usage, "total_tokens", "?") if response.usage else "?",
        )

        # Parse the verification JSON
        result = _parse_verification_response(raw_text)
        return result["flags"], result["confidence"], verifier_model

    except Exception as e:
        logger.error("AI verification failed: %s", str(e))
        return [], 0.5, verifier_model


def _parse_verification_response(raw_text: str) -> dict:
    """Parse the verification model's JSON response."""
    # Extract JSON from potential markdown fences
    text = raw_text.strip()
    if "```json" in text:
        try:
            start = text.index("```json") + 7
            end = text.index("```", start)
            text = text[start:end].strip()
        except ValueError:
            pass
    elif "```" in text:
        try:
            start = text.index("```") + 3
            end = text.index("```", start)
            text = text[start:end].strip()
        except ValueError:
            pass

    try:
        parsed = json.loads(text)
        flags = []
        for f in parsed.get("flags", []):
            flags.append(FieldFlag(
                field=f.get("field", "unknown"),
                severity=f.get("severity", "warning"),
                message=f.get("message", ""),
            ))
        return {
            "confidence": float(parsed.get("confidence", 0.5)),
            "flags": flags,
        }
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning("Failed to parse verification response: %s", str(e)[:200])
        return {"confidence": 0.5, "flags": []}


def verify_research(
    data: OnePagerData,
    company_name: str,
    im_text: Optional[str] = None,
    research_provider: str = "anthropic",
) -> VerificationResult:
    """
    Cross-check AI-generated research data for consistency and accuracy.

    Combines:
    1. Fast algorithmic checks (math, consistency)
    2. AI-based verification via a second model (different from research model)

    Args:
        data: The AI-generated OnePagerData to verify
        company_name: Original company name for context
        im_text: Optional IM text for additional context
        research_provider: Which provider was used for research (to pick a different verifier)

    Returns:
        VerificationResult with confidence score and any flagged issues
    """
    all_flags: list[FieldFlag] = []

    # Phase 1: Algorithmic checks (instant, free)
    algo_flags = _algorithmic_checks(data)
    all_flags.extend(algo_flags)
    logger.info("Algorithmic checks found %d issues", len(algo_flags))

    # Phase 2: AI cross-verification (costs tokens, but catches hallucinations)
    ai_flags, ai_confidence, verifier_model = _ai_verification(
        data, company_name, im_text, research_provider
    )
    all_flags.extend(ai_flags)
    logger.info("AI verification found %d issues (confidence: %.2f)", len(ai_flags), ai_confidence)

    # Calculate overall confidence
    has_errors = any(f.severity == "error" for f in all_flags)
    has_warnings = any(f.severity == "warning" for f in all_flags)

    if has_errors:
        confidence = min(ai_confidence, 0.4)
    elif has_warnings:
        confidence = min(ai_confidence, 0.7)
    else:
        confidence = ai_confidence

    return VerificationResult(
        verified=confidence >= 0.7 and not has_errors,
        confidence=round(confidence, 2),
        flags=all_flags,
        verifier_model=verifier_model,
    )
