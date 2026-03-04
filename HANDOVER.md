# Handover: M&A One-Pager Generator

**Branch:** `claude/review-progress-5vIvn`
**Date:** 2026-03-04
**Status:** Implementing Persistent Jobs + Deep Research (see PLAN.md for full spec).

---

## Current State Summary

The app is a working M&A One-Pager generator: user enters a company name + optional IM PDF, AI researches the company, user edits the result in a structured editor, and downloads a branded PPTX slide.

**What works:**
- Single-shot AI research (Claude Opus 4 with web search, or any model via OpenRouter)
- PDF IM extraction with 8-module structured prompts
- Cross-model verification (algorithmic + GPT-4.1)
- 3-column inline editor matching slide layout
- PPTX generation from template
- Editable AI prompts with admin key auth

**What's missing (next features):**
- No persistent storage — everything in browser sessionStorage, lost on refresh
- No job history — can't go back to previous research runs
- No deep research — single monolithic AI call, no per-topic specialization
- No progress streaming — 30-60 second spinner with no feedback

---

## Completed Work

### Initial Features (merged to main via PR #1)

1. **Structured IM Extraction** — 8 extraction modules mapping IM chapters to One-Pager fields
2. **Editable Prompts** — 5 prompts editable at runtime via `/api/prompts` + collapsible UI editor
3. **Optimal Model Selection** — Claude Opus 4 for research, GPT-4.1 for cross-verification
4. **Professional Frontend** — Inter font, CC brand colors, drag-and-drop PDF upload, clean editor
5. **Security Hardening** — Sanitized errors, safe prompt formatting, Content-Disposition escaping

### Security Fixes (Gemini Code Review)

| # | Severity | Issue | Fix |
|---|----------|-------|-----|
| 1 | **Critical** | `/api/prompts` mutation endpoints publicly accessible | Added `X-Admin-Key` header auth via `ADMIN_API_KEY` env var. If unset, mutations disabled entirely. |
| 2 | **Critical** | Prompt injection via editable templates + untrusted input | Added `_sanitize_company_name()` + injection guardrail in system prompt. |
| 3 | **Medium** | HTTP header injection via redundant `.replace()` in filename | Removed redundant call; `_sanitize_filename()` already handles it. |
| 4 | **Low** | Unused `copy` import in `prompt_manager.py` | Removed. |

---

## Full Architecture Reference

### System Overview

```
┌──────────────────────────────────────────────────────────────┐
│  FRONTEND (Next.js 14+ / TypeScript / Tailwind CSS)          │
│  Port: 3001                                                   │
│                                                                │
│  / (Input Page)         /editor (Editor Page)                  │
│  ┌─────────────────┐   ┌──────────────────────────────────┐   │
│  │ Company Name     │   │ VerificationBanner               │   │
│  │ PDF Upload       │   │ HeaderSection                    │   │
│  │ PromptEditor     │──→│ KeyFactsSection                  │   │
│  │ "Research" btn   │   │ BulletEditor (desc + portfolio)  │   │
│  └─────────────────┘   │ RationaleSection (pros/cons)     │   │
│                         │ RevenueTable                     │   │
│                         │ FinancialsTable                  │   │
│                         │ CriteriaSection (12 toggles)     │   │
│                         │ GenerateButton → PPTX download   │   │
│                         └──────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
                              │ HTTP
┌──────────────────────────────────────────────────────────────┐
│  BACKEND (FastAPI / Python)                                    │
│  Port: 8000                                                    │
│                                                                │
│  Routers:                                                      │
│  ├── POST /api/research  → ai_research.py + verification.py   │
│  ├── POST /api/generate  → pptx_generator.py                  │
│  ├── GET  /api/prompts   → prompt_manager.py (read-only)      │
│  ├── PUT  /api/prompts/* → prompt_manager.py (auth required)  │
│  ├── GET  /api/providers → ai_research.py                     │
│  └── GET  /api/health                                          │
│                                                                │
│  Services:                                                     │
│  ├── ai_research.py     → Claude/OpenRouter multi-turn loop   │
│  ├── pdf_extractor.py   → pypdfium2 + pdfplumber fallback     │
│  ├── verification.py    → Algorithmic + AI cross-check        │
│  ├── pptx_generator.py  → python-pptx template population     │
│  ├── chart_generator.py → matplotlib donut + bar charts       │
│  └── prompt_manager.py  → In-memory prompt store              │
│                                                                │
│  External APIs:                                                │
│  ├── Anthropic (Claude Opus 4) — research with web search     │
│  ├── OpenRouter (GPT-4.1)      — cross-verification           │
│  └── OpenRouter (any model)    — fallback research provider    │
└──────────────────────────────────────────────────────────────┘
```

