# Lance backend FastAPI (8000) + frontend Vite (5173) en parallèle. Windows / PowerShell.
$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot

Write-Host ">> backend on http://localhost:8000" -ForegroundColor Cyan
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONPATH = Join-Path $ROOT "src"
$back = Start-Process -PassThru -NoNewWindow `
  -FilePath python -ArgumentList "$($ROOT)\scripts\run_api.py"

try {
  Set-Location (Join-Path $ROOT "frontend")
  if (-not (Test-Path "node_modules")) {
    Write-Host ">> installing frontend deps" -ForegroundColor Yellow
    npm install
  }
  Write-Host ">> frontend on http://localhost:5173" -ForegroundColor Cyan
  npm run dev
}
finally {
  if ($back -and -not $back.HasExited) {
    Write-Host ">> shutting down backend" -ForegroundColor DarkGray
    Stop-Process -Id $back.Id -Force
  }
}
