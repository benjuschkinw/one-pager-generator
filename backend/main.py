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


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "one-pager-generator"}
