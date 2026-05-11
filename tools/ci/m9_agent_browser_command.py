from __future__ import annotations

import hashlib
import json
import os
import secrets
import subprocess
import sys
import urllib.error
import urllib.request


def _required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _build_traceparent() -> str:
    return f"00-{secrets.token_hex(16)}-{secrets.token_hex(8)}-01"


def _get_access_token(scope: str) -> str:
    completed = subprocess.run(
        ["az", "account", "get-access-token", "--scope", scope, "-o", "json"],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError("Unable to acquire access token for smoke scope.")
    payload = json.loads(completed.stdout or "{}")
    token = str(payload.get("accessToken", "")).strip()
    if not token:
        raise RuntimeError("Access token response missing token value.")
    return token


def main() -> int:
    try:
        chat_url = _required("M9_PLAYWRIGHT_CHAT_URL")
        scope = _required("LIVE_SMOKE_SCOPES")
        timeout_seconds = int(os.environ.get("M9_PLAYWRIGHT_TIMEOUT_SECONDS", "30").strip() or "30")
        token = _get_access_token(scope)
        request = urllib.request.Request(
            chat_url,
            data=json.dumps({"display_name": "M9 Browser Smoke"}).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "traceparent": _build_traceparent(),
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            body = response.read().decode("utf-8") if response else ""
            payload = json.loads(body or "{}")
            result = {
                "ok": 200 <= response.status < 300,
                "status": response.status,
                "sessionIdPresent": bool(payload.get("session_id")),
                "expiresAtPresent": bool(payload.get("expires_at")),
                "targetUrlDigest": hashlib.sha256(chat_url.encode("utf-8")).hexdigest()[:12],
                "resultSource": "agent-browser-az-token",
            }
            print(json.dumps(result))
            return 0
    except (OSError, ValueError, RuntimeError, urllib.error.URLError, json.JSONDecodeError) as exc:
        print(f"agent-browser command failed: {exc.__class__.__name__}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
