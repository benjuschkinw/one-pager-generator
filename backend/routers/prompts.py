"""
Prompts API: view and edit all AI prompts used in the research/verification pipeline.

Mutation endpoints (PUT, POST) require an API key via the X-Admin-Key header.
Set the ADMIN_API_KEY environment variable to enable authentication.
If ADMIN_API_KEY is not set, mutations are disabled entirely.
"""

import os

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel

from services.prompt_manager import (
    get_all_prompts,
    get_prompt,
    update_prompt,
    reset_prompt,
    reset_all_prompts,
)

router = APIRouter()

ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY", "")


def _require_admin(x_admin_key: str | None):
    """Verify the caller provided a valid admin key for mutation endpoints."""
    if not ADMIN_API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Prompt editing is disabled. Set ADMIN_API_KEY env var to enable.",
        )
    if x_admin_key != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing X-Admin-Key header")


class PromptUpdateRequest(BaseModel):
    template: str


@router.get("/prompts")
async def list_prompts():
    """List all editable prompts with their current templates."""
    return get_all_prompts()


@router.get("/prompts/{name}")
async def get_single_prompt(name: str):
    """Get a single prompt by name."""
    result = get_prompt(name)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Prompt '{name}' not found")
    return result


@router.put("/prompts/{name}")
async def update_single_prompt(
    name: str, body: PromptUpdateRequest, x_admin_key: str | None = Header(None)
):
    """Update a prompt's template text. Requires X-Admin-Key header."""
    _require_admin(x_admin_key)
    result = update_prompt(name, body.template)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Prompt '{name}' not found")
    return result


@router.post("/prompts/{name}/reset")
async def reset_single_prompt(name: str, x_admin_key: str | None = Header(None)):
    """Reset a prompt to its default template. Requires X-Admin-Key header."""
    _require_admin(x_admin_key)
    result = reset_prompt(name)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Prompt '{name}' not found")
    return result


@router.post("/prompts/reset")
async def reset_all(x_admin_key: str | None = Header(None)):
    """Reset all prompts to their defaults. Requires X-Admin-Key header."""
    _require_admin(x_admin_key)
    return reset_all_prompts()
