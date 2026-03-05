# Plan: Market Research Feature — Gesamtmarktrecherche

## Überblick

Neues Feature: **Standalone-Marktrecherche** für Gesamtmärkte (nicht firmenbezogen).
Der User gibt einen **Markt/Branche** ein (z.B. "Dental-Labore DACH", "Schlüsseldienste Deutschland") und bekommt eine strukturierte Marktstudie als JSON + PPTX (10 Folien).

Das Feature wird **parallel** zum bestehenden Company-One-Pager gebaut — gleiche Infrastruktur (Jobs, SSE, Deep Research Pipeline, Anti-Halluzination), aber eigenes Datenmodell und eigene Prompts.

---

## 1. Backend: Neues Datenmodell `MarketStudyData`

**Neue Datei: `backend/models/market_study.py`**

```python
class MarketStudyMeta(BaseModel):
    market_name: str = ""
    region: str = "DACH"
    research_date: str = ""
    sources: list[str] = []

class ExecutiveSummary(BaseModel):
    title: str = ""                    # Action Title, z.B. "Dental-Labore: Konsolidierung treibt Margen"
    key_findings: list[str] = []       # 3-5 Kernerkenntnisse
    market_verdict: str = ""           # Gesamtbewertung (1-2 Sätze)

class MarketSizing(BaseModel):
    tam: str = ""                      # "EUR X.Xbn"
    tam_year: str = ""
    sam: str = ""
    sam_year: str = ""
    som: str = ""
    cagr: float | None = None          # z.B. 0.068 = 6.8%
    cagr_period: str = ""              # "2025-2033"
    methodology: str = ""              # "Top-Down" / "Bottom-Up"
    assumptions: list[str] = []
    data_points: list[MarketDataPoint] = []  # Historisch + Prognose

class MarketDataPoint(BaseModel):
    year: str                          # "2023", "2025E", "2030P"
    value: float | None = None         # In Mrd. EUR
    label: str = ""                    # z.B. "TAM Global"

class MarketSegment(BaseModel):
    name: str
    size: str = ""                     # "EUR X.Xm"
    share_pct: float | None = None
    growth_rate: str = ""
    description: str = ""

class CompetitorProfile(BaseModel):
    name: str
    market_share: str = ""
    revenue: str = ""
    hq: str = ""
    strengths: list[str] = []

class CompetitiveLandscape(BaseModel):
    fragmentation: str = "medium"      # "high" / "medium" / "low"
    top_players: list[CompetitorProfile] = []
    hhi_index: float | None = None
    consolidation_trend: str = ""
    avg_company_revenue: str = ""

class TrendsDrivers(BaseModel):
    growth_drivers: list[str] = []
    headwinds: list[str] = []
    technological_shifts: list[str] = []
    regulatory_changes: list[str] = []

class PestelFactor(BaseModel):
    rating: str = "neutral"            # "positive" / "neutral" / "negative"
    points: list[str] = []

class PestelAnalysis(BaseModel):
    political: PestelFactor = PestelFactor()
    economic: PestelFactor = PestelFactor()
    social: PestelFactor = PestelFactor()
    technological: PestelFactor = PestelFactor()
    environmental: PestelFactor = PestelFactor()
    legal: PestelFactor = PestelFactor()

class ForceAssessment(BaseModel):
    rating: str = "medium"             # "low" / "medium" / "high"
    explanation: str = ""

class PortersFiveForces(BaseModel):
    rivalry: ForceAssessment = ForceAssessment()
    buyer_power: ForceAssessment = ForceAssessment()
    supplier_power: ForceAssessment = ForceAssessment()
    threat_new_entrants: ForceAssessment = ForceAssessment()
    threat_substitutes: ForceAssessment = ForceAssessment()

class ValueChainStage(BaseModel):
    name: str
    description: str = ""
    typical_margin: str = ""

class ValueChain(BaseModel):
    stages: list[ValueChainStage] = []
    dominant_business_models: list[str] = []
    margin_distribution: str = ""

class BuyAndBuild(BaseModel):
    fragmentation_score: float | None = None   # 0.0-1.0
    platform_candidates: list[str] = []
    add_on_profile: str = ""
    consolidation_rationale: str = ""
    estimated_targets_dach: str = ""

class StrategicRecommendation(BaseModel):
    title: str                         # Action Title
    description: str = ""
    risk_benefit: str = ""             # "high reward / low risk"

class StrategicImplications(BaseModel):
    recommendations: list[StrategicRecommendation] = []
    investment_attractiveness: str = ""  # "high" / "medium" / "low"
    key_risks: list[str] = []

class MarketStudyData(BaseModel):
    meta: MarketStudyMeta = MarketStudyMeta()
    executive_summary: ExecutiveSummary = ExecutiveSummary()
    market_sizing: MarketSizing = MarketSizing()
    market_segments: list[MarketSegment] = []
    competitive_landscape: CompetitiveLandscape = CompetitiveLandscape()
    trends_drivers: TrendsDrivers = TrendsDrivers()
    pestel: PestelAnalysis = PestelAnalysis()
    porters_five_forces: PortersFiveForces = PortersFiveForces()
    value_chain: ValueChain = ValueChain()
    buy_and_build: BuyAndBuild = BuyAndBuild()
    strategic_implications: StrategicImplications = StrategicImplications()
```

