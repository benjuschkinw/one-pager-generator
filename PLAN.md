# Plan: Market Research Feature — Gesamtmarktrecherche

## Überblick

Neues Feature: **Standalone-Marktrecherche** für Gesamtmärkte (nicht firmenbezogen).
Der User gibt einen **Markt/Branche** ein (z.B. "Dental-Labore DACH", "Schlüsseldienste Deutschland"), beantwortet **4 Scoping-Fragen** und bekommt eine strukturierte Marktstudie als JSON + PPTX (10 Folien).

Das Feature wird **parallel** zum bestehenden Company-One-Pager gebaut — gleiche Infrastruktur (Jobs, SSE, Deep Research Pipeline, Anti-Halluzination), aber eigenes Datenmodell und eigene Prompts.

---

## Architektur-Übersicht

```
┌──────────────────────────────────────────────────────┐
│  Frontend (Next.js)                                  │
│                                                      │
│  page.tsx ──→ [Markt/Branche] ──→ [Scoping-Form]    │
│                                      │               │
│              MarketScopingForm ◄─────┘               │
│              (4 Dimensionen)                         │
│                     │                                │
│                     ▼                                │
│  market-editor/[id]/page.tsx                         │
│  ├── 10 Section Cards (2-Spalten Grid)               │
│  ├── Auto-Save (500ms debounce)                      │
│  ├── JSON Export                                     │
│  └── PPTX Generation                                │
└──────────────────────┬───────────────────────────────┘
                       │ SSE / REST
┌──────────────────────▼───────────────────────────────┐
│  Backend (FastAPI)                                   │
│                                                      │
│  POST /api/market-research                           │
│  ├── Input Validation (max lengths, region allowlist)│
│  ├── Scoping Sanitization (key whitelist, length cap)│
│  └── 8-Step Pipeline (SSE streaming)                 │
│       ├── Steps 1-3: parallel (sizing, seg, comp)    │
│       ├── Steps 4-6: parallel (trends, porter, B&B)  │
│       ├── Step 7: merge (Claude Opus 4)              │
│       └── Step 8: verify (GPT-4.1)                   │
│                                                      │
│  PUT /api/jobs/{id}/market-data                      │
│  POST /api/jobs/{id}/generate-market → PPTX (10 Sl.) │
└──────────────────────────────────────────────────────┘
```

---

## 0. Scoping-Fragebogen (Intake)

**Vor** Beginn der Recherche stellt das System gezielte Fragen zu 4 Dimensionen, um Halluzinationen und zu generische Antworten zu vermeiden:

| # | Dimension | Felder | Beispiel |
|---|-----------|--------|----------|
| 1 | **Produkt-Scope** | Freitext (Inklusionen/Exklusionen) + Wertschöpfungsstufe (Dropdown) | "Nur alkoholfreie Getränke, ohne Wasser" / "Gesamte Kette" |
| 2 | **Geografie & Zeit** | Freitext (geografische Eingrenzung) + Zeithorizont (Dropdown) | "nur urbane Gebiete" / "Historisch 5J + Prognose 5J" |
| 3 | **Zielgruppe** | B2B/B2C/B2B2C/B2G (Dropdown) + Freitext Kundenmerkmale | "B2B" / "KMU mit 10-250 MA" |
| 4 | **Strategischer Kontext** | Maßeinheit (Umsatz/Menge/Kunden) + Studienzweck (Dropdown) | "Umsatzwert" / "Buy & Build Thesis validieren" |

**Sicherheit:** Scoping-Werte werden server-seitig sanitisiert:
- Key-Whitelist (nur die 8 bekannten Felder)
- Max. 500 Zeichen pro Feld, 10 KB gesamt
- Markdown-/Code-Block-Injection wird gefiltert

Die Antworten werden als `## SCOPING CONTEXT` Block in jeden Pipeline-Prompt injiziert.

---

## 1. Backend: Datenmodell `MarketStudyData`

**Datei: `backend/models/market_study.py`**

11 Pydantic-Modelle, die 1:1 auf die 10 PPTX-Folien mappen:

