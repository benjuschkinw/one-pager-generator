"""Market Research API: create jobs and run market research pipeline via SSE."""

import json
import logging

from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import StreamingResponse

from services.job_store import create_job, get_job, update_job
from services.market_research import run_market_research

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/market-research")
async def api_start_market_research(
    market_name: str = Form(...),
    region: str = Form("DACH"),
):
    """
    Create a market research job and immediately start the pipeline,
    streaming progress as SSE events.

    - **market_name**: Name of the market/industry to research (e.g. "Dental-Labore")
    - **region**: Geographic focus (default: "DACH")
    """
    if not market_name.strip():
        raise HTTPException(400, "Market name is required")

    # Create a job record
    job = await create_job(
        company_name=market_name.strip(),  # reuse company_name field for market_name
        research_mode="market",
    )
    job_id = job.id

    # Mark job as researching
    await update_job(job_id, status="researching", research_mode="market")

    async def event_stream():
        # First emit the job_id so the frontend can redirect
        yield f"event: job_created\ndata: {json.dumps({'job_id': job_id})}\n\n"

        async for event in run_market_research(job_id, market_name.strip(), region.strip()):
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
