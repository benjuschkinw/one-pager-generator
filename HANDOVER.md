# Handover: M&A One-Pager Generator

**Branch:** `claude/review-progress-5vIvn`
**Date:** 2026-03-04
**Status:** All phases implemented — Persistent Jobs + Deep Research with SSE streaming.

---

## Current State Summary

The app is a fully functional M&A One-Pager generator with persistent job storage and multi-step deep research.

**What works:**
- Single-shot AI research (Claude Opus 4 with web search, or any model via OpenRouter)
- Deep research: 7-step AI pipeline with parallel execution, per-step recheck, SSE streaming
- PDF IM extraction with 8-module structured prompts
- Cross-model verification (algorithmic + GPT-4.1) — both standard and deep research
- 3-layer anti-hallucination: prompt guards + per-step 2nd AI recheck + final cross-verification
- Persistent job storage (SQLite + filesystem) — jobs survive browser refresh
- Job history page with status tracking
- 3-column inline editor matching slide layout with auto-save
- PPTX generation from template
- 13 editable AI prompts with admin key auth, grouped by category
- Real-time deep research progress stepper via SSE

---

## Completed Work

### Phase A: Persistent Job Storage

Every research run is a persistent "job" stored in SQLite with:
- Uploaded IM PDF on disk (`data/uploads/{job_id}/original.pdf`)
- AI research results (OnePagerData + verification) in SQLite JSON columns
- User edits auto-saved (debounced 500ms) to `edited_data` column
- Generated PPTX on disk (`data/outputs/{job_id}/one_pager.pptx`) and downloadable

**Pages:** `/jobs` (history list), `/editor/[id]` (job-aware editor)
**Backend:** SQLite via aiosqlite, `/api/jobs` REST API, file storage in `data/`

### Phase B: Deep Research Pipeline

Multi-step AI pipeline with explicit model selection per sub-task:

| Step | Task | Model | Provider |
|------|------|-------|----------|
| 1 | IM Extraction | Claude Opus 4 | OpenRouter |
| 2 | Web Research | Claude Opus 4 | Anthropic (web search) |
| 3 | Financial Deep-Dive | Claude Opus 4 | Anthropic (web search) |
| 4 | Management & Org | Claude Opus 4 | Anthropic (web search) |
| 5 | Market & Competitive | Gemini 2.5 Pro | OpenRouter |
| 6 | Merge & Synthesize | Claude Opus 4 | OpenRouter |
| 7 | Cross-Verify | GPT-4.1 | OpenRouter |

- Steps 2-5 run in parallel via `asyncio.gather()`
- Each step has per-step 2nd AI recheck by a different model family
- Progress streamed via SSE (`POST /api/jobs/{id}/research/deep`)
- All results saved to job's `deep_research_steps` column

### Phase C: Deep Research Frontend

- `DeepResearchProgress.tsx` — SSE-connected vertical stepper with progress bar
- `DeepResearchResults.tsx` — Collapsible per-step results with verification details
- Research depth toggle (Standard/Deep) on input page
- Editor auto-starts deep research from `?deep=true` URL param
- "Run Deep Research" button in editor toolbar
- `PromptEditor.tsx` grouped into Standard / Deep Research / Other sections

### Security Fixes (Gemini Code Review)

| # | Severity | Issue | Fix |
|---|----------|-------|-----|
| 1 | **Critical** | `/api/prompts` mutation endpoints publicly accessible | Added `X-Admin-Key` header auth via `ADMIN_API_KEY` env var |
| 2 | **Critical** | Prompt injection via editable templates + untrusted input | Added `_sanitize_company_name()` + injection guardrail in system prompt |
| 3 | **Medium** | HTTP header injection via redundant `.replace()` in filename | Removed redundant call |
| 4 | **Low** | Unused `copy` import in `prompt_manager.py` | Removed |

---

## Full Architecture Reference

### System Overview

