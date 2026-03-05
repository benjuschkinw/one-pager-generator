# Known Issues & Security Review

**Date:** 2026-03-05
**Reviewer:** Automated security review (Claude Opus 4.6)

---

## Security Issues

### FIXED

| # | Severity | Issue | Fix | File |
|---|----------|-------|-----|------|
| S1 | HIGH | Prompt injection via `scoping_context` values — raw user input interpolated into AI prompts | `_sanitize_scoping()` with key whitelist (8 known keys), 500-char limit per field, markdown/code-block filter | `backend/routers/market_research.py` |
| S2 | HIGH | Prompt injection via `market_name` and `region` — free-form strings in prompts | `_sanitize_market_name()` strips markdown injection, newlines, collapses whitespace. `region` validated against allowlist | `backend/routers/market_research.py` |
| S3 | MEDIUM | No input size limits on backend Form fields — could cause DoS via oversized inputs or expensive API calls | `_MAX_MARKET_NAME_LEN=200`, `_MAX_SCOPING_JSON_LEN=10000`, `_MAX_SCOPING_FIELD_LEN=500` | `backend/routers/market_research.py` |
| S5 | MEDIUM | Error messages leak internal details (file paths, API URLs, partial keys) via SSE to client | All SSE error events now return generic messages ("Step failed. Please try again."). Full errors logged server-side | `backend/services/market_research.py` |
| S11 | LOW | `json.loads` on untrusted `scoping_context` without schema validation | Parsing validates dict type, applies key whitelist and type/length checks via `_sanitize_scoping()` | `backend/routers/market_research.py` |

### OPEN — Code Fixes Planned

| # | Severity | Issue | Planned Fix | File |
|---|----------|-------|-------------|------|
| S4 | MEDIUM | Dynamic SQL column names in `update_job` — field names interpolated into SQL via f-string. Currently safe (all callers use hardcoded kwargs) but fragile | Add `_ALLOWED_COLUMNS` set validation before SQL construction | `backend/services/job_store.py` |
| S8 | LOW | Race condition in `_save_step` — read-modify-write on `deep_research_steps` without locking. Steps 1-3 and 4-6 run in parallel, concurrent `_save_step` calls could overwrite each other | Add per-job `asyncio.Lock` to serialize `_save_step` calls | `backend/services/market_research.py`, `backend/services/deep_research.py` |
| S10 | LOW | Source URLs from AI rendered as `<a>` tags with only `startsWith("http")` check — could link to phishing sites | Add `new URL()` validation on frontend | `frontend/src/app/components/DeepResearchResults.tsx` |
| S12 | LOW | JSON export filename constructed from user-controlled `market_name` without sanitization — special chars could cause filesystem issues | Add frontend filename sanitization via regex | `frontend/src/app/market-editor/[id]/page.tsx` |

### OPEN — Architectural / Won't Fix (Requires Design Decision)

| # | Severity | Issue | Notes |
|---|----------|-------|-------|
| S6 | MEDIUM | No authentication on market research endpoints — any client can trigger expensive AI pipelines and access any job by UUID | Requires architectural decision on auth strategy. At minimum, implement rate limiting per client IP. |
| S7 | MEDIUM | `GET /prompts` exposes all system prompt templates without auth — aids prompt injection by revealing instructions | Consider requiring auth for read access too. Admin key for mutation is already implemented. |
| S9 | LOW | No dedup guard on market research endpoint — rapid fire creates multiple parallel AI pipelines | Implement rate limiting or track in-flight requests per client. Deep research endpoint already has a 409 guard. |

---

## Code Quality Issues

| # | Area | Issue | Status |
|---|------|-------|--------|
| Q1 | QA | Double `onComplete` in SSE handler | **FIXED** — completion flag prevents double callback |
| Q2 | QA | Shallow merge loses nested defaults in market editor | **FIXED** — deep merge for all object fields |
| Q3 | QA | CAGR input reformats on every keystroke | **FIXED** — `type="number"` with label "(%)"|
| Q4 | QA | `fragmentation_score` 0-1 vs 1-10 scale mismatch | **FIXED** — unified to 1-10 scale |
| Q5 | UX | Undefined `cc-primary` Tailwind token | **FIXED** — replaced with `cc-mid` |
| Q6 | UX | No responsive breakpoints on grids | **FIXED** — added `sm:grid-cols-*` |
| Q7 | UX | Missing aria-labels on icon buttons | **FIXED** — all icon buttons have `aria-label` |
| Q8 | Prompts | Fragmentation score scale mismatch in prompt | **FIXED** — updated to 1-10 scale |
| Q9 | Prompts | No source triangulation guidance | **FIXED** — added triangulation rules |
| Q10 | Prompts | German example in merge prompt | **FIXED** — switched to English |

---

## Risk Assessment

**Highest risk combination:** S6 (no auth) + S1/S2 (prompt injection, now fixed) meant any network client could manipulate AI outputs. With S1/S2 fixed, the remaining risk is cost-based DoS via unauthenticated API access (S6).

**Recommended priority:** Implement rate limiting (S6/S9) before any public deployment.
