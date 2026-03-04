"""Jobs REST API: CRUD for persistent job storage, file downloads, PPTX generation, deep research SSE."""

import asyncio
import json
import logging
import os
import re
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from models.job import Job, JobSummary
from models.one_pager import OnePagerData
from services.deep_research import run_deep_research
from services.job_store import (
    OUTPUTS_DIR,
    delete_job,
    get_job,
    list_jobs,
    save_edited_data,
    save_pptx_path,
    save_research_data,
    update_job,
)
from services.pptx_generator import generate_one_pager

router = APIRouter()
logger = logging.getLogger(__name__)


class EditDataRequest(BaseModel):
    """Request body for saving edited OnePagerData."""
    data: OnePagerData


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


@router.post("/jobs/{job_id}/research/deep")
async def deep_research(job_id: str):
    """
    Run the deep research pipeline for a job, streaming progress as SSE events.

    SSE event types:
      - progress: step status update (running, rechecking, etc.)
      - step_complete: a step finished with confidence score
      - complete: entire pipeline finished
      - error: a step or the pipeline encountered an error
    """
    job = await get_job(job_id)
    if job is None:
        raise HTTPException(404, "Job not found")

    if job.status not in ("pending", "completed", "failed"):
        raise HTTPException(
            409,
            f"Job is currently '{job.status}'. Cannot start deep research.",
        )

    # Mark job as researching
    await update_job(job_id, status="researching", research_mode="deep")

    # SSE event queue for progress streaming
    event_queue: asyncio.Queue = asyncio.Queue()

    def progress_callback(step_name: str, status: str, label: str, detail: str | None):
        """Push progress events to the SSE queue."""
        if status in ("done", "verified"):
            event_type = "step_complete"
        elif status == "error":
            event_type = "error"
        else:
            event_type = "progress"

        data: dict = {"step": step_name, "label": label, "status": status}
        if detail:
            data["detail"] = detail

        # For step_complete events, try to include confidence from detail
        if status == "verified" and detail and "Confidence:" in detail:
            try:
                pct_str = detail.split("Confidence:")[1].strip().rstrip("%")
                data["confidence"] = float(pct_str) / 100.0
            except (ValueError, IndexError):
                pass

        event_queue.put_nowait({"event": event_type, "data": data})

    async def run_pipeline():
        """Run the deep research pipeline and push final events."""
        try:
            final_data, verification, step_records = await run_deep_research(
                company_name=job.company_name,
                im_text=job.im_text,
                progress_callback=progress_callback,
            )

            # Save results to job
            await save_research_data(job_id, final_data, verification)
            await update_job(
                job_id,
                status="completed",
                deep_research_steps=step_records,
            )

            event_queue.put_nowait({
                "event": "complete",
                "data": {"job_id": job_id},
            })

        except Exception as e:
            logger.error("Deep research pipeline failed for job %s: %s", job_id, e)
            await update_job(job_id, status="failed")
            event_queue.put_nowait({
                "event": "error",
                "data": {"step": "pipeline", "message": str(e)},
            })

        # Sentinel to signal stream end
        event_queue.put_nowait(None)

    async def event_generator():
        """Generate SSE events from the queue."""
        # Start pipeline as a background task
        task = asyncio.create_task(run_pipeline())

        try:
            while True:
                event = await event_queue.get()
                if event is None:
                    # Pipeline finished
                    break

                event_type = event.get("event", "progress")
                data_json = json.dumps(event.get("data", {}))
                yield f"event: {event_type}\ndata: {data_json}\n\n"
        except asyncio.CancelledError:
            task.cancel()
            raise

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
