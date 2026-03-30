"""Claude Max 토큰 모니터 - macOS 메뉴바 앱."""

import os
import subprocess
import sys
import threading
import webbrowser

import rumps

from token_provider import TokenProvider
from usage_api import UsageAPI
from stats_reader import StatsReader

POLL_INTERVAL = 60  # 초
CLAUDE_CODE_INSTALL_URL = "https://docs.anthropic.com/en/docs/claude-code"


def format_number(n):
    """숫자를 천 단위 콤마로 포맷."""
    return f"{n:,}"


class ClaudeMonitorApp(rumps.App):
    def __init__(self):
        super().__init__("⏳", quit_button=None)

        self.token_provider = TokenProvider()
        self.usage_api = UsageAPI(self.token_provider)
        self.stats_reader = StatsReader()
        self._error_message = None
        self._setup_mode = False

        # 초기 상태 확인
        status, message = self.token_provider.check_status()

        if status != "ok":
            self._show_setup_ui(status, message)
        else:
            self._show_normal_ui()

    def _show_setup_ui(self, status, message):
        """Claude Code 미설치/미로그인 시 안내 UI."""
        self._setup_mode = True
        self.title = "⚠️ Claude Monitor"

        if status == "no_credentials":
            has_cli = subprocess.run(["which", "claude"], capture_output=True).returncode == 0
            if has_cli:
                self.menu = [
                    rumps.MenuItem("Claude Code 로그인이 필요합니다"),
                    rumps.separator,
                    rumps.MenuItem("터미널에서 'claude' 실행 후 로그인하세요"),
                    rumps.separator,
                    rumps.MenuItem("로그인 후 재시도", callback=self.on_retry),
                    rumps.MenuItem("종료", callback=self.on_quit),
                ]
            else:
                self.menu = [
                    rumps.MenuItem("Claude Code 설치가 필요합니다"),
                    rumps.separator,
                    rumps.MenuItem("1. Claude Code를 설치하세요"),
                    rumps.MenuItem("   터미널: npm install -g @anthropic-ai/claude-code"),
                    rumps.MenuItem("2. 'claude' 명령어로 로그인하세요"),
                    rumps.MenuItem("3. Claude Max 플랜이 활성화되어야 합니다"),
                    rumps.separator,
                    rumps.MenuItem("설치 가이드 열기", callback=self.on_open_install_guide),
                    rumps.MenuItem("설치 후 재시도", callback=self.on_retry),
                    rumps.MenuItem("종료", callback=self.on_quit),
                ]
        elif status == "no_oauth":
            self.menu = [
                rumps.MenuItem("OAuth 토큰이 없습니다"),
                rumps.separator,
                rumps.MenuItem("터미널에서 'claude' 실행 후 재로그인하세요"),
                rumps.separator,
                rumps.MenuItem("재시도", callback=self.on_retry),
                rumps.MenuItem("종료", callback=self.on_quit),
            ]
        elif status == "expired":
            self.menu = [
                rumps.MenuItem("토큰이 만료되었습니다"),
                rumps.separator,
                rumps.MenuItem("터미널에서 'claude' 실행 후 재로그인하세요"),
                rumps.separator,
                rumps.MenuItem("재시도", callback=self.on_retry),
                rumps.MenuItem("종료", callback=self.on_quit),
            ]

        # 셋업 모드에서도 주기적으로 재확인 (30초)
        self.timer = rumps.Timer(self.on_retry_tick, 30)
        self.timer.start()

    def _show_normal_ui(self):
        """정상 모니터링 UI."""
        self._setup_mode = False

        # 메뉴 구성
        self.menu_5h_title = rumps.MenuItem("5시간 사용량: --")
        self.menu_5h_reset = rumps.MenuItem("  리셋까지: --")
        self.menu_5h_time = rumps.MenuItem("  리셋 시각: --")

        self.menu_7d_title = rumps.MenuItem("7일 사용량: --")
        self.menu_7d_reset = rumps.MenuItem("  리셋까지: --")
        self.menu_7d_time = rumps.MenuItem("  리셋 시각: --")

        self.menu_today_header = rumps.MenuItem("오늘 토큰 사용량")
        self.menu_today_detail = rumps.MenuItem("  로딩 중...")

        self.menu_7d_total = rumps.MenuItem("최근 7일 합계: --")

        self.menu_status = rumps.MenuItem("마지막 갱신: --")
        self.menu_refresh = rumps.MenuItem("새로고침", callback=self.on_refresh)
        self.menu_quit = rumps.MenuItem("종료", callback=self.on_quit)

        self.menu.clear()
        self.menu = [
            self.menu_5h_title,
            self.menu_5h_reset,
            self.menu_5h_time,
            rumps.separator,
            self.menu_7d_title,
            self.menu_7d_reset,
            self.menu_7d_time,
            rumps.separator,
            self.menu_today_header,
            self.menu_today_detail,
            rumps.separator,
            self.menu_7d_total,
            rumps.separator,
            self.menu_status,
            self.menu_refresh,
            self.menu_quit,
        ]

        # 타이머 시작
        self.timer = rumps.Timer(self.on_tick, POLL_INTERVAL)
        self.timer.start()
        # 즉시 첫 갱신
        self._fetch_in_background()

    def on_tick(self, _):
        """타이머 콜백 - 백그라운드에서 데이터 갱신."""
        self._fetch_in_background()

    def _fetch_in_background(self):
        """메인 스레드 블로킹을 피하기 위해 백그라운드에서 API 호출."""
        thread = threading.Thread(target=self._fetch_and_update, daemon=True)
        thread.start()

    def _fetch_and_update(self):
        """API 호출 및 UI 업데이트."""
        try:
            result = self.usage_api.fetch_usage()
            self._error_message = None
            self._update_ui(result)
        except Exception as e:
            self._error_message = str(e)
            # 캐시된 결과가 있으면 계속 표시
            cached = self.usage_api.get_cached()
            if cached:
                self._update_ui(cached, stale=True)
            else:
                self.title = "⚠️ 오류"
                self.menu_status.title = f"오류: {self._error_message}"

    def _update_ui(self, result, stale=False):
        """API 결과로 메뉴바 UI 업데이트."""
        # 메뉴바 타이틀
        five_h = result.five_hour
        seven_d = result.seven_day
        if five_h and seven_d:
            stale_mark = "⚡" if stale else ""
            self.title = f"5H:{five_h.utilization:.0f}%({five_h.reset_short()}) 7D:{seven_d.utilization:.0f}%({seven_d.reset_short()}){stale_mark}"
        elif five_h:
            self.title = f"5H:{five_h.utilization:.0f}%({five_h.reset_short()})"
        elif seven_d:
            self.title = f"7D:{seven_d.utilization:.0f}%({seven_d.reset_short()})"

        # 아이콘 (사용률에 따라 이모지)
        worst = result.worst_utilization
        if worst >= 80:
            icon_prefix = "🔴"
        elif worst >= 50:
            icon_prefix = "🟡"
        else:
            icon_prefix = "🟢"
        self.title = f"{icon_prefix} {self.title}"

        # 5시간 사용량 메뉴
        if five_h:
            self.menu_5h_title.title = f"5시간 사용량: {five_h.utilization:.0f}%"
            self.menu_5h_reset.title = f"  리셋까지: {five_h.reset_description()}"
            self.menu_5h_time.title = f"  리셋 시각: {five_h.reset_time_local()}"

        # 7일 사용량 메뉴
        if seven_d:
            self.menu_7d_title.title = f"7일 사용량: {seven_d.utilization:.0f}%"
            self.menu_7d_reset.title = f"  리셋까지: {seven_d.reset_description()}"
            self.menu_7d_time.title = f"  리셋 시각: {seven_d.reset_time_local()}"

        # 로컬 통계
        today_tokens = self.stats_reader.get_today_tokens()
        if today_tokens:
            details = ", ".join(
                f"{model}: {format_number(count)}"
                for model, count in today_tokens.items()
            )
            self.menu_today_detail.title = f"  {details}"
        else:
            self.menu_today_detail.title = "  데이터 없음"

        total_7d = self.stats_reader.get_recent_days_tokens()
        self.menu_7d_total.title = f"최근 7일 합계: {format_number(total_7d)} tokens"

        # 상태
        from datetime import datetime
        now_str = datetime.now().strftime("%H:%M:%S")
        status = f"마지막 갱신: {now_str}"
        if stale:
            status += " (캐시)"
        self.menu_status.title = status

    def on_retry_tick(self, _):
        """셋업 모드에서 주기적으로 인증 상태 재확인."""
        status, message = self.token_provider.check_status()
        if status == "ok":
            self.timer.stop()
            self._show_normal_ui()

    def on_retry(self, _):
        """수동 재시도."""
        status, message = self.token_provider.check_status()
        if status == "ok":
            if hasattr(self, 'timer') and self.timer.is_alive():
                self.timer.stop()
            self._show_normal_ui()
        else:
            rumps.alert(
                title="Claude Monitor",
                message=message,
                ok="확인",
            )

    def on_open_install_guide(self, _):
        """Claude Code 설치 가이드 웹페이지를 연다."""
        webbrowser.open(CLAUDE_CODE_INSTALL_URL)

    def on_refresh(self, _):
        """수동 새로고침."""
        self.title = "⏳ 갱신중..."
        self._fetch_in_background()

    def on_quit(self, _):
        """앱 종료."""
        rumps.quit_application()


def main():
    ClaudeMonitorApp().run()


if __name__ == "__main__":
    main()
