# NASDAQ IS GOD - System Stop Script (Windows PowerShell)

$processes = Get-CimInstance Win32_Process | Where-Object { 
    $_.CommandLine -like "*python*main_api.py*" -or 
    $_.CommandLine -like "*python*serve_web.py*" -or 
    $_.CommandLine -like "*python*main.py*"
}

if ($processes) {
    foreach ($p in $processes) {
        Write-Host "Stopping process: $($p.ProcessId) - $($p.Name)" -ForegroundColor Yellow
        Stop-Process -Id $p.ProcessId -Force
    }
    Write-Host "All systems stopped successfully." -ForegroundColor Green
} else {
    Write-Host "No running systems found." -ForegroundColor Gray
}
