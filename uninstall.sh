#!/bin/bash
set -e

# Claude Token Monitor 제거 스크립트
# 사용법: curl -fsSL https://raw.githubusercontent.com/jkRaccoon/claude-token-monitor/main/uninstall.sh | bash

INSTALL_DIR="$HOME/.claude-monitor"
PLIST_NAME="com.local.claude-monitor.plist"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"

echo "🗑️  Claude Token Monitor를 제거합니다..."

# 1. 실행 중인 인스턴스 종료
pkill -f "python3.*claude_monitor.py" 2>/dev/null || true

# 2. LaunchAgent 제거
if [ -f "$LAUNCH_AGENTS_DIR/$PLIST_NAME" ]; then
    launchctl unload "$LAUNCH_AGENTS_DIR/$PLIST_NAME" 2>/dev/null || true
    rm "$LAUNCH_AGENTS_DIR/$PLIST_NAME"
    echo "✅ LaunchAgent 제거 완료"
fi

# 3. 소스 코드 제거
if [ -d "$INSTALL_DIR" ]; then
    rm -rf "$INSTALL_DIR"
    echo "✅ 소스 코드 제거 완료 ($INSTALL_DIR)"
fi

echo ""
echo "✅ 제거 완료!"