```
┌──────────────────────────────────────────────────────────────────┐
│  FRONTEND (Next.js 14+ / TypeScript / Tailwind CSS)               │
│  Port: 3001                                                        │
│                                                                     │
│  / (Input Page)         /editor/[id] (Job Editor)                   │
│  ┌─────────────────┐   ┌──────────────────────────────────┐       │
│  │ Company Name     │   │ DeepResearchProgress (SSE)       │       │
│  │ PDF Upload       │   │ DeepResearchResults (collapsible)│       │
│  │ Mode: Std/Deep   │   │ VerificationBanner               │       │
│  │ PromptEditor     │──→│ HeaderSection + KeyFacts          │       │
│  │ Recent Jobs      │   │ BulletEditor (desc + portfolio)  │       │
│  └─────────────────┘   │ RationaleSection + Revenue       │       │
│                          │ FinancialsTable + Criteria       │       │
│  /jobs (Job History)     │ Generate PPTX (sticky bottom)   │       │
│  ┌─────────────────┐   └──────────────────────────────────┘       │
│  │ JobCard list      │                                              │
│  │ Status badges     │                                              │
│  └─────────────────┘                                                │
└──────────────────────────────────────────────────────────────────┘
                              │ HTTP
┌──────────────────────────────────────────────────────────────────┐
│  BACKEND (FastAPI / Python)                                        │
│  Port: 8000                                                        │
│                                                                     │
│  Routers:                                                           │
│  ├── POST /api/research     → ai_research.py + verification.py    │
│  ├── POST /api/generate     → pptx_generator.py                   │
│  ├── GET  /api/jobs         → job_store.py (list)                  │
│  ├── GET  /api/jobs/{id}    → job_store.py (detail)                │
│  ├── DEL  /api/jobs/{id}    → job_store.py (delete)                │
│  ├── PUT  /api/jobs/{id}/data     → job_store.py (save edits)     │
│  ├── POST /api/jobs/{id}/generate → pptx_generator.py (from job)  │
│  ├── GET  /api/jobs/{id}/im       → file download (PDF)           │
│  ├── GET  /api/jobs/{id}/pptx     → file download (PPTX)          │
│  ├── POST /api/jobs/{id}/research/deep → SSE deep research        │
│  ├── GET  /api/prompts      → prompt_manager.py (read-only)       │
│  ├── PUT  /api/prompts/*    → prompt_manager.py (auth required)   │
│  ├── GET  /api/providers    → ai_research.py                      │
│  └── GET  /api/health                                               │
│                                                                     │
│  Services:                                                          │
│  ├── ai_research.py      → Claude/OpenRouter multi-turn loop      │
│  ├── deep_research.py    → 7-step pipeline, parallel, SSE events  │
│  ├── job_store.py        → SQLite CRUD via aiosqlite              │
│  ├── pdf_extractor.py    → pypdfium2 + pdfplumber fallback        │
│  ├── verification.py     → Algorithmic + AI cross-check           │
│  ├── pptx_generator.py   → python-pptx template population        │
│  ├── chart_generator.py  → matplotlib donut + bar charts          │
│  └── prompt_manager.py   → In-memory prompt store (13 prompts)    │
│                                                                     │
│  Config:                                                            │
│  └── config/models.py    → Per-step model selection + recheck map  │
│                                                                     │
│  External APIs:                                                     │
│  ├── Anthropic (Claude Opus 4) — research with web search         │
│  ├── OpenRouter (GPT-4.1)      — cross-verification               │
│  ├── OpenRouter (Gemini 2.5 Pro) — market analysis (deep)         │
│  └── OpenRouter (any model)    — fallback / per-step selection     │
│                                                                     │
│  Storage:                                                           │
│  ├── data/jobs.db        → SQLite database                         │
│  ├── data/uploads/{id}/  → Uploaded IM PDFs                        │
│  └── data/outputs/{id}/  → Generated PPTX files                   │
└──────────────────────────────────────────────────────────────────┘
```

### Data Flow

**Standard Research:**
```
User → Input Page → POST /api/research → AI research → Verification
    → SQLite job + /editor/{id} → Edit inline → POST /api/jobs/{id}/generate → PPTX
```

**Deep Research:**
```
User → Input Page (Deep mode) → POST /api/research → Standard research
    → /editor/{id}?deep=true → POST /api/jobs/{id}/research/deep (SSE)
    → 7 steps (parallel 2-5) → Per-step recheck → Merge → Cross-verify
    → Updated job data → Editor with DeepResearchResults
```

