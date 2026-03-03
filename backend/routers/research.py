"""Research endpoint: AI-powered company research for One-Pager generation."""

from fastapi import APIRouter, File, Form, UploadFile, HTTPException

from models.one_pager import OnePagerData
from services.ai_research import research_company
from services.pdf_extractor import extract_text_from_pdf

router = APIRouter()

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


@router.post("/research", response_model=OnePagerData)
async def research(
    company_name: str = Form(...),
    im_file: UploadFile | None = File(None),
):
    """
    Research a company using AI and optionally extract data from an uploaded IM PDF.

    - **company_name**: Name of the target company
    - **im_file**: Optional PDF file (Information Memorandum)

    Returns populated OnePagerData JSON.
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
        data = research_company(company_name, im_text)
    except Exception as e:
        raise HTTPException(500, f"Research failed: {str(e)}")

    return data