### Data Flow (current — sessionStorage-based)

```
User → Input Page → POST /api/research → AI research → Verification
    → sessionStorage → /editor → Edit inline → POST /api/generate → PPTX download
```

### Data Model (`OnePagerData`)

Root fields: `meta`, `header`, `investment_thesis`, `key_facts`, `description[]`, `product_portfolio[]`, `investment_rationale`, `revenue_split`, `financials`, `investment_criteria` (12 criteria with fulfilled/questions/not_interest).

### Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `ANTHROPIC_API_KEY` | One of these required | Claude API for research + web search |
| `OPENROUTER_API_KEY` | | OpenRouter for verification + fallback research |
| `ADMIN_API_KEY` | Optional | Enables prompt editing via API |

### Key Files

| File | Purpose |
|------|---------|
| `backend/main.py` | FastAPI app, CORS, router mounts |
| `backend/routers/research.py` | POST /api/research — PDF upload + AI research |
| `backend/routers/generate.py` | POST /api/generate — PPTX generation |
| `backend/routers/prompts.py` | Prompt CRUD with admin auth |
| `backend/services/ai_research.py` | Claude/OpenRouter multi-turn research |
| `backend/services/verification.py` | Algorithmic + AI cross-verification |
| `backend/services/prompt_manager.py` | In-memory prompt store with 5 editable prompts |
| `backend/services/pdf_extractor.py` | PDF text extraction |
| `backend/services/pptx_generator.py` | PPTX template population |
| `backend/services/chart_generator.py` | Matplotlib donut + bar charts |
| `backend/models/one_pager.py` | Pydantic models for all data types |
| `frontend/src/app/page.tsx` | Input page (company name + PDF upload) |
| `frontend/src/app/editor/page.tsx` | 3-column editor with all sections |
| `frontend/src/lib/api.ts` | API client functions |
| `frontend/src/lib/types.ts` | TypeScript types matching backend models |

---

## Next Up: Persistent Jobs + Deep Research

Full plan in `PLAN.md`. Summary:

### Phase A: Persistent Job Storage

Every research run becomes a persistent "job" with:
- Uploaded IM PDF stored on disk
- AI research results (OnePagerData + verification) in SQLite
- User edits auto-saved to the job
- Generated PPTX stored on disk and downloadable from job

**New pages:** `/jobs` (history list), `/editor/[id]` (job-aware editor)
**New backend:** SQLite via aiosqlite, `/api/jobs` REST API, file storage in `data/`
**Key change:** Replace sessionStorage with server-side job persistence

### Phase B: Deep Research (builds on jobs)

Multi-step AI pipeline with explicit model selection per sub-task:

| Step | Task | Model |
|------|------|-------|
| 1 | IM Extraction | Claude Opus 4 via OpenRouter |
| 2-4 | Web/Financial/Management research | Claude Opus 4 via Anthropic (web search) |
| 5 | Market & Competitive | Gemini 2.5 Pro via OpenRouter |
| 6 | Merge & Synthesize | Claude Opus 4 via OpenRouter |
| 7 | Cross-Verify | GPT-4.1 via OpenRouter |

Steps 2-5 run in parallel. Progress streamed via SSE. Each step result saved to job record.

**OpenRouter:** Confirmed — explicit model selection per API call works. Pass model ID in `model` field, that exact model runs. Single API key, different models per call.

### Anti-Hallucination (3 layers)

1. **Prompt-level guards** — Every step prompt enforces "never invent data, return null if unknown, prefix inferences with ~, cite sources"
2. **Per-step 2nd AI recheck** — Each step's output rechecked by a different model family (Claude→GPT, Gemini→Claude) before proceeding
3. **Final cross-verification** — Algorithmic checks + AI cross-verification on the merged result, including inter-step consistency checks

### All Prompts Editable (13 total)

5 existing (standard research) + 8 new (deep research sub-tasks + recheck + final verify). All visible and editable via the PromptEditor UI, grouped into Standard / Deep / Verification sections.

### Deep Research Results Frontend

New `DeepResearchResults.tsx` component shows:
- Per-step details: model used, duration, fields found, sources, recheck result
- Expandable raw output per step
- Document downloads (uploaded IM, generated PPTX, JSON export)
- Overall confidence score and verification status

### Phase C: Frontend

- Deep research progress stepper (SSE-connected, real-time)
- Deep research results panel above editor
- Research depth toggle (Standard vs Deep) on input page
- PromptEditor grouped by category
