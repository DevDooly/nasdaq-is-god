#!/bin/bash

# Nasdaq is God - Frontend Web Runner (Optimized)
# This script serves the built Flutter web files using a multi-threaded server.

PORT=8080
echo "🚀 Preparing Nasdaq is God Frontend (Optimized Server)..."

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

# 3. 빌드 파일 존재 확인
if [ ! -d "build/web" ]; then
    echo "📦 Build folder missing. Running flutter build web..."
    ~/flutter/bin/flutter build web --release --web-renderer html
fi

# 4. 최적화된 Python 서버 실행 (Threading 지원)
echo "🌐 Starting Threaded Web Server on port $PORT..."
nohup python3 serve_web.py > web_server.log 2>&1 &

echo "✅ Web server started in background. Logs available at frontend/web_server.log"
echo "👉 Access at: http://devdooly.iptime.org:$PORT"
