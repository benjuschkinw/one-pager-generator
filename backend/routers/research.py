"""Research endpoint: AI-powered company research for One-Pager generation."""
import logging
import os
from typing import Optional

from fastapi import APIRouter, File, Form, UploadFile, HTTPException

from models.one_pager import ResearchResponse
from services.ai_research import research_company
from services.job_store import (
    UPLOADS_DIR,
    create_job,
    save_research_data,
    update_job,
)
from services.pdf_extractor import extract_text_from_pdf
from services.verification import verify_research

router = APIRouter()
logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


@router.post("/research", response_model=ResearchResponse)
async def research(
    company_name: str = Form(...),
    im_file: Optional[UploadFile] = File(None),
    provider: Optional[str] = Form(None),
    model: Optional[str] = Form(None),
    verify: bool = Form(True),
):
    """
    Research a company using AI and optionally extract data from an uploaded IM PDF.

    - **company_name**: Name of the target company
    - **im_file**: Optional PDF file (Information Memorandum)
    - **provider**: AI provider — "anthropic" or "openrouter" (auto-detected if omitted)
    - **model**: Model ID override (uses provider default if omitted)
    - **verify**: Run cross-verification with a second AI model (default: true)

    Returns populated OnePagerData JSON with optional verification results and job_id.
    """
    im_text = None
    im_filename = None
    pdf_content = None

    if im_file and im_file.filename:
        # Validate file type
        if not im_file.filename.lower().endswith(".pdf"):
            raise HTTPException(400, "Only PDF files are supported")

        # Read and validate size
        pdf_content = await im_file.read()
        if len(pdf_content) > MAX_FILE_SIZE:
            raise HTTPException(400, f"File too large (max {MAX_FILE_SIZE // (1024*1024)} MB)")

        im_filename = im_file.filename

        # Extract text
        try:
            im_text = extract_text_from_pdf(pdf_content)
        except Exception as e:
            raise HTTPException(400, f"Failed to extract PDF text: {str(e)}")

    # Create a job record
    job_id = None
    try:
        job = await create_job(
            company_name=company_name,
            im_filename=im_filename,
            im_text=im_text,
            provider=provider,
            model=model,
            research_mode="standard",
        )
        job_id = job.id

        # Store uploaded PDF to disk
        if pdf_content and job_id:
            upload_dir = os.path.join(UPLOADS_DIR, job_id)
            os.makedirs(upload_dir, exist_ok=True)
            im_file_path = os.path.join(upload_dir, "original.pdf")
            with open(im_file_path, "wb") as f:
                f.write(pdf_content)
            await update_job(job_id, im_file_path=im_file_path)

        # Set status to researching
        await update_job(job_id, status="researching")
    except Exception as e:
        logger.error("Failed to create job: %s", str(e))
        # Continue without job — backwards compatible

    try:
        data = research_company(company_name, im_text, provider=provider, model=model)
    except ValueError as e:
        if job_id:
            try:
                await update_job(job_id, status="failed")
            except Exception:
                pass
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error("Research failed: %s", str(e))
        if job_id:
            try:
                await update_job(job_id, status="failed")
            except Exception:
                pass
        raise HTTPException(500, "Research failed. Please check API keys and try again.")

    # Cross-verify with a second AI model
    verification = None
    if verify:
        try:
            research_provider = provider or "anthropic"
            verification = verify_research(
                data,
                company_name,
                im_text=im_text,
                research_provider=research_provider,
            )
        except Exception as e:
            # Verification failure should not block the research result
            logger.error("Verification failed: %s", str(e))

    # Save research results to job
    if job_id:
        try:
            await save_research_data(job_id, data, verification)
        except Exception as e:
            logger.error("Failed to save research data to job: %s", str(e))

    return ResearchResponse(data=data, verification=verification, job_id=job_id)
