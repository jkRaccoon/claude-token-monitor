"""~/.claude/stats-cache.json에서 로컬 토큰 사용 통계를 읽는 모듈."""

import json
import os
from datetime import datetime, timedelta

STATS_PATH = os.path.expanduser("~/.claude/stats-cache.json")


class StatsReader:
    def get_today_tokens(self):
        """오늘 모델별 토큰 사용량을 반환한다."""
        data = self._read()
        if not data:
            return {}
        today = datetime.now().strftime("%Y-%m-%d")
        for entry in reversed(data.get("dailyModelTokens", [])):
            if entry.get("date") == today:
                return entry.get("tokensByModel", {})
        return {}

    def get_recent_days_tokens(self, days=7):
        """최근 N일간 총 토큰 사용량을 반환한다."""
        data = self._read()
        if not data:
            return 0
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        total = 0
        for entry in data.get("dailyModelTokens", []):
            if entry.get("date", "") >= cutoff:
                for count in entry.get("tokensByModel", {}).values():
                    total += count
        return total

    def get_total_messages(self):
        """전체 메시지 수를 반환한다."""
        data = self._read()
        return data.get("totalMessages", 0) if data else 0

    def get_today_activity(self):
        """오늘의 활동 통계 (메시지 수, 세션 수)."""
        data = self._read()
        if not data:
            return {"messages": 0, "sessions": 0}
        today = datetime.now().strftime("%Y-%m-%d")
        for entry in reversed(data.get("dailyActivity", [])):
            if entry.get("date") == today:
                return {
                    "messages": entry.get("messageCount", 0),
                    "sessions": entry.get("sessionCount", 0),
                }
        return {"messages": 0, "sessions": 0}

    def _read(self):
        try:
            with open(STATS_PATH, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None


if __name__ == "__main__":
    reader = StatsReader()
    print("오늘 토큰:", reader.get_today_tokens())
    print(f"최근 7일 합계: {reader.get_recent_days_tokens():,} tokens")
    print(f"전체 메시지: {reader.get_total_messages():,}")
    print(f"오늘 활동: {reader.get_today_activity()}")
