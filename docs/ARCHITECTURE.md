# System Architecture

**Last updated:** 2026-03-05

---

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     NEXT.JS FRONTEND                        │
│                    (Port 3001, TypeScript)                   │
│                                                              │
│  3 Modes:                                                   │
│  ├─ Company One-Pager (standard + deep research)            │
│  ├─ Market Study (8-step research pipeline)                 │
│  └─ Company Sourcing (find similar companies, planned)      │
│                                                              │
│  Pages:                                                     │
│  ├─ / (Input: Company | Market toggle)                      │
│  ├─ /editor/[id] (Company one-pager editor)                 │
│  ├─ /market-editor/[id] (10-section market study editor)    │
│  ├─ /jobs (Job history)                                     │
│  └─ /editor/[id]/sourcing (Company sourcing, planned)       │
└──────────────────┬──────────────────────────────────────────┘
                   │ HTTP + SSE
┌──────────────────▼──────────────────────────────────────────┐
│                    FASTAPI BACKEND                           │
│                   (Port 8000, Python)                        │
│                                                              │
│  5 Routers:                                                 │
│  ├─ research.py     → Standard company research             │
│  ├─ jobs.py         → Job CRUD, PPTX, deep research SSE    │
│  ├─ market_research → Market research SSE pipeline          │
│  ├─ generate.py     → Standalone PPTX generation            │
│  └─ prompts.py      → Prompt CRUD with admin auth           │
│                                                              │
│  8 Core Services:                                           │
│  ├─ ai_research.py           → Claude/OpenRouter research   │
│  ├─ deep_research.py         → 7-step parallel pipeline     │
│  ├─ market_research.py       → 8-step parallel pipeline     │
│  ├─ job_store.py             → SQLite persistence           │
│  ├─ verification.py          → Algorithmic + AI checks      │
│  ├─ prompt_manager.py        → 22 editable prompts          │
│  ├─ pptx_generator.py        → One-pager PPTX              │
│  └─ market_pptx_generator.py → 10-slide market PPTX        │
│                                                              │
│  External AI APIs:                                          │
│  ├─ Anthropic (Claude Opus 4) — with web search             │
│  ├─ OpenRouter (Gemini 2.5 Pro, GPT-4.1, Claude)           │
│  └─ OpenAI (via OpenRouter) — cross-verification            │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                    PERSISTENCE LAYER                        │
│  SQLite: data/jobs.db                                       │
│  Filesystem: data/uploads/ & data/outputs/                  │
└──────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### Standard Company Research
```
Input → POST /api/research → AI research → Verification → SQLite
→ /editor/{id} → Edit inline → POST /api/jobs/{id}/generate → PPTX
```

### Deep Company Research (7 steps)
```
/editor/{id}?deep=true → POST /api/jobs/{id}/research/deep (SSE)
→ Step 1: IM Extraction → Steps 2-5: Parallel web research
→ Step 6: Merge → Step 7: Cross-verify → Updated job data
```

### Market Research (8 steps)
```
Input → Scoping form → POST /api/market-research (SSE)
→ Steps 1-3: Parallel (sizing, segmentation, competition)
→ Steps 4-6: Parallel (trends, porters, buy&build)
→ Step 7: Merge → Step 8: Verify → /market-editor/{id}
```

### Company Sourcing (4 steps, planned)
```
/editor/{id} → "Find Similar Companies" → POST /api/jobs/{id}/source-companies (SSE)
→ Step 1: Extract Company DNA → Step 2: Search DACH (3 parallel)
→ Step 3: Verify & Enrich → Step 4: Rank & Synthesize
→ /editor/{id}/sourcing
```

---

## Multi-Model Strategy

| Step | Model | Provider | Capability |
|------|-------|----------|------------|
| Web research (company) | Claude Opus 4 | Anthropic | Web search |
| Financial deep-dive | Claude Opus 4 | Anthropic | Web search |
| Management research | Claude Opus 4 | Anthropic | Web search |
| Market analysis | Gemini 2.5 Pro | OpenRouter | Broad knowledge |
| IM extraction | Claude Opus 4 | OpenRouter | Document parsing |
| Merge & synthesize | Claude Opus 4 | OpenRouter | Structured output |
| Cross-verification | GPT-4.1 | OpenRouter | Independent check |
| Per-step recheck | Opposite family | Mixed | Cross-model validation |

**Recheck model mapping:**
- Claude steps → rechecked by GPT-4.1
- Gemini steps → rechecked by Claude Sonnet
- GPT steps → rechecked by Claude Sonnet

---

## Anti-Hallucination (3 Layers)

1. **Prompt Guards** — Every step includes: "Never invent data, return null if unknown, prefix inferences with ~, cite sources"
2. **Per-Step 2nd AI Recheck** — Each step's output rechecked by a different model family
3. **Final Cross-Verification** — Algorithmic checks (revenue sums, margin consistency) + AI cross-verification on merged result

---

## Input Validation & Security

| Layer | Mechanism |
|-------|-----------|
| Market name | `_sanitize_market_name()` — strips markdown, newlines, collapses whitespace, max 200 chars |
| Company name | `_sanitize_company_name()` — strips control chars, max 200 chars |
| Region | Allowlist: `{DACH, Germany, Europe, Global}` |
| Scoping context | Key whitelist (8 fields), max 500 chars/field, markdown filter, max 10KB total |
| PDF upload | `.pdf` extension check, 20MB size limit |
| Prompt editing | `X-Admin-Key` header auth via `ADMIN_API_KEY` env var |
| Error messages | Generic client-facing messages; full details logged server-side |

---

## Database Schema

```sql
CREATE TABLE jobs (
    id TEXT PRIMARY KEY,
    company_name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    status TEXT DEFAULT 'pending',     -- pending | researching | completed | failed
    research_mode TEXT DEFAULT 'standard', -- standard | deep | market
    im_filename TEXT,
    im_file_path TEXT,
    im_text TEXT,
    provider TEXT,
    model TEXT,
    research_data TEXT,         -- OnePagerData JSON
    verification TEXT,          -- VerificationResult JSON
    deep_research_steps TEXT,   -- DeepResearchStep[] JSON
    edited_data TEXT,           -- User-edited OnePagerData JSON
    pptx_file_path TEXT,
    market_study_data TEXT,     -- MarketStudyData JSON
    edited_market_data TEXT     -- User-edited MarketStudyData JSON
);
```

---

## Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `ANTHROPIC_API_KEY` | Yes (one of) | Claude API for research + web search |
| `OPENROUTER_API_KEY` | Yes (one of) | OpenRouter for verification + multi-model |
| `ADMIN_API_KEY` | Optional | Enables prompt editing via API |
| `MODEL_*` | Optional | Per-step model overrides |

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `backend/main.py` | FastAPI app, CORS, router mounts, DB init |
| `backend/config/models.py` | Per-step model config + recheck mapping |
| `backend/models/job.py` | Job, DeepResearchStep, StepVerification |
| `backend/models/one_pager.py` | OnePagerData, VerificationResult |
| `backend/models/market_study.py` | MarketStudyData (10-section schema) |
| `backend/services/market_research.py` | 8-step market research pipeline |
| `backend/services/deep_research.py` | 7-step deep research pipeline |
| `backend/services/prompt_manager.py` | 22 editable prompt templates |
| `frontend/src/lib/api.ts` | API client (research, jobs, SSE, prompts) |
| `frontend/src/lib/types.ts` | TypeScript types matching backend models |
