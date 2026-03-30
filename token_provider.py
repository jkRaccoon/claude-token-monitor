"""Claude Code OAuth 토큰을 macOS Keychain에서 읽어오는 모듈."""

import getpass
import json
import subprocess
import time
import requests


KEYCHAIN_SERVICE = "Claude Code-credentials"
REFRESH_URL = "https://console.anthropic.com/v1/oauth/token"
CLIENT_ID = "9d1c250a-e61b-44d9-88ed-5944d1962f5e"


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

    def _write_keychain(self, raw_data):
        """macOS Keychain에 credential JSON을 저장한다."""
        json_str = json.dumps(raw_data, separators=(",", ":"))
        cmd = [
            "security", "add-generic-password",
            "-s", KEYCHAIN_SERVICE,
            "-a", self._account,
            "-w", json_str,
            "-U",  # update if exists
        ]
        subprocess.run(cmd, capture_output=True, text=True)

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

    def _refresh_token(self, creds):
        """refresh token으로 새 access token을 발급받는다."""
        refresh_token = creds.get("refreshToken")
        if not refresh_token:
            raise RuntimeError("Refresh token이 없습니다. Claude Code에서 재인증하세요.")

        resp = requests.post(REFRESH_URL, json={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": CLIENT_ID,
        }, timeout=10)

        if resp.status_code != 200:
            raise RuntimeError(f"토큰 갱신 실패 (HTTP {resp.status_code}). Claude Code에서 재인증하세요.")

        return resp.json()

    def _update_keychain_with_new_token(self, raw_data, new_token_data):
        """새 토큰으로 Keychain을 업데이트한다."""
        expires_at_ms = int((time.time() + new_token_data.get("expires_in", 28800)) * 1000)
        updated_oauth = {
            "accessToken": new_token_data["access_token"],
            "refreshToken": new_token_data["refresh_token"],
            "expiresAt": expires_at_ms,
        }
        # 기존 필드 유지 (scopes, subscriptionType 등)
        if "claudeAiOauth" in raw_data:
            raw_data["claudeAiOauth"].update(updated_oauth)
        else:
            raw_data.update(updated_oauth)
        self._write_keychain(raw_data)

    def get_token(self):
        """유효한 access token을 반환한다."""
        # 메모리 캐시 확인
        if self._cached_token and time.time() < self._cached_token_expires:
            return self._cached_token

        raw_data, creds = self._get_oauth_creds()

        if self._is_expired(creds):
            new_data = self._refresh_token(creds)
            self._update_keychain_with_new_token(raw_data, new_data)
            self._cached_token = new_data["access_token"]
            self._cached_token_expires = time.time() + new_data.get("expires_in", 28800) - 300
        else:
            self._cached_token = creds["accessToken"]
            expires_at = creds.get("expiresAt", 0)
            if expires_at > 1e12:
                expires_at = expires_at / 1000
            self._cached_token_expires = expires_at - 300

        return self._cached_token

    def check_status(self):
        """Claude Code 설치 및 인증 상태를 확인한다.

        Returns:
            tuple: (status_code, message)
            status_code:
                "ok" - 정상
                "no_credentials" - Keychain에 credential 없음 (Claude Code 미설치/미로그인)
                "no_oauth" - credential은 있지만 OAuth 토큰 없음
                "expired" - 토큰 만료 + 갱신 실패
        """
        # 1. Claude Code CLI 존재 여부 확인
        cli_check = subprocess.run(["which", "claude"], capture_output=True, text=True)
        has_cli = cli_check.returncode == 0

        # 2. Keychain credential 확인
        try:
            raw_data = self._read_keychain_raw()
        except RuntimeError:
            if has_cli:
                return ("no_credentials", "Claude Code가 설치되어 있지만 로그인이 필요합니다.\n터미널에서 'claude' 명령어를 실행하여 로그인하세요.")
            return ("no_credentials", "Claude Code가 설치되어 있지 않습니다.\nhttps://docs.anthropic.com/en/docs/claude-code 에서 설치 후 로그인하세요.")

        # 3. OAuth 토큰 존재 여부
        oauth = raw_data.get("claudeAiOauth", raw_data)
        if not oauth.get("accessToken"):
            return ("no_oauth", "Claude Code 인증 정보에 OAuth 토큰이 없습니다.\n터미널에서 'claude' 명령어를 실행하여 재로그인하세요.")

        # 4. 토큰 유효성 확인
        if self._is_expired(oauth):
            try:
                self._refresh_token(oauth)
                return ("ok", "토큰이 갱신되었습니다.")
            except RuntimeError:
                return ("expired", "토큰이 만료되었고 갱신에 실패했습니다.\n터미널에서 'claude' 명령어를 실행하여 재로그인하세요.")

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
