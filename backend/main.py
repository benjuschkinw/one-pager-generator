"""
FastAPI backend for the M&A One-Pager Generator.

Endpoints:
  POST /api/research  - AI-powered company research
  POST /api/generate  - PPTX generation from structured data
  GET  /api/health    - Health check
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.research import router as research_router
from routers.generate import router as generate_router
from routers.prompts import router as prompts_router
from routers.jobs import router as jobs_router
from routers.market_research import router as market_research_router
from services.ai_research import get_available_providers
from services.job_store import init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")

app = FastAPI(
    title="M&A One-Pager Generator",
    description="Generate Constellation Capital AG One-Pager slides from AI research",
    version="1.0.0",
)

# CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

# Mount routers
app.include_router(research_router, prefix="/api", tags=["research"])
app.include_router(generate_router, prefix="/api", tags=["generate"])
app.include_router(prompts_router, prefix="/api", tags=["prompts"])
app.include_router(jobs_router, prefix="/api", tags=["jobs"])
app.include_router(market_research_router, prefix="/api", tags=["market-research"])


@app.on_event("startup")
async def startup():
    """Initialize the database on application startup."""
    await init_db()


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "one-pager-generator"}


@app.get("/api/providers")
async def providers():
    """List available AI providers and their models."""
    return get_available_providers()
