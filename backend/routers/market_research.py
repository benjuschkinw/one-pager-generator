"""Market Research API: create jobs and run market research pipeline via SSE."""

import json
import logging
import re

from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import StreamingResponse

from services.job_store import create_job, get_job, update_job
from services.market_research import run_market_research

router = APIRouter()
logger = logging.getLogger(__name__)

# Validation constants
_MAX_MARKET_NAME_LEN = 200
_MAX_SCOPING_JSON_LEN = 10_000
_MAX_SCOPING_FIELD_LEN = 500
_ALLOWED_REGIONS = {"DACH", "Germany", "Europe", "Global"}
_ALLOWED_SCOPING_KEYS = {
    "product_scope", "value_chain_focus", "geographic_detail",
    "time_horizon", "customer_type", "customer_detail",
    "market_metric", "study_purpose",
}


def _sanitize_market_name(name: str) -> str:
    """Strip characters that could be used for prompt structure injection."""
    # Remove triple backticks, markdown headings, and control sequences
    name = re.sub(r"[`#]{3,}", "", name)
    # Remove newlines and carriage returns (prevent prompt line injection)
    name = name.replace("\n", " ").replace("\r", " ")
    # Collapse multiple spaces
    name = re.sub(r"\s{2,}", " ", name)
    return name.strip()


def _sanitize_scoping(raw: dict) -> dict:
    """Validate and sanitize scoping context: whitelist keys, limit lengths."""
    clean: dict[str, str] = {}
    for key, val in raw.items():
        if key not in _ALLOWED_SCOPING_KEYS:
            continue
        if not isinstance(val, str):
            val = str(val)
        # Truncate overly long values
        val = val[:_MAX_SCOPING_FIELD_LEN]
        # Strip characters that could be used for prompt structure injection
        val = re.sub(r"[`#]{3,}", "", val)
        clean[key] = val
    return clean


@router.post("/market-research")
async def api_start_market_research(
    market_name: str = Form(...),
    region: str = Form("DACH"),
    scoping_context: str = Form("{}"),
):
    """
    Create a market research job and immediately start the pipeline,
    streaming progress as SSE events.

    - **market_name**: Name of the market/industry to research (e.g. "Dental-Labore")
    - **region**: Geographic focus (default: "DACH")
    - **scoping_context**: JSON string with scoping answers (product scope, customer, etc.)
    """
    # --- Input validation ---
    market_name = _sanitize_market_name(market_name)
    if not market_name:
        raise HTTPException(400, "Market name is required")
    if len(market_name) > _MAX_MARKET_NAME_LEN:
        raise HTTPException(400, f"Market name too long (max {_MAX_MARKET_NAME_LEN} characters)")

    if region not in _ALLOWED_REGIONS:
        region = "DACH"

    if len(scoping_context) > _MAX_SCOPING_JSON_LEN:
        raise HTTPException(400, "Scoping context too large")

    # Parse and sanitize scoping context
    try:
        scoping_raw = json.loads(scoping_context) if scoping_context else {}
    except json.JSONDecodeError:
        scoping_raw = {}

    if not isinstance(scoping_raw, dict):
        scoping_raw = {}

    scoping = _sanitize_scoping(scoping_raw)

    # Create a job record
    job = await create_job(
        company_name=market_name,
        research_mode="market",
    )
    job_id = job.id

    # Mark job as researching
    await update_job(job_id, status="researching", research_mode="market")

    async def event_stream():
        # First emit the job_id so the frontend can redirect
        yield f"event: job_created\ndata: {json.dumps({'job_id': job_id})}\n\n"

        async for event in run_market_research(
            job_id, market_name, region, scoping_context=scoping,
        ):
            event_type = event.pop("_event_type", "progress")
            yield f"event: {event_type}\ndata: {json.dumps(event)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