| Modell | Folie | Beschreibung |
|--------|-------|-------------|
| `MarketStudyMeta` | — | Metadaten (Name, Region, Datum) |
| `ExecutiveSummary` | 1 | Action Title + Key Findings + Verdict |
| `MarketSizing` | 2 | TAM/SAM/SOM + CAGR + Annahmen |
| `MarketSegment[]` | 3 | Segmente mit Größe, Anteil, Wachstum |
| `CompetitiveLandscape` | 4 | Fragmentierung + Top Players + HHI |
| `TrendsDrivers` | 5 | Treiber, Headwinds, Tech, Regulatorik |
| `PestelAnalysis` | 6 | 6 Dimensionen mit Rating + Points |
| `PortersFiveForces` | 7 | 5 Forces mit Rating + Erklärung |
| `ValueChain` | 8 | Stages + Business Models + Margen |
| `BuyAndBuild` | 9 | Fragmentierung (1-10) + Kandidaten |
| `StrategicImplications` | 10 | Empfehlungen + Risiken + Attraktivität |

---

## 2. Backend: 8-Step Research Pipeline

**Datei: `backend/services/market_research.py`**

| Step | Name | Modell | Beschreibung |
|------|------|--------|-------------|
| 1 | `market_sizing` | Anthropic (Web Search) | TAM/SAM/SOM, CAGR mit Quellen |
| 2 | `segmentation` | Anthropic (Web Search) | Marktsegmente, Anteile, Wachstum |
| 3 | `competition` | Anthropic (Web Search) | Top-5 Player, HHI, Konsolidierung |
| 4 | `trends_pestel` | Gemini 2.5 Pro | Trends, Treiber, PESTEL-Analyse |
| 5 | `porters_value_chain` | Anthropic (Web Search) | Five Forces + Wertschöpfungskette |
| 6 | `buy_and_build` | Anthropic (Web Search) | Fragmentierung, Plattform-Kandidaten |
| 7 | `merge` | Claude Opus 4 | Merge zu vollständigem MarketStudyData |
| 8 | `verify_final` | GPT-4.1 | Cross-Verification |

- Steps 1-3 parallel, Steps 4-6 parallel (nach 1-3)
- Jeder Step (1-6): Per-Step Recheck von anderem Modell
- Scoping-Kontext wird in jeden Step-Prompt injiziert
- SSE-Streaming für Echtzeit-Frontend-Updates

---

## 3. Backend: Prompts

**Datei: `backend/services/prompt_manager.py`** — 9 neue Templates:

- `market_sizing` / `market_segmentation` / `market_competition`
- `market_trends_pestel` / `market_porters` / `market_buy_and_build`
- `market_merge` / `market_verify` / `market_step_recheck`

Alle: Anti-Halluzination, DACH-Fokus, Quellenpflicht, ~Prefix für Schätzungen, JSON-Output.

---

## 4. Backend: API-Routen

| Method | Path | Beschreibung |
|--------|------|-------------|
| `POST` | `/api/market-research` | Job erstellen + SSE Pipeline starten. Akzeptiert: `market_name`, `region`, `scoping_context` (JSON) |
| `PUT` | `/api/jobs/{id}/market-data` | Editierte MarketStudyData speichern |
| `POST` | `/api/jobs/{id}/generate-market` | PPTX-Export (10 Folien) |

**Input Validation:**
- `market_name`: max 200 Zeichen
- `region`: Allowlist (`DACH`, `Germany`, `Europe`, `Global`)
- `scoping_context`: max 10 KB, Key-Whitelist, max 500 Zeichen pro Feld

---

## 5. Backend: PPTX-Generator

**Datei: `backend/services/market_pptx_generator.py`** — 10 Folien:

