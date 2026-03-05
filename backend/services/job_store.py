"""SQLite-backed persistent job storage using aiosqlite."""

import json
import logging
import os
import shutil
import uuid
from datetime import datetime
from typing import Any, Optional

import aiosqlite

from models.job import DeepResearchStep, Job, JobSummary, StepVerification
from models.market_study import MarketStudyData
from models.one_pager import OnePagerData, VerificationResult

logger = logging.getLogger(__name__)

# Resolve paths relative to the backend directory
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DATA_DIR = os.path.join(_BACKEND_DIR, "data")
DB_PATH = os.path.join(_DATA_DIR, "jobs.db")
UPLOADS_DIR = os.path.join(_DATA_DIR, "uploads")
OUTPUTS_DIR = os.path.join(_DATA_DIR, "outputs")

# JSON fields that are stored as TEXT in SQLite
_JSON_FIELDS = {
    "research_data",
    "verification",
    "deep_research_steps",
    "edited_data",
    "market_study_data",
    "edited_market_data",
}


def _ensure_dirs() -> None:
    """Create data directories if they don't exist."""
    os.makedirs(_DATA_DIR, exist_ok=True)
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    os.makedirs(OUTPUTS_DIR, exist_ok=True)


def _row_to_job(row: aiosqlite.Row) -> Job:
    """Convert a database row to a Job model."""
    d = dict(row)

    # Parse JSON fields
    if d.get("research_data"):
        d["research_data"] = OnePagerData(**json.loads(d["research_data"]))
    if d.get("verification"):
        d["verification"] = VerificationResult(**json.loads(d["verification"]))
    if d.get("deep_research_steps"):
        steps_raw = json.loads(d["deep_research_steps"])
        d["deep_research_steps"] = [DeepResearchStep(**s) for s in steps_raw]
    if d.get("edited_data"):
        d["edited_data"] = OnePagerData(**json.loads(d["edited_data"]))
    if d.get("market_study_data"):
        d["market_study_data"] = MarketStudyData(**json.loads(d["market_study_data"]))
    if d.get("edited_market_data"):
        d["edited_market_data"] = MarketStudyData(**json.loads(d["edited_market_data"]))

    return Job(**d)


def _row_to_summary(row: aiosqlite.Row) -> JobSummary:
    """Convert a database row to a JobSummary model."""
    d = dict(row)
    d["has_pptx"] = bool(d.get("pptx_file_path"))
    # Remove fields not in JobSummary
    for key in list(d.keys()):
        if key not in JobSummary.model_fields:
            del d[key]
    return JobSummary(**d)


async def init_db() -> None:
    """Create the jobs table if it doesn't exist. Called on app startup."""
    _ensure_dirs()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                company_name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                im_filename TEXT,
                im_file_path TEXT,
                im_text TEXT,
                provider TEXT,
                model TEXT,
                research_mode TEXT DEFAULT 'standard',
                research_data TEXT,
                verification TEXT,
                deep_research_steps TEXT,
                edited_data TEXT,
                pptx_file_path TEXT,
                market_study_data TEXT,
                edited_market_data TEXT
            )
        """)
        # Add columns if upgrading from older schema
        for col in ("market_study_data", "edited_market_data"):
            try:
                await db.execute(f"ALTER TABLE jobs ADD COLUMN {col} TEXT")
            except Exception:
                pass  # Column already exists
        await db.commit()
    logger.info("Job database initialized at %s", DB_PATH)


async def create_job(
    company_name: str,
    im_filename: Optional[str] = None,
    im_text: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    research_mode: str = "standard",
) -> Job:
    """Create a new job record and return it."""
    now = datetime.utcnow().isoformat()
    job_id = str(uuid.uuid4())

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO jobs (id, company_name, created_at, updated_at, status,
                              im_filename, im_text, provider, model, research_mode)
            VALUES (?, ?, ?, ?, 'pending', ?, ?, ?, ?, ?)
            """,
            (job_id, company_name, now, now, im_filename, im_text,
             provider, model, research_mode),
        )
        await db.commit()

    return Job(
        id=job_id,
        company_name=company_name,
        created_at=now,
        updated_at=now,
        status="pending",
        im_filename=im_filename,
        im_text=im_text,
        provider=provider,
        model=model,
        research_mode=research_mode,
    )


async def get_job(job_id: str) -> Optional[Job]:
    """Retrieve a job by ID, or None if not found."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        row = await cursor.fetchone()
        if row is None:
            return None
        return _row_to_job(row)


async def list_jobs() -> list[JobSummary]:
    """List all jobs sorted by created_at descending."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM jobs ORDER BY created_at DESC"
        )
        rows = await cursor.fetchall()
        return [_row_to_summary(row) for row in rows]


async def update_job(job_id: str, **fields: Any) -> Optional[Job]:
    """Update specific fields on a job. Returns the updated job or None."""
    if not fields:
        return await get_job(job_id)

    # Serialize JSON fields
    for key in _JSON_FIELDS:
        if key in fields and fields[key] is not None:
            val = fields[key]
            if hasattr(val, "model_dump"):
                fields[key] = json.dumps(val.model_dump())
            elif isinstance(val, list):
                fields[key] = json.dumps(
                    [item.model_dump() if hasattr(item, "model_dump") else item
                     for item in val]
                )
            elif isinstance(val, dict):
                fields[key] = json.dumps(val)

    fields["updated_at"] = datetime.utcnow().isoformat()

    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [job_id]

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"UPDATE jobs SET {set_clause} WHERE id = ?",
            values,
        )
        await db.commit()

    return await get_job(job_id)


async def delete_job(job_id: str) -> bool:
    """Delete a job and its associated files. Returns True if job existed."""
    job = await get_job(job_id)
    if job is None:
        return False

    # Delete files
    upload_dir = os.path.join(UPLOADS_DIR, job_id)
    output_dir = os.path.join(OUTPUTS_DIR, job_id)
    if os.path.exists(upload_dir):
        shutil.rmtree(upload_dir)
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
        await db.commit()

    return True


async def save_research_data(
    job_id: str,
    data: OnePagerData,
    verification: Optional[VerificationResult] = None,
) -> Optional[Job]:
    """Save research results to a job."""
    fields: dict[str, Any] = {
        "research_data": data,
        "status": "completed",
    }
    if verification is not None:
        fields["verification"] = verification
    return await update_job(job_id, **fields)


async def save_edited_data(job_id: str, data: OnePagerData) -> Optional[Job]:
    """Save user-edited data to a job."""
    return await update_job(job_id, edited_data=data)


async def save_pptx_path(job_id: str, path: str) -> Optional[Job]:
    """Save the PPTX file path to a job."""
    return await update_job(job_id, pptx_file_path=path)


async def save_market_study_data(
    job_id: str,
    data: MarketStudyData,
    verification: Optional[VerificationResult] = None,
) -> Optional[Job]:
    """Save market study results to a job."""
    fields: dict[str, Any] = {
        "market_study_data": data,
        "status": "completed",
    }
    if verification is not None:
        fields["verification"] = verification
    return await update_job(job_id, **fields)


async def save_edited_market_data(
    job_id: str, data: MarketStudyData
) -> Optional[Job]:
    """Save user-edited market study data to a job."""
    return await update_job(job_id, edited_market_data=data)
