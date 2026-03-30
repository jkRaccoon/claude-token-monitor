# Claude Token Monitor

macOS menu bar app for real-time monitoring of Claude Max plan token usage.

[한국어](#한국어) | English

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![macOS](https://img.shields.io/badge/macOS-12.0+-black)
![License](https://img.shields.io/badge/License-MIT-green)

## Screenshot

**Menu bar** — 5-hour usage and time until reset at a glance

```
🟢 14% · 3h20m
```

**Click for details** — progress bars for 5-hour / 7-day usage

```
5-Hour ▓▓░░░░░░░░░░░░░ 14%
  Resets in: 3h 20m
  Reset at:  03/30 20:00
───────────────────────────
7-Day  ▓▓▓▓▓▓▓▓▓░░░░░░ 58%
  Resets in: 3d 23h
  Reset at:  04/03 16:00
───────────────────────────
Today's tokens
  claude-opus-4-6: 173,832
───────────────────────────
Last 7 days: 333,534 tokens
───────────────────────────
Source: statusline
Last updated: 18:30:45
```

## Features

- **5-hour usage in menu bar** with percentage and countdown to reset
- Color-coded status: 🟢 Normal / 🟡 Warning (50%+) / 🔴 Critical (80%+)
- **Progress bars** for 5-hour and 7-day usage in dropdown
- Reset times, per-model token usage, 7-day totals
- **Hybrid data source**: statusline file (primary, 5s) + Usage API (fallback, 60s)
- Data source indicator and 429 rate limit countdown in dropdown
- Setup guide UI when Claude Code is not installed

## How it works

```
┌─────────────┐    statusline     ┌────────────────────────┐
│ Claude Code  │───────────────▶  │ /tmp/claude-rate-      │
│ (CLI/Desktop)│   (every turn)   │  limits.json           │
└─────────────┘                   └───────────┬────────────┘
                                              │ 5s polling
                                              ▼
                                  ┌────────────────────────┐
                                  │  Claude Token Monitor   │
                                  │  (menu bar app)         │
                                  └───────────┬────────────┘
                                              │ fallback (60s)
┌─────────────┐   read-only       ┌───────────▼────────────┐
│ macOS        │◀─────────────────│  Usage API              │
│ Keychain     │   (no refresh)   │  (User-Agent trick)     │
└─────────────┘                   └────────────────────────┘
```

1. **Primary**: Reads rate limit data from `/tmp/claude-rate-limits.json`, written by Claude Code's statusline wrapper script (every 5 seconds, zero API calls)
2. **Fallback**: When statusline data is stale (>10min), reads OAuth token from macOS Keychain (read-only, no refresh) and queries the Usage API every 60 seconds
3. **Safe**: Never refreshes tokens — won't disrupt active Claude Code sessions
4. Supplements with local token stats from `~/.claude/stats-cache.json`

## Prerequisites

- **macOS 12.0+** (Apple Silicon / Intel)
- **Claude Code CLI** installed and logged in
- **Claude Max plan** (5x or 20x) subscription
- **jq** (`brew install jq`)

> If Claude Code is not installed, the app will show a setup guide.

## Installation

### One-line install (recommended)

```bash
curl -fsSL https://raw.githubusercontent.com/jkRaccoon/claude-token-monitor/main/install.sh | bash
```

This automatically:
- Downloads source code to `~/.claude-monitor/`
- Installs dependencies
- Sets up statusline wrapper (preserves your existing statusline)
- Configures auto-launch on login
- **Starts the app immediately** — look for the icon in your menu bar

After installation, start using Claude Code normally. Rate limit data will appear in the menu bar after your first conversation.

If the app is not running, you can start it manually:
```bash
python3 ~/.claude-monitor/claude_monitor.py &
```

Uninstall (restores original statusline):
```bash
curl -fsSL https://raw.githubusercontent.com/jkRaccoon/claude-token-monitor/main/uninstall.sh | bash
```

### Run from source

```bash
git clone https://github.com/jkRaccoon/claude-token-monitor.git
cd claude-token-monitor
pip3 install -r requirements.txt
python3 claude_monitor.py
```

### Install Claude Code (if not already installed)

```bash
npm install -g @anthropic-ai/claude-code
claude  # run and log in
```

## Project structure

```
├── claude_monitor.py        # Main menu bar app (rumps)
├── rate_limit_reader.py     # Reads /tmp/claude-rate-limits.json
├── token_provider.py        # macOS Keychain token reader (read-only)
├── usage_api.py             # Usage API client (fallback, User-Agent trick)
├── stats_reader.py          # Local ~/.claude/stats-cache.json parser
├── statusline-wrapper.sh    # Wraps user's statusline, extracts rate limits
├── install.sh               # One-line installer (sets up wrapper + LaunchAgent)
├── uninstall.sh             # Uninstaller (restores original statusline)
└── requirements.txt         # Python dependencies
```

## Notes

- The statusline wrapper **preserves your existing statusline** — it extracts rate limit data and passes input through to your original command
- Usage API is a fallback with rate limits (~10 requests per 5 minutes with User-Agent trick)
- When rate-limited (429), a countdown timer is shown and cached data is displayed
- **Claude Desktop app alone is not sufficient** — Claude Code CLI is required

---

# 한국어

macOS 메뉴바에서 Claude Max 플랜의 토큰 사용량을 실시간으로 모니터링하는 앱입니다.

## 스크린샷

**메뉴바** — 5시간 사용량과 리셋 남은 시간을 한눈에 확인

```
🟢 14% · 3h20m
```

**클릭 시 상세 정보** — 프로그레스 바로 5시간/7일 사용량 시각화

```
5시간  ▓▓░░░░░░░░░░░░░ 14%
  리셋까지: 3시간 20분
  리셋 시각: 03/30 20:00
───────────────────────────
7일    ▓▓▓▓▓▓▓▓▓░░░░░░ 58%
  리셋까지: 3일 23시간
  리셋 시각: 04/03 16:00
───────────────────────────
오늘 토큰 사용량
  claude-opus-4-6: 173,832
───────────────────────────
최근 7일 합계: 333,534 tokens
───────────────────────────
소스: statusline
마지막 갱신: 18:30:45
```

## 기능

- **메뉴바에 5시간 사용량 실시간 표시** (퍼센트 + 리셋 남은 시간)
- 사용률에 따른 색상: 🟢 정상 / 🟡 주의(50%+) / 🔴 위험(80%+)
- 클릭 시 **프로그레스 바**로 5시간/7일 사용량 상세 표시
- 리셋 시각, 오늘 모델별 토큰 사용량, 7일 합계 확인
- **하이브리드 데이터 소스**: statusline 파일(primary, 5초) + Usage API(fallback, 60초)
- 데이터 소스 표시 및 429 rate limit 카운트다운
- Claude Code 미설치 시 설치 안내 UI 제공

## 동작 원리

```
┌─────────────┐    statusline     ┌────────────────────────┐
│ Claude Code  │───────────────▶  │ /tmp/claude-rate-      │
│ (CLI/Desktop)│   (매 대화마다)   │  limits.json           │
└─────────────┘                   └───────────┬────────────┘
                                              │ 5초 폴링
                                              ▼
                                  ┌────────────────────────┐
                                  │  Claude Token Monitor   │
                                  │  (메뉴바 앱)            │
                                  └───────────┬────────────┘
                                              │ fallback (60초)
┌─────────────┐   읽기 전용       ┌───────────▼────────────┐
│ macOS        │◀─────────────────│  Usage API              │
│ Keychain     │  (갱신 안 함)     │  (User-Agent trick)     │
└─────────────┘                   └────────────────────────┘
```

1. **Primary**: Claude Code statusline 래퍼가 `/tmp/claude-rate-limits.json`에 기록한 rate limit 데이터를 5초마다 읽음 (API 호출 없음)
2. **Fallback**: statusline 데이터가 10분 이상 오래되면, macOS Keychain에서 OAuth 토큰을 읽어(읽기 전용, 갱신 없음) 60초마다 Usage API 호출
3. **안전**: 토큰을 직접 갱신하지 않으므로 Claude Code 세션에 영향 없음
4. `~/.claude/stats-cache.json`에서 로컬 토큰 통계 보조 표시

## 사전 요구사항

- **macOS 12.0+** (Apple Silicon / Intel)
- **Claude Code CLI** 설치 및 로그인 필수
- **Claude Max 플랜** (5x 또는 20x) 구독 필요
- **jq** (`brew install jq`)

> Claude Code가 설치되지 않은 상태에서 앱을 실행하면 설치 안내 UI가 표시됩니다.

## 설치

### 원라인 설치 (권장)

```bash
curl -fsSL https://raw.githubusercontent.com/jkRaccoon/claude-token-monitor/main/install.sh | bash
```

자동으로:
- `~/.claude-monitor/`에 소스 코드 다운로드
- 의존성 설치
- statusline 래퍼 설정 (기존 statusline 보존)
- 로그인 시 자동 실행 설정
- **설치 즉시 앱 실행** — 메뉴바에 아이콘이 표시됩니다

설치 후 Claude Code를 평소처럼 사용하면 됩니다. 첫 대화 후 메뉴바에 rate limit 데이터가 표시됩니다.

앱이 실행되지 않은 경우 수동 실행:
```bash
python3 ~/.claude-monitor/claude_monitor.py &
```

제거 (원본 statusline 복원):
```bash
curl -fsSL https://raw.githubusercontent.com/jkRaccoon/claude-token-monitor/main/uninstall.sh | bash
```

### 소스에서 실행

```bash
git clone https://github.com/jkRaccoon/claude-token-monitor.git
cd claude-token-monitor
pip3 install -r requirements.txt
python3 claude_monitor.py
```

### Claude Code 설치 (아직 없는 경우)

```bash
npm install -g @anthropic-ai/claude-code
claude  # 실행 후 로그인
```

## 참고 사항

- statusline 래퍼는 **기존 statusline을 보존**합니다 — rate limit 데이터만 추출하고 원본 명령에 그대로 전달
- Usage API는 fallback으로, rate limit이 있습니다 (~5분당 10회, User-Agent trick 적용)
- Rate limit(429) 발생 시 카운트다운 타이머 표시 + 캐시 데이터 사용
- Claude Desktop 앱만으로는 동작하지 않습니다 (Claude Code CLI 필요)

## License

MIT
