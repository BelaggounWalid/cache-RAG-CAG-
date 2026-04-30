# Kill backend (uvicorn) + frontend (vite/node) launched by start.ps1.
Get-Process -Name "python","node" -ErrorAction SilentlyContinue |
    Where-Object {
        $_.CommandLine -match "run_api|sapa_rag|vite" -or
        $_.MainWindowTitle -match "Chacal|sapa_rag"
    } | ForEach-Object {
        Write-Host "  ✗ kill PID $($_.Id) — $($_.ProcessName)"
        Stop-Process -Id $_.Id -Force
    }

# Fallback: kill anything listening on 8000 / 5173
foreach ($port in 8000, 5173) {
    $cnx = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    foreach ($c in $cnx) {
        try {
            Write-Host "  ✗ kill PID $($c.OwningProcess) (port $port)"
            Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue
        } catch {}
    }
}
Write-Host "  ✓ stopped" -ForegroundColor Cyan
