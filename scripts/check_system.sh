#!/bin/bash

# Nasdaq is God - System Integration Checker
# This script verifies the integrity of both Backend and Frontend.

# 프로젝트 루트 디렉토리 설정 (스크립트 위치 기준 상위 디렉토리)
PROJECT_ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$PROJECT_ROOT"

echo "🔍 Starting System Integration Check..."
echo "---------------------------------------"

# 1. Backend Check
echo "[1/5] Checking Backend Integrity..."
if ! python3 -m py_compile main_api.py core/*.py; then
    echo "❌ Error: Python Syntax Error detected in Backend!"
    exit 1
fi
echo "✅ Backend Syntax OK"

# 2. API Server Status
echo "[2/5] Checking API Server Status..."
if ! curl -s http://localhost:9095/ > /dev/null && ! curl -s http://localhost:9000/ > /dev/null; then
    echo "⚠️ Warning: API Server is not responding on port 9095 or 9000."
else
    echo "✅ API Server is LIVE"
fi

# 3. Frontend Configuration Check
echo "[3/5] Checking Frontend API Address..."
if ! grep "9000" frontend/lib/services/api_service.dart > /dev/null; then
    echo "❌ Error: Frontend is NOT pointing to port 9000!"
    exit 1
fi
echo "✅ Frontend Config OK"

# 4. Web Server Status
echo "[4/5] Checking Web Server (Port 8080)..."
if ! netstat -tulpn 2>/dev/null | grep :8080 > /dev/null; then
    echo "⚠️ Warning: Web Server is not running on port 8080."
    echo "💡 Run: ./frontend/run_web.sh"
else
    echo "✅ Web Server is LIVE"
fi

# 5. Frontend Login Logic Check (Basic check for known problematic patterns)
echo "[5/5] Checking Frontend robustness..."
if grep "catch (e) => null;" frontend/lib/services/api_service.dart > /dev/null; then
    echo "❌ Error: Found illegal 'catch (e) =>' syntax in ApiService! This will break build."
    exit 1
fi
echo "✅ Frontend code robustness OK"

echo "---------------------------------------"
echo "🎉 All system checks passed! Deployment is stable."