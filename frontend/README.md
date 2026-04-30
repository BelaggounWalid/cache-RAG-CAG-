# Chacal Bot — Frontend

React + TypeScript + Vite. Reprise 1:1 du design `design/` câblé sur le backend FastAPI (`src/sapa_rag/api`).

## Lancement (dev)

Depuis la racine du projet :

```bash
# Backend FastAPI (port 8000)
PYTHONIOENCODING=utf-8 PYTHONPATH=src python scripts/run_api.py

# Frontend Vite (port 5173) — dans un autre terminal
cd frontend && npm install && npm run dev
```

Ou tout en un coup :

```bash
# Linux/macOS/Git Bash
bash scripts/dev.sh

# Windows PowerShell
./scripts/dev.ps1
```

Le proxy Vite envoie automatiquement `/api/*` vers `http://localhost:8000`, donc rien à configurer côté CORS pour le dev.

## Build prod

```bash
cd frontend
npm run build
# le bundle est dans frontend/dist/ — peut être servi par n'importe quel static server
```

## Endpoints API consommés

| Méthode | Route | Usage |
|---|---|---|
| GET  | `/api/health` | sanity |
| GET  | `/api/index/status` | bandeau statut topbar / empty state |
| GET  | `/api/conversations` | sidebar liste |
| POST | `/api/conversations` | bouton "Nouvelle conversation" |
| GET  | `/api/conversations/{id}` | charge une conversation |
| DELETE | `/api/conversations/{id}` | corbeille dans sidebar |
| POST | `/api/chat` | mode non-streamé (fallback) |
| POST | `/api/chat/stream` | SSE — `step` puis `delta` puis `done` |
| GET  | `/api/pages/{n}` | image PNG d'une page (cliquée depuis une citation) |
| POST | `/api/feedback` | thumbs up/down sous une réponse bot |

## Personnalisation

- **Tweaks panel** (FAB en bas à droite) : thème (slate / midnight / warm), accent (teal / indigo / amber / lime / orange), densité (compact / cozy / roomy), nom utilisateur / bot.
- Persiste en `localStorage` clé `chacal.tweaks.v1`.
