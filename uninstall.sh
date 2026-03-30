#!/bin/bash
set -e

# Claude Token Monitor 제거 스크립트
# 사용법: curl -fsSL https://raw.githubusercontent.com/jkRaccoon/claude-token-monitor/main/uninstall.sh | bash

INSTALL_DIR="$HOME/.claude-monitor"
PLIST_NAME="com.local.claude-monitor.plist"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
SETTINGS_FILE="$HOME/.claude/settings.json"
ORIGINAL_CMD_FILE="$INSTALL_DIR/.original-statusline"

echo "🗑️  Claude Token Monitor를 제거합니다..."

# 1. 실행 중인 인스턴스 종료
pkill -f "python3.*claude_monitor.py" 2>/dev/null || true

# 2. statusline 원본 복원
if [ -f "$SETTINGS_FILE" ] && command -v jq &>/dev/null; then
    current_cmd=$(jq -r '.statusLine.command // empty' "$SETTINGS_FILE" 2>/dev/null)

    if echo "$current_cmd" | grep -q "statusline-wrapper.sh"; then
        if [ -f "$ORIGINAL_CMD_FILE" ]; then
            # 원본 명령 복원
            original_cmd=$(cat "$ORIGINAL_CMD_FILE")
            tmp=$(mktemp)
            jq --arg cmd "$original_cmd" '.statusLine = {"type": "command", "command": $cmd}' "$SETTINGS_FILE" > "$tmp"
            mv "$tmp" "$SETTINGS_FILE"
            echo "✅ statusline 원본 복원: $original_cmd"
        else
            # 원본이 없으면 statusLine 항목 제거
            tmp=$(mktemp)
            jq 'del(.statusLine)' "$SETTINGS_FILE" > "$tmp"
            mv "$tmp" "$SETTINGS_FILE"
            echo "✅ statusline 설정 제거"
        fi
    fi
fi

# 3. LaunchAgent 제거
if [ -f "$LAUNCH_AGENTS_DIR/$PLIST_NAME" ]; then
    launchctl unload "$LAUNCH_AGENTS_DIR/$PLIST_NAME" 2>/dev/null || true
    rm "$LAUNCH_AGENTS_DIR/$PLIST_NAME"
    echo "✅ LaunchAgent 제거 완료"
fi

# 4. rate limit 파일 제거
rm -f /tmp/claude-rate-limits.json 2>/dev/null || true

# 5. 소스 코드 제거
if [ -d "$INSTALL_DIR" ]; then
    rm -rf "$INSTALL_DIR"
    echo "✅ 소스 코드 제거 완료 ($INSTALL_DIR)"
fi

echo ""
echo "✅ 제거 완료!"
