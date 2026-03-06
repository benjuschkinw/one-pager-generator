"""
Deep Research Pipeline: multi-step AI research with SSE streaming.

Runs a 7-step pipeline:
  1. im_extraction  - Extract structured data from IM PDF text (skipped if no IM)
  2. web_research   - Web research via Google/Anthropic API (with web search)
  3. financials     - Financial deep-dive via Anthropic API (web search)
  4. management     - Management & org research via Google API (web search)
  5. market         - Market & competitive via OpenRouter (GPT-5.2)
  6. merge          - Merge & synthesize all step results (GPT-5.2)
  7. verify_final   - Cross-verify merged output (GPT-5.2)

Steps 2-5 run in parallel.  Each step (1-5) gets rechecked by a 2nd AI from
a different model family.  The function is an async generator that yields SSE
event dicts for the frontend DeepResearchProgress component.

Provider routing: model_id "google" → Google native API with Search grounding,
"anthropic" → Anthropic API with web search, anything else → OpenRouter.
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from typing import AsyncGenerator, Optional

import anthropic
from openai import OpenAI

from config.models import DEEP_RESEARCH_MODELS, RECHECK_MODELS
from models.job import DeepResearchStep, StepVerification
from models.one_pager import FieldFlag, OnePagerData, VerificationResult
from services.ai_research import (
    _build_json_schema,
    _extract_json_from_text,
    _parse_response_json,
    _safe_format,
    _sanitize_company_name,
    ANTHROPIC_API_KEY,
    OPENROUTER_API_KEY,
    GOOGLE_API_KEY,
    ALLOWED_DOMAINS,
)
from services.job_store import get_job, update_job, save_research_data
from services.prompt_manager import get_prompt_template

logger = logging.getLogger(__name__)

# Human-readable labels for each step
STEP_LABELS = {
    "im_extraction": "IM Extraction",
    "web_research": "Web Research",
    "financials": "Financial Deep-Dive",
    "management": "Management & Org",
    "market": "Market & Competitive",
    "merge": "Merge & Synthesize",
    "verify_final": "Final Verification",
}

# Steps are now routed by their model_id in config:
# "google" → _call_google_with_search (Google native API + Search grounding)
# "anthropic" → _call_anthropic_with_search (Anthropic API + web search)
# anything else → _call_openrouter (OpenRouter, no search)


# ─── Helpers ────────────────────────────────────────────────────────────────

def _model_family(model_or_provider: str) -> str:
    """Derive the model family key used for RECHECK_MODELS lookup."""
    s = model_or_provider.lower()
    if s == "anthropic" or "anthropic" in s or "claude" in s:
        return "anthropic"
    if "openai" in s or "gpt" in s:
        return "openai"
    if "google" in s or "gemini" in s:
        return "google"
    return "openrouter"


def _recheck_model_for(step_model: str) -> str:
    """Pick a recheck model from a different family."""
    family = _model_family(step_model)
    return RECHECK_MODELS.get(family, "openai/gpt-4.1")


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def _make_event(
    step: str,
    status: str,
    message: str,
    *,
    model: str = "",
    duration: Optional[float] = None,
    confidence: Optional[float] = None,
    event_type: str = "progress",
) -> dict:
    """Build an SSE event dict for the frontend DeepResearchProgress component."""
    evt: dict = {
        "step": step,
        "status": status,
        "message": message,
        "_event_type": event_type,
    }
    if model:
        evt["model"] = model
    if duration is not None:
        evt["duration"] = round(duration, 1)
    if confidence is not None:
        evt["confidence"] = confidence
    return evt


def _build_web_search_tool() -> dict:
    """Build the Anthropic web search tool definition with domain filtering."""
    tool = {
        "type": "web_search_20250305",
        "name": "web_search",
        "max_uses": 10,
    }
    if ALLOWED_DOMAINS:
        tool["allowed_domains"] = ALLOWED_DOMAINS
    return tool


def _extract_json_from_anthropic_response(response) -> str:
    """Extract JSON text from Anthropic's response content blocks."""
    text_parts = []
    for block in response.content:
        if hasattr(block, "text") and block.text:
            text_parts.append(block.text)
    return _extract_json_from_text("\n".join(text_parts).strip())


