#!/bin/bash
set -e

PROJECT_ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$PROJECT_ROOT"

echo "🚀 [1/3] Building Flutter Web Bundle..."
cd frontend
flutter build web
cd ..

echo "🐳 [2/3] Rebuilding & Force Recreating Docker Containers..."
docker compose -f docker-compose.coolify.yml up -d --build --force-recreate

echo "✅ [3/3] Docker Containers Redeployed Successfully!"
docker ps | grep nasdaq-is-god
