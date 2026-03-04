# Handover: Editable Prompts, Structured IM Extraction & Model Upgrade

**Branch:** `claude/review-progress-5vIvn`
**Date:** 2026-03-04
**Status:** COMPLETE — All changes implemented, ready for testing

---

## What Changed

### 1. Structured IM Extraction Prompts (Part 1)

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
- Each module specifies: which IM chapter to look in, what format to output, and what rules to follow

**Files:**
- `backend/services/prompt_manager.py` — **NEW** (prompt storage + defaults + edit/reset API)

---

### 2. Editable Prompts in the UI (Part 2)

**Problem:** Prompts were hardcoded. Users couldn't iterate on prompt quality without code changes.

**What was done:**

**Backend:**
- `backend/services/prompt_manager.py` — Stores 5 prompts as `PromptDefinition` objects with `name`, `description`, `template`, and `is_default` tracking
- `backend/routers/prompts.py` — **NEW** REST API:
  - `GET /api/prompts` — List all prompts
  - `GET /api/prompts/{name}` — Get single prompt
  - `PUT /api/prompts/{name}` — Update template text
  - `POST /api/prompts/{name}/reset` — Reset to default
  - `POST /api/prompts/reset` — Reset all
- `backend/main.py` — Mounted prompts router
- `backend/services/ai_research.py` — Now reads prompts via `get_prompt_template()` instead of module constants
- `backend/services/verification.py` — Same: reads verification prompt from prompt_manager

**Frontend:**
- `frontend/src/lib/types.ts` — Added `PromptDefinition` interface
- `frontend/src/lib/api.ts` — Added `getPrompts()`, `updatePrompt()`, `resetPrompt()`, `resetAllPrompts()`
- `frontend/src/app/components/PromptEditor.tsx` — **NEW** Collapsible prompt editor with:
  - Accordion-style expand/collapse per prompt
  - Monospace textarea for editing
  - Unsaved change tracking with "unsaved" badge
  - "modified" badge for non-default prompts
  - Save and Reset to Default buttons per prompt
  - Reset All to Defaults button
- `frontend/src/app/page.tsx` — Added gear icon toggle "Edit AI Prompts" below the main form

**Prompt names and their roles:**
| Name | Description |
|------|-------------|
| `research_system` | System prompt for Anthropic (web search enabled) |
| `research_system_no_search` | System prompt for OpenRouter (no web search) |
| `research_user_with_im` | User prompt when IM PDF provided. Placeholders: `{company_name}`, `{im_text}`, `{json_schema}` |
| `research_user_no_im` | User prompt for public research only. Placeholders: `{company_name}`, `{json_schema}` |
| `verification` | System prompt for the cross-verification model |

---

### 3. Model Upgrade to Opus (Part 3)

**Problem:** Default model was Claude Sonnet 4. For complex IM extraction, Opus 4 produces more thorough and accurate results.

**What was done:**
- `DEFAULT_MODELS["anthropic"]` changed from `claude-sonnet-4-20250514` to `claude-opus-4-20250514`
- `DEFAULT_MODELS["openrouter"]` changed from `anthropic/claude-sonnet-4` to `anthropic/claude-opus-4`
- Provider model lists reordered to show Opus first with "(Recommended)" label
- **Verification stays on GPT-4.1** — cross-model diversity is more important than raw capability for catching errors

**Rationale for model choices:**
| Step | Model | Why |
|------|-------|-----|
| Research (with/without IM) | Claude Opus 4 | Best at careful, thorough document analysis. Less likely to miss financial details in 50+ page IMs. |
| Verification | GPT-4.1 (OpenRouter) | Different model family catches correlated errors. Strong at structured analysis. |

---

## File Change Summary

| File | Status | Description |
|------|--------|-------------|
| `backend/services/prompt_manager.py` | NEW | Prompt storage, defaults, get/update/reset |
| `backend/routers/prompts.py` | NEW | REST API for prompt CRUD |
| `backend/services/ai_research.py` | MODIFIED | Uses prompt_manager, defaults to Opus |
| `backend/services/verification.py` | MODIFIED | Uses prompt_manager for verification prompt |
| `backend/main.py` | MODIFIED | Mounts prompts router |
| `frontend/src/lib/types.ts` | MODIFIED | Added PromptDefinition type |
| `frontend/src/lib/api.ts` | MODIFIED | Added prompt API functions |
| `frontend/src/app/components/PromptEditor.tsx` | NEW | Prompt editor UI component |
| `frontend/src/app/page.tsx` | MODIFIED | Added prompt editor toggle |

---

## Testing Checklist

- [ ] Backend starts without errors (`cd backend && uvicorn main:app`)
- [ ] `GET /api/prompts` returns 5 prompts
- [ ] `PUT /api/prompts/research_system` updates the prompt
- [ ] `POST /api/prompts/research_system/reset` restores default
- [ ] Frontend builds (`cd frontend && npm run build`)
- [ ] "Edit AI Prompts" toggle shows/hides prompt editor
- [ ] Editing a prompt shows "unsaved" badge, saving clears it
- [ ] Research with IM uses the structured module-by-module extraction
- [ ] Research without IM uses the public research prompt
- [ ] Model selector shows Opus as default/recommended

---

## Architecture Notes

- Prompts are stored **in-memory** (per process). Restarting the backend resets all prompts to defaults. This is intentional for now — a database-backed store can be added later.
- Prompt templates use Python `str.format()` placeholders (`{company_name}`, `{im_text}`, `{json_schema}`). Users editing prompts must keep these placeholders intact or the research will fail.
- The prompt editor is on the input page (not the editor page) because prompts affect research, not PPTX generation.
