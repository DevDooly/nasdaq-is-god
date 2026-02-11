#!/bin/bash

# Nasdaq is God - Frontend Web Runner (Robust Version)
# This script ensures the web boilerplate exists and runs the Flutter web server.

PORT=8080
FLUTTER_BIN="$HOME/flutter/bin/flutter"

echo "🚀 Preparing Nasdaq is God Frontend (Web)..."

# 1. 8080 포트 정리
PID=$(lsof -t -i:$PORT 2>/dev/null || netstat -tulpn 2>/dev/null | grep ":$PORT " | awk '{print $7}' | cut -d/ -f1)
if [ ! -z "$PID" ]; then
    echo "⚠️ Killing existing process on port $PORT..."
    kill -9 $PID 2>/dev/null || true
    sleep 1
fi

# 2. 프론트엔드 디렉토리 이동
PARENT_DIR=$(basename "$PWD")
if [ "$PARENT_DIR" != "frontend" ]; then
    if [ -d "frontend" ]; then
        cd frontend
    else
        echo "❌ Error: frontend directory not found."
        exit 1
    fi
fi

# 3. Web Boilerplate 체크 및 생성
if [ ! -d "web" ]; then
    echo "📦 Web folder missing. Generating web boilerplate..."
    $FLUTTER_BIN create . --platforms=web
fi

# 4. 의존성 설치
echo "📦 Fetching dependencies..."
$FLUTTER_BIN pub get

# 5. Flutter Web 서버 실행
echo "🌐 Starting Flutter Web Server on port $PORT..."
# 0.0.0.0으로 바인딩하여 외부 접속 허용
$FLUTTER_BIN run -d web-server --web-port $PORT --web-hostname 0.0.0.0
