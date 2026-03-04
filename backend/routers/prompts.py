"""
Prompts API: view and edit all AI prompts used in the research/verification pipeline.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.prompt_manager import (
    get_all_prompts,
    get_prompt,
    update_prompt,
    reset_prompt,
    reset_all_prompts,
)

router = APIRouter()


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
async def update_single_prompt(name: str, body: PromptUpdateRequest):
    """Update a prompt's template text."""
    result = update_prompt(name, body.template)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Prompt '{name}' not found")
    return result


@router.post("/prompts/{name}/reset")
async def reset_single_prompt(name: str):
    """Reset a prompt to its default template."""
    result = reset_prompt(name)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Prompt '{name}' not found")
    return result


@router.post("/prompts/reset")
async def reset_all():
    """Reset all prompts to their defaults."""
    return reset_all_prompts()
