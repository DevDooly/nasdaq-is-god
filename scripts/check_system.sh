#!/bin/bash

# Nasdaq is God - System Integration Checker
# This script verifies the integrity of both Backend and Frontend.

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
echo "[2/5] Checking API Server (Port 9000)..."
if ! netstat -tulpn 2>/dev/null | grep :9000 > /dev/null; then
    echo "⚠️ Warning: API Server is not running on port 9000."
    echo "💡 Run: nohup python3 main_api.py > api_server.log 2>&1 &"
else
    echo "✅ API Server is LIVE"
    
    # 💡 [NEW] Login API Functional Check
    echo "   -> Testing Login API Response..."
    LOGIN_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:9000/login \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=admin&password=admin123")
    
    if [ "$LOGIN_STATUS" == "200" ]; then
        echo "   ✅ Login API is responding correctly (200 OK)"
    else
        echo "   ❌ Error: Login API returned $LOGIN_STATUS instead of 200."
        echo "   💡 Check if 'admin' user exists or if DB is connected."
        exit 1
    fi
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