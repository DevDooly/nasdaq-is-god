#!/bin/bash

# Nasdaq is God - Frontend Web Runner
# This script runs the Flutter web server on port 8080, accessible externally.

PORT=8080
echo "🚀 Preparing Nasdaq is God Frontend (Web)..."

# 1. 8080 포트를 사용 중인 기존 프로세스 종료
PID=$(lsof -t -i:$PORT 2>/dev/null || netstat -tulpn 2>/dev/null | grep ":$PORT " | awk '{print $7}' | cut -d/ -f1)

if [ ! -z "$PID" ]; then
    echo "⚠️ Port $PORT is already in use by PID $PID. Killing existing process..."
    kill -9 $PID 2>/dev/null || true
    sleep 2
fi

# 2. 혹시 남아있을 수 있는 다른 flutter 관련 프로세스 정리 (선택 사항)
# pkill -f "flutter_tools.snapshot" 2>/dev/null || true

# 3. 프론트엔드 디렉토리 체크 및 이동
PARENT_DIR=$(basename "$PWD")
if [ "$PARENT_DIR" != "frontend" ]; then
    if [ -d "frontend" ]; then
        cd frontend
    else
        echo "❌ Error: frontend directory not found."
        exit 1
    fi
fi

# 4. Flutter Web 서버 실행
echo "🌐 Starting Flutter Web Server on port $PORT..."
flutter run -d web-server --web-port $PORT --web-hostname 0.0.0.0