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
```

## Features

- **5-hour usage in menu bar** with percentage and countdown to reset
- Color-coded status: 🟢 Normal / 🟡 Warning (50%+) / 🔴 Critical (80%+)
- **Progress bars** for 5-hour and 7-day usage in dropdown
- Reset times, per-model token usage, 7-day totals
- Auto-refresh every 60 seconds
- Automatic OAuth token refresh via refresh token
- Setup guide UI when Claude Code is not installed

## Prerequisites

- **macOS 12.0+** (Apple Silicon / Intel)
- **Claude Code CLI** installed and logged in
- **Claude Max plan** (5x or 20x) subscription

> If Claude Code is not installed, the app will show a setup guide.

## Installation

### One-line install (recommended)

```bash
curl -fsSL https://raw.githubusercontent.com/jkRaccoon/claude-token-monitor/main/install.sh | bash
```

Automatically downloads, installs dependencies, and sets up auto-launch on login.

Uninstall:
```bash
curl -fsSL https://raw.githubusercontent.com/jkRaccoon/claude-token-monitor/main/uninstall.sh | bash
```

### Download .app

1. Download zip from [Releases](https://github.com/jkRaccoon/claude-token-monitor/releases/latest)
2. Unzip and copy to `/Applications/`
3. Remove Gatekeeper flag: `xattr -cr "/Applications/Claude Monitor.app"`

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

## Auto-launch on login

```bash
cp com.local.claude-monitor.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.local.claude-monitor.plist
```

Remove:
```bash
launchctl unload ~/Library/LaunchAgents/com.local.claude-monitor.plist
rm ~/Library/LaunchAgents/com.local.claude-monitor.plist
```

## Build from source

```bash
pip3 install pyinstaller
pyinstaller --windowed --name "Claude Monitor" --osx-bundle-identifier com.local.claude-monitor claude_monitor.py
# Creates dist/Claude Monitor.app
```

## Project structure

```
├── claude_monitor.py      # Main menu bar app (rumps)
├── token_provider.py      # macOS Keychain OAuth token management + auto-refresh
├── usage_api.py           # Anthropic Usage API client
├── stats_reader.py        # Local ~/.claude/stats-cache.json parser
├── install.sh             # One-line installer
├── uninstall.sh           # Uninstaller
├── setup.py               # py2app build config
├── run.sh                 # Run script
└── com.local.claude-monitor.plist  # LaunchAgent config
```

## How it works

1. Reads **OAuth token** stored by Claude Code in macOS Keychain
2. Queries usage via `https://api.anthropic.com/api/oauth/usage`
3. **Auto-refreshes** expired tokens using refresh token + updates Keychain
4. Supplements with local token stats from `~/.claude/stats-cache.json`

## Notes

- The Usage API is an unofficial endpoint with **strict rate limits** (~5 requests per token)
- When rate-limited, the last cached result is displayed
- The .app is not code-signed; `xattr -cr` is needed on first launch
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
```

## 기능

- **메뉴바에 5시간 사용량 실시간 표시** (퍼센트 + 리셋 남은 시간)
- 사용률에 따른 색상: 🟢 정상 / 🟡 주의(50%+) / 🔴 위험(80%+)
- 클릭 시 **프로그레스 바**로 5시간/7일 사용량 상세 표시
- 리셋 시각, 오늘 모델별 토큰 사용량, 7일 합계 확인
- 60초마다 자동 갱신
- OAuth 토큰 자동 갱신 (만료 시 refresh token 사용)
- Claude Code 미설치 시 설치 안내 UI 제공

## 사전 요구사항

- **macOS 12.0+** (Apple Silicon / Intel)
- **Claude Code CLI** 설치 및 로그인 필수
- **Claude Max 플랜** (5x 또는 20x) 구독 필요

> Claude Code가 설치되지 않은 상태에서 앱을 실행하면 설치 안내 UI가 표시됩니다.

## 설치

### 원라인 설치 (권장)

```bash
curl -fsSL https://raw.githubusercontent.com/jkRaccoon/claude-token-monitor/main/install.sh | bash
```

자동으로 다운로드, 의존성 설치, 로그인 시 자동 실행까지 설정됩니다.

제거:
```bash
curl -fsSL https://raw.githubusercontent.com/jkRaccoon/claude-token-monitor/main/uninstall.sh | bash
```

### .app 다운로드

1. [Releases](https://github.com/jkRaccoon/claude-token-monitor/releases/latest)에서 zip 다운로드
2. 압축 해제 후 `/Applications/`에 복사
3. Gatekeeper 해제: `xattr -cr "/Applications/Claude Monitor.app"`

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

## 로그인 시 자동 실행

```bash
cp com.local.claude-monitor.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.local.claude-monitor.plist
```

해제:
```bash
launchctl unload ~/Library/LaunchAgents/com.local.claude-monitor.plist
rm ~/Library/LaunchAgents/com.local.claude-monitor.plist
```

## 직접 빌드

```bash
pip3 install pyinstaller
pyinstaller --windowed --name "Claude Monitor" --osx-bundle-identifier com.local.claude-monitor claude_monitor.py
# dist/Claude Monitor.app 생성
```

## 동작 원리

1. Claude Code가 macOS Keychain에 저장한 **OAuth 토큰**을 읽음
2. `https://api.anthropic.com/api/oauth/usage` 엔드포인트로 사용량 조회
3. 토큰 만료 시 **refresh token으로 자동 갱신** + Keychain 업데이트
4. `~/.claude/stats-cache.json`에서 로컬 토큰 통계 보조 표시

## 참고 사항

- Usage API는 비공식 엔드포인트로, **rate limit이 엄격**합니다 (토큰당 ~5회)
- Rate limit 초과 시 마지막 캐시된 결과를 표시합니다
- 코드 서명이 없으므로 첫 실행 시 `xattr -cr` 명령이 필요합니다
- Claude Desktop 앱만으로는 동작하지 않습니다 (Claude Code CLI 필요)

## License

MIT
