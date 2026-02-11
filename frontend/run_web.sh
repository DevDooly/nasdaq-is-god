#!/bin/bash

# Nasdaq is God - Frontend Web Runner (Static Server)
# This script serves the built Flutter web files on port 8080.

PORT=8080
echo "🚀 Preparing Nasdaq is God Frontend (Static Web Server)..."

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

# 3. 빌드 파일 존재 확인 및 빌드 (필요시)
if [ ! -d "build/web" ]; then
    echo "📦 Build folder missing. Running flutter build web..."
    ~/flutter/bin/flutter build web --release
fi

# 4. Python으로 정적 웹 서버 실행
echo "🌐 Serving static web files on port $PORT..."
echo "👉 Access at: http://YOUR_SERVER_IP:$PORT"

# build/web 폴더로 이동하여 서버 시작
cd build/web
# nohup을 사용하여 백그라운드에서 실행 (선택 사항이나 권장)
nohup python3 -m http.server $PORT > ../../web_server.log 2>&1 &

echo "✅ Web server started in background. Logs available at frontend/web_server.log"