# Plan: Persistent Jobs + Deep Research

## Overview

Two interconnected features:
1. **Persistent Job Storage** — Every research run becomes a "job" with uploaded docs, AI research, extracted data, PPTX output, and deep research all saved and browsable
2. **Deep Research** — Multi-step AI pipeline with per-step model selection via OpenRouter

---

## Part 1: Persistent Job Storage

### Problem

Currently all data lives in browser `sessionStorage` — it's lost on refresh, can't be shared, and there's no history. Users can't go back to previous research runs to compare results or re-download artifacts.

### Data Model

**New file: `backend/models/job.py`**

```python
class Job:
    id: str                    # UUID
    company_name: str
    created_at: datetime
    updated_at: datetime
    status: "pending" | "researching" | "completed" | "failed"

    # Inputs
    im_filename: str | None    # Original uploaded filename
    im_file_path: str | None   # Path to stored PDF on disk
    im_text: str | None        # Extracted text from PDF

    # Research config
    provider: str | None
    model: str | None
    research_mode: "standard" | "deep"

    # Outputs
    research_data: OnePagerData | None        # AI research result
    verification: VerificationResult | None   # Cross-verification
    deep_research_steps: list[DeepResearchStep] | None  # Per-step results (deep mode)
    edited_data: OnePagerData | None          # User-edited version
    pptx_file_path: str | None               # Path to generated PPTX

class DeepResearchStep:
    step_name: str             # e.g. "im_extraction", "web_research"
    model_used: str            # e.g. "anthropic/claude-opus-4"
    status: "pending" | "running" | "done" | "error"
    started_at: datetime | None
    completed_at: datetime | None
    result_json: dict | None   # Partial result from this step
    error_message: str | None
```

### Storage

**SQLite + aiosqlite** — lightweight, zero-config, perfect for a single-user tool:
- `backend/services/job_store.py` — CRUD operations for jobs
- DB file: `data/jobs.db` (gitignored)
- File uploads stored in: `data/uploads/{job_id}/` (original PDFs)
- Generated PPTX stored in: `data/outputs/{job_id}/` (PPTX files)

Tables:
```sql
CREATE TABLE jobs (
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
    research_data TEXT,        -- JSON
    verification TEXT,         -- JSON
    deep_research_steps TEXT,  -- JSON array
    edited_data TEXT,          -- JSON
    pptx_file_path TEXT
);
```

### API Endpoints

**New file: `backend/routers/jobs.py`**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/jobs` | List all jobs (summary: id, company, status, created_at, has_im, has_pptx) |
| `GET` | `/api/jobs/{id}` | Full job details (all data, verification, deep research steps) |
| `DELETE` | `/api/jobs/{id}` | Delete job + associated files |
| `GET` | `/api/jobs/{id}/im` | Download the original uploaded IM PDF |
| `GET` | `/api/jobs/{id}/pptx` | Download the generated PPTX |
| `PUT` | `/api/jobs/{id}/data` | Save edited OnePagerData back to the job |
| `POST` | `/api/jobs/{id}/generate` | Generate PPTX from job's edited_data, save to job |

### Modified Research Flow

**Current flow:**
```
POST /api/research → returns JSON → sessionStorage → /editor
```

**New flow:**
```
POST /api/research → creates job → saves inputs → runs AI → saves outputs → returns job_id
Frontend redirects to /editor/{job_id}
All edits auto-save to PUT /api/jobs/{id}/data
PPTX generation saves to job via POST /api/jobs/{id}/generate
```

The existing `POST /api/research` endpoint is modified to:
1. Create a job record with status "pending"
2. Store the uploaded PDF in `data/uploads/{job_id}/`
3. Run research (sets status "researching")
4. Save research_data + verification to job (sets status "completed")
5. Return `{ job_id, data, verification }` (backwards-compatible, adds job_id)

### Frontend Changes

**New page: `/jobs` — Job History**
- Table/card list of all previous research jobs
- Each row: company name, date, status badge, has IM icon, has PPTX icon
- Click → navigates to `/editor/{job_id}`
- Delete button per job

**Modified: `/editor` → `/editor/[id]` — Job-aware Editor**
- Dynamic route: loads job data from `GET /api/jobs/{id}` instead of sessionStorage
- Auto-saves edits to backend via debounced `PUT /api/jobs/{id}/data`
- "Download IM" button (if job has IM)
- "Download PPTX" button (if job has generated PPTX)
- Generate button calls `POST /api/jobs/{id}/generate`

**Modified: `/` — Input Page**
- After research completes, redirects to `/editor/{job_id}` instead of `/editor`
- Add "Recent Jobs" section below the form showing last 5 jobs

**New component: `JobCard.tsx`**
- Compact card showing: company name, date, status, action icons (view, download IM, download PPTX, delete)

### File Structure

```
data/                          # gitignored
├── jobs.db                    # SQLite database
├── uploads/
│   └── {job_id}/
│       └── original.pdf       # Uploaded IM
└── outputs/
    └── {job_id}/
        └── one_pager.pptx     # Generated PPTX
