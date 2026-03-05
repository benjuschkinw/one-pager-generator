"""
Company Sourcing Pipeline: find similar companies in DACH based on a completed one-pager.

4-step pipeline with SSE streaming:
  1. extract_dna    - Extract Company DNA from OnePagerData
  2. search_dach    - Search for comparable companies (parallel by country)
  3. verify_enrich  - Verify & enrich each company, calculate similarity
  4. rank_synthesize - Rank by similarity, generate summary
"""

import asyncio
import json
import logging
import time
from typing import AsyncGenerator

from models.company_sourcing import CompanyProfile, CompanySourcingResult, CompSummaryStats
from models.job import DeepResearchStep
from models.one_pager import OnePagerData
from services.deep_research import (
    _call_anthropic_with_search,
    _call_openrouter,
    _make_event,
    _now_iso,
    _parse_partial_json,
)
from services.job_store import save_sourcing_data
from services.prompt_manager import get_prompt_template

logger = logging.getLogger(__name__)

SOURCING_STEP_LABELS = {
    "extract_dna": "Extract Company DNA",
    "search_dach": "Search DACH Companies",
    "verify_enrich": "Verify & Enrich",
    "rank_synthesize": "Rank & Synthesize",
}

SOURCING_MODELS = {
    "extract_dna": "anthropic/claude-opus-4",
    "search_dach": "anthropic",  # Needs web search
    "verify_enrich": "openai/gpt-4.1",
    "rank_synthesize": "anthropic/claude-opus-4",
}


async def _save_step(job_id: str, step: DeepResearchStep) -> None:
    """Track sourcing step progress. Intentionally does NOT write to
    deep_research_steps to avoid overwriting actual deep research data."""
    # Progress is communicated via SSE events; no DB persistence needed
    # for sourcing steps (the final result goes into sourcing_data).
    pass


# ─── Synchronous step implementations ──────────────────────────────────────

def _run_extract_dna_sync(one_pager_data: dict) -> dict:
    """Step 1: Extract Company DNA from OnePagerData."""
    system_prompt = get_prompt_template("sourcing_extract_dna")
    user_prompt = (
        "Extract the Company DNA from this completed one-pager:\n\n"
        f"```json\n{json.dumps(one_pager_data, indent=2, default=str)}\n```\n\n"
        "Return ONLY valid JSON."
    )
    raw = _call_openrouter(system_prompt, user_prompt, SOURCING_MODELS["extract_dna"])
    return _parse_partial_json(raw)


def _run_search_country_sync(
    company_name: str,
    dna: dict,
    country: str,
    country_label: str,
    target_count: int,
) -> tuple[dict, list[str]]:
    """Search for comparable companies in a specific country."""
    system_prompt = get_prompt_template("sourcing_search_companies")
    user_prompt = (
        f"Seed company: {company_name}\n"
        f"Search in: {country_label} ({country})\n"
        f"Find {target_count} comparable companies.\n\n"
        f"Company DNA / Search Criteria:\n```json\n{json.dumps(dna, indent=2)}\n```\n\n"
        "Return ONLY valid JSON."
    )
    json_text, sources = _call_anthropic_with_search(system_prompt, user_prompt)
    result = _parse_partial_json(json_text)
    result_sources = result.pop("_sources", [])
    return result, list(dict.fromkeys(sources + result_sources))


def _run_verify_enrich_sync(
    seed_company: str,
    seed_data: dict,
    companies: list[dict],
) -> dict:
    """Step 3: Verify and enrich companies, calculate similarity."""
    system_prompt = get_prompt_template("sourcing_verify_enrich")
    user_prompt = (
        f"Seed company: {seed_company}\n\n"
        f"Seed company data:\n```json\n{json.dumps(seed_data, indent=2, default=str)}\n```\n\n"
        f"Companies to verify ({len(companies)}):\n"
        f"```json\n{json.dumps(companies, indent=2, default=str)}\n```\n\n"
        "Return ONLY valid JSON."
    )
    raw = _call_openrouter(system_prompt, user_prompt, SOURCING_MODELS["verify_enrich"])
    return _parse_partial_json(raw)


def _run_rank_synthesize_sync(
    seed_company: str,
    verified_companies: list[dict],
) -> dict:
    """Step 4: Rank by similarity and generate summary."""
    system_prompt = get_prompt_template("sourcing_rank_synthesize")
    user_prompt = (
        f"Seed company: {seed_company}\n\n"
        f"Verified companies ({len(verified_companies)}):\n"
        f"```json\n{json.dumps(verified_companies, indent=2, default=str)}\n```\n\n"
        "Rank by similarity score and generate summary statistics.\n"
        "Return ONLY valid JSON."
    )
    raw = _call_openrouter(system_prompt, user_prompt, SOURCING_MODELS["rank_synthesize"])
    return _parse_partial_json(raw)


