#!/bin/sh
# Claude Monitor statusline 래퍼
# stdin으로 받은 JSON에서 rate limit만 추출하여 파일에 저장한 뒤,
# 사용자의 원본 statusline 명령에 동일한 입력을 전달한다.
#
# 설치: install.sh가 settings.json의 statusLine.command를 이 래퍼로 교체하고,
#       원본 명령을 CLAUDE_MONITOR_ORIGINAL_CMD 환경변수 또는 .original-statusline 파일에 저장.

RATE_FILE="/tmp/claude-rate-limits.json"
ORIGINAL_CMD_FILE="$HOME/.claude-monitor/.original-statusline"

# stdin 전체를 변수에 저장 (원본 명령에도 전달해야 하므로)
input=$(cat)

# rate limit 데이터 추출 → 파일 저장
if command -v jq >/dev/null 2>&1; then
  five_h_used=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty')
  five_h_resets=$(echo "$input" | jq -r '.rate_limits.five_hour.resets_at // empty')
  seven_d_used=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty')
  seven_d_resets=$(echo "$input" | jq -r '.rate_limits.seven_day.resets_at // empty')

  now_ts=$(date +%s)
  cat > "$RATE_FILE" <<JSONEOF
{"timestamp":${now_ts},"five_hour":{"used_percentage":${five_h_used:-null},"resets_at":${five_h_resets:-null}},"seven_day":{"used_percentage":${seven_d_used:-null},"resets_at":${seven_d_resets:-null}}}
JSONEOF
fi

# 사용자의 원본 statusline 명령 실행
if [ -f "$ORIGINAL_CMD_FILE" ]; then
  original_cmd=$(cat "$ORIGINAL_CMD_FILE")
  if [ -n "$original_cmd" ]; then
    echo "$input" | eval "$original_cmd"
    exit $?
  fi
fi

# 원본 명령이 없으면 기본 출력 (간단한 statusline)
model=$(echo "$input" | jq -r '.model.display_name // empty' 2>/dev/null)
used=$(echo "$input" | jq -r '.context_window.used_percentage // empty' 2>/dev/null)
if [ -n "$model" ] && [ -n "$used" ]; then
  remain=$((100 - $(printf "%.0f" "$used")))
  printf "%s  ctx %d%%" "$model" "$remain"
fi
