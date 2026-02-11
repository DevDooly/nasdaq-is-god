#!/bin/bash

# Nasdaq is God - System Integration Checker
# This script verifies the integrity of both Backend and Frontend.

echo "🔍 Starting System Integration Check..."
echo "---------------------------------------"

# 1. Backend Check
echo "[1/4] Checking Backend Integrity..."
if ! python3 -m py_compile main_api.py core/*.py; then
    echo "❌ Error: Python Syntax Error detected in Backend!"
    exit 1
fi
echo "✅ Backend Syntax OK"

# 2. API Server Status
echo "[2/4] Checking API Server (Port 9000)..."
if ! netstat -tulpn 2>/dev/null | grep :9000 > /dev/null; then
    echo "⚠️ Warning: API Server is not running on port 9000."
    echo "💡 Run: nohup python3 main_api.py > api_server.log 2>&1 &"
else
    echo "✅ API Server is LIVE"
fi

# 3. Frontend Configuration Check
echo "[3/4] Checking Frontend API Address..."
if ! grep "9000" frontend/lib/services/api_service.dart > /dev/null; then
    echo "❌ Error: Frontend is NOT pointing to port 9000!"
    exit 1
fi
echo "✅ Frontend Config OK"

# 4. Web Server Status
echo "[4/4] Checking Web Server (Port 8080)..."
if ! netstat -tulpn 2>/dev/null | grep :8080 > /dev/null; then
    echo "⚠️ Warning: Web Server is not running on port 8080."
    echo "💡 Run: ./frontend/run_web.sh"
else
    echo "✅ Web Server is LIVE"
fi

echo "---------------------------------------"
echo "🎉 All basic checks passed! System is ready."
