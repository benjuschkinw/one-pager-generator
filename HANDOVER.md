# Handover: M&A One-Pager Generator

**Branch:** `claude/review-progress-5vIvn`
**Date:** 2026-03-06
**Status:** Fully functional — Market Study PPTX closely matches human C VII quality with remaining visual polish gaps documented below.

---

## Current State Summary

The app is an M&A research platform with three core features:

1. **Company One-Pager** — AI-powered research → editable 3-column layout → PPTX export
2. **Market Research** — 8-step AI pipeline → 10-section market study editor → PPTX export
3. **Company Sourcing** — 4-step pipeline to find similar DACH companies from a completed one-pager

### What works end-to-end:

- **Company One-Pager:** Single-shot or 7-step deep research (Claude Opus 4, Gemini 2.5 Pro, GPT-4.1), 3-layer anti-hallucination, PDF IM extraction, inline editor, PPTX generation
- **Market Research:** 8-step pipeline (market sizing, segmentation, competition, trends/PESTEL, sourcing/multiples/Porter's, buy & build, merge, verify) with scoping questionnaire, per-step 2nd AI recheck, 10-section editor, PPTX export (4 core slides + up to 3 optional). See "Market PPTX Quality Status" below for detailed comparison vs human C VII templates.
- **Company Sourcing:** 4-step pipeline (extract DNA → search DACH → verify & enrich → rank & synthesize) with SSE streaming, triggered from one-pager editor
- **Shared Infrastructure:** Persistent SQLite jobs, SSE real-time progress, admin-protected prompt editing (30+ prompts), per-step model configuration with runtime overrides via Settings page

### Running the app:

```bash
# Backend
cd backend && pip install -r requirements.txt
ANTHROPIC_API_KEY=... OPENROUTER_API_KEY=... uvicorn main:app --host 0.0.0.0 --port 8000

# Frontend
cd frontend && npm install && npm run dev -- -p 3001
```

Environment variables: `ANTHROPIC_API_KEY` (required), `OPENROUTER_API_KEY` (required for deep/market/sourcing), `ADMIN_API_KEY` (optional, for prompt editing).

---

## Market PPTX Quality Status

### Benchmarked against 4 human C VII templates:
- `251013 C VII Pest Control.pptx` (5 slides)
- `250609 C VII Intro Heilmittel_v7.pptx` (5 slides)
- `251216 C VII Intro Dentallabore_v3.pptx` (4 slides)
- `260107 C VII Fourpager Locksmith Services.pptx` (6 slides)

### Current PPTX slide structure:

| Slide | Content | Layout |
|-------|---------|--------|
| S1 (Cover) | Market name, region, date | Cover layout |
| S2 (Market Overview) | TL: Segmentation table, TR: TAM bar chart, BL: Fragmentation bar chart, BR: Key Drivers | Content quadrant |
| S3 (Sourcing & Thesis) | TL: Key Sourcing Dynamics, TR: KPC importance matrix, BL: EBITDA Margin Profile, BR: Investment Thesis (Organic/M&A split) | Content quadrant |
| S4 (Multiples & Leaders) | TL: Transaction Multiples table, TR: Market Leaders with logos, BL: Trading Multiples table, BR: Exit Considerations (Strategic/Financial split) | Content quadrant |
| S5 (optional) | Competitor Deep-Dive — PE-backed competitor profiles with metrics | Content quadrant |
| S6 (optional) | Buy & Build Strategy — geographic rollout phases | Content quadrant |
| S7 (optional) | Appendix — PESTEL, Porter's, Value Chain, sources | List layout |

All content slides (S2-S4) include an "Investment Criteria" traffic light row at the bottom.

### What matches human templates:

- **Slide structure:** 4 core slides + optional extras (humans use 4-6)
- **S2 TAM chart:** COLUMN_CLUSTERED bar chart with year labels and CAGR annotation
- **S2 Fragmentation:** BAR_CLUSTERED chart showing company size distribution bands
- **S3 KPC matrix:** Key Purchase Criteria with High↔Low importance bars (matches Heilmittel/Pest Control format)
- **S3 Investment Thesis:** Split into Organic Growth / M&A Consolidation sections
- **S4 Transaction Multiples:** Table with Target, Acquirer, Year, EV/EBITDA, Deal Size
- **S4 Trading Multiples:** Table with Company, EV/EBITDA, EV/Revenue, Market Cap
- **S4 Market Leaders:** Table with company logos (via Google Favicon API)
- **S4 Exit Considerations:** Split into Strategic Buyers / Financial Buyers
- **Traffic light criteria row:** Present on all 3 content slides with met/limitations/not met legend
- **Optional slides:** Competitor deep-dive and buy-and-build strategy slides

### Remaining gaps vs human templates:

| Gap | Human Format | Current AI Format | Priority |
|-----|-------------|-------------------|----------|
| EBITDA margins visual | BAR_STACKED chart | Text table | Medium |
| Segmentation visual | Tree/matrix diagram with grouped textboxes | Simple table | Medium |
| Logo density | 19-56 logos on S4 | 3-5 logos (limited by AI research) | Low |
| Drivers format | Table with Trend/Relevance/Rationale/Impact columns | Bullet lists | Low |
| Source citations | Numbered inline citations in sources row | Generic source text | Low |
| Country flags | Small flag icons next to company HQ | Text only | Low |

### Data model fields added for C VII matching:

All in `backend/models/market_study.py`:
- `EbitdaMarginBenchmark` — company/segment EBITDA margin benchmarks
- `TransactionMultiple` — PE deal transaction multiples
- `TradingMultiple` — public company trading multiples
- `KeyPurchaseCriterion` — KPC name, importance (high/medium/low), description
- `CompanySizeBand` — company count by size band for fragmentation chart
- `CompetitorDeepDive` — detailed PE-backed competitor profiles
- `BuyAndBuildPhase` — geographic rollout strategy phases
- `CompetitorProfile` extended with: `website`, `ebitda`, `employees`, `locations`
- `CompetitiveLandscape` extended with: `company_size_distribution`
- `MarketStudyData` extended with: `ebitda_benchmarks`, `transaction_multiples`, `trading_multiples`, `sourcing_dynamics`, `coverage_notes`, `key_purchase_criteria`, `competitor_deep_dives`, `buy_and_build_phases`

### Pipeline changes for C VII matching:

- Step 5 renamed from "Porter's & Value Chain" to "Sourcing, Multiples & Porter's"
- Prompt now asks for: EBITDA benchmarks, transaction multiples, trading multiples, sourcing dynamics, KPC criteria, competitor deep-dives, buy-and-build phases
- Porter's/PESTEL data still collected but moved to appendix slide

---

## Full Architecture

### Pages & Routes

| Page | URL | Purpose |
|------|-----|---------|
| Input | `/` | Company or Market toggle, PDF upload, Standard/Deep mode, scoping questionnaire (market) |
| Job History | `/jobs` | All jobs with status badges, grouped by type |
| Company Editor | `/editor/[id]` | 3-column one-pager editor, deep research trigger, PPTX generation |
| Market Editor | `/market-editor/[id]` | 10-section market study editor, PPTX export, JSON export |
| Company Sourcing | `/editor/[id]/sourcing` | Find similar companies, triggered from one-pager editor |
| Settings | `/settings` | View/override AI models per pipeline step |

### Backend API Endpoints

```
Routers:
├── POST /api/research              → ai_research.py (standard one-pager)
├── POST /api/generate              → pptx_generator.py (standalone)
│
├── GET  /api/jobs                  → job_store.py (list all)
├── GET  /api/jobs/{id}             → job_store.py (detail)
├── DEL  /api/jobs/{id}             → job_store.py (delete)
├── PUT  /api/jobs/{id}/data        → job_store.py (save edits)
├── POST /api/jobs/{id}/generate    → pptx_generator.py (from job)
├── GET  /api/jobs/{id}/im          → file download (PDF)
├── GET  /api/jobs/{id}/pptx        → file download (PPTX)
├── POST /api/jobs/{id}/research/deep    → SSE deep research (7 steps)
├── POST /api/jobs/{id}/sourcing         → SSE company sourcing (4 steps)
│
├── POST /api/market-research       → market_research.py (8-step SSE)
├── PUT  /api/jobs/{id}/market-data → save edited market data
├── POST /api/jobs/{id}/market-pptx → market PPTX generation
│
├── GET  /api/prompts               → prompt_manager.py (read-only)
├── PUT  /api/prompts/*             → prompt_manager.py (admin auth)
│
├── GET  /api/models/deep-research     → per-step model config
├── GET  /api/models/market-research   → per-step model config
├── PUT  /api/models/deep-research/{step}   → override model
├── PUT  /api/models/market-research/{step} → override model
├── POST /api/models/reset              → reset all to defaults
│
├── GET  /api/providers             → available AI providers
└── GET  /api/health
```

### Backend Services

| Service | Purpose |
|---------|---------|
| `ai_research.py` | Claude/OpenRouter multi-turn standard research |
| `deep_research.py` | 7-step deep research pipeline with SSE, parallel steps 2-5 |
| `market_research.py` | 8-step market study pipeline with SSE, parallel steps 1-3 then 4-6 |
| `company_sourcing.py` | 4-step company sourcing pipeline with SSE (extract DNA → search → verify → rank) |
| `job_store.py` | SQLite CRUD via aiosqlite |
| `verification.py` | Algorithmic + AI cross-verification |
| `prompt_manager.py` | In-memory prompt store (30+ prompts across all pipelines) |
| `pdf_extractor.py` | PDF text extraction (pypdfium2 + pdfplumber fallback) |
| `pptx_generator.py` | Company one-pager PPTX from template |
| `market_pptx_generator.py` | Market study PPTX generation (4 core + up to 3 optional slides) |
| `chart_generator.py` | Matplotlib donut + bar charts for PPTX |
| `template_builder.py` | Template construction utilities |

### Frontend Components (key files)

| Component | Purpose |
|-----------|---------|
| `app/page.tsx` | Input page — company/market toggle, PDF upload, scoping form |
| `app/editor/[id]/page.tsx` | Company one-pager editor (3-column layout) |
| `app/editor/[id]/sourcing/page.tsx` | Company sourcing results + SSE progress |
| `app/market-editor/[id]/page.tsx` | 10-section market study editor |
| `app/settings/page.tsx` | Model configuration per pipeline step |
| `app/jobs/page.tsx` | Job history list |
| `components/DeepResearchProgress.tsx` | SSE-connected vertical stepper |
| `components/DeepResearchResults.tsx` | Collapsible per-step results with sources |
| `components/PromptEditor.tsx` | Grouped prompt editor (standard/deep/market/sourcing) |
| `components/market/*.tsx` | 10+ section editors (executive summary, sizing, segmentation, competition, trends, PESTEL, Porter's, value chain, buy & build, strategic implications) |
| `lib/api.ts` | Full API client (research, jobs, SSE, prompts, models) |
| `lib/types.ts` | TypeScript types matching all backend models |

### Config & Models

| File | Purpose |
|------|---------|
| `config/models.py` | Per-step model selection for deep research + market research, known model registry, recheck model mapping, runtime overrides |
| `models/one_pager.py` | OnePagerData, VerificationResult, ResearchResponse |
| `models/job.py` | Job, JobSummary, DeepResearchStep, StepVerification |
| `models/market_study.py` | MarketStudyData with PE-focused extensions (KPC, multiples, EBITDA benchmarks, competitor deep-dives, B&B phases) |
| `models/company_sourcing.py` | CompanyProfile, CompSummaryStats, CompanySourcingResult |

### Storage

```
data/
├── jobs.db              → SQLite database (all job metadata + research results)
├── uploads/{id}/        → Uploaded IM PDFs
└── outputs/{id}/        → Generated PPTX files
```

---

## AI Pipeline Details

### Company One-Pager — Deep Research (7 steps)

| Step | Task | Default Model | Provider |
|------|------|---------------|----------|
| 1 | IM Extraction | Claude Opus 4 | OpenRouter |
| 2 | Web Research | Claude Opus 4 | Anthropic (web search) |
| 3 | Financial Deep-Dive | Claude Opus 4 | Anthropic (web search) |
| 4 | Management & Org | Claude Opus 4 | Anthropic (web search) |
| 5 | Market & Competitive | Gemini 2.5 Pro | OpenRouter |
| 6 | Merge & Synthesize | Claude Opus 4 | OpenRouter |
| 7 | Cross-Verify | GPT-4.1 | OpenRouter |

Steps 2-5 run in parallel. Each step has per-step 2nd AI recheck by a different model family.

### Market Research (8 steps)

| Step | Task | Default Model | Provider |
|------|------|---------------|----------|
| 1 | Market Sizing (TAM/SAM/SOM) | Claude Opus 4 | Anthropic (web search) |
| 2 | Segmentation | Claude Opus 4 | Anthropic (web search) |
| 3 | Competitive Landscape | Claude Opus 4 | Anthropic (web search) |
| 4 | Trends + PESTEL | Gemini 2.5 Pro | OpenRouter |
| 5 | Sourcing, Multiples & Porter's | Claude Opus 4 | Anthropic (web search) |
| 6 | Buy & Build Potential | Claude Opus 4 | Anthropic (web search) |
| 7 | Merge | Claude Opus 4 | OpenRouter |
| 8 | Cross-Verify | GPT-4.1 | OpenRouter |

Steps 1-3 parallel, then steps 4-6 parallel. Per-step recheck on steps 1-6.

### Company Sourcing (4 steps)

| Step | Task | Default Model | Provider |
|------|------|---------------|----------|
| 1 | Extract Company DNA | Claude Opus 4 | Anthropic (web search) |
| 2 | Search DACH Companies | Claude Opus 4 | Anthropic (web search) |
| 3 | Verify & Enrich | Claude Opus 4 | Anthropic (web search) |
| 4 | Rank & Synthesize | Claude Opus 4 | Anthropic (web search) |

### Anti-Hallucination (3 layers, all pipelines)

1. **Prompt-level guards** — "never invent data, return null if unknown, prefix inferences with ~, cite sources"
2. **Per-step 2nd AI recheck** — Each step's output rechecked by a different model family (Claude→GPT, Gemini→Claude, GPT→Claude)
3. **Final cross-verification** — Algorithmic checks + AI cross-verification on merged result

---

## Security Status

### Fixed
- Prompt injection via scoping_context, market_name, region (sanitization + allowlists)
- Input size limits on all form fields
- Error message scrubbing in SSE (generic client messages, detailed server logs)
- Admin key auth on prompt mutation endpoints

### Open (documented in `docs/KNOWN_ISSUES.md`)
- S4: Dynamic SQL column names — needs allowlist validation
- S6: No auth on research endpoints — needs rate limiting before public deployment
- S7: Prompts readable without auth
- S8: Race condition in `_save_step` (read-modify-write without locking)
- S9: No dedup guard on market research endpoint
- S10: Source URLs not strictly validated on frontend
- S12: JSON export filename not sanitized

---

## Docs

| File | Contents |
|------|----------|
| `docs/ARCHITECTURE.md` | System architecture diagram, data flow, all endpoints |
| `docs/BEST_PRACTICES.md` | AI-led M&A/PE market research best practices (sourcing, quality framework) |
| `docs/KNOWN_ISSUES.md` | All security + code quality issues with status and planned fixes |
| `PLAN.md` | Implementation plan for known issues, best practices, and company sourcing |

---

## Recent Git History (latest first)

```
ffc5420 Fix sourcing pipeline: don't overwrite deep_research_steps or job status
8391b46 Add company sourcing pipeline, per-step model configuration, and source triangulation
81502b2 Fix remaining security issues, add docs, update plan with company sourcing
877511b Security: sanitize market_name input, scrub error messages from SSE
18d33c5 Polish: switch UI to English, fix UX issues, improve prompt quality
a08274c Polish market research: QA, UX, security fixes from 3-agent review
c61f60c Add market research scoping questionnaire (4-dimension intake)
e22a8e1 Add market research feature: full-stack 8-step pipeline with 10-slide PPTX export
5106fe1 Simplify SSE endpoint to use async generator directly
4b574f5 Update HANDOVER.md with all phases complete
fa142d5 Phase B+C: Deep research pipeline with SSE streaming and frontend
38a2801 Replace legacy editor page with redirect to /jobs
62cbef8 Complete Phase A: job persistence backend wiring + frontend pages
a48de62 Phase A: Add persistent job storage (backend + frontend foundation)
9cf3d7b Refine plan: editable prompts, anti-hallucination, results UI, PPTX
58355ca Add persistent jobs + deep research plan, update HANDOVER
74d7c2d Fix security issues from Gemini code review (PR #1)
79312e2 Merge claude/review-progress-5vIvn into main
82328d5 Final HANDOVER update: mark all phases complete with pipeline verification
9ee0272 Professional frontend redesign for Constellation Capital
```

Note: Market PPTX C VII quality upgrade changes are uncommitted on the current branch.
