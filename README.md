# Claude Token Monitor

macOS 메뉴바에서 Claude Max 플랜의 토큰 사용량을 실시간으로 모니터링하는 앱입니다.

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![macOS](https://img.shields.io/badge/macOS-12.0+-black)
![License](https://img.shields.io/badge/License-MIT-green)

## 기능

- **5시간 / 7일 사용량** 퍼센트를 메뉴바에 실시간 표시
- **리셋 남은 시간** 표시 (예: `5H:14%(3h20m) 7D:58%(3d23h)`)
- 사용률에 따른 색상 표시: 🟢 정상 / 🟡 주의(50%+) / 🔴 위험(80%+)
- 클릭 시 상세 정보: 리셋 시각, 오늘 토큰 사용량, 7일 합계
- 60초마다 자동 갱신
- OAuth 토큰 자동 갱신 (만료 시 refresh token 사용)
- Claude Code 미설치 시 설치 안내 UI 제공

## 사전 요구사항

- **macOS 12.0+**
- **Python 3.9+**
- **Claude Code CLI** 설치 및 로그인 필수
  - `npm install -g @anthropic-ai/claude-code`
  - 터미널에서 `claude` 실행 후 로그인
- **Claude Max 플랜** (5x 또는 20x) 구독 필요

## 설치 및 실행

```bash
# 1. 클론
git clone https://github.com/jkRaccoon/claude-token-monitor.git
cd claude-token-monitor

# 2. 의존성 설치
pip3 install -r requirements.txt

# 3. 실행
python3 claude_monitor.py
```

## 로그인 시 자동 실행

```bash
# LaunchAgent 등록
cp com.local.claude-monitor.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.local.claude-monitor.plist
```

해제하려면:
```bash
launchctl unload ~/Library/LaunchAgents/com.local.claude-monitor.plist
rm ~/Library/LaunchAgents/com.local.claude-monitor.plist
```

## .app 번들 빌드 (선택)

```bash
pip3 install pyinstaller
pyinstaller --windowed --name "Claude Monitor" --osx-bundle-identifier com.local.claude-monitor claude_monitor.py
```

`dist/Claude Monitor.app`이 생성됩니다. `/Applications/`에 복사하여 사용하세요.

## 구조

```
├── claude_monitor.py      # 메인 메뉴바 앱 (rumps)
├── token_provider.py      # macOS Keychain OAuth 토큰 관리
├── usage_api.py           # Anthropic Usage API 클라이언트
├── stats_reader.py        # 로컬 stats-cache.json 파서
├── setup.py               # py2app 빌드 설정
├── run.sh                 # 실행 스크립트
└── com.local.claude-monitor.plist  # LaunchAgent 설정
```

## 동작 원리

1. Claude Code가 macOS Keychain에 저장한 OAuth 토큰을 읽음
2. `https://api.anthropic.com/api/oauth/usage` 엔드포인트로 사용량 조회
3. 토큰 만료 시 refresh token으로 자동 갱신
4. `~/.claude/stats-cache.json`에서 로컬 토큰 통계 보조 표시

## 참고

- Usage API는 비공식 엔드포인트로, rate limit이 엄격합니다 (토큰당 ~5회)
- Rate limit 초과 시 마지막 캐시된 결과를 표시합니다
- Claude Code가 설치되지 않은 경우 설치 안내 UI가 표시됩니다

## License

MIT
