# M&A One-Pager Generator

AI-powered web app that generates Constellation Capital AG One-Pager PPTX slides from company research.

## Architecture

```
Frontend (Next.js)     →  Backend (FastAPI)  →  Claude API (research)
     ↓                         ↓                     ↓
Review & Edit UI         PPTX Generator        Web Search + PDF Extract
                              ↓
                      python-pptx + matplotlib
                              ↓
                         Download .pptx
```

## Quick Start

### Backend

```bash
cd backend
pip install -r requirements.txt
ANTHROPIC_API_KEY=sk-ant-... uvicorn main:app --port 8000 --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3001 — the frontend proxies API calls to the backend at :8000.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/research` | AI company research (multipart: `company_name` + optional `im_file` PDF) |
| `POST` | `/api/generate` | Generate PPTX from JSON data |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes (for /research) | Claude API key |

## Project Structure

```
one-pager-generator/
├── frontend/              # Next.js + Tailwind UI
│   ├── src/app/           # Pages (input + editor)
│   ├── src/app/components/# Form components
│   └── src/lib/           # Types + API client
├── backend/               # FastAPI + python-pptx
│   ├── main.py            # App entry point
│   ├── routers/           # API endpoints
│   ├── services/          # Business logic
│   │   ├── ai_research.py     # Claude API + web search
│   │   ├── chart_generator.py # matplotlib charts
│   │   ├── pdf_extractor.py   # PDF text extraction
│   │   ├── pptx_generator.py  # PPTX fill + export
│   │   └── template_builder.py# Programmatic template creation
│   ├── models/            # Pydantic schemas
│   └── template/          # Generated PPTX template
└── README.md
```