def _collect_sources_from_anthropic(response) -> list[str]:
    """Extract source URLs from Anthropic web search result blocks."""
    sources: list[str] = []
    for block in response.content:
        if hasattr(block, "type") and block.type == "web_search_tool_result":
            if hasattr(block, "search_results"):
                for result in block.search_results:
                    url = getattr(result, "url", "")
                    if url and url not in sources:
                        sources.append(url)
    return sources


def _parse_partial_json(text: str) -> dict:
    """Parse a JSON string with fallback strategies."""
    json_text = _extract_json_from_text(text)
    try:
        return json.loads(json_text)
    except json.JSONDecodeError:
        pass
    try:
        return json.loads(json_text.replace("'", '"'))
    except json.JSONDecodeError as e:
        logger.warning("Failed to parse step JSON: %s", str(e)[:200])
        return {}


# ─── Synchronous AI call functions (wrapped via asyncio.to_thread) ──────────

def _call_google_with_search(
    system_prompt: str,
    user_prompt: str,
) -> tuple[str, list[str]]:
    """
    Call Google Gemini API with Google Search grounding.
    Returns (response_json_text, source_urls).
    Synchronous -- call via asyncio.to_thread.
    """
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY not set.")

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=GOOGLE_API_KEY)
    model = "gemini-2.5-pro"

    logger.info("Google Search call: model=%s", model)
    response = client.models.generate_content(
        model=model,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            tools=[types.Tool(google_search=types.GoogleSearch())],
            max_output_tokens=16000,
            temperature=0.2,
        ),
    )

    # Extract text from all parts (thinking models have thought_signature parts)
    text_parts = []
    sources = []
    if response.candidates and response.candidates[0].content:
        for part in response.candidates[0].content.parts:
            if hasattr(part, "text") and part.text:
                text_parts.append(part.text)
    raw_text = "\n".join(text_parts)

    # Extract grounding sources if available
    candidate = response.candidates[0] if response.candidates else None
    if candidate and hasattr(candidate, "grounding_metadata") and candidate.grounding_metadata:
        gm = candidate.grounding_metadata
        if hasattr(gm, "grounding_chunks") and gm.grounding_chunks:
            for chunk in gm.grounding_chunks:
                if hasattr(chunk, "web") and chunk.web:
                    url = getattr(chunk.web, "uri", "")
                    if url and url not in sources:
                        sources.append(url)

    logger.info("Google response: length=%d chars, sources=%d", len(raw_text), len(sources))

    json_text = _extract_json_from_text(raw_text)
    return json_text, sources


def _call_anthropic_with_search(
    system_prompt: str,
    user_prompt: str,
    max_turns: int = 15,
) -> tuple[str, list[str]]:
    """
    Call Anthropic Claude API with web search tool in a multi-turn loop.
    Returns (response_json_text, source_urls).
    Synchronous -- call via asyncio.to_thread.
    """
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY not set.")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    model = "claude-sonnet-4-20250514"

    messages = [{"role": "user", "content": user_prompt}]
    web_search_tool = _build_web_search_tool()
    all_sources: list[str] = []
    response = None

    for turn in range(max_turns):
        logger.info("Anthropic web search turn %d/%d", turn + 1, max_turns)
        response = client.messages.create(
            model=model,
            max_tokens=8000,
            system=system_prompt,
            messages=messages,
            tools=[web_search_tool],
        )

        all_sources.extend(_collect_sources_from_anthropic(response))

        if response.stop_reason == "end_turn":
            break

        if response.stop_reason == "pause_turn":
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": "Please continue."})
            continue

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

        logger.warning("Unexpected stop_reason: %s", response.stop_reason)
        break

    if response is None:
        raise RuntimeError("No response from Anthropic API")

    json_text = _extract_json_from_anthropic_response(response)
    return json_text, list(dict.fromkeys(all_sources))


