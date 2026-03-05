# Implementation Plan: Known Issues, Best Practices, and Company Sourcing Feature

## Overview

This plan covers three workstreams:

1. **Document & fix all known issues** (security, code quality, race conditions)
2. **Re-verify best practices** for AI-led market research in M&A/PE
3. **New feature: Company Sourcing** — given a company from a one-pager, find similar companies across DACH

---

## Workstream 1: Known Issues — Documentation & Fixes

### 1.1 Security Issues (from security review)

| # | Severity | Issue | Status | Action |
|---|----------|-------|--------|--------|
| S1 | HIGH | Prompt injection via `scoping_context` values | **FIXED** | `_sanitize_scoping()` with key whitelist, length caps, markdown filter |
| S2 | HIGH | Prompt injection via `market_name` and `region` | **FIXED** | `_sanitize_market_name()`, region allowlist |
| S3 | MEDIUM | No input size limits on backend Form fields | **FIXED** | `_MAX_MARKET_NAME_LEN=200`, `_MAX_SCOPING_JSON_LEN=10000`, region allowlist |
| S4 | MEDIUM | Dynamic SQL column names in `update_job` | OPEN | Add column name allowlist validation |
| S5 | MEDIUM | Error messages leak internal details via SSE | **FIXED** | Generic error messages returned to client |
| S6 | MEDIUM | No authentication on market research endpoints | OPEN | Add rate limiting (auth is architectural decision) |
| S7 | MEDIUM | Editable prompts readable without auth | OPEN | Require auth for `GET /prompts` |
| S8 | LOW | Race condition in `_save_step` (read-modify-write) | OPEN | Add per-job `asyncio.Lock` |
| S9 | LOW | No dedup guard on market research endpoint | OPEN | Track in-flight requests per client |
| S10 | LOW | Source URLs from AI rendered without strict validation | OPEN | Add `new URL()` validation |
| S11 | LOW | `json.loads` on scoping_context without depth limit | **FIXED** | Schema validation via `_sanitize_scoping()` |
| S12 | LOW | XSS via download filename on frontend | OPEN | Add frontend filename sanitization |

### 1.2 Code Fixes to Implement

#### Fix S4: SQL Column Name Allowlist

**File:** `backend/services/job_store.py`

```python
_ALLOWED_COLUMNS = {
    "company_name", "status", "im_filename", "im_file_path", "im_text",
    "provider", "model", "research_mode", "research_data", "verification",
    "deep_research_steps", "edited_data", "pptx_file_path",
    "market_study_data", "edited_market_data", "updated_at",
}

async def update_job(job_id: str, **fields: Any) -> Optional[Job]:
    if not fields:
        return await get_job(job_id)

    # Validate column names against allowlist
    invalid = set(fields.keys()) - _ALLOWED_COLUMNS
    if invalid:
        raise ValueError(f"Invalid field names: {invalid}")

    # ... rest of function unchanged
```

#### Fix S8: Per-Job Lock for `_save_step`

**File:** `backend/services/market_research.py`

```python
import asyncio

_job_locks: dict[str, asyncio.Lock] = {}

def _get_job_lock(job_id: str) -> asyncio.Lock:
    if job_id not in _job_locks:
        _job_locks[job_id] = asyncio.Lock()
    return _job_locks[job_id]

async def _save_step(job_id: str, step: DeepResearchStep) -> None:
    async with _get_job_lock(job_id):
        job = await get_job(job_id)
        if job is None:
            return
        steps = list(job.deep_research_steps or [])
        # ... rest unchanged
```

Same fix needed in `backend/services/deep_research.py`.

#### Fix S12: Frontend Filename Sanitization

**File:** `frontend/src/app/market-editor/[id]/page.tsx`

```typescript
const sanitizeFilename = (name: string): string =>
  name.replace(/[^a-zA-Z0-9_\-. ]/g, "_").substring(0, 100);

// Usage:
a.download = `Market_Study_${sanitizeFilename(data.meta.market_name || "export")}.json`;
```

#### Fix S10: URL Validation for AI Sources

**File:** `frontend/src/app/components/DeepResearchResults.tsx`

```typescript
const isValidUrl = (s: string): boolean => {
  try { new URL(s); return true; } catch { return false; }
};

// Usage:
href={isValidUrl(src) && src.startsWith("http") ? src : undefined}
```

---

## Workstream 2: Best Practices Verification

### 2.1 Current State vs. Industry Best Practices

