"""Generate endpoint: produces the One-Pager PPTX file from structured data."""

import logging
import re

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from models.one_pager import GenerateRequest
from services.pptx_generator import generate_one_pager

router = APIRouter()
logger = logging.getLogger(__name__)


def _sanitize_filename(name: str) -> str:
    """Sanitize a string for use in a filename (prevent header injection)."""
    # Strip control characters (CR, LF, null, etc.) first
    sanitized = re.sub(r'[\x00-\x1f\x7f]', '', name)
    # Keep only safe filename characters
    sanitized = re.sub(r'[^\w\s\-.]', '', sanitized)
    sanitized = sanitized.replace(" ", "_").strip("_.")
    return sanitized[:100] or "Company"


@router.post("/generate")
async def generate(request: GenerateRequest):
    """
    Generate a One-Pager PPTX from structured data.

    Accepts the full OnePagerData JSON and returns a downloadable PPTX file.
    """
    try:
        pptx_bytes = generate_one_pager(request.data)
    except FileNotFoundError:
        raise HTTPException(500, "PPTX template not found. Check backend deployment.")
    except Exception as e:
        logger.error("PPTX generation failed: %s", str(e))
        raise HTTPException(500, "PPTX generation failed. Please try again.")

    company = _sanitize_filename(request.data.header.company_name or "Company")
    # Escape quotes in filename to prevent header injection
    filename = f"One_Pager_{company}.pptx".replace('"', "'")

    return Response(
        content=pptx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
