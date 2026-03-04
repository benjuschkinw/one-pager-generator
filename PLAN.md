# Plan: Persistent Jobs + Deep Research

## Overview

Two interconnected features:
1. **Persistent Job Storage** — Every research run becomes a "job" with uploaded docs, AI research, extracted data, PPTX output, and deep research results all saved and browsable
2. **Deep Research** — Multi-step AI pipeline with per-step model selection via OpenRouter, strict anti-hallucination, 2nd AI recheck per step, all prompts editable, nice results frontend, PPTX generation from deep research

---

## Part 1: Persistent Job Storage

### Problem

Currently all data lives in browser `sessionStorage` — it's lost on refresh, can't be shared, and there's no history. Users can't go back to previous research runs to compare results or re-download artifacts.

### Data Model

**New file: `backend/models/job.py`**

```python
class Job(BaseModel):
    id: str                    # UUID
    company_name: str
    created_at: datetime
    updated_at: datetime
    status: Literal["pending", "researching", "completed", "failed"]

    # Inputs
    im_filename: str | None    # Original uploaded filename
    im_file_path: str | None   # Path to stored PDF on disk
    im_text: str | None        # Extracted text from PDF

    # Research config
    provider: str | None
    model: str | None
    research_mode: Literal["standard", "deep"]

    # Outputs
    research_data: OnePagerData | None        # AI research result (raw)
    verification: VerificationResult | None   # Cross-verification result
    deep_research_steps: list[DeepResearchStep] | None  # Per-step results
    edited_data: OnePagerData | None          # User-edited version
    pptx_file_path: str | None               # Path to generated PPTX

class DeepResearchStep(BaseModel):
    step_name: str             # e.g. "im_extraction", "web_research"
    label: str                 # Human-readable: "IM Extraction"
    model_used: str            # e.g. "anthropic/claude-opus-4"
    status: Literal["pending", "running", "done", "error", "verified"]
    started_at: datetime | None
    completed_at: datetime | None
    result_json: dict | None   # Partial result from this step
    verification: StepVerification | None  # Per-step 2nd AI recheck
    error_message: str | None
    sources: list[str]         # URLs / doc references used

class StepVerification(BaseModel):
    verifier_model: str
    confidence: float          # 0.0 - 1.0
    flags: list[FieldFlag]
    hallucination_risk: Literal["low", "medium", "high"]
```

### Storage

**SQLite + aiosqlite** — lightweight, zero-config, single-user tool:
- `backend/services/job_store.py` — CRUD operations for jobs
- DB file: `data/jobs.db` (gitignored)
- File uploads: `data/uploads/{job_id}/` (original PDFs)
- Generated PPTX: `data/outputs/{job_id}/` (PPTX files)

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
- "Download PPTX" button (if job has previously generated PPTX)
- Generate button calls `POST /api/jobs/{id}/generate`

**Modified: `/` — Input Page**
- After research completes, redirects to `/editor/{job_id}` instead of `/editor`
- Add "Recent Jobs" section below the form showing last 5 jobs

**New component: `JobCard.tsx`**
- Compact card: company name, date, status, action icons (view, download IM, download PPTX, delete)

---

## Part 2: Deep Research (builds on job persistence)

### OpenRouter Model Routing

**Confirmed:** OpenRouter supports explicit model selection per API call. Pass a model ID like `anthropic/claude-opus-4` in the `model` field → that exact model runs. Single API key, different models per call.

**Constraint:** Web search only works via Anthropic's native API (not OpenRouter). Steps needing web search must use the Anthropic client directly.

### Pipeline