def _call_openrouter(
    system_prompt: str,
    user_prompt: str,
    model: str,
) -> str:
    """
    Call OpenRouter (OpenAI-compatible) API.  Returns raw response text.
    Synchronous -- call via asyncio.to_thread.
    """
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY not set.")

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )

    response = client.chat.completions.create(
        model=model,
        max_tokens=8000,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        extra_headers={
            "HTTP-Referer": "https://constellation-capital.de",
            "X-Title": "M&A One-Pager Deep Research",
        },
    )

    if not response.choices:
        raise RuntimeError("No response from OpenRouter API")
    return response.choices[0].message.content or ""


# ─── Generic dispatcher ────────────────────────────────────────────────────

def _call_by_model(
    model_id: str,
    system_prompt: str,
    user_prompt: str,
) -> tuple[str, list[str]]:
    """
    Route a call to the right provider based on model_id.
    Returns (json_text, source_urls).
    - "google" → Google Gemini API with Search grounding
    - "anthropic" → Anthropic API with web search
    - anything else → OpenRouter (no web search)
    """
    if model_id == "google":
        return _call_google_with_search(system_prompt, user_prompt)
    elif model_id == "anthropic":
        return _call_anthropic_with_search(system_prompt, user_prompt)
    else:
        raw = _call_openrouter(system_prompt, user_prompt, model_id)
        return raw, []


# ─── Individual step implementations (all synchronous) ──────────────────────

def _run_im_extraction_sync(company_name: str, im_text: str) -> tuple[dict, list[str]]:
    """Step 1: Extract structured data from IM document."""
    model = DEEP_RESEARCH_MODELS["im_extraction"]
    system_prompt = get_prompt_template("deep_im_extraction")
    json_schema = _build_json_schema()

    truncated = im_text[:80_000] if len(im_text) > 80_000 else im_text
    user_prompt = (
        f"Company: {company_name}\n\n"
        f"Extract ALL structured data from this Information Memorandum.\n\n"
        f"JSON Schema to fill:\n{json_schema}\n\n"
        f"<im_document>\n{truncated}\n</im_document>\n\n"
        f"Return ONLY valid JSON."
    )

    json_text, sources = _call_by_model(model, system_prompt, user_prompt)
    result = _parse_partial_json(json_text)
    result_sources = result.pop("_sources", [])
    return result, list(dict.fromkeys(sources + result_sources))


def _run_web_research_sync(company_name: str) -> tuple[dict, list[str]]:
    """Step 2: Web research for company basics."""
    model = DEEP_RESEARCH_MODELS["web_research"]
    system_prompt = get_prompt_template("deep_web_research")
    user_prompt = (
        f"Research basic company information for: {company_name}\n\n"
        f"Return ONLY valid JSON."
    )
    json_text, sources = _call_by_model(model, system_prompt, user_prompt)
    result = _parse_partial_json(json_text)
    result_sources = result.pop("_sources", [])
    return result, list(dict.fromkeys(sources + result_sources))


def _run_financials_sync(company_name: str) -> tuple[dict, list[str]]:
    """Step 3: Financial deep-dive."""
    model = DEEP_RESEARCH_MODELS["financials"]
    system_prompt = get_prompt_template("deep_financials")
    user_prompt = (
        f"Research financial data for: {company_name}\n\n"
        f"Search Bundesanzeiger, North Data, Unternehmensregister, "
        f"and the company website.\n\nReturn ONLY valid JSON."
    )
    json_text, sources = _call_by_model(model, system_prompt, user_prompt)
    result = _parse_partial_json(json_text)
    result_sources = result.pop("_sources", [])
    return result, list(dict.fromkeys(sources + result_sources))


def _run_management_sync(company_name: str) -> tuple[dict, list[str]]:
    """Step 4: Management & org research."""
    model = DEEP_RESEARCH_MODELS["management"]
    system_prompt = get_prompt_template("deep_management")
    user_prompt = (
        f"Research the management team and organizational structure for: "
        f"{company_name}\n\nSearch LinkedIn, Handelsregister, North Data, "
        f"and the company website.\n\nReturn ONLY valid JSON."
    )
    json_text, sources = _call_by_model(model, system_prompt, user_prompt)
    result = _parse_partial_json(json_text)
    result_sources = result.pop("_sources", [])
    return result, list(dict.fromkeys(sources + result_sources))


