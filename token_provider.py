"""Claude Code OAuth 토큰을 macOS Keychain에서 읽어오는 모듈.

이 모듈은 토큰을 읽기만 하며, 직접 갱신하지 않는다.
토큰 갱신은 Claude Code가 담당한다.
갱신 시 이전 access token이 즉시 무효화되므로,
이 앱에서 갱신하면 Claude Code 작업이 중단될 수 있다.
"""

import getpass
import json
import subprocess
import time


KEYCHAIN_SERVICE = "Claude Code-credentials"


class TokenProvider:
    def __init__(self, account=None):
        self._account = account or getpass.getuser()
        self._cached_token = None
        self._cached_token_expires = 0

    def _read_keychain_raw(self):
        """macOS Keychain에서 전체 credential JSON을 읽는다."""
        cmd = ["security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-a", self._account, "-w"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Keychain 읽기 실패: {result.stderr.strip()}")
        return json.loads(result.stdout.strip())

    def _get_oauth_creds(self):
        """claudeAiOauth 부분을 추출한다."""
        data = self._read_keychain_raw()
        if "claudeAiOauth" in data:
            return data, data["claudeAiOauth"]
        return data, data

    def _is_expired(self, creds):
        """토큰이 만료되었거나 5분 내 만료 예정인지 확인."""
        expires_at = creds.get("expiresAt", 0)
        if expires_at > 1e12:
            expires_at = expires_at / 1000
        return time.time() > (expires_at - 300)

    def get_token(self):
        """Keychain에서 현재 access token을 읽어 반환한다.

        직접 토큰을 갱신하지 않는다. Claude Code가 토큰을 갱신하면
        Keychain이 업데이트되고, 다음 호출 시 새 토큰을 읽게 된다.
        """
        if self._cached_token and time.time() < self._cached_token_expires:
            return self._cached_token

        _, creds = self._get_oauth_creds()
        self._cached_token = creds["accessToken"]
        self._cached_token_expires = time.time() + 10

        return self._cached_token

    def check_status(self):
        """Claude Code 설치 및 인증 상태를 확인한다.

        Returns:
            tuple: (status_code, message)
        """
        cli_check = subprocess.run(["which", "claude"], capture_output=True, text=True)
        has_cli = cli_check.returncode == 0

        try:
            raw_data = self._read_keychain_raw()
        except RuntimeError:
            if has_cli:
                return ("no_credentials", "Claude Code가 설치되어 있지만 로그인이 필요합니다.\n터미널에서 'claude' 명령어를 실행하여 로그인하세요.")
            return ("no_credentials", "Claude Code가 설치되어 있지 않습니다.\nhttps://docs.anthropic.com/en/docs/claude-code 에서 설치 후 로그인하세요.")

        oauth = raw_data.get("claudeAiOauth", raw_data)
        if not oauth.get("accessToken"):
            return ("no_oauth", "Claude Code 인증 정보에 OAuth 토큰이 없습니다.\n터미널에서 'claude' 명령어를 실행하여 재로그인하세요.")

        if self._is_expired(oauth):
            return ("expired", "토큰이 만료되었습니다.\nClaude Code를 실행하면 자동으로 갱신됩니다.")

        return ("ok", "정상")

    def get_token_info(self):
        """토큰 정보 요약을 반환한다 (디버그용)."""
        try:
            _, creds = self._get_oauth_creds()
            expires_at = creds.get("expiresAt", 0)
            if expires_at > 1e12:
                expires_at = expires_at / 1000
            remaining = expires_at - time.time()
            return {
                "has_access_token": bool(creds.get("accessToken")),
                "has_refresh_token": bool(creds.get("refreshToken")),
                "expires_in_seconds": max(0, int(remaining)),
                "is_expired": remaining <= 0,
                "subscription_type": creds.get("subscriptionType"),
                "rate_limit_tier": creds.get("rateLimitTier"),
            }
        except Exception as e:
            return {"error": str(e)}


if __name__ == "__main__":
    provider = TokenProvider()
    info = provider.get_token_info()
    print("토큰 정보:", json.dumps(info, indent=2, ensure_ascii=False))
    try:
        token = provider.get_token()
        print(f"Access token: {token[:20]}...{token[-10:]}")
    except Exception as e:
        print(f"토큰 읽기 실패: {e}")
