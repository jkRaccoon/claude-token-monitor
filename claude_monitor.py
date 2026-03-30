"""Claude Max 토큰 모니터 - macOS 메뉴바 앱.

데이터 소스 (하이브리드):
  1. Primary: Claude Code statusline → /tmp/claude-rate-limits.json (5초 간격)
  2. Fallback: 키체인 토큰(읽기 전용) → Usage API (stale 시 60초 간격)

키체인 토큰은 읽기만 하므로 Claude Code 세션에 영향 없음.
Usage API는 User-Agent: claude-code로 호출하여 rate limit 완화.
"""

import subprocess
import threading
import time
import webbrowser
from datetime import datetime

import rumps

from rate_limit_reader import RateLimitReader
from token_provider import TokenProvider
from usage_api import UsageAPI
from stats_reader import StatsReader

POLL_INTERVAL = 5  # 초
API_POLL_INTERVAL = 60  # API fallback 간격 (초)


def format_number(n):
    return f"{n:,}"


def progress_bar(percent, width=15):
    filled = int(width * percent / 100)
    return "▓" * filled + "░" * (width - filled)


class ClaudeMonitorApp(rumps.App):
    def __init__(self):
        super().__init__("⏳", quit_button=None)

        self.token_provider = TokenProvider()
        self.rate_limit_reader = RateLimitReader()
        self.usage_api = UsageAPI(self.token_provider)
        self.stats_reader = StatsReader()
        self._last_api_call = 0
        self._api_cache = None

        status, message = self.token_provider.check_status()
        if status != "ok":
            self._show_setup_ui(status, message)
        else:
            self._show_normal_ui()

    # ─── 셋업 UI ───

    def _show_setup_ui(self, status, message):
        self.title = "⚠️ Claude"

        has_cli = subprocess.run(
            ["which", "claude"], capture_output=True
        ).returncode == 0

        if status == "no_credentials" and not has_cli:
            self.menu = [
                rumps.MenuItem("Claude Code 설치가 필요합니다"),
                rumps.separator,
                rumps.MenuItem("1. Claude Code를 설치하세요"),
                rumps.MenuItem("   터미널: npm install -g @anthropic-ai/claude-code"),
                rumps.MenuItem("2. 'claude' 명령어로 로그인하세요"),
                rumps.separator,
                rumps.MenuItem(
                    "설치 가이드 열기",
                    callback=lambda _: webbrowser.open(
                        "https://docs.anthropic.com/en/docs/claude-code"
                    ),
                ),
                rumps.MenuItem("설치 후 재시도", callback=self.on_retry),
                rumps.MenuItem("종료", callback=self.on_quit),
            ]
        else:
            self.menu = [
                rumps.MenuItem(message.split("\n")[0]),
                rumps.separator,
                rumps.MenuItem("재시도", callback=self.on_retry),
                rumps.MenuItem("종료", callback=self.on_quit),
            ]

        self.timer = rumps.Timer(self._retry_tick, 30)
        self.timer.start()

    def _retry_tick(self, _):
        status, _ = self.token_provider.check_status()
        if status == "ok":
            self.timer.stop()
            self._show_normal_ui()

    def on_retry(self, _):
        status, message = self.token_provider.check_status()
        if status == "ok":
            if hasattr(self, "timer") and self.timer.is_alive():
                self.timer.stop()
            self._show_normal_ui()
        else:
            rumps.alert(title="Claude Monitor", message=message, ok="확인")

    # ─── 정상 모니터링 UI ───

    def _show_normal_ui(self):
        self.menu_5h_title = rumps.MenuItem("5시간 사용량: --")
        self.menu_5h_reset = rumps.MenuItem("  리셋까지: --")
        self.menu_5h_time = rumps.MenuItem("  리셋 시각: --")

        self.menu_7d_title = rumps.MenuItem("7일 사용량: --")
        self.menu_7d_reset = rumps.MenuItem("  리셋까지: --")
        self.menu_7d_time = rumps.MenuItem("  리셋 시각: --")

        self.menu_today_header = rumps.MenuItem("오늘 토큰 사용량")
        self.menu_today_detail = rumps.MenuItem("  로딩 중...")
        self.menu_7d_total = rumps.MenuItem("최근 7일 합계: --")

        self.menu_source = rumps.MenuItem("소스: --")
        self.menu_status = rumps.MenuItem("대기 중...")
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
            self.menu_source,
            self.menu_status,
            self.menu_refresh,
            self.menu_quit,
        ]

        self.timer = rumps.Timer(self._on_tick, POLL_INTERVAL)
        self.timer.start()
        self._fetch_in_background()

    # ─── 데이터 갱신 ───

    def _on_tick(self, _):
        self._fetch_in_background()

    def _fetch_in_background(self):
        threading.Thread(target=self._fetch_and_update, daemon=True).start()

    def _fetch_and_update(self):
        """하이브리드: statusline 파일(primary) → Usage API(fallback, 60초)."""
        # 1차: statusline 파일 (fresh)
        file_result = self.rate_limit_reader.read()
        if file_result and not file_result.is_stale:
            self._update_ui(file_result, source="statusline")
            return

        # 2차: Usage API (60초 간격, 429 대기 중이면 스킵)
        now = time.time()
        if now - self._last_api_call >= API_POLL_INTERVAL and now >= self.usage_api.rate_limited_until:
            self._last_api_call = now
            try:
                api_result = self.usage_api.fetch_usage()
                if api_result:
                    self._api_cache = api_result
                    self._update_ui_api(api_result, source="API")
                    return
            except Exception:
                pass

        # 3차: API 캐시
        if self._api_cache:
            self._update_ui_api(self._api_cache, source="API (캐시)")
            return

        # 4차: stale statusline
        if file_result:
            self._update_ui(file_result, source="statusline (stale)")
            return

        # 데이터 없음
        self.title = "⏳ 대기"
        self.menu_source.title = "소스: 데이터 없음"
        self.menu_status.title = "Claude에서 대화를 시작하세요"

    # ─── UI 업데이트 ───

    def _update_ui(self, result, source=""):
        """RateLimitResult(statusline)로 UI 업데이트."""
        five_h = result.five_hour
        seven_d = result.seven_day
        worst = result.worst_utilization

        self._set_title(five_h, worst)
        self._set_5h(five_h)
        self._set_7d(seven_d)
        self._set_stats()
        self._set_status(source)

    def _update_ui_api(self, api_result, source=""):
        """UsageResult(API)로 UI 업데이트."""
        five_h = api_result.five_hour
        seven_d = api_result.seven_day
        worst = api_result.worst_utilization

        self._set_title(five_h, worst)
        self._set_5h(five_h)
        self._set_7d(seven_d)
        self._set_stats()

        if api_result.is_rate_limited:
            api_result.is_rate_limited = False
        self._set_status(source)

    def _set_title(self, five_h, worst):
        if five_h:
            icon = "🔴" if worst >= 80 else "🟡" if worst >= 50 else "🟢"
            self.title = f"{icon} {five_h.utilization:.0f}% · {five_h.reset_short()}"
        else:
            self.title = "⏳ --"

    def _set_5h(self, five_h):
        if five_h:
            bar = progress_bar(five_h.utilization)
            self.menu_5h_title.title = f"5시간  {bar} {five_h.utilization:.0f}%"
            self.menu_5h_reset.title = f"  리셋까지: {five_h.reset_description()}"
            self.menu_5h_time.title = f"  리셋 시각: {five_h.reset_time_local()}"

    def _set_7d(self, seven_d):
        if seven_d:
            bar = progress_bar(seven_d.utilization)
            self.menu_7d_title.title = f"7일    {bar} {seven_d.utilization:.0f}%"
            self.menu_7d_reset.title = f"  리셋까지: {seven_d.reset_description()}"
            self.menu_7d_time.title = f"  리셋 시각: {seven_d.reset_time_local()}"

    def _set_stats(self):
        today_tokens = self.stats_reader.get_today_tokens()
        if today_tokens:
            details = ", ".join(
                f"{m}: {format_number(c)}" for m, c in today_tokens.items()
            )
            self.menu_today_detail.title = f"  {details}"
        else:
            self.menu_today_detail.title = "  데이터 없음"

        total_7d = self.stats_reader.get_recent_days_tokens()
        self.menu_7d_total.title = f"최근 7일 합계: {format_number(total_7d)} tokens"

    def _set_status(self, source):
        now_str = datetime.now().strftime("%H:%M:%S")

        # 429 카운트다운
        remaining = self.usage_api.rate_limited_until - time.time()
        if remaining > 0:
            mins = int(remaining) // 60
            secs = int(remaining) % 60
            source = f"API 제한 ({mins}:{secs:02d} 후 재시도)"

        self.menu_source.title = f"소스: {source}"
        self.menu_status.title = f"마지막 갱신: {now_str}"

    # ─── 액션 ───

    def on_refresh(self, _):
        self.title = "⏳ 갱신중..."
        self._last_api_call = 0
        self._fetch_in_background()

    def on_quit(self, _):
        rumps.quit_application()


def main():
    ClaudeMonitorApp().run()


if __name__ == "__main__":
    main()
