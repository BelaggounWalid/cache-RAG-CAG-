# ============================================================
#  CHACAL BOT — One-shot launcher (backend + frontend)
#  Usage from PowerShell at repo root :
#    .\start.ps1
#  Stop : Ctrl+C dans chaque fenêtre, OU `.\stop.ps1`
# ============================================================

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host ""
Write-Host "  CHACAL BOT — démarrage" -ForegroundColor Cyan
Write-Host "  ----------------------" -ForegroundColor Cyan
Write-Host ""

# 1. Sanity checks ------------------------------------------------
if (-not (Test-Path ".env")) {
    Write-Host "  ⚠ .env manquant — copie .env.example en .env et mets ta clé." -ForegroundColor Yellow
    exit 1
}
if (-not (Test-Path "data\output\qdrant_local")) {
    Write-Host "  ⚠ Qdrant pas indexé — lance d'abord :" -ForegroundColor Yellow
    Write-Host "       python scripts\run_phase01.py" -ForegroundColor Yellow
    Write-Host "       python -m sapa_rag.cli vlm" -ForegroundColor Yellow
    Write-Host "       python -m sapa_rag.cli chunk" -ForegroundColor Yellow
    Write-Host "       python -m sapa_rag.cli index" -ForegroundColor Yellow
    exit 1
}
if (-not (Test-Path "frontend\node_modules")) {
    Write-Host "  → npm install (premier lancement)" -ForegroundColor Yellow
    Push-Location frontend
    npm install
    Pop-Location
}

# 2. Backend FastAPI -----------------------------------------------
Write-Host "  → Backend FastAPI sur http://localhost:8000" -ForegroundColor Green
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$root'; `$env:PYTHONIOENCODING='utf-8'; `$env:PYTHONPATH='src'; python scripts\run_api.py"
) -WindowStyle Normal

# 3. Frontend Vite -------------------------------------------------
Write-Host "  → Frontend Vite sur http://localhost:5173" -ForegroundColor Green
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$root\frontend'; npm run dev"
) -WindowStyle Normal

Start-Sleep -Seconds 3
Write-Host ""
Write-Host "  ✓ Lancé. Ouvre :  http://localhost:5173" -ForegroundColor Cyan
Write-Host "  ✓ Backend warmup ~25s avant la première requête." -ForegroundColor DarkGray
Write-Host ""