### Anti-Hallucination (3 layers)

1. **Prompt-level guards** — Every step prompt enforces "never invent data, return null if unknown, prefix inferences with ~, cite sources"
2. **Per-step 2nd AI recheck** — Each step's output rechecked by a different model family (Claude→GPT, Gemini→Claude, GPT→Claude)
3. **Final cross-verification** — Algorithmic checks + AI cross-verification on the merged result, including inter-step consistency checks

### 13 Editable Prompts

| Category | Prompt | Description |
|----------|--------|-------------|
| Standard | `research_system` | System prompt for Anthropic research (with web search) |
| Standard | `research_system_no_search` | System prompt for OpenRouter research (no web search) |
| Standard | `research_user_with_im` | User prompt when IM PDF is provided |
| Standard | `research_user_no_im` | User prompt for public research only |
| Standard | `verification` | Cross-verification system prompt |
| Deep | `deep_im_extraction` | IM document extraction sub-step |
| Deep | `deep_web_research` | Company basics via web search |
| Deep | `deep_financials` | Financial deep-dive (Bundesanzeiger, etc.) |
| Deep | `deep_management` | Management team research |
| Deep | `deep_market` | Market & competitive analysis |
| Deep | `deep_merge` | Merge sub-task results into final OnePagerData |
| Deep | `deep_step_recheck` | Per-step 2nd AI verification |
| Deep | `deep_final_verify` | Enhanced final cross-verification |

### Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `ANTHROPIC_API_KEY` | One of these required | Claude API for research + web search |
| `OPENROUTER_API_KEY` | | OpenRouter for verification + deep research models |
| `ADMIN_API_KEY` | Optional | Enables prompt editing via API |
| `MODEL_IM_EXTRACTION` | Optional | Override model for IM extraction step |
| `MODEL_MARKET` | Optional | Override model for market analysis step |
| `MODEL_MERGE` | Optional | Override model for merge step |
| `MODEL_VERIFY` | Optional | Override model for final verification step |

### Key Files

| File | Purpose |
|------|---------|
| `backend/main.py` | FastAPI app, CORS, router mounts, DB init |
| `backend/config/models.py` | Per-step model config + recheck model mapping |
| `backend/models/job.py` | Job, JobSummary, DeepResearchStep, StepVerification |
| `backend/models/one_pager.py` | OnePagerData + VerificationResult + ResearchResponse |
| `backend/routers/research.py` | POST /api/research — creates job + AI research |
| `backend/routers/jobs.py` | Jobs REST API + SSE deep research endpoint |
| `backend/routers/generate.py` | POST /api/generate — standalone PPTX generation |
| `backend/routers/prompts.py` | Prompt CRUD with admin auth |
| `backend/services/ai_research.py` | Claude/OpenRouter multi-turn research |
| `backend/services/deep_research.py` | 7-step deep research pipeline with SSE |
| `backend/services/job_store.py` | SQLite CRUD via aiosqlite |
| `backend/services/verification.py` | Algorithmic + AI cross-verification |
| `backend/services/prompt_manager.py` | In-memory prompt store (13 prompts) |
| `backend/services/pdf_extractor.py` | PDF text extraction |
| `backend/services/pptx_generator.py` | PPTX template population |
| `backend/services/chart_generator.py` | Matplotlib donut + bar charts |
| `frontend/src/app/page.tsx` | Input page with Standard/Deep toggle |
| `frontend/src/app/jobs/page.tsx` | Job history page |
| `frontend/src/app/editor/[id]/page.tsx` | Job-aware editor with deep research |
| `frontend/src/app/editor/page.tsx` | Legacy redirect to /jobs |
| `frontend/src/app/components/DeepResearchProgress.tsx` | SSE progress stepper |
| `frontend/src/app/components/DeepResearchResults.tsx` | Collapsible step results |
| `frontend/src/app/components/PromptEditor.tsx` | Grouped prompt editor |
| `frontend/src/app/components/JobCard.tsx` | Compact card for job list |
| `frontend/src/lib/api.ts` | API client (research, jobs, SSE, prompts) |
| `frontend/src/lib/types.ts` | TypeScript types matching backend models |
