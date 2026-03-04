# Handover: M&A One-Pager Generator

**Branch:** `claude/review-progress-5vIvn`
**Date:** 2026-03-04
**Status:** COMPLETE — All changes implemented, tested, and verified

---

## Completed Changes

### 1. Structured IM Extraction Prompts

The `research_user_with_im` prompt now provides 8 extraction modules mapping IM chapters to One Pager fields:

| Module | IM Source | One Pager Target |
|--------|-----------|-----------------|
| 1. Header & Thesis | Executive Summary | `header.tagline`, `investment_thesis` |
| 2. Key Facts | Front matter, Company Overview | `key_facts.*` (founded, HQ, revenue, etc.) |
| 3. Financials | P&L chapter | `financials.*` (years, revenue, EBITDA arrays) |
| 4. Description & Portfolio | Executive Summary, Business Model | `description[]`, `product_portfolio[]` |
| 5. Investment Rationale | Key Investment Highlights, Risk | `investment_rationale.pros/cons` |
| 6. Revenue Split | Revenue Analysis, Market Positioning | `revenue_split.segments[]` |
| 7. Investment Criteria | Various | 12 criteria with evidence-based evaluation |
| 8. Meta/Status | Cover page | `meta.source`, `meta.status` |

### 2. Editable Prompts in the UI

5 prompts editable at runtime via `/api/prompts` REST API + collapsible editor on input page.

| Prompt | Placeholders |
|--------|-------------|
| `research_system` | (none — system prompt with web search) |
| `research_system_no_search` | (none — system prompt for OpenRouter) |
| `research_user_with_im` | `{company_name}`, `{im_text}`, `{json_schema}` |
| `research_user_no_im` | `{company_name}`, `{json_schema}` |
| `verification` | (none — verification system prompt) |

### 3. Optimal Model Selection

| Pipeline Step | Model | Rationale |
|---------------|-------|-----------|
| Research | **Claude Opus 4** | Best at thorough document analysis; fewer hallucinations on financial data in 50+ page IMs |
| Verification | **GPT-4.1** (OpenRouter) | Cross-model diversity catches correlated errors; strong at structured analysis |

### 4. Security Hardening

- Error messages sanitized: no internal exceptions leaked to clients
- `_safe_format()` handles missing/extra prompt placeholders gracefully
- Content-Disposition filename escaping prevents header injection
- Specific exception handling: `FileNotFoundError` (500), `ValueError` (400)

### 5. Code Maintainability

- Module-level loggers in all routers (no inline `import logging`)
- Fixed non-functional CSS `ring: 2px` → proper `box-shadow`
- Removed unused `recharts` dependency from frontend

### 6. Professional Frontend Redesign

