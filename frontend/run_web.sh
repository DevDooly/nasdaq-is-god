#!/bin/bash

# Nasdaq is God - Frontend Web Runner
# This script runs the Flutter web server on port 8080, accessible externally.

echo "🚀 Starting Nasdaq is God Frontend (Web)..."

# Ensure we are in the frontend directory
PARENT_DIR=$(basename "$PWD")
if [ "$PARENT_DIR" != "frontend" ]; then
    if [ -d "frontend" ]; then
        cd frontend
    else
        echo "❌ Error: frontend directory not found."
        exit 1
    fi
fi

# Run Flutter Web Server
# --web-port 8080: External access port
# --web-hostname 0.0.0.0: Bind to all interfaces
flutter run -d web-server --web-port 8080 --web-hostname 0.0.0.0