```

---

## Part 2: Deep Research (builds on job persistence)

### OpenRouter Model Routing

**Confirmed:** OpenRouter supports explicit model selection per API call. Pass a model ID like `anthropic/claude-opus-4` in the `model` field → that exact model runs. Single API key, different models per call.

**Constraint:** Web search only works via Anthropic's native API (not OpenRouter). Steps needing web search must use the Anthropic client directly.

### Pipeline

**New file: `backend/services/deep_research.py`**

| Step | Sub-task | Model | Why |
|------|----------|-------|-----|
| 1 | **IM Extraction** (if PDF) | `anthropic/claude-opus-4` via OpenRouter | Best at long doc analysis |
| 2 | **Web Research** | `claude-opus-4` via Anthropic API | Needs web search |
| 3 | **Financial Deep-Dive** | `claude-opus-4` via Anthropic API | Needs web search for registries |
| 4 | **Management & Org** | `claude-opus-4` via Anthropic API | Needs web search for LinkedIn |
| 5 | **Market & Competitive** | `google/gemini-2.5-pro-preview` via OpenRouter | Strong synthesis, large context |
| 6 | **Merge & Synthesize** | `anthropic/claude-opus-4` via OpenRouter | Best structured output |
| 7 | **Cross-Verify** | `openai/gpt-4.1` via OpenRouter | Cross-model diversity |

```
                    ┌──────────────┐
                    │ 1. IM Extract│ (if PDF provided)
                    └──────┬───────┘
                           │
            ┌──────────────┼──────────────┬─────────────────┐
            ▼              ▼              ▼                 ▼
    ┌──────────────┐ ┌──────────┐ ┌────────────────┐ ┌──────────────┐
    │ 2. Web       │ │ 3. Fin   │ │ 4. Management  │ │ 5. Market &  │
    │   Research   │ │ Deep-Dive│ │    & Org       │ │ Competitive  │
    └──────┬───────┘ └────┬─────┘ └───────┬────────┘ └──────┬───────┘
           └──────────────┼───────────────┘                  │
                          ▼                                  │
                    ┌──────────────┐◄────────────────────────┘
                    │ 6. Merge &   │
                    │   Synthesize │
                    └──────┬───────┘
                           ▼
                    ┌──────────────┐
                    │ 7. Verify    │
                    └──────────────┘
```

Steps 2-5 run in parallel via `asyncio.gather`. Each step's result is saved to `deep_research_steps` in the job record as it completes.

### SSE Progress Streaming

**New endpoint: `POST /api/jobs/{id}/research/deep`** (returns SSE stream)

The job must already exist (created by the initial `POST /api/research` or a new `POST /api/jobs` endpoint). Deep research streams progress events:

```
event: progress
data: {"step": "im_extraction", "label": "Extracting IM document...", "status": "running"}

event: step_complete
data: {"step": "web_research", "fields_found": ["header.tagline", "key_facts.hq"]}

event: complete
data: {"job_id": "abc-123"}