| Best Practice | Current Status | Gap | Action |
|--------------|----------------|-----|--------|
| **Multi-model orchestration** | 3 providers, per-step model selection | Good | No change needed |
| **Parallel execution** | Steps 1-3 and 4-6 parallel | Good | No change needed |
| **Anti-hallucination (3 layers)** | Prompt guards + per-step recheck + final verify | Good | Strengthen source triangulation |
| **Source attribution** | URLs collected from web search results | Partial | Add per-claim citation linking |
| **Confidence scoring** | Overall confidence 0-1 | Partial | Add per-section confidence scores |
| **Data quality tiers** | Not implemented | Gap | Add source tier classification |
| **Scoping context** | 4-dimension intake form | Good | No change needed |
| **Structured output** | Pydantic validation on all AI responses | Good | No change needed |

### 2.2 Improvements to Implement

#### 2.2.1 Per-Section Confidence Scores

Add confidence metadata to each section of `MarketStudyData`:

```python
class SectionConfidence(BaseModel):
    score: float = 0.0          # 0.0-1.0
    source_count: int = 0       # Number of sources backing this section
    source_tier: str = "mixed"  # "primary" | "secondary" | "mixed"
    notes: str = ""             # e.g., "Based on 2 industry reports + 1 government stat"
```

Each top-level section (market_sizing, segmentation, etc.) gets a `confidence: SectionConfidence` field.

#### 2.2.2 Source Tier Classification

Classify sources into tiers during collection:

| Tier | Source Type | Weight |
|------|-----------|--------|
| 1 (Primary) | Government statistics, SEC/Bundesanzeiger filings, company disclosures | Highest |
| 2 (Secondary) | Industry reports (Statista, IBISWorld), analyst reports | High |
| 3 (Tertiary) | News articles, press releases, blog posts | Medium |
| 4 (Derived) | AI inference, estimates (prefixed with ~) | Lowest |

Add to the merge step prompt: classify each source URL by tier and include tier in output.

#### 2.2.3 Triangulation Enforcement

Strengthen the merge prompt to require:
- Key figures (TAM, CAGR, market shares) must be supported by 2+ independent sources
- If only 1 source available, prefix with `~` and note "single-source estimate"
- Conflicting sources should be noted with the range

---

## Workstream 3: Company Sourcing Feature — "Find Similar Companies"

### 3.1 Concept

**User flow:**
1. User receives an IM → creates a one-pager → market is attractive, investment criteria met
2. User clicks **"Find Similar Companies in DACH"** on the completed one-pager
3. System extracts the "company DNA" (industry, size, business model, geography, products)
4. AI searches for comparable companies across Germany, Austria, Switzerland
5. Results displayed as a comp table with similarity scores and rationale

**This is essentially AI-powered deal sourcing** — using the example company as a seed to map the market for similar acquisition targets.

### 3.2 Data Model

**File:** `backend/models/company_sourcing.py` (new)

```python
class CompanyProfile(BaseModel):
    """A single comparable company."""
    name: str
    hq_city: str
    hq_country: str  # DE, AT, CH
    website: Optional[str] = None
    founded_year: Optional[int] = None
    description: str  # 1-2 sentence description

    # Industry classification
    industry: str
    nace_code: Optional[str] = None
    sub_sector: Optional[str] = None

    # Size & scale
    revenue_eur_m: Optional[float] = None  # EUR millions
    revenue_estimate: bool = False  # True if estimated
    ebitda_eur_m: Optional[float] = None
    ebitda_margin_pct: Optional[float] = None
    employee_count: Optional[int] = None
    employee_estimate: bool = False

    # Business characteristics
    business_model: str  # "B2B Services", "B2B SaaS", "Manufacturing", etc.
    ownership_type: str  # "Family-owned", "PE-backed", "Founder-led", "Public subsidiary"
    customer_segments: list[str] = []
    key_products_services: list[str] = []

    # Similarity assessment
    similarity_score: float  # 0-100
    similarity_rationale: str  # AI-generated explanation
    similarity_dimensions: dict[str, float] = {}  # {"industry": 95, "size": 80, ...}

    # Data quality
    data_sources: list[str] = []
    data_freshness: str = ""  # "2025", "2024", etc.
    confidence: float = 0.0  # 0-1


class CompanySourcingResult(BaseModel):
    """Full result of a company sourcing run."""
    seed_company: str  # The original company name
    seed_industry: str
    seed_revenue_range: str  # e.g., "EUR 10-50M"
    search_region: str  # "DACH"
    search_criteria: dict  # What was used to search

    companies: list[CompanyProfile]  # 10-20 comparable companies

    # Summary statistics
    summary: CompSummaryStats


class CompSummaryStats(BaseModel):
    """Aggregate statistics across all comparable companies."""
    count: int
    avg_revenue_eur_m: Optional[float] = None
    median_revenue_eur_m: Optional[float] = None
    avg_ebitda_margin: Optional[float] = None
    avg_employees: Optional[int] = None
    country_distribution: dict[str, int] = {}  # {"DE": 12, "AT": 4, "CH": 3}
    ownership_distribution: dict[str, int] = {}
```

