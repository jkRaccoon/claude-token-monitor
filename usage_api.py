"""Claude Max 플랜 사용량 API 클라이언트."""

import requests
from datetime import datetime, timezone

USAGE_URL = "https://api.anthropic.com/api/oauth/usage"


class UsageData:
    """파싱된 사용량 데이터."""
    def __init__(self, utilization, resets_at):
        self.utilization = utilization  # 0~100 퍼센트
        self.resets_at = resets_at      # datetime (UTC)

    @property
    def time_until_reset(self):
        """리셋까지 남은 시간 (timedelta)."""
        if not self.resets_at:
            return None
        now = datetime.now(timezone.utc)
        delta = self.resets_at - now
        if delta.total_seconds() < 0:
            return None
        return delta

    def reset_description(self):
        """리셋까지 남은 시간을 한국어 문자열로 반환."""
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
        """메뉴바 타이틀용 짧은 리셋 시간 문자열."""
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
        """리셋 시각을 로컬 시간 문자열로 반환."""
        if not self.resets_at:
            return "알 수 없음"
        local_time = self.resets_at.astimezone()
        return local_time.strftime("%m/%d %H:%M")


class UsageResult:
    """Usage API 응답 전체."""
    def __init__(self):
        self.five_hour = None       # UsageData
        self.seven_day = None       # UsageData
        self.seven_day_opus = None   # UsageData (optional)
        self.seven_day_sonnet = None # UsageData (optional)
        self.extra_usage_enabled = False
        self.raw = None

    @property
    def worst_utilization(self):
        """가장 높은 사용률을 반환."""
        vals = []
        if self.five_hour:
            vals.append(self.five_hour.utilization)
        if self.seven_day:
            vals.append(self.seven_day.utilization)
        return max(vals) if vals else 0


MAX_REQUESTS_PER_TOKEN = 5


class UsageAPI:
    def __init__(self, token_provider):
        self._token_provider = token_provider
        self._last_result = None
        self._request_count = 0

    @property
    def remaining_requests(self):
        """현재 토큰으로 남은 API 호출 횟수."""
        return max(0, MAX_REQUESTS_PER_TOKEN - self._request_count)

    def _parse_window(self, data):
        """개별 윈도우 데이터를 UsageData로 파싱."""
        if not data:
            return None
        utilization = data.get("utilization", 0)
        resets_at = None
        reset_str = data.get("resets_at")
        if reset_str:
            try:
                resets_at = datetime.fromisoformat(reset_str)
                if resets_at.tzinfo is None:
                    resets_at = resets_at.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                pass
        return UsageData(utilization, resets_at)

    def _call_api(self, token):
        """Usage API를 호출한다."""
        return requests.get(USAGE_URL, headers={
            "Authorization": f"Bearer {token}",
            "anthropic-beta": "oauth-2025-04-20",
        }, timeout=10)

    def fetch_usage(self):
        """Usage API를 호출하여 사용량 정보를 가져온다."""
        token = self._token_provider.get_token()
        resp = self._call_api(token)
        self._request_count += 1

        # 429/401 시 토큰 갱신 후 재시도
        if resp.status_code in (401, 429):
            try:
                self._token_provider.force_refresh()
                self._request_count = 0
                new_token = self._token_provider.get_token()
                resp = self._call_api(new_token)
                self._request_count += 1
            except Exception:
                pass

        if resp.status_code == 401:
            raise RuntimeError("인증 실패. Claude Code에서 재인증 필요.")
        if resp.status_code == 429:
            if self._last_result:
                return self._last_result
            raise RuntimeError("Rate limit 초과. 잠시 후 다시 시도합니다.")
        if resp.status_code != 200:
            raise RuntimeError(f"API 오류 (HTTP {resp.status_code})")

        data = resp.json()
        result = UsageResult()
        result.raw = data
        result.five_hour = self._parse_window(data.get("five_hour"))
        result.seven_day = self._parse_window(data.get("seven_day"))
        result.seven_day_opus = self._parse_window(data.get("seven_day_opus"))
        result.seven_day_sonnet = self._parse_window(data.get("seven_day_sonnet"))

        extra = data.get("extra_usage", {})
        result.extra_usage_enabled = extra.get("is_enabled", False) if extra else False

        self._last_result = result
        return result

    def get_cached(self):
        """마지막 성공 결과를 반환."""
        return self._last_result


if __name__ == "__main__":
    import json
    from token_provider import TokenProvider

    provider = TokenProvider()
    api = UsageAPI(provider)

    print("Usage API 호출 중...")
    try:
        result = api.fetch_usage()
        if result.five_hour:
            print(f"\n5시간 사용량: {result.five_hour.utilization}%")
            print(f"  리셋까지: {result.five_hour.reset_description()}")
            print(f"  리셋 시각: {result.five_hour.reset_time_local()}")
        if result.seven_day:
            print(f"\n7일 사용량: {result.seven_day.utilization}%")
            print(f"  리셋까지: {result.seven_day.reset_description()}")
            print(f"  리셋 시각: {result.seven_day.reset_time_local()}")
        if result.seven_day_sonnet:
            print(f"\n7일 Sonnet: {result.seven_day_sonnet.utilization}%")
        print(f"\n최대 사용률: {result.worst_utilization}%")
    except Exception as e:
        print(f"API 호출 실패: {e}")