| Folie | Inhalt | Visualisierung |
|-------|--------|---------------|
| 1 | Executive Summary | Titel + Key Findings Bullets |
| 2 | Market Sizing | TAM/SAM/SOM Tabelle + CAGR |
| 3 | Market Segmentation | Segment-Tabelle mit Anteilen |
| 4 | Competitive Landscape | Benchmarking-Matrix (Top 5) |
| 5 | Trends & Drivers | 2-Spalten: Treiber vs. Headwinds |
| 6 | PESTEL Analysis | 6er-Grid (P/E/S/T/E/L) mit Farbcodierung |
| 7 | Porter's Five Forces | 5-Kräfte mit Farbcodierung (high=rot, low=grün) |
| 8 | Value Chain | Stages + Business Models |
| 9 | Buy & Build | Fragmentierung (X/10) + Kandidaten |
| 10 | Strategic Implications | Priorisierte Empfehlungen |

---

## 6. Frontend: Marktstudie-Flow

### Startseite (`page.tsx`)
- Tab-Toggle: **"Company One-Pager"** | **"Marktstudie"**
- Markt-Modus: Marktname + Region → **"Weiter: Scoping"** → Scoping-Form → **"Analyse starten"**
- UI-Sprache: Deutsch (DACH-Zielgruppe)

### Scoping-Form (`MarketScopingForm.tsx`)
- 4 nummerierte Dimensionen mit Dropdowns + Freitext
- Back-Button zum Marktname-Schritt
- Submit startet SSE-Pipeline und leitet zu Editor weiter

### Market Editor (`market-editor/[id]/page.tsx`)
- 10 Section Cards im 2-Spalten-Grid
- Deep Merge beim Laden (Nested-Defaults werden erhalten)
- Auto-Save mit 500ms Debounce
- JSON-Export + PPTX-Generation (Sticky Bottom Bar)

### 10 Section-Editor-Komponenten (`components/market/`)
- `ExecutiveSummarySection` / `MarketSizingSection` / `SegmentationSection`
- `CompetitiveLandscapeSection` / `TrendsSection` / `PestelSection`
- `PortersSection` / `ValueChainSection` / `BuyAndBuildSection`
- `StrategicImplicationsSection`
- Shared: `MarketSectionCard` (Wrapper), `MarketBulletEditor` (Bullet-Liste)

---

## 7. QA / UX / Security (Review-Ergebnisse)

### Behobene Issues:

| Bereich | Issue | Fix |
|---------|-------|-----|
| **QA** | Double `onComplete` in SSE handler | Completion-Flag verhindert doppelten Aufruf |
| **QA** | Shallow Merge verliert Nested-Defaults | Deep Merge für alle Objekt-Felder |
| **QA** | CAGR-Input reformatiert bei jedem Keystroke | `type="number"` mit Label "(%)"|
| **QA** | `fragmentation_score` 0-1 vs 1-10 Mismatch | Einheitlich 1-10, PPTX zeigt "X/10" |
| **UX** | Gemischte Sprachen DE/EN | Marktstudie-UI durchgängig auf Deutsch |
| **UX** | Fehlende aria-labels auf Icon-Buttons | Alle Icon-Buttons haben `aria-label` |
| **Security** | Keine Input-Validierung (Länge, Region) | Max-Lengths, Region-Allowlist |
| **Security** | Prompt Injection via Scoping | Key-Whitelist, Längen-Cap, Markdown-Filter |
| **Security** | Kein Scoping-Sanitizing | `_sanitize_scoping()` mit Whitelist + Truncation |

---

## Abgrenzung

| | Company One-Pager | Marktstudie |
|---|---|---|
| **Input** | Firmenname + optional IM PDF | Marktname + Region + Scoping |
| **Output-Schema** | `OnePagerData` | `MarketStudyData` |
| **Pipeline** | 7 Steps (firmenbezogen) | 8 Steps (marktbezogen) |
| **PPTX** | 1 Folie (One-Pager) | 10 Folien (Marktstudie) |
| **Zielgruppe** | Investment Committee | Strategy / Deal-Screening |
| **research_mode** | `"standard"` / `"deep"` | `"market"` |

**Shared:** Jobs, SSE-Streaming, Anti-Halluzination, Prompt-Editor, Job-History, Model-Config.
