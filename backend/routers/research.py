"""Research endpoint: AI-powered company research for One-Pager generation."""
from typing import Optional

from fastapi import APIRouter, File, Form, UploadFile, HTTPException

from models.one_pager import ResearchResponse
from services.ai_research import research_company
from services.pdf_extractor import extract_text_from_pdf
from services.verification import verify_research

router = APIRouter()

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

    Returns populated OnePagerData JSON with optional verification results.
    """
    im_text = None

    if im_file and im_file.filename:
        # Validate file type
        if not im_file.filename.lower().endswith(".pdf"):
            raise HTTPException(400, "Only PDF files are supported")

        # Read and validate size
        content = await im_file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(400, f"File too large (max {MAX_FILE_SIZE // (1024*1024)} MB)")

        # Extract text
        try:
            im_text = extract_text_from_pdf(content)
        except Exception as e:
            raise HTTPException(400, f"Failed to extract PDF text: {str(e)}")

    try:
        data = research_company(company_name, im_text, provider=provider, model=model)
    except Exception as e:
        raise HTTPException(500, f"Research failed: {str(e)}")

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
            import logging
            logging.getLogger(__name__).error("Verification failed: %s", str(e))

    return ResearchResponse(data=data, verification=verification)