| Step | Sub-task | Model | Why | Web search |
|------|----------|-------|-----|------------|
| 1 | **IM Extraction** (if PDF) | `anthropic/claude-opus-4` via OpenRouter | Best at long doc analysis | No |
| 2 | **Web Research** | `claude-opus-4` via Anthropic API | Company basics | Yes |
| 3 | **Financial Deep-Dive** | `claude-opus-4` via Anthropic API | Bundesanzeiger, North Data | Yes |
| 4 | **Management & Org** | `claude-opus-4` via Anthropic API | LinkedIn, Handelsregister | Yes |
| 5 | **Market & Competitive** | `google/gemini-2.5-pro-preview` via OpenRouter | Synthesis, large context | No |
| 6 | **Merge & Synthesize** | `anthropic/claude-opus-4` via OpenRouter | Best structured output | No |
| 7 | **Final Cross-Verify** | `openai/gpt-4.1` via OpenRouter | Cross-model diversity | No |

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
    │  + recheck   │ │ + recheck│ │  + recheck     │ │  + recheck   │
    └──────┬───────┘ └────┬─────┘ └───────┬────────┘ └──────┬───────┘
           └──────────────┼───────────────┘                  │
                          ▼                                  │
                    ┌──────────────┐◄────────────────────────┘
                    │ 6. Merge &   │
                    │   Synthesize │
                    └──────┬───────┘
                           ▼
                    ┌──────────────┐
                    │ 7. Final     │
                    │   Verify     │
                    └──────────────┘
```

Steps 2-5 run in parallel. Each step includes an inline 2nd-AI recheck before proceeding.

### Anti-Hallucination Strategy (3 layers)

Critical for M&A research — fabricated financials or management names are worse than no data.

#### Layer 1: Prompt-Level Guards (per step)

Every sub-task prompt includes:
- "NEVER invent financial figures. If you cannot find data, return null."
- "Prefix inferred values with ~ (e.g., ~120 employees)"
- "For each fact, include the source URL or document reference in a `_sources` field"
- "Default investment criteria to 'questions' unless you have concrete evidence"
- "Return a confidence score (0.0-1.0) for the overall output"

#### Layer 2: Per-Step 2nd AI Recheck

After each of steps 1-5, a **different model** rechecks that step's output:
- Claude research → GPT-4.1 recheck
- Gemini research → Claude Sonnet 4 recheck

The recheck prompt receives the step's output + source material and returns:
- Per-field confidence scores
- Hallucination risk assessment (low/medium/high)
- Specific flags for suspicious claims

Result stored in `DeepResearchStep.verification`.

#### Layer 3: Final Cross-Verification (existing, enhanced)

After merge (step 6), the full verification pipeline runs:
- **Algorithmic checks**: Revenue split sums, EBITDA margin consistency, criteria logic
- **AI cross-verification**: Complete data reviewed by a different model family
- **Inter-step consistency**: Financial data from step 3 vs IM extraction in step 1

### All Prompts Editable (13 total)

| Prompt Name | Used In | Description |
|-------------|---------|-------------|
| `research_system` | Standard | System prompt (web search mode) |
| `research_system_no_search` | Standard | System prompt (no web search) |
| `research_user_with_im` | Standard | User prompt with IM |
| `research_user_no_im` | Standard | User prompt without IM |
| `verification` | Standard | Cross-verification prompt |
| `deep_im_extraction` | Step 1 | Extract structured data from IM |
| `deep_web_research` | Step 2 | Find company basics via web search |
| `deep_financials` | Step 3 | Find/verify financial data |
| `deep_management` | Step 4 | Find management team, ownership |
| `deep_market` | Step 5 | Market sizing, competitive landscape |
| `deep_merge` | Step 6 | Merge sub-task results into OnePagerData |
| `deep_step_recheck` | Steps 1-5 | Per-step 2nd AI recheck |
| `deep_final_verify` | Step 7 | Final cross-verification |

PromptEditor UI groups them: Standard Research / Deep Research / Verification.

### Frontend: Deep Research Results

**New component: `DeepResearchResults.tsx`**

Expandable panel above the editor showing the full research trail:

```
┌─────────────────────────────────────────────────────────┐
│  Deep Research Results          ▾ Expand                │
│  Overall: 87% confidence · 5/5 steps verified           │
│                                                         │
│  ┌─ Step 1: IM Extraction ──── ✓ verified (92%) ──────┐ │
│  │  Model: claude-opus-4 · 12s · 23 fields extracted   │ │
│  │  Recheck: GPT-4.1 — no issues                      │ │
│  │  [Show data]  [Show raw output]                     │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                         │
│  ┌─ Step 3: Financials ──── ⚠ warnings (72%) ────────┐  │
│  │  Model: claude-opus-4 · 35s · 4 web searches       │  │
│  │  Found: Revenue 22A-24A, EBITDA 23A-24A            │  │
│  │  Recheck: GPT-4.1 — EBITDA margin inconsistency    │  │
│  │  Sources: bundesanzeiger.de, northdata.de           │  │
│  │  [Show data]  [Show sources]                        │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                         │
│  📄 Documents: IM_ACCEL.pdf (3.2 MB) [Download]        │
│  📊 Outputs: One_Pager_ACCEL.pptx [Download] [JSON]    │
└─────────────────────────────────────────────────────────┘
```

### PPTX from Deep Research

Deep research produces the same `OnePagerData` (via step 6 merge), so the existing PPTX generator and template work as-is. Same one-pager slide design. No changes to `pptx_generator.py`.

### Model Configuration

**New file: `backend/config/models.py`**

```python
DEEP_RESEARCH_MODELS = {
    "im_extraction":   env("MODEL_IM_EXTRACTION", "anthropic/claude-opus-4"),
    "web_research":    "anthropic",        # Anthropic API for web search
    "financials":      "anthropic",        # Anthropic API for web search
    "management":      "anthropic",        # Anthropic API for web search
    "market":          env("MODEL_MARKET", "google/gemini-2.5-pro-preview"),
    "merge":           env("MODEL_MERGE", "anthropic/claude-opus-4"),
    "verify_final":    env("MODEL_VERIFY", "openai/gpt-4.1"),
}

