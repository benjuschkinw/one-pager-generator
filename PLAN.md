# Plan: Structured IM Extraction, Editable Prompts & Optimal Model Selection

## Overview

Three interconnected improvements:
1. Integrate the detailed IM-to-One-Pager mapping spec into the research prompts
2. Make all prompts viewable and editable in the UI
3. Use the best model for each pipeline step (money is not the issue)

---

## Part 1: Structured IM Extraction Prompts

### Problem
The current IM extraction prompt is generic: "extract from the IM." The user's spec defines a precise module-by-module mapping from IM chapters to One Pager fields, with specific transformation logic.

### Changes

**`backend/services/ai_research.py`** — Rewrite `_build_user_prompt()` when `im_text` is provided:

Replace the generic IM source instructions with structured module-by-module extraction:

```
Module 1 — Header: Create project name + 15-word Company Headline
Module 2 — Financial Extraction: Revenue + Adj. EBITDA for [Year-2]A, [Year-1]A, [Current]E, [Year+1]P–[Year+3]P. Calculate EBITDA margins.
Module 3 — Rationale: 3 specific investment rationales, bold keywords, include ≥1 risk factor
Module 4 — Revenue Split: List "Revenue Split by [Category]" ensuring total = 100%
Module 5 — Criteria Checklist: Evaluate 6 core criteria with Fulfilled/Not Fulfilled logic
```

Also include the IM chapter → One Pager mapping table so the AI knows where to look:
- "Executive Summary" → Description (summarize 3-5 pages into 2-3 sentences)
- "Key Investment Highlights" → Rationale (top 2-3 Plus, 2-3 Minus)
- "Financials" chapter → Key Financials (P&L tables)
- "Market Positioning" / "Revenue Analysis" → Revenue Split
- "Investment Highlights" + "Organization" → Investment Criteria

**`backend/services/ai_research.py`** — Update `RESEARCH_SYSTEM_PROMPT`:

Add the role framing: "Act as a Senior M&A Associate at an Investment firm. Review the provided IM and extract content for a standardized One Pager."

Reinforce: "Professional, clinical, data-driven. Avoid marketing fluff."

---

## Part 2: Editable Prompts in the UI

### Architecture

**Backend: Prompt storage & API**

Create **`backend/services/prompt_manager.py`**:
- Store all prompts as a dict/config (keyed by name, e.g. `research_system`, `research_user_im`, `research_user_no_im`, `verification_system`)
- Each prompt has: `name`, `description`, `template` (the actual prompt text with `{placeholders}`)
- Default prompts are hardcoded constants (the current ones, improved per Part 1)
- Prompts are stored in-memory per session (no database needed for now)
- Functions: `get_prompts()`, `get_prompt(name)`, `update_prompt(name, template)`, `reset_prompt(name)`

Create **`backend/routers/prompts.py`**:
- `GET /api/prompts` — List all prompt names + descriptions + current templates
- `GET /api/prompts/{name}` — Get single prompt
- `PUT /api/prompts/{name}` — Update a prompt template
- `POST /api/prompts/{name}/reset` — Reset to default

Update **`backend/services/ai_research.py`**:
- Import prompts from `prompt_manager` instead of module-level constants
- `_build_user_prompt()` and system prompt read from `prompt_manager.get_prompt()`

Update **`backend/main.py`**:
- Mount the new prompts router

**Frontend: Prompt editor UI**

Create **`frontend/src/app/components/PromptEditor.tsx`**:
- Collapsible panel/drawer accessible from the input page (gear icon or "Advanced" toggle)
- Lists all prompts with their descriptions
- Each prompt is a labeled, resizable textarea
- "Reset to Default" button per prompt
- Changes are sent to `PUT /api/prompts/{name}` on blur or save

Update **`frontend/src/lib/api.ts`**:
- Add `getPrompts()`, `updatePrompt(name, template)`, `resetPrompt(name)` functions

Update **`frontend/src/app/page.tsx`**:
- Add a "Prompts" or "Advanced Settings" toggle/button below the main form
- Render `PromptEditor` when toggled open

---

## Part 3: Optimal Model Selection

### Analysis

The pipeline has 3 AI-intensive steps. For each, the best model depends on the task:

| Step | Current Model | Recommended | Rationale |
|------|--------------|-------------|-----------|
| **Research (with IM)** | Claude Sonnet 4 | **Claude Opus 4** | Complex document analysis, structured extraction from 50+ page IMs. Opus excels at careful, thorough analysis of long documents. Sonnet sometimes misses subtleties in financial tables. |
| **Research (no IM, web search)** | Claude Sonnet 4 | **Claude Opus 4** | Web search + synthesis. Opus produces more accurate financial data and is less likely to hallucinate. Web search is Anthropic-only anyway. |
| **Verification** | GPT-4.1 (via OpenRouter) | **GPT-4.1** (keep as-is) | Cross-model verification is the key value here. GPT-4.1 is strong at structured analysis and catches different errors than Claude. The model family diversity matters more than raw capability. |

### Changes

**`backend/services/ai_research.py`**:
- Change `DEFAULT_MODELS["anthropic"]` from `claude-sonnet-4-20250514` to `claude-opus-4-20250514`
- Change `DEFAULT_MODELS["openrouter"]` from `anthropic/claude-sonnet-4` to `anthropic/claude-opus-4`
- Update the provider model lists to show Opus first (as default/recommended)

**`backend/services/verification.py`**:
- Keep GPT-4.1 as verification model (correct choice for cross-model diversity)
- No changes needed

**Frontend model selector** (if it exists in provider dropdown):
- Update default selection to show Opus as recommended

---

## File Change Summary

| File | Action |
|------|--------|
| `backend/services/prompt_manager.py` | **NEW** — Prompt storage, defaults, get/update/reset |
| `backend/routers/prompts.py` | **NEW** — REST API for prompts |
| `backend/services/ai_research.py` | **EDIT** — Use prompt_manager, upgrade defaults to Opus, improve IM extraction prompt |
| `backend/main.py` | **EDIT** — Mount prompts router |
| `frontend/src/app/components/PromptEditor.tsx` | **NEW** — Prompt editing UI |
| `frontend/src/lib/api.ts` | **EDIT** — Add prompt API functions |
| `frontend/src/app/page.tsx` | **EDIT** — Add prompt editor toggle |

---

## Implementation Order

1. Create `prompt_manager.py` with improved prompts (Part 1 + Part 2 backend)
2. Create `routers/prompts.py` API endpoints (Part 2 backend)
3. Update `ai_research.py` to use prompt_manager + upgrade models (Part 1 + Part 3)
4. Update `main.py` to mount new router
5. Add prompt API functions to `api.ts` (Part 2 frontend)
6. Create `PromptEditor.tsx` component (Part 2 frontend)
7. Update `page.tsx` to include prompt editor toggle (Part 2 frontend)
