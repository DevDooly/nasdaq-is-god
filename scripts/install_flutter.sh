#!/bin/bash

# Nasdaq is God - Flutter Auto Installer
# This script installs the Flutter SDK in the home directory and sets up the PATH.

set -e

echo "🚀 Starting Flutter SDK installation..."

# 1. 설치 경로 설정 (홈 디렉토리의 flutter 폴더)
INSTALL_DIR="$HOME/flutter"

if [ -d "$INSTALL_DIR" ]; then
    echo "⚠️ Flutter is already installed at $INSTALL_DIR. Updating instead..."
    cd "$INSTALL_DIR"
    git pull
else
    echo "📥 Cloning Flutter SDK from GitHub (stable branch)..."
    git clone https://github.com/flutter/flutter.git -b stable "$INSTALL_DIR"
fi

# 2. 환경 변수(PATH) 설정
echo "⚙️ Setting up environment variables..."

# .bashrc에 PATH 추가 (중복 방지 체크)
if ! grep -q "flutter/bin" "$HOME/.bashrc"; then
    echo "" >> "$HOME/.bashrc"
    echo "# Flutter SDK" >> "$HOME/.bashrc"
    echo "export PATH="\$PATH:$INSTALL_DIR/bin"" >> "$HOME/.bashrc"
    echo "✅ Added Flutter to PATH in .bashrc"
else
    echo "ℹ️ Flutter PATH is already in .bashrc"
fi

# 현재 세션에도 적용
export PATH="$PATH:$INSTALL_DIR/bin"

# 3. 설치 확인 및 초기화
echo "🔍 Verifying installation..."
flutter --version

echo ""
echo "===================================================="
echo "🎉 Flutter installation completed successfully!"
echo "===================================================="
echo "⚠️  IMPORTANT: Run the following command to refresh your terminal:"
echo "   source ~/.bashrc"
echo "===================================================="

# 4. Flutter Web 엔진 다운로드 (미리 진행)
echo "📦 Pre-downloading Web artifacts..."
flutter precache --web