RECHECK_MODELS = {
    "anthropic":   "openai/gpt-4.1",
    "openrouter":  "openai/gpt-4.1",
    "google":      "anthropic/claude-sonnet-4",
    "openai":      "anthropic/claude-sonnet-4",
}
```

---

## Implementation Order

### Phase A: Job Persistence (foundation)

1. `backend/models/job.py` — Job + DeepResearchStep + StepVerification models
2. `backend/services/job_store.py` — SQLite CRUD with aiosqlite
3. `backend/routers/jobs.py` — REST API for jobs
4. Modify `backend/routers/research.py` — Create job on research, save results
5. Modify `backend/routers/generate.py` — Save PPTX to job
6. `backend/main.py` — Mount jobs router, init DB on startup
7. `frontend/src/lib/types.ts` — Job, DeepResearchStep, StepVerification types
8. `frontend/src/lib/api.ts` — Job API functions
9. `frontend/src/app/editor/[id]/page.tsx` — Job-aware editor
10. `frontend/src/app/jobs/page.tsx` — Job history page
11. `frontend/src/app/components/JobCard.tsx` — Job list item
12. Modify `frontend/src/app/page.tsx` — Recent jobs, redirect to `/editor/{id}`
13. Modify `frontend/src/app/layout.tsx` — Add "Jobs" nav link

### Phase B: Deep Research Pipeline

14. `backend/config/models.py` — Model config per sub-task + recheck
15. `backend/services/deep_research.py` — Orchestrator with per-step recheck
16. Add 8 new prompts to `prompt_manager.py`
17. `POST /api/jobs/{id}/research/deep` SSE endpoint

### Phase C: Deep Research Frontend

18. `frontend/src/app/components/DeepResearchProgress.tsx` — SSE progress stepper
19. `frontend/src/app/components/DeepResearchResults.tsx` — Results panel
20. Modify `frontend/src/app/page.tsx` — Depth toggle + SSE
21. Modify `frontend/src/app/editor/[id]/page.tsx` — Show DeepResearchResults
22. Update `PromptEditor.tsx` — Group prompts into sections

## Dependencies

**Backend:** `aiosqlite`
**Frontend:** None

## Non-Goals

- No multi-user auth — single-user tool
- No cloud storage — local disk
- No job queue (Celery) — async within FastAPI
- Keep standard research mode as-is
- No PPTX template changes — deep research feeds the same one-pager
