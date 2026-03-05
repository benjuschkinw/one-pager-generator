"""
Market Research Pipeline: multi-step AI research for market studies with SSE streaming.

Runs an 8-step pipeline:
  1. market_sizing     - TAM/SAM/SOM via Anthropic API (web search)
  2. segmentation      - Market segments via Anthropic API (web search)
  3. competition       - Competitive landscape via Anthropic API (web search)
  4. trends_pestel     - Trends + PESTEL via OpenRouter (Gemini 2.5 Pro)
  5. porters_value_chain - Porter's Five Forces + Value Chain via Anthropic API
  6. buy_and_build     - Buy & Build potential via Anthropic API (web search)
  7. merge             - Merge all sub-results into MarketStudyData
  8. verify_final      - Cross-verify with GPT-4.1

Steps 1-3 run in parallel, steps 4-6 run in parallel after them.
Each step (1-6) gets rechecked by a 2nd AI from a different model family.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import AsyncGenerator, Optional

from config.models import MARKET_RESEARCH_MODELS, RECHECK_MODELS
from models.job import DeepResearchStep, StepVerification
from models.market_study import MarketStudyData
from models.one_pager import FieldFlag, VerificationResult
from services.deep_research import (
    _build_web_search_tool,
    _call_anthropic_with_search,
    _call_openrouter,
    _collect_sources_from_anthropic,
    _extract_json_from_anthropic_response,
    _make_event,
    _model_family,
    _now_iso,
    _parse_partial_json,
    _recheck_model_for,
)
from services.job_store import get_job, save_market_study_data, update_job
from services.prompt_manager import get_prompt_template

logger = logging.getLogger(__name__)

# Human-readable labels for each step
MARKET_STEP_LABELS = {
    "market_sizing": "Market Sizing",
    "segmentation": "Market Segmentation",
    "competition": "Competitive Landscape",
    "trends_pestel": "Trends & PESTEL",
    "porters_value_chain": "Porter's & Value Chain",
    "buy_and_build": "Buy & Build Potential",
    "merge": "Merge & Synthesize",
    "verify_final": "Final Verification",
}

# Steps that use Anthropic's web search API
_ANTHROPIC_SEARCH_STEPS = {
    "market_sizing", "segmentation", "competition",
    "porters_value_chain", "buy_and_build",
}

# Labels for scoping fields
_SCOPING_LABELS = {
    "product_scope": "Product Scope / Inclusions & Exclusions",
    "value_chain_focus": "Value Chain Focus",
    "geographic_detail": "Geographic Detail",
    "time_horizon": "Time Horizon",
    "customer_type": "Customer Type (B2B/B2C)",
    "customer_detail": "Customer Characteristics",
    "market_metric": "Market Size Metric",
    "study_purpose": "Study Purpose",
}


def _build_scoping_block(scoping: dict) -> str:
    """Build a structured scoping context block for injection into prompts."""
    if not scoping:
        return ""
    lines = ["## SCOPING CONTEXT (user-provided — respect these constraints strictly)"]
    for key, label in _SCOPING_LABELS.items():
        val = scoping.get(key, "")
        if val and val not in ("", "entire", "current", "b2b", "value", "market_entry"):
            # Only include non-default values
            lines.append(f"- **{label}**: {val}")
        elif val and key in ("value_chain_focus", "time_horizon", "customer_type",
                             "market_metric", "study_purpose"):
            # Always include select fields
            lines.append(f"- **{label}**: {val}")
    if len(lines) == 1:
        return ""
    return "\n".join(lines) + "\n\n"


def _build_market_study_schema() -> str:
    """Build a JSON schema description for MarketStudyData."""
    return json.dumps(MarketStudyData.model_json_schema(), indent=2)


# ─── Individual step implementations (all synchronous) ──────────────────────

def _run_market_sizing_sync(market_name: str, region: str, scoping_block: str = "") -> tuple[dict, list[str]]:
    """Step 1: Market sizing via Anthropic API with web search."""
    system_prompt = get_prompt_template("market_sizing")
    user_prompt = (
        f"Research the market sizing for: {market_name}\n"
        f"Region focus: {region}\n\n"
        f"{scoping_block}"
        f"Find TAM, SAM, SOM, CAGR, and historical/projected data points.\n\n"
        f"Return ONLY valid JSON."
    )
    json_text, sources = _call_anthropic_with_search(system_prompt, user_prompt)
    result = _parse_partial_json(json_text)
    result_sources = result.pop("_sources", [])
    return result, list(dict.fromkeys(sources + result_sources))


def _run_segmentation_sync(market_name: str, region: str, scoping_block: str = "") -> tuple[dict, list[str]]:
    """Step 2: Market segmentation via Anthropic API with web search."""
    system_prompt = get_prompt_template("market_segmentation")
    user_prompt = (
        f"Analyze the market segmentation for: {market_name}\n"
        f"Region focus: {region}\n\n"
        f"{scoping_block}"
        f"Identify primary segments, their sizes, shares, and growth rates.\n\n"
        f"Return ONLY valid JSON."
    )
    json_text, sources = _call_anthropic_with_search(system_prompt, user_prompt)
    result = _parse_partial_json(json_text)
    result_sources = result.pop("_sources", [])
    return result, list(dict.fromkeys(sources + result_sources))


def _run_competition_sync(market_name: str, region: str, scoping_block: str = "") -> tuple[dict, list[str]]:
    """Step 3: Competitive landscape via Anthropic API with web search."""
    system_prompt = get_prompt_template("market_competition")
    user_prompt = (
        f"Analyze the competitive landscape for: {market_name}\n"
        f"Region focus: {region}\n\n"
        f"{scoping_block}"
        f"Identify top 5-7 competitors, market fragmentation, and consolidation trends.\n\n"
        f"Return ONLY valid JSON."
    )
    json_text, sources = _call_anthropic_with_search(system_prompt, user_prompt)
    result = _parse_partial_json(json_text)
    result_sources = result.pop("_sources", [])
    return result, list(dict.fromkeys(sources + result_sources))


def _run_trends_pestel_sync(market_name: str, region: str, scoping_block: str = "") -> tuple[dict, list[str]]:
    """Step 4: Trends & PESTEL via OpenRouter (Gemini)."""
    model = MARKET_RESEARCH_MODELS["trends_pestel"]
    system_prompt = get_prompt_template("market_trends_pestel")
    user_prompt = (
        f"Analyze market trends and perform a PESTEL analysis for: {market_name}\n"
        f"Region focus: {region}\n\n"
        f"{scoping_block}"
        f"Return ONLY valid JSON."
    )
    raw = _call_openrouter(system_prompt, user_prompt, model)
    result = _parse_partial_json(raw)
    sources = result.pop("_sources", [])
    return result, sources


def _run_porters_value_chain_sync(market_name: str, region: str, scoping_block: str = "") -> tuple[dict, list[str]]:
    """Step 5: Porter's Five Forces & Value Chain via Anthropic with web search."""
    system_prompt = get_prompt_template("market_porters")
    user_prompt = (
        f"Perform a Porter's Five Forces analysis and map the value chain for: {market_name}\n"
        f"Region focus: {region}\n\n"
        f"{scoping_block}"
        f"Return ONLY valid JSON."
    )
    json_text, sources = _call_anthropic_with_search(system_prompt, user_prompt)
    result = _parse_partial_json(json_text)
    result_sources = result.pop("_sources", [])
    return result, list(dict.fromkeys(sources + result_sources))