### 3.3 Pipeline Architecture

**4-Step Pipeline** (SSE-streamed, similar to market research):

```
Step 1: Extract Company DNA
  ├─ Model: Claude Opus 4 (local, no web)
  ├─ Input: OnePagerData from the completed one-pager
  ├─ Output: Structured search criteria
  │   - Industry / NACE codes
  │   - Revenue range (±50% of seed)
  │   - Employee range
  │   - Business model type
  │   - Key product/service categories
  │   - Geographic focus within DACH
  └─ Duration: ~5s

Step 2: Search for Comparable Companies (parallel x3)
  ├─ Model: Claude Opus 4 (Anthropic, web search enabled)
  ├─ 3 parallel searches:
  │   ├─ Search A: Germany (DE) — find 8-10 companies
  │   ├─ Search B: Austria (AT) — find 4-6 companies
  │   └─ Search C: Switzerland (CH) — find 4-6 companies
  ├─ Each search uses Company DNA as context
  ├─ Prompt: "Find real companies matching these criteria.
  │   For each, provide name, HQ, website, revenue/employee estimates,
  │   ownership type, and business description.
  │   NEVER invent companies — only return real, verifiable companies."
  └─ Duration: ~30-60s

Step 3: Verify & Enrich (parallel per company)
  ├─ Model: GPT-4.1 (cross-verification)
  ├─ For each company found in Step 2:
  │   ├─ Verify the company exists (cross-reference)
  │   ├─ Enrich with additional data points
  │   ├─ Calculate similarity score (0-100) vs. seed
  │   └─ Generate similarity rationale
  ├─ Remove any company that can't be verified
  └─ Duration: ~20-40s

Step 4: Rank & Synthesize
  ├─ Model: Claude Opus 4
  ├─ Sort by similarity score
  ├─ Generate summary statistics
  ├─ Produce executive summary of the comp landscape
  └─ Duration: ~10s
```

### 3.4 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/jobs/{id}/source-companies` | Start company sourcing from a completed one-pager (SSE) |
| `GET` | `/api/jobs/{id}/sourcing-results` | Get sourcing results |
| `PUT` | `/api/jobs/{id}/sourcing-results` | Save edited sourcing results |
| `POST` | `/api/jobs/{id}/generate-comp-table` | Export comp table as PPTX/Excel |

### 3.5 Database Changes

Add columns to `jobs` table:

```sql
ALTER TABLE jobs ADD COLUMN sourcing_data TEXT;      -- CompanySourcingResult JSON
ALTER TABLE jobs ADD COLUMN edited_sourcing_data TEXT; -- User-edited version
```

### 3.6 Frontend Design

#### Trigger Point

On the **company editor page** (`/editor/[id]`), when status is "completed":
- New button in the sticky bottom bar: **"Find Similar Companies in DACH"**
- Only enabled when one-pager has enough data (industry, revenue known)

#### Company Sourcing Results Page

**New page:** `/editor/[id]/sourcing`

```
┌─────────────────────────────────────────────────────────────┐
│  Company Sourcing: [Seed Company Name]                      │
│  Industry: [X] | Revenue: EUR [Y]M | Region: DACH          │
│                                                              │
│  ┌─── SSE Progress Stepper (reuse DeepResearchProgress) ───┐│
│  │ Step 1: Extract Company DNA          ✓ Done (3s)         ││
│  │ Step 2: Search DACH Companies        ✓ Done (45s)        ││
│  │ Step 3: Verify & Enrich              ⟳ Running...        ││
│  │ Step 4: Rank & Synthesize            ○ Pending           ││
│  └──────────────────────────────────────────────────────────┘│
│                                                              │
│  ┌─── Comp Table ───────────────────────────────────────────┐│
│  │ ☑ │ Company  │ Country│Revenue│EBITDA│Margin│Empl│Score  ││
│  │───│──────────│────────│───────│──────│──────│────│───────││
│  │ ☑ │ CompA    │ DE     │ 45M   │ 9M   │ 20%  │320 │ 92%   ││
│  │ ☑ │ CompB    │ AT     │ 38M   │ 7M   │ 18%  │280 │ 87%   ││
│  │ ☐ │ CompC    │ CH     │ 52M   │ 8M   │ 15%  │410 │ 71%   ││
│  │───│──────────│────────│───────│──────│──────│────│───────││
│  │   │ Mean     │        │ 45M   │ 8M   │ 18%  │337 │       ││
│  │   │ Median   │        │ 45M   │ 8M   │ 18%  │320 │       ││
│  └──────────────────────────────────────────────────────────┘│
│                                                              │
│  ┌─── Expandable Company Cards ─────────────────────────────┐│
│  │ ▸ CompA GmbH (92% match)                                ││
│  │   Munich, Germany | Family-owned | B2B Services          ││
│  │   "Leading provider of dental lab equipment..."          ││
│  │   Similarity: Industry 95% | Size 88% | Model 93%       ││
│  │   Sources: handelsregister.de, company website           ││
│  │                                                           ││
│  │ ▸ CompB AG (87% match)                                   ││
│  │   Vienna, Austria | Founder-led | Manufacturing          ││
│  │   ...                                                     ││
│  └──────────────────────────────────────────────────────────┘│
│                                                              │
│  [Export PPTX]  [Export Excel]  [Back to One-Pager]         │
└─────────────────────────────────────────────────────────────┘
```