# ─── Main pipeline ──────────────────────────────────────────────────────────

async def run_company_sourcing(
    job_id: str,
    company_name: str,
    one_pager_data: OnePagerData,
) -> AsyncGenerator[dict, None]:
    """
    Run the company sourcing pipeline, yielding SSE event dicts.
    """
    data_dict = one_pager_data.model_dump()

    # Initialize step records
    all_steps: list[DeepResearchStep] = []
    step_order = ["extract_dna", "search_dach", "verify_enrich", "rank_synthesize"]
    for sn in step_order:
        model = SOURCING_MODELS.get(sn, "unknown")
        display_model = "claude-opus-4 (Anthropic API)" if model == "anthropic" else model
        all_steps.append(DeepResearchStep(
            step_name=sn,
            label=SOURCING_STEP_LABELS[sn],
            model_used=display_model,
            status="pending",
        ))

    def _find(name: str) -> DeepResearchStep:
        return next(s for s in all_steps if s.step_name == name)

    # ── Step 1: Extract Company DNA ────────────────────────────────────
    dna_step = _find("extract_dna")
    dna_step.status = "running"
    dna_step.started_at = _now_iso()
    await _save_step(job_id, dna_step)
    yield _make_event("extract_dna", "running", "Extracting company DNA...", model=dna_step.model_used)

    dna: dict = {}
    t0 = time.monotonic()
    try:
        dna = await asyncio.to_thread(_run_extract_dna_sync, data_dict)
        elapsed = time.monotonic() - t0
        dna_step.result_json = dna
        dna_step.status = "done"
        dna_step.completed_at = _now_iso()
        await _save_step(job_id, dna_step)
        yield _make_event("extract_dna", "done", f"DNA extracted ({elapsed:.1f}s)", model=dna_step.model_used, duration=elapsed)
    except Exception as e:
        elapsed = time.monotonic() - t0
        logger.error("DNA extraction failed: %s", e, exc_info=True)
        dna_step.status = "error"
        dna_step.error_message = str(e)[:500]
        dna_step.completed_at = _now_iso()
        await _save_step(job_id, dna_step)
        yield _make_event("extract_dna", "error", "DNA extraction failed", model=dna_step.model_used, duration=elapsed)
        yield _make_event("complete", "error", "Sourcing failed at DNA extraction", event_type="complete")
        return

    # ── Step 2: Search DACH (parallel by country) ─────────────────────
    search_step = _find("search_dach")
    search_step.status = "running"
    search_step.started_at = _now_iso()
    await _save_step(job_id, search_step)
    yield _make_event("search_dach", "running", "Searching DACH companies...", model=search_step.model_used)

    all_companies: list[dict] = []
    all_sources: list[str] = []
    t0 = time.monotonic()

    search_tasks = [
        ("DE", "Germany", 8),
        ("AT", "Austria", 5),
        ("CH", "Switzerland", 5),
    ]

    async def _search_country(country, label, count):
        try:
            result, sources = await asyncio.to_thread(
                _run_search_country_sync, company_name, dna, country, label, count
            )
            companies = result.get("companies", [])
            return companies, sources
        except Exception as exc:
            logger.warning("Search failed for %s: %s", country, exc)
            return [], []

    search_results = await asyncio.gather(
        *[_search_country(c, l, n) for c, l, n in search_tasks],
        return_exceptions=True,
    )

    for res in search_results:
        if isinstance(res, tuple):
            companies, sources = res
            all_companies.extend(companies)
            all_sources.extend(sources)

    elapsed = time.monotonic() - t0
    search_step.result_json = {"companies_found": len(all_companies)}
    search_step.sources = list(dict.fromkeys(all_sources))
    search_step.status = "done"
    search_step.completed_at = _now_iso()
    await _save_step(job_id, search_step)
    yield _make_event(
        "search_dach", "done",
        f"Found {len(all_companies)} companies ({elapsed:.1f}s)",
        model=search_step.model_used, duration=elapsed,
    )

    if not all_companies:
        result = CompanySourcingResult(
            seed_company=company_name,
            seed_industry=dna.get("industry", ""),
            search_criteria=dna,
            executive_summary="No comparable companies found in the DACH region.",
        )
        await save_sourcing_data(job_id, result)
        yield _make_event("complete", "done", "Sourcing complete (no results)", event_type="complete")
        return

    # ── Step 3: Verify & Enrich ─────────────────────────────────────────
    verify_step = _find("verify_enrich")
    verify_step.status = "running"
    verify_step.started_at = _now_iso()
    await _save_step(job_id, verify_step)
    yield _make_event("verify_enrich", "running", f"Verifying {len(all_companies)} companies...", model=verify_step.model_used)

    verified_companies: list[dict] = []
    t0 = time.monotonic()
    try:
        verify_result = await asyncio.to_thread(
            _run_verify_enrich_sync, company_name, data_dict, all_companies
        )
        elapsed = time.monotonic() - t0
        verified_companies = verify_result.get("verified_companies", [])
        removed = verify_result.get("removed_companies", [])
        verify_step.result_json = {
            "verified": len(verified_companies),
            "removed": len(removed),
        }
        verify_step.status = "done"
        verify_step.completed_at = _now_iso()
        await _save_step(job_id, verify_step)
        yield _make_event(
            "verify_enrich", "done",
            f"Verified {len(verified_companies)}, removed {len(removed)} ({elapsed:.1f}s)",
            model=verify_step.model_used, duration=elapsed,
        )
    except Exception as e:
        elapsed = time.monotonic() - t0
        logger.error("Verification failed: %s", e, exc_info=True)
        verify_step.status = "error"
        verify_step.error_message = str(e)[:500]
        verify_step.completed_at = _now_iso()
        await _save_step(job_id, verify_step)
        yield _make_event("verify_enrich", "error", "Verification failed", model=verify_step.model_used, duration=elapsed)
        # Continue with unverified companies
        verified_companies = [{"name": c.get("name", ""), **c, "similarity_score": 50, "confidence": 0.3} for c in all_companies]

    # ── Step 4: Rank & Synthesize ──────────────────────────────────────
    rank_step = _find("rank_synthesize")
    rank_step.status = "running"
    rank_step.started_at = _now_iso()
    await _save_step(job_id, rank_step)
    yield _make_event("rank_synthesize", "running", "Ranking and synthesizing...", model=rank_step.model_used)

    t0 = time.monotonic()
    try:
        rank_result = await asyncio.to_thread(
            _run_rank_synthesize_sync, company_name, verified_companies
        )
        elapsed = time.monotonic() - t0

        # Build final result
        ranked = rank_result.get("ranked_companies", verified_companies)
        summary_data = rank_result.get("summary", {})
        exec_summary = rank_result.get("executive_summary", "")

        # Parse into typed models
        company_profiles = []
        for c in ranked:
            try:
                company_profiles.append(CompanyProfile(**{
                    k: v for k, v in c.items()
                    if k in CompanyProfile.model_fields
                }))
            except Exception:
                logger.warning("Failed to parse company: %s", c.get("name", "?"))

        summary = CompSummaryStats(**{
            k: v for k, v in summary_data.items()
            if k in CompSummaryStats.model_fields
        }) if summary_data else CompSummaryStats(count=len(company_profiles))

        revenue_range = ""
        if dna.get("revenue_range_eur_m"):
            rr = dna["revenue_range_eur_m"]
            revenue_range = f"EUR {rr.get('min', '?')}-{rr.get('max', '?')}M"

        sourcing_result = CompanySourcingResult(
            seed_company=company_name,
            seed_industry=dna.get("industry", data_dict.get("key_facts", {}).get("industry", "")),
            seed_revenue_range=revenue_range,
            search_region="DACH",
            search_criteria=dna,
            companies=company_profiles,
            summary=summary,
            executive_summary=exec_summary,
        )

        await save_sourcing_data(job_id, sourcing_result)

        rank_step.result_json = {"ranked_count": len(company_profiles)}
        rank_step.status = "done"
        rank_step.completed_at = _now_iso()
        await _save_step(job_id, rank_step)

        yield _make_event(
            "rank_synthesize", "done",
            f"Ranked {len(company_profiles)} companies ({elapsed:.1f}s)",
            model=rank_step.model_used, duration=elapsed,
        )
        yield _make_event(
            "complete", "done",
            f"Company sourcing complete: {len(company_profiles)} comparable companies found",
            event_type="complete",
        )

    except Exception as e:
        elapsed = time.monotonic() - t0
        logger.error("Rank & synthesize failed: %s", e, exc_info=True)
        rank_step.status = "error"
        rank_step.error_message = str(e)[:500]
        rank_step.completed_at = _now_iso()
        await _save_step(job_id, rank_step)
        yield _make_event("rank_synthesize", "error", "Ranking failed", model=rank_step.model_used, duration=elapsed)
        yield _make_event("complete", "error", "Sourcing failed", event_type="complete")