def _run_market_sync(company_name: str) -> tuple[dict, list[str]]:
    """Step 5: Market & competitive analysis."""
    model = DEEP_RESEARCH_MODELS["market"]
    system_prompt = get_prompt_template("deep_market")
    user_prompt = (
        f"Analyze the market landscape and competitive positioning for: "
        f"{company_name}\n\nFocus on the DACH region.\n\nReturn ONLY valid JSON."
    )
    json_text, sources = _call_by_model(model, system_prompt, user_prompt)
    result = _parse_partial_json(json_text)
    result_sources = result.pop("_sources", [])
    return result, list(dict.fromkeys(sources + result_sources))


def _run_merge_sync(
    company_name: str,
    sub_results: dict[str, dict],
) -> dict:
    """Step 6: Merge all sub-task results into complete OnePagerData."""
    model = DEEP_RESEARCH_MODELS["merge"]
    system_prompt = _safe_format(
        get_prompt_template("deep_merge"),
        json_schema=_build_json_schema(),
    )

    parts = []
    for step_name, data in sub_results.items():
        label = STEP_LABELS.get(step_name, step_name)
        parts.append(
            f"### {label}\n```json\n"
            f"{json.dumps(data, indent=2, default=str)}\n```"
        )

    user_prompt = (
        f"Company: {company_name}\n\n"
        f"Merge the following research sub-task results into a single "
        f"complete OnePagerData JSON.\n\n"
        + "\n\n".join(parts)
        + "\n\nReturn ONLY valid JSON matching the complete OnePagerData schema."
    )

    json_text, _ = _call_by_model(model, system_prompt, user_prompt)
    return _parse_partial_json(json_text)


def _run_verify_final_sync(merged_data: dict) -> dict:
    """Step 7: Cross-verify merged output with a different model family."""
    model = DEEP_RESEARCH_MODELS["verify_final"]
    system_prompt = get_prompt_template("deep_final_verify")
    user_prompt = (
        f"## Complete OnePagerData to Verify\n\n"
        f"```json\n{json.dumps(merged_data, indent=2, default=str)}\n```"
    )

    json_text, _ = _call_by_model(model, system_prompt, user_prompt)
    result = _parse_partial_json(json_text)
    # Ensure required fields
    result.setdefault("confidence", 0.5)
    result.setdefault("verified", False)
    result.setdefault("flags", [])
    return result


