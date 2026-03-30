#!/bin/bash
set -e

# Claude Token Monitor 설치 스크립트
# 사용법: curl -fsSL https://raw.githubusercontent.com/jkRaccoon/claude-token-monitor/main/install.sh | bash

REPO="https://github.com/jkRaccoon/claude-token-monitor.git"
INSTALL_DIR="$HOME/.claude-monitor"
PLIST_NAME="com.local.claude-monitor.plist"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"

echo "🔍 Claude Token Monitor 설치를 시작합니다..."
echo ""

# 1. Python3 확인
if ! command -v python3 &>/dev/null; then
    echo "❌ Python3가 설치되어 있지 않습니다."
    echo "   brew install python3 또는 https://www.python.org 에서 설치하세요."
    exit 1
fi
echo "✅ Python3: $(python3 --version)"

# 2. 기존 설치 확인
if [ -d "$INSTALL_DIR" ]; then
    echo "📦 기존 설치를 발견했습니다. 업데이트합니다..."
    cd "$INSTALL_DIR"
    git pull --quiet
else
    echo "📥 소스 코드를 다운로드합니다..."
    git clone --quiet "$REPO" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# 3. 의존성 설치
echo "📦 의존성을 설치합니다..."
pip3 install --quiet -r requirements.txt

# 4. 실행 중인 인스턴스 종료
pkill -f "python3.*claude_monitor.py" 2>/dev/null || true

# 5. LaunchAgent 설정 (로그인 시 자동 실행)
mkdir -p "$LAUNCH_AGENTS_DIR"

cat > "$LAUNCH_AGENTS_DIR/$PLIST_NAME" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.local.claude-monitor</string>
    <key>ProgramArguments</key>
    <array>
        <string>$(which python3)</string>
        <string>${INSTALL_DIR}/claude_monitor.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>${INSTALL_DIR}</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardErrorPath</key>
    <string>/tmp/claude-monitor.err</string>
    <key>StandardOutPath</key>
    <string>/tmp/claude-monitor.out</string>
</dict>
</plist>
PLIST

# 6. LaunchAgent 로드
launchctl unload "$LAUNCH_AGENTS_DIR/$PLIST_NAME" 2>/dev/null || true
launchctl load "$LAUNCH_AGENTS_DIR/$PLIST_NAME"

echo ""
echo "✅ 설치 완료!"
echo ""
echo "   메뉴바에 Claude Token Monitor가 표시됩니다."
echo "   (Claude Code CLI 로그인이 필요합니다)"
echo ""
echo "   제거하려면: curl -fsSL https://raw.githubusercontent.com/jkRaccoon/claude-token-monitor/main/uninstall.sh | bash"
