from __future__ import annotations

import io
import json
import sys
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import tools.ci.m9_agent_browser_command as command  # noqa: E402


def test_split_scopes_supports_multiple_delimiters() -> None:
    scopes = command._split_scopes("api://one/access_as_user api://two/.default,api://three/read;api://four")
    assert scopes == [
        "api://one/access_as_user",
        "api://two/.default",
        "api://three/read",
        "api://four",
    ]


def test_scope_candidates_include_default_variant() -> None:
    assert command._scope_candidates("api://contoso/access_as_user") == [
        "api://contoso/access_as_user",
        "api://contoso/.default",
    ]


def test_get_access_token_tries_multiple_scope_candidates(monkeypatch) -> None:
    calls: list[str] = []

    class FakeCompleted:
        def __init__(self, *, returncode: int, stdout: str) -> None:
            self.returncode = returncode
            self.stdout = stdout

    def _fake_run(args, **_kwargs):  # type: ignore[no-untyped-def]
        scope = args[4]
        calls.append(scope)
        if scope == "api://second/.default":
            return FakeCompleted(returncode=0, stdout=json.dumps({"accessToken": "token-2"}))
        return FakeCompleted(returncode=1, stdout="{}")

    monkeypatch.setattr(command.subprocess, "run", _fake_run)

    token = command._get_access_token("api://first/access_as_user api://second/read")

    assert token == "token-2"
    assert "api://first/access_as_user" in calls
    assert "api://first/.default" in calls
    assert "api://second/read" in calls
    assert "api://second/.default" in calls


def test_main_outputs_json_and_zero_on_http_error(monkeypatch, capsys) -> None:
    monkeypatch.setenv("M9_PLAYWRIGHT_CHAT_URL", "https://contoso.example.com/chat/session")
    monkeypatch.setenv("LIVE_SMOKE_SCOPES", "api://contoso/access_as_user")
    monkeypatch.setattr(command, "_get_access_token", lambda _scope: "token")

    def _fake_urlopen(_request, timeout=30):  # type: ignore[no-untyped-def]
        payload = io.BytesIO(b'{"error":"unauthorized"}')
        raise urllib.error.HTTPError(
            url="https://contoso.example.com/chat/session",
            code=401,
            msg="Unauthorized",
            hdrs=None,
            fp=payload,
        )

    monkeypatch.setattr(command.urllib.request, "urlopen", _fake_urlopen)

    rc = command.main()
    output = capsys.readouterr().out.strip()
    payload = json.loads(output)

    assert rc == 0
    assert payload["ok"] is False
    assert payload["status"] == 401
    assert payload["resultSource"] == "agent-browser-az-token"
    assert payload["targetUrlDigest"]


def test_main_outputs_fallback_json_and_zero_on_preflight_error(monkeypatch, capsys) -> None:
    monkeypatch.delenv("M9_PLAYWRIGHT_CHAT_URL", raising=False)
    monkeypatch.delenv("LIVE_SMOKE_SCOPES", raising=False)

    rc = command.main()
    output = capsys.readouterr().out.strip()
    payload = json.loads(output)

    assert rc == 0
    assert payload["ok"] is False
    assert payload["status"] == 0
    assert payload["sessionIdPresent"] is False
    assert payload["expiresAtPresent"] is False
