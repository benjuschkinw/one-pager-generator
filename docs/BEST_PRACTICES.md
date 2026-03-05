# AI Market Research Best Practices Audit

**Date:** 2026-03-05
**Context:** M&A / Private Equity market research and company research

---

## Industry Landscape (2025-2026)

- 86% of organizations have integrated GenAI into M&A workflows (Deloitte 2025)
- 83% investing $1M+ specifically for M&A AI tools
- McKinsey reports ~20% cost reduction and 30-50% faster deal cycles from GenAI
- AlphaSense (acquired Tegus for $930M) sets the benchmark with sentence-level citations
- DiligenceSquared (YC-backed) delivers AI due diligence comparable to $500K-$1M consulting reports

---

## Best Practice Audit

### Multi-Model Orchestration

| Best Practice | Our Status | Notes |
|--------------|-----------|-------|
| Use specialized models per task | **Implemented** | Claude (web search), Gemini (market), GPT-4.1 (verification) |
| Plan-and-Execute pattern | **Implemented** | Steps decomposed, parallel execution, merge/verify |
| Heterogeneous model routing | **Implemented** | Frontier models for reasoning, cross-model for verification |
| Cost optimization via model selection | **Partial** | Could use smaller models for simpler extraction tasks |

### Anti-Hallucination

| Best Practice | Our Status | Notes |
|--------------|-----------|-------|
| Prompt-level guards ("never invent") | **Implemented** | Every prompt includes anti-hallucination text |
| Per-step cross-model recheck | **Implemented** | Different model family rechecks each step |
| Final cross-verification | **Implemented** | Algorithmic + AI cross-verification |
| Source triangulation (3+ sources for key claims) | **Partial** | Guidance added to prompts; not yet enforced programmatically |
| Sentence-level citations | **Not implemented** | Currently collect URLs per step, not per claim |
| Grounding in curated content | **Not applicable** | We use web search (broader but less controlled) |

### Source Attribution & Data Quality

| Best Practice | Our Status | Notes |
|--------------|-----------|-------|
| Source URLs collected per step | **Implemented** | Web search results tracked |
| Source tier classification (primary/secondary/tertiary) | **Not implemented** | Planned: classify in merge step |
| Per-section confidence scores | **Not implemented** | Planned: add to MarketStudyData |
| Data freshness tracking | **Partial** | Timestamps on steps, not on individual data points |
| "Estimated" vs "reported" flags | **Implemented** | `~` prefix convention in prompts |

### Verification & QA

| Best Practice | Our Status | Notes |
|--------------|-----------|-------|
| Automated fact-checking (AI verifies AI) | **Implemented** | Per-step recheck + final verification |
| Consistency checks (revenue sums, margins) | **Implemented** | Algorithmic verification |
| Human-in-the-loop (inline editing) | **Implemented** | Auto-save editor with manual override |
| Confidence scoring | **Partial** | Overall confidence; need per-section |
| Audit trail (full traceability) | **Implemented** | Per-step results saved with model, duration, sources |

### Input Quality

| Best Practice | Our Status | Notes |
|--------------|-----------|-------|
| Scoping questionnaire before research | **Implemented** | 4-dimension intake form |
| Input sanitization | **Implemented** | Key whitelist, length caps, markdown filter |
| Structured region selection | **Implemented** | Allowlist: DACH, Germany, Europe, Global |

---

## Planned Improvements

### 1. Per-Section Confidence Scores

Add a `SectionConfidence` model to each section of `MarketStudyData`:
- Score (0-1), source count, source tier, notes
- Populated by the merge step based on source quality and corroboration

### 2. Source Tier Classification

During the merge step, classify each source URL:
- Tier 1: Government statistics, official filings (Bundesanzeiger, Destatis)
- Tier 2: Industry reports (Statista, IBISWorld, analyst reports)
- Tier 3: News articles, press releases
- Tier 4: AI inference / estimates

### 3. Triangulation Enforcement

Strengthen merge prompts:
- Key figures (TAM, CAGR, market shares) must cite 2+ independent sources
- Single-source estimates must be flagged with `~` and noted
- Conflicting sources should present the range, not a single number

### 4. Company Sourcing Feature

New pipeline: given a seed company from a completed one-pager, find 10-20 comparable companies across DACH using web search + cross-verification. See `PLAN.md` for full design.

---

## References

- Deloitte 2025 M&A Generative AI Study
- McKinsey: Gen AI in M&A — From Theory to Practice
- AlphaSense Deep Research (agentic AI on 500M+ curated documents)
- DiligenceSquared (YC-backed AI due diligence)
- Company2Vec (arXiv:2307.09332) — embeddings from German corporate websites
- ICC/ESOMAR 2025 Code — human oversight requirements for AI research
- ISO 42001 — AI Management System standard