---

## 2. Backend: Market Research Pipeline

**Neue Datei: `backend/services/market_research.py`**

8-Step Pipeline analog zu `deep_research.py`:

| Step | Name | Modell | Beschreibung |
|------|------|--------|-------------|
| 1 | `market_sizing` | Anthropic (Web Search) | TAM/SAM/SOM, CAGR, Marktvolumen mit Quellen |
| 2 | `segmentation` | Anthropic (Web Search) | Marktsegmente, Anteile, Wachstumsraten |
| 3 | `competition` | Anthropic (Web Search) | Top-5 Player, Marktanteile, HHI, Konsolidierung |
| 4 | `trends_pestel` | Gemini 2.5 Pro (OpenRouter) | Trends, Treiber, PESTEL-Analyse |
| 5 | `porters_value_chain` | Anthropic (Web Search) | Porter's Five Forces, Wertschöpfungskette |
| 6 | `buy_and_build` | Anthropic (Web Search) | Fragmentierung, Plattform-Kandidaten, Add-on-Profil |
| 7 | `merge` | Claude Opus 4 (OpenRouter) | Merge aller Sub-Results zu MarketStudyData |
| 8 | `verify_final` | GPT-4.1 (OpenRouter) | Cross-Verification |

- Steps 1-3 parallel, Steps 4-6 parallel (nach 1-3)
- Jeder Step (1-6) bekommt 2nd AI Recheck von anderem Modell
- SSE-Streaming für Echtzeit-Frontend-Updates

---

## 3. Backend: Prompts

**Erweitern: `backend/services/prompt_manager.py`**

10 neue Prompt-Templates:
- `market_sizing_prompt` — TAM/SAM/SOM + CAGR
- `market_segmentation_prompt` — Segmente + Wachstum
- `market_competition_prompt` — Wettbewerbslandschaft
- `market_trends_pestel_prompt` — Trends + PESTEL
- `market_porters_prompt` — Five Forces + Wertschöpfungskette
- `market_buy_and_build_prompt` — Fragmentierung + Konsolidierung
- `market_merge_prompt` — Merge zu MarketStudyData
- `market_verify_prompt` — Final Verification
- `market_step_recheck_prompt` — Per-Step Recheck

Alle Prompts: Anti-Halluzination, DACH-Fokus, Quellenpflicht, ~Prefix für Schätzungen, JSON-Schema.

---

## 4. Backend: Job-Modell erweitern

**Erweitern: `backend/models/job.py`**

```python
class Job(BaseModel):
    # ... bestehende Felder ...
    research_mode: Literal["standard", "deep", "market"] = "standard"  # "market" NEU
    market_study_data: Optional[MarketStudyData] = None                # NEU
    edited_market_data: Optional[MarketStudyData] = None               # NEU
```

**Erweitern: `backend/services/job_store.py`**
- `_JSON_FIELDS` um `"market_study_data"`, `"edited_market_data"` erweitern
- `_row_to_job` parsen
- `save_market_study_data()` hinzufügen

**DB-Migration:** Zwei neue TEXT-Spalten in `jobs` Tabelle.

---

## 5. Backend: API-Routen

**Neue Datei: `backend/routers/market_research.py`**

| Method | Path | Beschreibung |
|--------|------|-------------|
| `POST` | `/api/market-research` | Job erstellen (Form: `market_name`, `region`) + sofort SSE Pipeline starten |

**Erweitern: `backend/routers/jobs.py`**

| Method | Path | Beschreibung |
|--------|------|-------------|
| `PUT` | `/api/jobs/{id}/market-data` | Editierte MarketStudyData speichern |
| `POST` | `/api/jobs/{id}/generate-market` | PPTX-Export (10 Folien) |

**Erweitern: `backend/main.py`**
- Market Research Router mounten

---

## 6. Backend: PPTX-Generator für Marktstudien

**Neue Datei: `backend/services/market_pptx_generator.py`**

10-Folien-PPTX programmatisch erstellt (analog zu `template_builder.py`):

| Folie | Inhalt | Visualisierung |
|-------|--------|---------------|
| 1 | Executive Summary | Titel + Key Findings Bullets |
| 2 | Market Sizing | TAM/SAM/SOM Tabelle + CAGR |
| 3 | Market Segmentation | Segment-Tabelle mit Anteilen |
| 4 | Competitive Landscape | Benchmarking-Matrix (Top 5) |
| 5 | Trends & Drivers | 2-Spalten: Treiber vs. Headwinds |
| 6 | PESTEL Analysis | 6er-Grid (P/E/S/T/E/L) |
| 7 | Porter's Five Forces | 5-Kräfte Bewertung |
| 8 | Value Chain | Stages + Business Models |
| 9 | Buy & Build Potential | Fragmentierung + Kandidaten |
| 10 | Strategic Implications | 3 priorisierte Empfehlungen |

