#!/bin/bash

# Nasdaq is God - Flutter Auto Installer (Zsh & Bash support)
# This script installs the Flutter SDK in the home directory and sets up the PATH.

set -e

echo "🚀 Starting Flutter SDK installation..."

# 1. 설치 경로 설정 (홈 디렉토리의 flutter 폴더)
INSTALL_DIR="$HOME/flutter"

if [ -d "$INSTALL_DIR/bin" ]; then
    echo "✅ Flutter is already installed at $INSTALL_DIR. Skipping clone..."
    # 업데이트가 필요하면 여기서 git pull을 할 수 있으나, 재설치 방지를 위해 생략하거나 체크
else
    echo "📥 Cloning Flutter SDK from GitHub (stable branch)..."
    git clone https://github.com/flutter/flutter.git -b stable "$INSTALL_DIR"
fi

# 2. 환경 변수(PATH) 설정 함수
add_to_path_if_missing() {
    local rc_file=$1
    if [ -f "$rc_file" ]; then
        if ! grep -q "flutter/bin" "$rc_file"; then
            echo "" >> "$rc_file"
            echo "# Flutter SDK" >> "$rc_file"
            echo "export PATH=\"\$PATH:$INSTALL_DIR/bin\"" >> "$rc_file"
            echo "✅ Added Flutter to PATH in $rc_file"
        else
            echo "ℹ️ Flutter PATH is already in $rc_file"
        fi
    fi
}

echo "⚙️ Setting up environment variables..."

# .zshrc와 .bashrc 모두에 설정 (사용자 환경에 맞춤)
add_to_path_if_missing "$HOME/.zshrc"
add_to_path_if_missing "$HOME/.bashrc"

# 현재 세션에도 즉시 적용
export PATH="$PATH:$INSTALL_DIR/bin"

# 3. 설치 확인 및 초기화
echo "🔍 Verifying installation..."
if command -v flutter >/dev/null 2>&1; then
    flutter --version
else
    "$INSTALL_DIR/bin/flutter" --version
fi

echo ""
echo "===================================================="
echo "🎉 Flutter setup completed!"
echo "===================================================="
echo "⚠️  IMPORTANT: Run the following command to refresh your terminal:"
echo "   source ~/.zshrc"
echo "===================================================="

# 4. Flutter Web 엔진 다운로드 (미리 진행)
echo "📦 Pre-downloading Web artifacts..."
"$INSTALL_DIR/bin/flutter" precache --web