def _run_buy_and_build_sync(market_name: str, region: str, scoping_block: str = "") -> tuple[dict, list[str]]:
    """Step 6: Buy & Build potential via Anthropic with web search."""
    system_prompt = get_prompt_template("market_buy_and_build")
    user_prompt = (
        f"Assess the buy-and-build potential for: {market_name}\n"
        f"Region focus: {region}\n\n"
        f"{scoping_block}"
        f"Analyze fragmentation, platform candidates, add-on profiles, "
        f"and consolidation rationale.\n\n"
        f"Return ONLY valid JSON."
    )
    json_text, sources = _call_anthropic_with_search(system_prompt, user_prompt)
    result = _parse_partial_json(json_text)
    result_sources = result.pop("_sources", [])
    return result, list(dict.fromkeys(sources + result_sources))


def _run_market_merge_sync(
    market_name: str,
    region: str,
    sub_results: dict[str, dict],
    scoping_block: str = "",
) -> dict:
    """Step 7: Merge all sub-task results into complete MarketStudyData."""
    model = MARKET_RESEARCH_MODELS["merge"]
    system_prompt = get_prompt_template("market_merge").replace(
        "{json_schema}", _build_market_study_schema()
    )

    parts = []
    for step_name, data in sub_results.items():
        label = MARKET_STEP_LABELS.get(step_name, step_name)
        parts.append(
            f"### {label}\n```json\n"
            f"{json.dumps(data, indent=2, default=str)}\n```"
        )

    user_prompt = (
        f"Market: {market_name}\n"
        f"Region: {region}\n\n"
        f"{scoping_block}"
        f"Merge the following market research sub-task results into a single "
        f"complete MarketStudyData JSON.\n\n"
        + "\n\n".join(parts)
        + "\n\nReturn ONLY valid JSON matching the complete MarketStudyData schema."
    )

    raw = _call_openrouter(system_prompt, user_prompt, model)
    return _parse_partial_json(raw)


