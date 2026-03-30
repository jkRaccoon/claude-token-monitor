# Claude Token Monitor

macOS 메뉴바에서 Claude Max 플랜의 토큰 사용량을 실시간으로 모니터링하는 앱입니다.

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![macOS](https://img.shields.io/badge/macOS-12.0+-black)
![License](https://img.shields.io/badge/License-MIT-green)

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

## 설치 및 실행

### 방법 1: .app 다운로드 (간편)

1. [Releases](https://github.com/jkRaccoon/claude-token-monitor/releases/latest)에서 `Claude-Monitor-v1.0.0-macOS-arm64.zip` 다운로드
2. 압축 해제 후 `/Applications/`에 복사
3. 첫 실행 시 Gatekeeper 해제:
   ```bash
   xattr -cr "/Applications/Claude Monitor.app"
   ```
4. `Claude Monitor.app` 실행

### 방법 2: 소스에서 실행

```bash
# 1. 클론
git clone https://github.com/jkRaccoon/claude-token-monitor.git
cd claude-token-monitor

# 2. 의존성 설치
pip3 install -r requirements.txt

# 3. 실행
python3 claude_monitor.py
```

### Claude Code 설치 (아직 없는 경우)

```bash
npm install -g @anthropic-ai/claude-code
claude  # 실행 후 로그인
```

## 로그인 시 자동 실행

```bash
# LaunchAgent 등록
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

## 프로젝트 구조

```
├── claude_monitor.py      # 메인 메뉴바 앱 (rumps)
├── token_provider.py      # macOS Keychain OAuth 토큰 관리 + 자동 갱신
├── usage_api.py           # Anthropic Usage API 클라이언트
├── stats_reader.py        # 로컬 ~/.claude/stats-cache.json 파서
├── setup.py               # py2app 빌드 설정
├── run.sh                 # 실행 스크립트
└── com.local.claude-monitor.plist  # LaunchAgent (자동 시작)
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