---

## 7. Frontend: Types erweitern

**Erweitern: `frontend/src/lib/types.ts`**

- TypeScript-Interfaces für alle `MarketStudyData` Sub-Modelle
- `EMPTY_MARKET_STUDY` Konstante
- `JobSummary.research_mode`: `"standard" | "deep" | "market"`

---

## 8. Frontend: API-Client erweitern

**Erweitern: `frontend/src/lib/api.ts`**

- `startMarketResearch(marketName, region, onEvent, onComplete, onError)` — SSE Stream
- `saveMarketData(jobId, data)` — PUT
- `generateMarketPptx(jobId)` — POST + Download

---

## 9. Frontend: Startseite erweitern

**Erweitern: `frontend/src/app/page.tsx`**

Tab/Toggle oben: **"Company One-Pager"** | **"Market Study"**

Im Market-Study-Modus:
- Input: Marktname (Pflicht) + Region (Default: DACH)
- Kein PDF-Upload
- Kein Research-Mode-Toggle (Market ist immer Deep)
- Button: "Research Market"
- Redirect zu `/market-editor/{job_id}`

---

## 10. Frontend: Market Editor Page

**Neue Datei: `frontend/src/app/market-editor/[id]/page.tsx`**

- DeepResearchProgress (wiederverwendbar, gleiche SSE-Logik)
- 10 editierbare Section-Cards (eine pro Slide)
- Auto-Save wie beim Company-Editor
- PPTX-Export-Button

---

## 11. Frontend: Market Editor Components

**Neue Dateien in `frontend/src/app/components/market/`:**

- `ExecutiveSummarySection.tsx` — Titel + Key Findings + Verdict
- `MarketSizingSection.tsx` — TAM/SAM/SOM + CAGR Tabelle
- `SegmentationSection.tsx` — Segment-Liste Editor
- `CompetitiveLandscapeSection.tsx` — Player-Tabelle + Fragmentierung
- `TrendsSection.tsx` — Treiber / Headwinds / Tech / Regulatorik
- `PestelSection.tsx` — 6er-Grid mit Rating + Bullets
- `PortersSection.tsx` — 5 Forces mit Rating + Erklärung
- `ValueChainSection.tsx` — Stages + Business Models
- `BuyAndBuildSection.tsx` — Score + Kandidaten + Rationale
- `StrategicImplicationsSection.tsx` — Empfehlungen + Risiken

---

## 12. Config: Market Research Models

**Erweitern: `backend/config/models.py`**

```python
MARKET_RESEARCH_MODELS = {
    "market_sizing": "anthropic",
    "segmentation": "anthropic",
    "competition": "anthropic",
    "trends_pestel": env("MODEL_MARKET_TRENDS", "google/gemini-2.5-pro-preview"),
    "porters_value_chain": "anthropic",
    "buy_and_build": "anthropic",
    "merge": env("MODEL_MARKET_MERGE", "anthropic/claude-opus-4"),
    "verify_final": env("MODEL_MARKET_VERIFY", "openai/gpt-4.1"),
}
```

---

## Implementierungsreihenfolge

### Phase A: Backend Foundation
1. `backend/models/market_study.py` — Datenmodell
2. `backend/models/job.py` erweitern — `research_mode: "market"`, neue Felder
3. `backend/services/job_store.py` erweitern — DB-Schema + JSON-Parsing
4. `backend/config/models.py` erweitern — Market Research Models

### Phase B: Backend Pipeline + Prompts
5. `backend/services/prompt_manager.py` erweitern — 10 neue Prompts
6. `backend/services/market_research.py` — 8-Step Pipeline mit SSE
7. `backend/routers/market_research.py` — API-Endpunkte
8. `backend/main.py` erweitern — Router mounten

### Phase C: Backend PPTX
9. `backend/services/market_pptx_generator.py` — 10-Folien-Generator
10. `backend/routers/jobs.py` erweitern — Market PPTX Endpoint

### Phase D: Frontend
11. `frontend/src/lib/types.ts` erweitern — MarketStudyData Interfaces
12. `frontend/src/lib/api.ts` erweitern — Market API Client
13. `frontend/src/app/page.tsx` erweitern — Tab Company/Market
14. `frontend/src/app/market-editor/[id]/page.tsx` — Market Editor Page
15. `frontend/src/app/components/market/*.tsx` — 10 Section-Editoren

---

## Abgrenzung

| | Company One-Pager | Market Study |
|---|---|---|
| **Input** | Firmenname + optional IM PDF | Marktname + Region |
| **Output-Schema** | `OnePagerData` | `MarketStudyData` |
| **Pipeline** | 7 Steps (firmenbezogen) | 8 Steps (marktbezogen) |
| **PPTX** | 1 Folie (One-Pager) | 10 Folien (Marktstudie) |
| **Zielgruppe** | Investment Committee | Strategy / Deal-Screening |
| **research_mode** | `"standard"` / `"deep"` | `"market"` |

**Shared:** Jobs, SSE-Streaming, Anti-Halluzination, Prompt-Editor, Job-History, Model-Config.