#### Key UI Features

- **Checkboxes** to include/exclude companies from the comp table
- **Inline editing** of company data (same auto-save pattern)
- **Expandable cards** showing full details + similarity breakdown
- **Mean/Median row** auto-calculated from selected companies
- **Export options:** PPTX (1-2 slide comp table) and Excel (for modeling)
- **Reuse `DeepResearchProgress`** component for the 4-step pipeline

### 3.7 Prompts

**4 new prompt templates** added to `prompt_manager.py`:

| Prompt | Description |
|--------|-------------|
| `sourcing_extract_dna` | Extract searchable criteria from OnePagerData |
| `sourcing_search_companies` | Find real companies in a specific country matching criteria |
| `sourcing_verify_enrich` | Cross-verify company existence and enrich data |
| `sourcing_rank_synthesize` | Rank by similarity and generate summary |

**Critical anti-hallucination rules for sourcing:**
- "NEVER invent company names. Only return companies that verifiably exist."
- "If you cannot find enough real companies, return fewer rather than fabricating entries."
- "For each company, provide at least one verifiable data point (website, Handelsregister entry, news mention)."
- "Clearly mark all estimated figures with `~` prefix."

### 3.8 PPTX Export

**2 slides added to existing one-pager or standalone:**

| Slide | Content |
|-------|---------|
| Comp Table | Selected companies in tabular format with key metrics |
| Comp Map | Country distribution + ownership breakdown + similarity chart |

---

## Implementation Order

### Phase 1: Documentation & Fixes (Day 1)

1. Create `docs/` directory with:
   - `docs/KNOWN_ISSUES.md` — All issues from security review
   - `docs/ARCHITECTURE.md` — System architecture reference
   - `docs/BEST_PRACTICES.md` — AI market research best practices audit

2. Fix remaining security issues:
   - S4: SQL column name allowlist in `job_store.py`
   - S8: Per-job locks in `market_research.py` and `deep_research.py`
   - S10: URL validation in `DeepResearchResults.tsx`
   - S12: Filename sanitization in `market-editor/[id]/page.tsx`

3. Commit and push all fixes

### Phase 2: Best Practices Improvements (Day 2)

4. Add per-section confidence scores to `MarketStudyData`
5. Add source tier classification to merge prompts
6. Strengthen triangulation enforcement in merge prompts
7. Re-run verification to confirm adherence

### Phase 3: Company Sourcing Feature (Days 3-5)

8. Create data model (`models/company_sourcing.py`)
9. Add DB columns (`sourcing_data`, `edited_sourcing_data`)
10. Create sourcing pipeline (`services/company_sourcing.py`)
11. Add prompts to `prompt_manager.py`
12. Create API endpoints (`routers/company_sourcing.py` or extend `jobs.py`)
13. Build frontend sourcing results page
14. Add comp table export (PPTX + Excel)
15. Integration testing

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| AI invents fake companies | 3-layer verification: web search → cross-model verify → human review. Require verifiable data points. |
| Stale/inaccurate financial data | Mark all estimates clearly. Show data freshness. Let analyst edit inline. |
| Too few results for niche markets | Fall back to broader search (EU-wide, adjacent industries). Show why results are limited. |
| API cost per sourcing run | ~4 API calls total (cheaper than market research). Cache results per job. |
| Prompt injection via seed company data | Seed data comes from our own OnePagerData (already validated). No raw user input in sourcing prompts. |