def _run_market_verify_final_sync(merged_data: dict) -> dict:
    """Step 8: Cross-verify merged output with a different model family."""
    model = MARKET_RESEARCH_MODELS["verify_final"]
    system_prompt = get_prompt_template("market_verify")
    user_prompt = (
        f"## Complete MarketStudyData to Verify\n\n"
        f"```json\n{json.dumps(merged_data, indent=2, default=str)}\n```"
    )

    raw = _call_openrouter(system_prompt, user_prompt, model)
    result = _parse_partial_json(raw)
    result.setdefault("confidence", 0.5)
    result.setdefault("verified", False)
    result.setdefault("flags", [])
    return result


def _run_market_step_recheck_sync(step_name: str, step_output: dict) -> dict:
    """Run per-step recheck with a model from a different family."""
    import anthropic as anthropic_lib

    from services.ai_research import ANTHROPIC_API_KEY

    step_model = MARKET_RESEARCH_MODELS.get(step_name, "anthropic")
    recheck_model = _recheck_model_for(step_model)

    system_prompt = get_prompt_template("market_step_recheck")
    user_prompt = (
        f"Step: {step_name}\n\n"
        f"Market research output to verify:\n```json\n"
        f"{json.dumps(step_output, indent=2, default=str)}\n```\n\n"
        f"Check for hallucinated data, implausible market figures, and internal "
        f"inconsistencies.\nReturn ONLY valid JSON."
    )

    if "anthropic" in recheck_model.lower() or "claude" in recheck_model.lower():
        if not ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not set for recheck.")
        client = anthropic_lib.Anthropic(api_key=ANTHROPIC_API_KEY)
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

async def _save_step(job_id: str, step: DeepResearchStep) -> None:
    """Update a single step inside the job's deep_research_steps list."""
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