- **Inter font** from Google Fonts, anti-aliased rendering
- **CC brand colors**: added `cc-navy` (#223F6A), `cc-surface` (#F0F5FA)
- **Header**: CC monogram badge, "M&A Deal Tools" label
- **Input page**: narrower card, client-side file validation, file size display, drag-and-drop feedback
- **Editor**: refined toolbar with divider, smaller professional typography
- **Section cards**: uppercase tracking-wide headers, clean rounded corners
- **Generate button**: backdrop blur, subtle upward shadow, inline status icons
- **Criteria buttons**: amber instead of yellow (more professional)

### 7. IM/Teaser Upload Pipeline — Verified End-to-End

Full pipeline tested and verified:

```
[Frontend] File selected
  → Client-side validation (type: PDF only, size: max 20 MB)
  → File size displayed in UI
  → FormData POST to /api/research
      ↓
[Backend] research.py
  → Server-side validation (filename, size)
  → PDF text extraction (pypdfium2 → pdfplumber fallback)
  → IM text truncated to 50k chars if needed
      ↓
[Prompt Builder] ai_research.py
  → Loads editable prompt template from prompt_manager
  → _safe_format() injects {company_name}, {im_text}, {json_schema}
  → 8-module extraction instructions included
      ↓
[LLM Call] Claude Opus 4 (Anthropic) or via OpenRouter
  → System prompt + user prompt with IM text
  → Multi-turn web search loop (Anthropic only)
  → Up to 15 turns with pause_turn/tool_use handling
      ↓
[JSON Parsing] _parse_response_json()
  → Strategy 1: Direct Pydantic validation
  → Strategy 2: Parse as dict → Pydantic
  → Strategy 3: Fix single quotes → parse
  → Fallback: Empty template with company name
      ↓
[Verification] verify_research()
  → Phase 1: Algorithmic checks (revenue split %, EBITDA margin, criteria)
  → Phase 2: AI cross-verification (GPT-4.1 via OpenRouter)
      ↓
[Frontend] Editor page
  → Data loaded from sessionStorage
  → Verification banner with expandable flags
  → 3-column editor matching slide layout
  → Generate PPTX button
```

**Verified checks:**
- Prompt with IM includes all 8 modules and `<im_document>` tag
- Prompt without IM does NOT include IM-related sections
- Long IMs correctly truncated to 50,000 characters
- Safe formatting preserves unknown placeholders instead of crashing
- JSON parsing handles: raw JSON, markdown-wrapped, text-embedded, and falls back gracefully
- Algorithmic verification catches: revenue split != 100%, EBITDA margin inconsistencies, criteria mismatches

---

## File Change Summary

| File | Status | Description |
|------|--------|-------------|
| `backend/services/prompt_manager.py` | NEW | Prompt storage + defaults + edit/reset |
| `backend/routers/prompts.py` | NEW | REST API for prompt CRUD |
| `backend/services/ai_research.py` | MODIFIED | prompt_manager, Opus default, safe formatting |
| `backend/services/verification.py` | MODIFIED | Uses prompt_manager |
| `backend/routers/research.py` | MODIFIED | Sanitized errors, module-level logger |
| `backend/routers/generate.py` | MODIFIED | Sanitized errors, filename escaping |
| `backend/main.py` | MODIFIED | Mounts prompts router |
| `frontend/tailwind.config.ts` | MODIFIED | cc-navy, cc-surface, Inter font |
| `frontend/src/app/layout.tsx` | MODIFIED | Professional header, Inter font |
| `frontend/src/app/globals.css` | MODIFIED | Proper layers, focus ring, amber criteria |
| `frontend/src/app/page.tsx` | MODIFIED | File validation, redesigned input |
| `frontend/src/app/editor/page.tsx` | MODIFIED | Refined toolbar |
| `frontend/src/app/components/SectionCard.tsx` | MODIFIED | Uppercase headers |
| `frontend/src/app/components/GenerateButton.tsx` | MODIFIED | Backdrop blur |
| `frontend/src/app/components/PromptEditor.tsx` | NEW | Prompt editor UI |
| `frontend/src/lib/types.ts` | MODIFIED | PromptDefinition type |
| `frontend/src/lib/api.ts` | MODIFIED | Prompt API functions |
| `frontend/package.json` | MODIFIED | Removed recharts |

---

## Security Fixes (Gemini Code Review — PR #1)

| # | Severity | Issue | Fix |
|---|----------|-------|-----|
| 1 | **Critical** | `/api/prompts` mutation endpoints publicly accessible | Added `X-Admin-Key` header auth; requires `ADMIN_API_KEY` env var. If unset, mutations are disabled entirely. GET (read-only) remains open. |
| 2 | **Critical** | Prompt injection via editable templates + untrusted input | Added `_sanitize_company_name()` (strips control chars, caps at 200 chars). Added injection guardrail to system prompt instructing model to treat inputs as data only. |
| 3 | **Medium** | HTTP header injection via redundant `.replace('"', "'")` in filename | Removed redundant call; `_sanitize_filename()` already strips all control chars and non-safe characters. |
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

### Data Flow

1. **Input**: User enters company name + optional IM PDF
2. **Research**: PDF extracted → AI research (Claude + web search, up to 15 turns)
3. **Parsing**: JSON extracted with 4-strategy fallback cascade
4. **Verification**: Algorithmic checks + cross-model AI verification
5. **Editor**: User reviews/edits all fields in 3-column form
6. **Generate**: PPTX populated from template with charts embedded as PNG

### Data Model (`OnePagerData`)

Root fields: `meta`, `header`, `investment_thesis`, `key_facts`, `description[]`, `product_portfolio[]`, `investment_rationale`, `revenue_split`, `financials`, `investment_criteria` (12 criteria with fulfilled/questions/not_interest).

### Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `ANTHROPIC_API_KEY` | One of these | Claude API for research + web search |
| `OPENROUTER_API_KEY` | required | OpenRouter for verification + fallback research |
| `ADMIN_API_KEY` | Optional | Enables prompt editing via API |

### Architecture Notes

- Prompts stored **in-memory** per process. Backend restart resets to defaults.
- Prompt templates use `str.format()` with `_safe_format()` fallback for robustness.
- Frontend validates PDF type + size before uploading.
- IM text truncated to 50k chars to stay within token limits.
- Cross-model verification (Claude → GPT-4.1) prevents correlated hallucination errors.
- Prompt mutations require `ADMIN_API_KEY` env var + `X-Admin-Key` header.
