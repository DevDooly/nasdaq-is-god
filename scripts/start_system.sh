#!/bin/bash

# Nasdaq is God - System Startup Script
# This script starts all running components: Database, Backend, Frontend, and Bot.

echo "🚀 Starting Nasdaq is God System..."
echo "---------------------------------------"

# 1. Start Database (Docker)
echo "[1/4] Starting Database Container (nasdaq-db)..."
docker compose up -d
echo "⏳ Waiting for Database to be ready..."
sleep 5

# 2. Start Backend API
echo "[2/4] Starting Backend API (main_api.py)..."
if ! ps aux | grep "main_api.py" | grep -v "grep" > /dev/null; then
    nohup python3 main_api.py > api_server.log 2>&1 &
    echo "✅ Backend API started in background."
else
    echo "ℹ️ Backend API is already running."
fi

# 3. Start Frontend Web Server
echo "[3/4] Starting Frontend Web Server (run_web.sh)..."
if [ -d "frontend" ]; then
    cd frontend
    ./run_web.sh
    cd ..
    echo "✅ Frontend deployment triggered."
else
    echo "❌ Error: frontend directory not found."
fi

# 4. Start Telegram Bot
echo "[4/4] Starting Telegram Bot (main.py)..."
if ! ps aux | grep "main.py" | grep -v "grep" > /dev/null; then
    nohup python3 main.py > bot.log 2>&1 &
    echo "✅ Telegram Bot started in background."
else
    echo "ℹ️ Telegram Bot is already running."
fi

echo "---------------------------------------"
echo "🎉 System startup sequence completed!"
echo "📊 Check status with: ./scripts/check_system.sh"
