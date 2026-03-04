# Handover: M&A One-Pager Generator

**Branch:** `claude/review-progress-5vIvn`
**Date:** 2026-03-04
**Status:** IN PROGRESS — Security + maintainability complete, frontend redesign next

---

## Completed Changes

### 1. Structured IM Extraction Prompts

**Problem:** The research prompt gave generic instructions to "extract from the IM." The new prompts provide module-by-module extraction rules mapping IM chapters to One Pager fields.

**What was done:**
- Created `backend/services/prompt_manager.py` with 5 editable prompts
- The `research_user_with_im` prompt now includes 8 extraction modules:
  - Module 1: Header & Thesis (tagline, investment_thesis)
  - Module 2: Key Facts (founded, HQ, revenue, EBITDA, management, employees)
  - Module 3: Financial Extraction (multi-year P&L with A/E/P suffixes)
  - Module 4: Description & Portfolio (bullet point summaries)
  - Module 5: Investment Rationale (pros/cons from investment highlights)
  - Module 6: Revenue Split (only if explicit breakdown in IM)
  - Module 7: Investment Criteria Evaluation (12 criteria with evidence rules)
  - Module 8: Meta/Status (source, dates)

### 2. Editable Prompts in the UI

All 5 AI prompts are editable at runtime via `/api/prompts` REST API and a collapsible UI editor on the input page.

**Prompts:**
| Name | Placeholders |
|------|-------------|
| `research_system` | (none — system prompt with web search) |
| `research_system_no_search` | (none — system prompt without web search) |
| `research_user_with_im` | `{company_name}`, `{im_text}`, `{json_schema}` |
| `research_user_no_im` | `{company_name}`, `{json_schema}` |
| `verification` | (none — verification system prompt) |

### 3. Model Upgrade to Opus 4

| Step | Model | Rationale |
|------|-------|-----------|
| Research | Claude Opus 4 | Best at thorough document analysis, fewer hallucinations on financial data |
| Verification | GPT-4.1 (OpenRouter) | Cross-model diversity catches correlated errors |

### 4. Security Hardening

- **Error messages sanitized**: Backend no longer leaks internal exceptions to clients. Errors are logged server-side, clients get generic messages.
- **Safe prompt formatting**: `_safe_format()` in `ai_research.py` handles missing/extra placeholders gracefully instead of crashing.
- **Content-Disposition hardened**: Filename quotes escaped to prevent header injection.
- **Specific exception handling**: `FileNotFoundError` for missing templates, `ValueError` for bad user input — each returns appropriate HTTP status.

### 5. Code Maintainability

- **Moved inline imports**: All `import logging` moved to module-level in routers.
- **Module-level loggers**: `research.py` and `generate.py` now use module-level `logger` instances.
- **Fixed broken CSS**: `globals.css` had non-functional `ring: 2px` (Tailwind utility, not CSS property) — replaced with proper `box-shadow`.
- **Removed unused dependency**: `recharts` removed from `package.json` (never imported).

---

## File Change Summary

| File | Status | Description |
|------|--------|-------------|
| `backend/services/prompt_manager.py` | NEW | Prompt storage, defaults, edit/reset |
| `backend/routers/prompts.py` | NEW | REST API for prompt CRUD |
| `backend/services/ai_research.py` | MODIFIED | prompt_manager integration, Opus default, safe formatting |
| `backend/services/verification.py` | MODIFIED | Uses prompt_manager |
| `backend/routers/research.py` | MODIFIED | Sanitized errors, module-level logger |
| `backend/routers/generate.py` | MODIFIED | Sanitized errors, filename escaping |
| `backend/main.py` | MODIFIED | Mounts prompts router |
| `frontend/src/lib/types.ts` | MODIFIED | Added PromptDefinition type |
| `frontend/src/lib/api.ts` | MODIFIED | Added prompt API functions |
| `frontend/src/app/components/PromptEditor.tsx` | NEW | Prompt editor UI |
| `frontend/src/app/page.tsx` | MODIFIED | Added prompt editor toggle |
| `frontend/src/app/globals.css` | MODIFIED | Fixed focus ring CSS |
| `frontend/package.json` | MODIFIED | Removed unused recharts |

---

## Architecture Notes

- Prompts stored **in-memory** (per process). Restart resets to defaults.
- Prompt templates use `str.format()` with `_safe_format()` fallback for robustness.
- Prompt editor is on input page (affects research, not PPTX generation).

---

## Next Steps

- [ ] Professional frontend redesign for Constellation Capital
- [ ] Verify IM/Teaser upload + LLM pipeline end-to-end
