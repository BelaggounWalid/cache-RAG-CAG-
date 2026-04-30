#!/usr/bin/env bash
# Lance backend FastAPI (8000) + frontend Vite (5173) en parallèle.
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo ">> backend on http://localhost:8000"
PYTHONIOENCODING=utf-8 PYTHONPATH=src python scripts/run_api.py &
BACK_PID=$!

cleanup() {
  echo ">> shutting down (PID $BACK_PID)"
  kill $BACK_PID 2>/dev/null || true
}
trap cleanup EXIT INT TERM

cd frontend
if [ ! -d node_modules ]; then
  echo ">> installing frontend deps"
  npm install
fi
echo ">> frontend on http://localhost:5173"
npm run dev
