# NASDAQ IS GOD - System Start Script (Windows PowerShell)

Write-Host "🚀 Starting NASDAQ IS GOD Ecosystem..." -ForegroundColor Cyan

# 1. Backend API
Write-Host "1/3 Starting Backend API..." -ForegroundColor White
Start-Process python -ArgumentList "main_api.py" -WorkingDirectory "$PSScriptRoot\.." -WindowStyle Hidden
Start-Sleep -Seconds 3

# 2. Telegram Bot
Write-Host "2/3 Starting Telegram Bot..." -ForegroundColor White
Start-Process python -ArgumentList "main.py" -WorkingDirectory "$PSScriptRoot\.." -WindowStyle Hidden
Start-Sleep -Seconds 2

# 3. Frontend Web Server
Write-Host "3/3 Starting Frontend Web Server..." -ForegroundColor White
Start-Process python -ArgumentList "serve_web.py" -WorkingDirectory "$PSScriptRoot\..\frontend" -WindowStyle Hidden

Write-Host "✅ All systems started!" -ForegroundColor Green
Write-Host "- API Docs: http://localhost:9000/docs"
Write-Host "- Web App: http://localhost:8080"
