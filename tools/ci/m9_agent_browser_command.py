from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import subprocess
import urllib.error
import urllib.request


def _required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _build_traceparent() -> str:
    return f"00-{secrets.token_hex(16)}-{secrets.token_hex(8)}-01"


def _scope_candidates(scope: str) -> list[str]:
    normalized_scope = scope.strip()
    candidates = [normalized_scope]
    if not normalized_scope.endswith("/.default"):
        audience = normalized_scope
        if "://" in normalized_scope:
            scheme, remainder = normalized_scope.split("://", 1)
            host = remainder.split("/", 1)[0]
            audience = f"{scheme}://{host}"
        elif "/" in normalized_scope:
            audience = normalized_scope.rsplit("/", 1)[0]
        candidates.append(f"{audience}/.default")
    return list(dict.fromkeys(candidate for candidate in candidates if candidate))


def _split_scopes(raw_scope_value: str) -> list[str]:
    return [value.strip() for value in re.split(r"[\s,;]+", raw_scope_value.strip()) if value.strip()]


def _get_access_token(scope_value: str) -> str:
    for scope in _split_scopes(scope_value):
        for candidate in _scope_candidates(scope):
            completed = subprocess.run(
                ["az", "account", "get-access-token", "--scope", candidate, "-o", "json"],
                capture_output=True,
                text=True,
                check=False,
            )
            if completed.returncode != 0:
                continue
            payload = json.loads(completed.stdout or "{}")
            token = str(payload.get("accessToken", "")).strip()
            if token:
                return token
    raise RuntimeError("Unable to acquire access token for smoke scope.")


def _json_payload(body: str) -> dict[str, object]:
    try:
        parsed = json.loads(body or "{}")
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _build_result(*, chat_url: str, status: int, payload: dict[str, object]) -> dict[str, object]:
    return {
        "ok": 200 <= status < 300,
        "status": status,
        "sessionIdPresent": bool(payload.get("session_id")),
        "expiresAtPresent": bool(payload.get("expires_at")),
        "targetUrlDigest": hashlib.sha256(chat_url.encode("utf-8")).hexdigest()[:12],
        "resultSource": "agent-browser-az-token",
    }


def main() -> int:
    chat_url = os.environ.get("M9_PLAYWRIGHT_CHAT_URL", "").strip()
    try:
        chat_url = _required("M9_PLAYWRIGHT_CHAT_URL")
        scope = _required("LIVE_SMOKE_SCOPES")
        timeout_seconds = int(
            os.environ.get("M9_AGENT_BROWSER_TIMEOUT_SECONDS", "").strip()
            or os.environ.get("M9_PLAYWRIGHT_TIMEOUT_SECONDS", "30").strip()
            or "30"
        )
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
        status = 0
        payload: dict[str, object] = {}
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                body = response.read().decode("utf-8") if response else ""
                payload = _json_payload(body)
                status = int(getattr(response, "status", 0) or 0)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore") if exc.fp else ""
            payload = _json_payload(body)
            status = int(getattr(exc, "code", 0) or 0)

        print(json.dumps(_build_result(chat_url=chat_url, status=status, payload=payload)))
        return 0
    except (OSError, ValueError, RuntimeError, urllib.error.URLError, json.JSONDecodeError):
        if chat_url:
            fallback_result = _build_result(chat_url=chat_url, status=0, payload={})
        else:
            fallback_result = {
                "ok": False,
                "status": 0,
                "sessionIdPresent": False,
                "expiresAtPresent": False,
                "targetUrlDigest": "",
                "resultSource": "agent-browser-az-token",
            }
        print(json.dumps(fallback_result))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