def _run_step_recheck_sync(step_name: str, step_output: dict) -> dict:
    """Run per-step recheck with a model from a different family."""
    step_model = DEEP_RESEARCH_MODELS.get(step_name, "anthropic")
    recheck_model = _recheck_model_for(step_model)

    system_prompt = get_prompt_template("deep_step_recheck")
    user_prompt = (
        f"Step: {step_name}\n\n"
        f"Research output to verify:\n```json\n"
        f"{json.dumps(step_output, indent=2, default=str)}\n```\n\n"
        f"Check for hallucinated data, implausible claims, and internal "
        f"inconsistencies.\nReturn ONLY valid JSON."
    )

    # Route to correct API based on model string
    if "anthropic" in recheck_model.lower() or "claude" in recheck_model.lower():
        if not ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not set for recheck.")
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        bare_model = recheck_model.split("/")[-1] if "/" in recheck_model else recheck_model
        resp = client.messages.create(
            model=bare_model,
            max_tokens=4000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        raw = ""
        for block in resp.content:
            if hasattr(block, "text") and block.text:
                raw += block.text
    else:
        raw = _call_openrouter(system_prompt, user_prompt, recheck_model)

    result = _parse_partial_json(raw)
    result.setdefault("confidence", 0.5)
    result.setdefault("flags", [])
    result.setdefault("hallucination_risk", "medium")
    return result


# ─── Step persistence ───────────────────────────────────────────────────────

_job_locks: dict[str, asyncio.Lock] = {}


def _get_job_lock(job_id: str) -> asyncio.Lock:
    """Return a per-job lock to serialize _save_step calls."""
    if job_id not in _job_locks:
        _job_locks[job_id] = asyncio.Lock()
    return _job_locks[job_id]


async def _save_step(job_id: str, step: DeepResearchStep) -> None:
    """Update a single step inside the job's deep_research_steps list."""
    async with _get_job_lock(job_id):
        job = await get_job(job_id)
        if job is None:
            return
        steps = list(job.deep_research_steps or [])

        replaced = False
        for i, s in enumerate(steps):
            if s.step_name == step.step_name:
                steps[i] = step
                replaced = True
                break
        if not replaced:
            steps.append(step)

        await update_job(job_id, deep_research_steps=steps)


# ─── Main pipeline (async generator) ───────────────────────────────────────

async def run_deep_research(
    job_id: str,
    company_name: str,
    im_text: Optional[str] = None,
) -> AsyncGenerator[dict, None]:
    """
    Run the deep research pipeline, yielding SSE event dicts.

    Each event has the shape expected by the frontend DeepResearchProgress:
      {step, status, message, model?, duration?, confidence?, _event_type}
    """
    safe_company = _sanitize_company_name(company_name)
    sub_results: dict[str, dict] = {}
    has_im = bool(im_text)

    # ── Initialise step records ─────────────────────────────────────────
    all_steps: list[DeepResearchStep] = []
    step_order = [
        "im_extraction", "web_research", "financials",
        "management", "market", "merge", "verify_final",
    ]
    for sn in step_order:
        model_cfg = DEEP_RESEARCH_MODELS.get(sn, "unknown")
        if model_cfg == "anthropic":
            display_model = "claude-sonnet-4 (Anthropic API)"
        elif model_cfg == "google":
            display_model = "gemini-2.5-pro (Google API)"
        else:
            display_model = model_cfg
        all_steps.append(DeepResearchStep(
            step_name=sn,
            label=STEP_LABELS[sn],
            model_used=display_model,
            status="pending",
        ))

    await update_job(job_id, deep_research_steps=all_steps)

    def _find(name: str) -> DeepResearchStep:
        return next(s for s in all_steps if s.step_name == name)

    # ── Helper: run a research step + recheck, persist, return result ───

    async def _execute_research_step(
        step_name: str,
        sync_fn,
        *args,
    ) -> tuple[dict, list[str]]:
        """
        Run one research step (1-5) in a thread, then recheck, persist.
        Returns (result_dict, sources).
        """
        step = _find(step_name)
        step.status = "running"
        step.started_at = _now_iso()
        await _save_step(job_id, step)

        t0 = time.monotonic()
        result, sources = await asyncio.to_thread(sync_fn, *args)
        elapsed = time.monotonic() - t0

        step.result_json = result
        step.sources = sources
        step.status = "done"
        step.completed_at = _now_iso()
        await _save_step(job_id, step)

        # Per-step recheck
        recheck_confidence: Optional[float] = None
        if result:
            try:
                recheck_data = await asyncio.to_thread(
                    _run_step_recheck_sync, step_name, result,
                )
                step_model = DEEP_RESEARCH_MODELS.get(step_name, "anthropic")
                flags = [
                    FieldFlag(
                        field=f.get("field", "unknown"),
                        severity=f.get("severity", "warning"),
                        message=f.get("message", ""),
                    )
                    for f in recheck_data.get("flags", [])
                    if isinstance(f, dict)
                ]
                step.verification = StepVerification(
                    verifier_model=_recheck_model_for(step_model),
                    confidence=float(recheck_data.get("confidence", 0.5)),
                    flags=flags,
                    hallucination_risk=recheck_data.get(
                        "hallucination_risk", "medium"
                    ),
                )
                step.status = "verified"
                recheck_confidence = step.verification.confidence
                await _save_step(job_id, step)
            except Exception as exc:
                logger.warning("Recheck failed for %s: %s", step_name, exc)

        return result, sources

    # ── Step 1: IM Extraction ───────────────────────────────────────────
    im_step = _find("im_extraction")
    if has_im:
        yield _make_event(
            "im_extraction", "running",
            f"Extracting data from IM for {safe_company}...",
            model=im_step.model_used,
        )
        t0 = time.monotonic()
        try:
            result, sources = await _execute_research_step(
                "im_extraction", _run_im_extraction_sync, safe_company, im_text,
            )
            elapsed = time.monotonic() - t0
            if result:
                sub_results["im_extraction"] = result
            im_step_final = _find("im_extraction")
            conf = (
                im_step_final.verification.confidence
                if im_step_final.verification
                else None
            )
            yield _make_event(
                "im_extraction",
                im_step_final.status,
                f"IM extraction complete ({elapsed:.1f}s)",
                model=im_step.model_used,
                duration=elapsed,
                confidence=conf,
            )
        except Exception as e:
            elapsed = time.monotonic() - t0
            logger.error("IM extraction failed: %s", e, exc_info=True)
            im_step.status = "error"
            im_step.error_message = str(e)[:500]
            im_step.completed_at = _now_iso()
            await _save_step(job_id, im_step)
            yield _make_event(
                "im_extraction", "error",
                f"IM extraction failed: {str(e)[:200]}",
                model=im_step.model_used, duration=elapsed,
            )
    else:
        im_step.status = "done"
        im_step.completed_at = _now_iso()
        await _save_step(job_id, im_step)
        yield _make_event(
            "im_extraction", "skipped",
            "No IM provided, skipping extraction",
        )

    # ── Steps 2-5: Parallel research ────────────────────────────────────

    parallel_config = [
        ("web_research", _run_web_research_sync, (safe_company,)),
        ("financials", _run_financials_sync, (safe_company,)),
        ("management", _run_management_sync, (safe_company,)),
        ("market", _run_market_sync, (safe_company,)),
    ]

    # Emit "running" for all parallel steps
    for sn, _, _ in parallel_config:
        step = _find(sn)
        yield _make_event(
            sn, "running",
            f"Starting {STEP_LABELS[sn]}...",
            model=step.model_used,
        )

    # Wrap each parallel step so exceptions don't kill the gather
    async def _safe_parallel(step_name, sync_fn, args):
        t0 = time.monotonic()
        try:
            result, sources = await _execute_research_step(
                step_name, sync_fn, *args,
            )
            elapsed = time.monotonic() - t0
            if result:
                sub_results[step_name] = result
            step_final = _find(step_name)
            conf = (
                step_final.verification.confidence
                if step_final.verification
                else None
            )
            return _make_event(
                step_name,
                step_final.status,
                f"{STEP_LABELS[step_name]} complete ({elapsed:.1f}s)",
                model=step_final.model_used,
                duration=elapsed,
                confidence=conf,
            )
        except Exception as e:
            elapsed = time.monotonic() - t0
            logger.error("Step %s failed: %s", step_name, e, exc_info=True)
            step = _find(step_name)
            step.status = "error"
            step.error_message = str(e)[:500]
            step.completed_at = _now_iso()
            await _save_step(job_id, step)
            return _make_event(
                step_name, "error",
                f"{STEP_LABELS[step_name]} failed: {str(e)[:200]}",
                model=step.model_used, duration=elapsed,
            )

    completion_events = await asyncio.gather(
        *[_safe_parallel(sn, fn, args) for sn, fn, args in parallel_config],
        return_exceptions=True,
    )

    for evt in completion_events:
        if isinstance(evt, dict):
            yield evt
        elif isinstance(evt, Exception):
            logger.error("Unexpected exception in parallel step: %s", evt)

    # ── Step 6: Merge ───────────────────────────────────────────────────

    merge_step = _find("merge")
    merge_step.status = "running"
    merge_step.started_at = _now_iso()
    await _save_step(job_id, merge_step)
    yield _make_event(
        "merge", "running",
        f"Merging {len(sub_results)} research results...",
        model=merge_step.model_used,
    )

    merged: dict = {}
    t0 = time.monotonic()
    try:
        merged = await asyncio.to_thread(
            _run_merge_sync, safe_company, sub_results,
        )
        elapsed = time.monotonic() - t0
        merge_step.result_json = merged
        merge_step.status = "done"
        merge_step.completed_at = _now_iso()
        await _save_step(job_id, merge_step)
        yield _make_event(
            "merge", "done",
            f"Merge complete ({elapsed:.1f}s)",
            model=merge_step.model_used, duration=elapsed,
        )
    except Exception as e:
        elapsed = time.monotonic() - t0
        logger.error("Merge step failed: %s", e, exc_info=True)
        merge_step.status = "error"
        merge_step.error_message = str(e)[:500]
        merge_step.completed_at = _now_iso()
        await _save_step(job_id, merge_step)
        yield _make_event(
            "merge", "error",
            f"Merge failed: {str(e)[:200]}",
            model=merge_step.model_used, duration=elapsed,
        )

    # ── Step 7: Final Verification ──────────────────────────────────────

    verify_step = _find("verify_final")
    verify_step.status = "running"
    verify_step.started_at = _now_iso()
    await _save_step(job_id, verify_step)
    yield _make_event(
        "verify_final", "running",
        "Cross-verifying merged output...",
        model=verify_step.model_used,
    )

    verification_result = VerificationResult(
        verified=False,
        confidence=0.0,
        verifier_model=DEEP_RESEARCH_MODELS["verify_final"],
    )

    t0 = time.monotonic()
    try:
        verify_data = await asyncio.to_thread(
            _run_verify_final_sync, merged,
        )
        elapsed = time.monotonic() - t0

        confidence = float(verify_data.get("confidence", 0.5))
        verified = bool(verify_data.get("verified", False))
        flags = [
            FieldFlag(
                field=f.get("field", "unknown"),
                severity=f.get("severity", "warning"),
                message=f.get("message", ""),
            )
            for f in verify_data.get("flags", [])
            if isinstance(f, dict)
        ]

        verification_result = VerificationResult(
            verified=verified,
            confidence=confidence,
            flags=flags,
            verifier_model=DEEP_RESEARCH_MODELS["verify_final"],
        )

        verify_step.result_json = verify_data
        verify_step.status = "done"
        verify_step.completed_at = _now_iso()
        await _save_step(job_id, verify_step)

        yield _make_event(
            "verify_final", "done",
            f"Verification complete ({elapsed:.1f}s) - confidence: {confidence:.0%}",
            model=verify_step.model_used,
            duration=elapsed,
            confidence=confidence,
        )
    except Exception as e:
        elapsed = time.monotonic() - t0
        logger.error("Final verification failed: %s", e, exc_info=True)
        verify_step.status = "error"
        verify_step.error_message = str(e)[:500]
        verify_step.completed_at = _now_iso()
        await _save_step(job_id, verify_step)
        yield _make_event(
            "verify_final", "error",
            f"Verification failed: {str(e)[:200]}",
            model=verify_step.model_used, duration=elapsed,
        )

    # ── Save final results ──────────────────────────────────────────────

    try:
        # Remove internal fields (prefixed with _) before parsing
        clean_merged = {k: v for k, v in merged.items() if not k.startswith("_")}
        one_pager = _parse_response_json(
            json.dumps(clean_merged, default=str), safe_company,
        )
        if not one_pager.header.company_name:
            one_pager.header.company_name = safe_company

        await save_research_data(job_id, one_pager, verification_result)

        yield _make_event(
            "complete", "done",
            f"Deep research complete for {safe_company}",
            confidence=verification_result.confidence,
            event_type="complete",
        )
    except Exception as e:
        logger.error("Failed to save final research data: %s", e, exc_info=True)
        await update_job(job_id, status="failed")
        yield _make_event(
            "complete", "error",
            f"Failed to save results: {str(e)[:200]}",
            event_type="complete",
        )
