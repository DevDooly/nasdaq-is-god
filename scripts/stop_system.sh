#!/bin/bash

# Nasdaq is God - System Shutdown Script
# This script stops all running components: Database, Backend, Frontend, and Bot.

# 프로젝트 루트 디렉토리 설정
PROJECT_ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$PROJECT_ROOT"

echo "🛑 Stopping Nasdaq is God System..."
echo "---------------------------------------"

# 1. Stop Telegram Bot
echo "[1/4] Stopping Telegram Bot (main.py)..."
BOT_PID=$(ps aux | grep "main.py" | grep -v "grep" | awk '{print $2}')
if [ ! -z "$BOT_PID" ]; then
    kill $BOT_PID
    echo "✅ Bot stopped (PID: $BOT_PID)"
else
    echo "ℹ️ Bot is not running."
fi

# 2. Stop Backend API
echo "[2/4] Stopping Backend API (main_api.py)..."
API_PID=$(ps aux | grep "main_api.py" | grep -v "grep" | awk '{print $2}')
if [ ! -z "$API_PID" ]; then
    kill $API_PID
    echo "✅ Backend API stopped (PID: $API_PID)"
else
    echo "ℹ️ Backend API is not running."
fi

# 3. Stop Frontend Web Server
echo "[3/4] Stopping Frontend Web Server (serve_web.py)..."
WEB_PID=$(ps aux | grep "serve_web.py" | grep -v "grep" | awk '{print $2}')
if [ ! -z "$WEB_PID" ]; then
    kill $WEB_PID
    echo "✅ Frontend stopped (PID: $WEB_PID)"
else
    echo "ℹ️ Frontend is not running."
fi

# 4. Stop Database (Docker)
echo "[4/4] Stopping Database Container (nasdaq-db)..."
if docker ps -q -f name=nasdaq-db | grep -q . ; then
    docker compose down
    echo "✅ Database container stopped."
else
    echo "ℹ️ Database container is not running."
fi

echo "---------------------------------------"
echo "🎉 All components have been stopped."
