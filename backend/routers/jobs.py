"""Jobs REST API: CRUD for persistent job storage, file downloads, PPTX generation, deep research SSE."""

import json
import logging
import os
import re

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from models.job import Job, JobSummary
from models.market_study import MarketStudyData
from models.one_pager import OnePagerData
from services.deep_research import run_deep_research
from services.job_store import (
    OUTPUTS_DIR,
    delete_job,
    get_job,
    list_jobs,
    save_edited_data,
    save_edited_market_data,
    save_pptx_path,
    update_job,
)
from services.market_pptx_generator import generate_market_study
from services.pptx_generator import generate_one_pager

router = APIRouter()
logger = logging.getLogger(__name__)


class EditDataRequest(BaseModel):
    """Request body for saving edited OnePagerData."""
    data: OnePagerData


class EditMarketDataRequest(BaseModel):
    """Request body for saving edited MarketStudyData."""
    data: MarketStudyData


def _sanitize_filename(name: str) -> str:
    """Sanitize a string for use in a filename."""
    sanitized = re.sub(r'[\x00-\x1f\x7f]', '', name)
    sanitized = re.sub(r'[^\w\s\-.]', '', sanitized)
    sanitized = sanitized.replace(" ", "_").strip("_.")
    return sanitized[:100] or "Company"


@router.get("/jobs", response_model=list[JobSummary])
async def api_list_jobs():
    """List all jobs sorted by creation date (newest first)."""
    return await list_jobs()


@router.get("/jobs/{job_id}", response_model=Job)
async def api_get_job(job_id: str):
    """Get full job details by ID."""
    job = await get_job(job_id)
    if job is None:
        raise HTTPException(404, "Job not found")
    return job


@router.delete("/jobs/{job_id}")
async def api_delete_job(job_id: str):
    """Delete a job and its associated files."""
    deleted = await delete_job(job_id)
    if not deleted:
        raise HTTPException(404, "Job not found")
    return {"ok": True}


@router.get("/jobs/{job_id}/im")
async def api_get_im(job_id: str):
    """Download the original uploaded IM PDF for a job."""
    job = await get_job(job_id)
    if job is None:
        raise HTTPException(404, "Job not found")
    if not job.im_file_path or not os.path.exists(job.im_file_path):
        raise HTTPException(404, "No IM file available for this job")

    filename = job.im_filename or "document.pdf"
    return FileResponse(
        path=job.im_file_path,
        media_type="application/pdf",
        filename=filename,
    )


@router.get("/jobs/{job_id}/pptx")
async def api_get_pptx(job_id: str):
    """Download the generated PPTX for a job."""
    job = await get_job(job_id)
    if job is None:
        raise HTTPException(404, "Job not found")
    if not job.pptx_file_path or not os.path.exists(job.pptx_file_path):
        raise HTTPException(404, "No PPTX file available for this job")

    company = _sanitize_filename(job.company_name)
    filename = f"One_Pager_{company}.pptx"
    return FileResponse(
        path=job.pptx_file_path,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=filename,
    )


@router.put("/jobs/{job_id}/data", response_model=Job)
async def api_save_edited_data(job_id: str, request: EditDataRequest):
    """Save edited OnePagerData back to the job."""
    job = await get_job(job_id)
    if job is None:
        raise HTTPException(404, "Job not found")

    updated = await save_edited_data(job_id, request.data)
    if updated is None:
        raise HTTPException(500, "Failed to save edited data")
    return updated


@router.post("/jobs/{job_id}/generate")
async def api_generate_pptx(job_id: str):
    """Generate PPTX from the job's edited_data (or research_data), save it, and return the file."""
    job = await get_job(job_id)
    if job is None:
        raise HTTPException(404, "Job not found")

    # Use edited data if available, otherwise fall back to research data
    data = job.edited_data or job.research_data
    if data is None:
        raise HTTPException(400, "No research data available to generate PPTX")

    try:
        pptx_bytes = generate_one_pager(data)
    except FileNotFoundError:
        raise HTTPException(500, "PPTX template not found. Check backend deployment.")
    except Exception as e:
        logger.error("PPTX generation failed for job %s: %s", job_id, str(e))
        raise HTTPException(500, "PPTX generation failed. Please try again.")

    # Save to disk
    output_dir = os.path.join(OUTPUTS_DIR, job_id)
    os.makedirs(output_dir, exist_ok=True)
    pptx_path = os.path.join(output_dir, "one_pager.pptx")
    with open(pptx_path, "wb") as f:
        f.write(pptx_bytes)

    # Update job record
    await save_pptx_path(job_id, pptx_path)

    company = _sanitize_filename(job.company_name)
    filename = f"One_Pager_{company}.pptx"
    return FileResponse(
        path=pptx_path,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=filename,
    )


@router.put("/jobs/{job_id}/market-data", response_model=Job)
async def api_save_edited_market_data(job_id: str, request: EditMarketDataRequest):
    """Save edited MarketStudyData back to the job."""
    job = await get_job(job_id)
    if job is None:
        raise HTTPException(404, "Job not found")

    updated = await save_edited_market_data(job_id, request.data)
    if updated is None:
        raise HTTPException(500, "Failed to save market data")
    return updated


@router.post("/jobs/{job_id}/generate-market")
async def api_generate_market_pptx(job_id: str):
    """Generate a 10-slide market study PPTX from job data."""
    job = await get_job(job_id)
    if job is None:
        raise HTTPException(404, "Job not found")

    data = job.edited_market_data or job.market_study_data
    if data is None:
        raise HTTPException(400, "No market study data available")

    try:
        pptx_bytes = generate_market_study(data)
    except Exception as e:
        logger.error("Market PPTX generation failed for job %s: %s", job_id, str(e))
        raise HTTPException(500, "Market study PPTX generation failed.")

    # Save to disk
    output_dir = os.path.join(OUTPUTS_DIR, job_id)
    os.makedirs(output_dir, exist_ok=True)
    pptx_path = os.path.join(output_dir, "market_study.pptx")
    with open(pptx_path, "wb") as f:
        f.write(pptx_bytes)

    await save_pptx_path(job_id, pptx_path)

    company = _sanitize_filename(job.company_name)
    filename = f"Market_Study_{company}.pptx"
    return FileResponse(
        path=pptx_path,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=filename,
    )


@router.post("/jobs/{job_id}/research/deep")
async def api_deep_research(job_id: str):
    """
    Run the deep research pipeline for a job, streaming progress as SSE events.

    The pipeline is an async generator that yields event dicts.  Each dict
    contains an ``_event_type`` key (progress | complete) plus fields the
    frontend DeepResearchProgress component expects:
      step, status, message, model?, duration?, confidence?
    """
    job = await get_job(job_id)
    if job is None:
        raise HTTPException(404, "Job not found")

    if job.status == "researching":
        raise HTTPException(
            409,
            "Deep research is already running for this job.",
        )

    # Mark job as researching
    await update_job(job_id, status="researching", research_mode="deep")

    async def event_stream():
        async for event in run_deep_research(job_id, job.company_name, job.im_text):
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
