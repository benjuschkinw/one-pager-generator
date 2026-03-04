# Handover: M&A One-Pager Generator

**Branch:** `claude/review-progress-5vIvn`
**Date:** 2026-03-04
**Status:** IN PROGRESS — Frontend redesign complete, verifying IM pipeline next

---

## Completed Changes

### 1. Structured IM Extraction Prompts

The research prompt now provides module-by-module extraction rules mapping IM chapters to One Pager fields (8 modules: Header, Key Facts, Financials, Description, Rationale, Revenue Split, Investment Criteria, Meta).

### 2. Editable Prompts in the UI

All 5 AI prompts editable at runtime via `/api/prompts` REST API + collapsible UI editor on input page.

| Prompt | Placeholders |
|--------|-------------|
| `research_system` | (none) |
| `research_system_no_search` | (none) |
| `research_user_with_im` | `{company_name}`, `{im_text}`, `{json_schema}` |
| `research_user_no_im` | `{company_name}`, `{json_schema}` |
| `verification` | (none) |

### 3. Model Upgrade to Opus 4

| Step | Model | Rationale |
|------|-------|-----------|
| Research | Claude Opus 4 | Best at thorough document analysis |
| Verification | GPT-4.1 (OpenRouter) | Cross-model diversity |

### 4. Security Hardening

- Error messages sanitized (no internal exceptions leaked)
- Safe prompt formatting with `_safe_format()` fallback
- Content-Disposition filename escaping
- Specific exception handling (FileNotFoundError, ValueError)

### 5. Code Maintainability

- Module-level loggers in all routers
- Fixed broken CSS focus ring
- Removed unused `recharts` dependency

### 6. Professional Frontend Redesign

**Typography & Branding:**
- Inter font loaded from Google Fonts
- Added `cc-navy` (#223F6A), `cc-surface` (#F0F5FA) to Tailwind palette
- Font family set to Inter with system-ui fallback
- Anti-aliased rendering

**Layout (`layout.tsx`):**
- Professional header with CC monogram badge and "M&A Deal Tools" label
- Background changed from `bg-slate-50` to `bg-cc-surface` (branded light blue)
- Border-based header separation instead of shadow

**Input Page (`page.tsx`):**
- Narrower card (max-w-xl) with separated header/body sections
- Client-side file validation (type + size) before upload
- File size display (MB) when file selected
- Drag-and-drop visual feedback (hover states)
- Better loading indicator with pulsing dot
- Bottom toolbar with prompts and skip links side-by-side

**Editor Page (`editor/page.tsx`):**
- Refined toolbar with divider between back button and title
- Smaller, more professional typography throughout

**Section Cards (`SectionCard.tsx`):**
- Uppercase tracking-wide headers
- Overflow-hidden for clean rounded corners

**Generate Button:**
- Backdrop blur for sticky bottom bar
- Subtle shadow (upward)
- Success/error states with inline icons
- Smaller, more refined button sizing

**CSS (`globals.css`):**
- Proper Tailwind layer structure (@layer base, @layer components)
- Focus ring uses rgba for subtle blue glow instead of solid ring
- Criteria buttons use amber instead of yellow (more professional)

---

## Full File Change Summary

| File | Status | Description |
|------|--------|-------------|
| `backend/services/prompt_manager.py` | NEW | Prompt storage + defaults + edit/reset |
| `backend/routers/prompts.py` | NEW | REST API for prompt CRUD |
| `backend/services/ai_research.py` | MODIFIED | prompt_manager, Opus default, safe formatting |
| `backend/services/verification.py` | MODIFIED | Uses prompt_manager |
| `backend/routers/research.py` | MODIFIED | Sanitized errors, module-level logger |
| `backend/routers/generate.py` | MODIFIED | Sanitized errors, filename escaping |
| `backend/main.py` | MODIFIED | Mounts prompts router |
| `frontend/tailwind.config.ts` | MODIFIED | Added cc-navy, cc-surface, Inter font |
| `frontend/src/app/layout.tsx` | MODIFIED | Professional header, Inter font, branded bg |
| `frontend/src/app/globals.css` | MODIFIED | Proper layers, focus ring, amber criteria |
| `frontend/src/app/page.tsx` | MODIFIED | File validation, redesigned input page |
| `frontend/src/app/editor/page.tsx` | MODIFIED | Refined toolbar and layout |
| `frontend/src/app/components/SectionCard.tsx` | MODIFIED | Uppercase headers, overflow-hidden |
| `frontend/src/app/components/GenerateButton.tsx` | MODIFIED | Backdrop blur, refined button |
| `frontend/src/app/components/PromptEditor.tsx` | NEW | Prompt editor UI |
| `frontend/src/lib/types.ts` | MODIFIED | Added PromptDefinition type |
| `frontend/src/lib/api.ts` | MODIFIED | Added prompt API functions |
| `frontend/package.json` | MODIFIED | Removed unused recharts |

---

## Architecture Notes

- Prompts stored **in-memory** (per process). Restart resets to defaults.
- Prompt templates use `str.format()` with `_safe_format()` fallback.
- Prompt editor is on input page (affects research, not PPTX generation).
- Frontend validates PDF file type and size before uploading.

---

## Next Steps

- [ ] Verify IM/Teaser upload + LLM pipeline end-to-end
