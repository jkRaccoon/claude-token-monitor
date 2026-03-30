"""Claude Code statusline이 저장하는 rate limit 파일을 읽는 모듈.

Claude Code가 API 응답을 받을 때마다 statusline 스크립트가 실행되고,
rate limit 데이터를 /tmp/claude-rate-limits.json에 저장한다.
이 모듈은 그 파일을 읽기만 한다. API 호출 없음.
"""

import json
import os
from datetime import datetime, timezone, timedelta

RATE_LIMIT_FILE = "/tmp/claude-rate-limits.json"
STALE_THRESHOLD = 600  # 10분 이상 갱신 없으면 stale 취급


class RateLimitData:
    """개별 rate limit 윈도우 데이터."""
    def __init__(self, used_percentage, resets_at_epoch):
        self.utilization = used_percentage  # 0~100
        self.resets_at = None
        if resets_at_epoch:
            try:
                self.resets_at = datetime.fromtimestamp(resets_at_epoch, tz=timezone.utc)
            except (OSError, ValueError):
                pass

    @property
    def time_until_reset(self):
        if not self.resets_at:
            return None
        delta = self.resets_at - datetime.now(timezone.utc)
        return delta if delta.total_seconds() > 0 else None

    def reset_description(self):
        delta = self.time_until_reset
        if not delta:
            return "곧 리셋"
        total_seconds = int(delta.total_seconds())
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        if days > 0:
            return f"{days}일 {hours}시간"
        if hours > 0:
            return f"{hours}시간 {minutes}분"
        return f"{minutes}분"

    def reset_short(self):
        delta = self.time_until_reset
        if not delta:
            return "0m"
        total_seconds = int(delta.total_seconds())
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        if days > 0:
            return f"{days}d{hours}h"
        if hours > 0:
            return f"{hours}h{minutes}m"
        return f"{minutes}m"

    def reset_time_local(self):
        if not self.resets_at:
            return "알 수 없음"
        return self.resets_at.astimezone().strftime("%m/%d %H:%M")


class RateLimitResult:
    """rate limit 파일 전체 결과."""
    def __init__(self):
        self.five_hour = None      # RateLimitData
        self.seven_day = None      # RateLimitData
        self.timestamp = 0         # 마지막 갱신 epoch
        self.is_stale = True       # 데이터가 오래된 경우

    @property
    def worst_utilization(self):
        vals = []
        if self.five_hour:
            vals.append(self.five_hour.utilization)
        if self.seven_day:
            vals.append(self.seven_day.utilization)
        return max(vals) if vals else 0


class RateLimitReader:
    """rate limit 파일을 읽는다."""

    def __init__(self, file_path=RATE_LIMIT_FILE):
        self._file_path = file_path
        self._last_mtime = 0
        self._cached_result = None

    @property
    def has_data(self):
        return os.path.exists(self._file_path)

    def read(self):
        """파일에서 rate limit 데이터를 읽는다."""
        if not os.path.exists(self._file_path):
            return None

        # 파일이 변경되지 않았으면 캐시 반환
        try:
            mtime = os.path.getmtime(self._file_path)
        except OSError:
            return self._cached_result
        if mtime == self._last_mtime and self._cached_result:
            # stale 여부만 재계산
            import time
            self._cached_result.is_stale = (time.time() - self._cached_result.timestamp) > STALE_THRESHOLD
            return self._cached_result

        try:
            with open(self._file_path, "r") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return self._cached_result

        result = RateLimitResult()
        result.timestamp = data.get("timestamp", 0)

        import time
        result.is_stale = (time.time() - result.timestamp) > STALE_THRESHOLD

        five_h = data.get("five_hour", {})
        if five_h and five_h.get("used_percentage") is not None:
            result.five_hour = RateLimitData(
                five_h["used_percentage"],
                five_h.get("resets_at"),
            )

        seven_d = data.get("seven_day", {})
        if seven_d and seven_d.get("used_percentage") is not None:
            result.seven_day = RateLimitData(
                seven_d["used_percentage"],
                seven_d.get("resets_at"),
            )

        self._last_mtime = mtime
        self._cached_result = result
        return result


if __name__ == "__main__":
    reader = RateLimitReader()
    if not reader.has_data:
        print("rate limit 파일이 없습니다. Claude Code에서 대화를 시작하세요.")
    else:
        result = reader.read()
        if result and result.five_hour:
            print(f"5시간: {result.five_hour.utilization}% (리셋: {result.five_hour.reset_description()})")
        if result and result.seven_day:
            print(f"7일: {result.seven_day.utilization}% (리셋: {result.seven_day.reset_description()})")
        print(f"stale: {result.is_stale}")