event: error
data: {"step": "financials", "message": "Timed out, using partial data"}
```

Each step completion updates the job record in the database, so progress is persisted even if the browser disconnects.

### Model Configuration

**New file: `backend/config/models.py`**

```python
DEEP_RESEARCH_MODELS = {
    "im_extraction": env("MODEL_IM_EXTRACTION", "anthropic/claude-opus-4"),
    "web_research": "anthropic",        # Must use Anthropic API for web search
    "financials": "anthropic",           # Must use Anthropic API for web search
    "management": "anthropic",           # Must use Anthropic API for web search
    "market": env("MODEL_MARKET", "google/gemini-2.5-pro-preview"),
    "merge": env("MODEL_MERGE", "anthropic/claude-opus-4"),
    "verify": env("MODEL_VERIFY", "openai/gpt-4.1"),
}
```

### Sub-task Prompts

6 new prompts in `prompt_manager.py` (all editable via existing prompt editor):

| Prompt Name | Purpose |
|-------------|---------|
| `deep_im_extraction` | Extract structured data from IM |
| `deep_web_research` | Find public company basics |
| `deep_financials` | Find/verify financial data |
| `deep_management` | Find management team, ownership |
| `deep_market` | Market sizing, competitive landscape |
| `deep_merge` | Merge sub-task results into OnePagerData |

### Frontend: Deep Research Progress

**New component: `DeepResearchProgress.tsx`**
- Vertical stepper showing all steps
- Each step: status icon (pending/running/done/error) + label + model badge + duration
- Partial data arrival shows summary badges
- Connected to SSE stream

**Changes to input page:**
- "Research Depth" toggle: Standard vs Deep Research
- Deep mode uses SSE endpoint, shows progress stepper

---

## Implementation Order

### Phase A: Job Persistence (do first — foundation for everything)

1. `backend/models/job.py` — Job + DeepResearchStep Pydantic models
2. `backend/services/job_store.py` — SQLite CRUD with aiosqlite
3. `backend/routers/jobs.py` — REST API for jobs
4. Modify `backend/routers/research.py` — Create job on research, save results
5. Modify `backend/routers/generate.py` — Save PPTX to job
6. `backend/main.py` — Mount jobs router, init DB on startup
7. `frontend/src/lib/types.ts` — Job types
8. `frontend/src/lib/api.ts` — Job API functions
9. `frontend/src/app/editor/[id]/page.tsx` — Job-aware editor (replaces sessionStorage)
10. `frontend/src/app/jobs/page.tsx` — Job history page
11. `frontend/src/app/components/JobCard.tsx` — Job list item
12. Modify `frontend/src/app/page.tsx` — Show recent jobs, redirect to `/editor/{id}`
13. Modify `frontend/src/app/layout.tsx` — Add "Jobs" nav link

### Phase B: Deep Research (builds on job persistence)

14. `backend/config/models.py` — Model configuration per sub-task
15. `backend/services/deep_research.py` — Multi-step orchestrator
16. Add deep research prompts to `prompt_manager.py`
17. `POST /api/jobs/{id}/research/deep` SSE endpoint
18. `frontend/src/app/components/DeepResearchProgress.tsx` — Progress stepper
19. Modify `frontend/src/app/page.tsx` — Research depth toggle + SSE integration

## New Dependencies

**Backend:** `aiosqlite` (async SQLite — zero-config, no external DB server needed)
**Frontend:** None (EventSource is built-in browser API)

## File Change Summary

| File | Action | Phase |
|------|--------|-------|
| `backend/models/job.py` | **NEW** | A |
| `backend/services/job_store.py` | **NEW** | A |
| `backend/routers/jobs.py` | **NEW** | A |
| `backend/routers/research.py` | **EDIT** | A |
| `backend/routers/generate.py` | **EDIT** | A |
| `backend/main.py` | **EDIT** | A |
| `backend/config/__init__.py` | **NEW** | B |
| `backend/config/models.py` | **NEW** | B |
| `backend/services/deep_research.py` | **NEW** | B |
| `backend/services/prompt_manager.py` | **EDIT** | B |
| `frontend/src/lib/types.ts` | **EDIT** | A |
| `frontend/src/lib/api.ts` | **EDIT** | A+B |
| `frontend/src/app/jobs/page.tsx` | **NEW** | A |
| `frontend/src/app/editor/[id]/page.tsx` | **NEW** | A |
| `frontend/src/app/editor/page.tsx` | **DELETE** | A |
| `frontend/src/app/components/JobCard.tsx` | **NEW** | A |
| `frontend/src/app/components/DeepResearchProgress.tsx` | **NEW** | B |
| `frontend/src/app/page.tsx` | **EDIT** | A+B |
| `frontend/src/app/layout.tsx` | **EDIT** | A |
| `backend/requirements.txt` | **EDIT** | A |
| `.gitignore` | **EDIT** | A |

## Non-Goals

- No multi-user auth / user accounts — single-user tool
- No cloud file storage — local disk is fine
- No real-time collaboration
- No job queuing system (Celery etc.) — async within FastAPI is sufficient
- Keep existing standard research mode working (deep is opt-in)
