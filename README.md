# SAPA RAG — Chacal Bot

Pipeline RAG + extraction Excel structurée pour catalogues techniques de menuiserie aluminium SAPA (Performance 70 GTI/GTI+, et catalogues à structure équivalente à venir).

```
PDF (480 p)
   │
   ├─▶ Docling 2.x        layout-aware parsing + tables structurées (cellules)
   │     + PyMuPDF        rasterization PNG 200 DPI · TOC · counters
   │
   ├─▶ Classifier         11 PageType (text / table / coupe / plan_debit / …)
   │
   ├─▶ VLM Claude Sonnet  extractions strictes via tool-use (Pydantic schemas)
   │   - Profile / Performance / Vitrage / Coupe / PlanDebit
   │   - tenacity retry · diskcache idempotent
   │
   ├─▶ Excel 14 onglets   stats, codes, profilés, perf thermiques,
   │                      vitrage, coupes, plans débits, mentions, etc.
   │
   └─▶ RAG Qdrant         dense e5-large + sparse BM25, RRF fusion
         + Q&A streaming  Anthropic SSE, multimodal (images coupes), citations
                          obligatoires (page + section)
```

## Stack

- **Python 3.11** — `pymupdf`, `docling`, `pdfplumber`, `anthropic`, `qdrant-client`, `fastembed`, `pydantic`, `fastapi`, `uvicorn`, `polars`, `openpyxl`, `tenacity`, `diskcache`, `structlog`, `typer`
- **TypeScript / React 18 (Vite)** — `react-markdown`, `remark-gfm`
- **Modèles** — `intfloat/multilingual-e5-large` (1024-dim, FR fort), `Qdrant/bm25` (sparse multilingue), Claude Sonnet 4.5 multimodal

## Lancement rapide

```powershell
# 1. config
copy .env.example .env
# édite .env → ANTHROPIC_API_KEY=sk-ant-...

# 2. install
pip install -r requirements.txt
cd frontend; npm install; cd ..

# 3. (1ʳᵉ fois seulement) construire l'index
python scripts\run_phase01.py
python -m sapa_rag.cli vlm        # extraction VLM tous types
python -m sapa_rag.cli chunk      # chunks.jsonl
python -m sapa_rag.cli index      # Qdrant local

# 4. lancer l'app
.\start.ps1                       # backend + frontend en 1 commande
# → http://localhost:5173
```

Stop : `.\stop.ps1`

## Structure

```
src/sapa_rag/
├─ ingest/                  pdf_loader, docling_parser, classify, codes, sections, rasterize
├─ vlm/                     extractor (Claude SDK), schemas (Pydantic strict)
├─ rag/                     chunker adaptatif, index Qdrant, qa (hybrid + LLM)
├─ excel/                   exporter multi-onglets
├─ api/                     FastAPI (chat, chat/stream SSE, conversations, pages)
├─ cli.py                   Typer CLI
├─ config.py · cache.py · logging_setup.py · models.py
frontend/
├─ src/components/          Sidebar, TopBar, Composer, Messages (markdown), Tweaks, ...
├─ src/api/client.ts        fetch + SSE streaming
├─ src/hooks/               useTweaks (theme/accent/density)
└─ src/styles.css           thème slate/midnight/warm
docs/
└─ architecture.html · architecture.mmd
```

## CLI

| commande | effet |
|---|---|
| `python -m sapa_rag.cli classify` | Classe les 480 pages, dump `pages_manifest.json` |
| `python -m sapa_rag.cli excel` | Génère `catalog_perf70_gti_v3.xlsx` |
| `python -m sapa_rag.cli vlm [--types …]` | Lance VLM par page-type (Sonnet vision) |
| `python -m sapa_rag.cli chunk` | Construit `chunks.jsonl` |
| `python -m sapa_rag.cli index` | Indexe dans Qdrant local |
| `python -m sapa_rag.cli ask "Question?"` | Q&A one-shot CLI |
| `python -m sapa_rag.cli all` | Pipeline complet |

## Données / artefacts

Aucun PDF source, aucun Excel généré, aucun cache, aucun index Qdrant n'est versionné — voir `.gitignore`. Pour reconstruire à partir de zéro après clone : voir « Lancement rapide » étape 3.