async def run_market_research(
    job_id: str,
    market_name: str,
    region: str = "DACH",
    scoping_context: dict | None = None,
) -> AsyncGenerator[dict, None]:
    """
    Run the market research pipeline, yielding SSE event dicts.

    Each event has the shape expected by the frontend DeepResearchProgress:
      {step, status, message, model?, duration?, confidence?, _event_type}
    """
    scoping_block = _build_scoping_block(scoping_context or {})
    sub_results: dict[str, dict] = {}

    # ── Initialise step records ─────────────────────────────────────────
    all_steps: list[DeepResearchStep] = []
    step_order = [
        "market_sizing", "segmentation", "competition",
        "trends_pestel", "porters_value_chain", "buy_and_build",
        "merge", "verify_final",
    ]
    for sn in step_order:
        model_cfg = MARKET_RESEARCH_MODELS.get(sn, "unknown")
        display_model = (
            "claude-opus-4 (Anthropic API)" if model_cfg == "anthropic" else model_cfg
        )
        all_steps.append(DeepResearchStep(
            step_name=sn,
            label=MARKET_STEP_LABELS[sn],
            model_used=display_model,
            status="pending",
        ))

    await update_job(job_id, deep_research_steps=all_steps)

    def _find(name: str) -> DeepResearchStep:
        return next(s for s in all_steps if s.step_name == name)

    # ── Helper: run a research step + recheck ────────────────────────────

    async def _execute_research_step(
        step_name: str,
        sync_fn,
        *args,
    ) -> tuple[dict, list[str]]:
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
        if result:
            try:
                recheck_data = await asyncio.to_thread(
                    _run_market_step_recheck_sync, step_name, result,
                )
                step_model = MARKET_RESEARCH_MODELS.get(step_name, "anthropic")
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
                await _save_step(job_id, step)
            except Exception as exc:
                logger.warning("Recheck failed for %s: %s", step_name, exc)

        return result, sources

    # ── Helper: safe parallel execution ──────────────────────────────────

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
                f"{MARKET_STEP_LABELS[step_name]} complete ({elapsed:.1f}s)",
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
                f"{MARKET_STEP_LABELS[step_name]} failed: {str(e)[:200]}",
                model=step.model_used, duration=elapsed,
            )

    # ── Steps 1-3: Parallel (sizing, segmentation, competition) ─────────

    batch_1 = [
        ("market_sizing", _run_market_sizing_sync, (market_name, region, scoping_block)),
        ("segmentation", _run_segmentation_sync, (market_name, region, scoping_block)),
        ("competition", _run_competition_sync, (market_name, region, scoping_block)),
    ]

    for sn, _, _ in batch_1:
        step = _find(sn)
        yield _make_event(
            sn, "running",
            f"Starting {MARKET_STEP_LABELS[sn]}...",
            model=step.model_used,
        )

    batch_1_events = await asyncio.gather(
        *[_safe_parallel(sn, fn, args) for sn, fn, args in batch_1],
        return_exceptions=True,
    )
    for evt in batch_1_events:
        if isinstance(evt, dict):
            yield evt
        elif isinstance(evt, Exception):
            logger.error("Unexpected exception in batch 1: %s", evt)

    # ── Steps 4-6: Parallel (trends, porters, buy_and_build) ─────────────

    batch_2 = [
        ("trends_pestel", _run_trends_pestel_sync, (market_name, region, scoping_block)),
        ("porters_value_chain", _run_porters_value_chain_sync, (market_name, region, scoping_block)),
        ("buy_and_build", _run_buy_and_build_sync, (market_name, region, scoping_block)),
    ]

    for sn, _, _ in batch_2:
        step = _find(sn)
        yield _make_event(
            sn, "running",
            f"Starting {MARKET_STEP_LABELS[sn]}...",
            model=step.model_used,
        )

    batch_2_events = await asyncio.gather(
        *[_safe_parallel(sn, fn, args) for sn, fn, args in batch_2],
        return_exceptions=True,
    )
    for evt in batch_2_events:
        if isinstance(evt, dict):
            yield evt
        elif isinstance(evt, Exception):
            logger.error("Unexpected exception in batch 2: %s", evt)

    # ── Step 7: Merge ───────────────────────────────────────────────────

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
            _run_market_merge_sync, market_name, region, sub_results, scoping_block,
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

    # ── Step 8: Final Verification ──────────────────────────────────────

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
        verifier_model=MARKET_RESEARCH_MODELS["verify_final"],
    )

    t0 = time.monotonic()
    try:
        verify_data = await asyncio.to_thread(
            _run_market_verify_final_sync, merged,
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
            verifier_model=MARKET_RESEARCH_MODELS["verify_final"],
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

        # Set meta fields
        if "meta" not in clean_merged:
            clean_merged["meta"] = {}
        clean_merged["meta"]["market_name"] = market_name
        clean_merged["meta"]["region"] = region
        clean_merged["meta"]["research_date"] = datetime.utcnow().strftime("%Y-%m-%d")

        market_study = MarketStudyData(**clean_merged)
        await save_market_study_data(job_id, market_study, verification_result)

        yield _make_event(
            "complete", "done",
            f"Market research complete for {market_name}",
            confidence=verification_result.confidence,
            event_type="complete",
        )
    except Exception as e:
        logger.error("Failed to save market study data: %s", e, exc_info=True)
        await update_job(job_id, status="failed")
        yield _make_event(
            "complete", "error",
            f"Failed to save results: {str(e)[:200]}",
            event_type="complete",
        )
