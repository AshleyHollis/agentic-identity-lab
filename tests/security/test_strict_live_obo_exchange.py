from __future__ import annotations

import importlib
import importlib.machinery
import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest
from starlette.requests import Request

ROOT = Path(__file__).resolve().parents[2]
SHARED_PYTHON = ROOT / "apps" / "shared" / "python"
BFF_PYTHON = ROOT / "apps" / "bff" / "python-fastapi"
AGENT_PYTHON = ROOT / "apps" / "agent-execution" / "python-fastapi-agent-framework"

if str(SHARED_PYTHON) not in sys.path:
    sys.path.insert(0, str(SHARED_PYTHON))

from identity_lab_auth.guards import AuthContext  # noqa: E402
import identity_lab_auth.obo as obo_module  # noqa: E402

ISSUER = "https://login.microsoftonline.com/11111111-1111-4111-8111-111111111111/v2.0"
JWKS_URL = "https://login.microsoftonline.com/11111111-1111-4111-8111-111111111111/discovery/v2.0/keys"
TENANT = "11111111-1111-4111-8111-111111111111"
BFF_AUD = "api://11111111-1111-4111-8111-111111111101"
AGENT_AUD = "api://11111111-1111-4111-8111-111111111102"
MCP_AUD = "api://11111111-1111-4111-8111-111111111103"
TOKEN_URL = "https://login.microsoftonline.com/11111111-1111-4111-8111-111111111111/oauth2/v2.0/token"


class _FakeResponse:
    def __init__(self, status_code: int = 200, payload: dict[str, Any] | None = None):
        self.status_code = status_code
        self._payload = payload or {
            "access_token": "redacted-exchanged-access-token",
            "token_type": "Bearer",
        }

    def json(self) -> dict[str, Any]:
        return self._payload


def _bootstrap_package(name: str, package_path: Path) -> None:
    spec = importlib.machinery.ModuleSpec(name, loader=None, is_package=True)
    module = importlib.util.module_from_spec(spec)
    module.__path__ = [str(package_path)]
    sys.modules[name] = module


def _clear_package(name: str) -> None:
    for module_name in list(sys.modules):
        if module_name == name or module_name.startswith(f"{name}."):
            sys.modules.pop(module_name, None)


def _request(headers: dict[str, str]) -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/",
            "headers": [(key.lower().encode(), value.encode()) for key, value in headers.items()],
        }
    )


def _strict_common_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUTH_MODE", "strict")
    monkeypatch.setenv("AUTH_ISSUER", ISSUER)
    monkeypatch.setenv("AUTH_JWKS_URL", JWKS_URL)
    monkeypatch.setenv("TRUSTED_TENANTS", TENANT)
    monkeypatch.setenv("OBO_TOKEN_URL", TOKEN_URL)
    monkeypatch.setenv("OBO_CLIENT_ID", "protected-client-id-placeholder")
    monkeypatch.setenv("OBO_CLIENT_SECRET", "protected-client-secret-placeholder")
    monkeypatch.setenv("DOWNSTREAM_TIMEOUT_SECONDS", "5")


def test_bff_strict_chain_exchanges_inbound_token_before_agent_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _strict_common_env(monkeypatch)
    monkeypatch.setenv("ALLOWED_AUDIENCES", BFF_AUD)
    monkeypatch.setenv("REQUIRED_SCOPES", "bff.access")
    monkeypatch.setenv("CHAT_SESSION_CHAIN_ENABLED", "true")
    monkeypatch.setenv("AGENT_EXECUTION_BASE_URL", "https://agent.example.invalid")
    monkeypatch.setenv("OBO_REQUIRED_SCOPES", f"{AGENT_AUD}/.default")

    _clear_package("bff_strict_obo_app")
    _bootstrap_package("bff_strict_obo_app", BFF_PYTHON / "app")
    bff_main = importlib.import_module("bff_strict_obo_app.main")

    captured: dict[str, Any] = {}

    def _fake_post(url: str, *, data: dict[str, Any], headers: dict[str, str], timeout: float):
        captured["url"] = url
        captured["data"] = data
        captured["headers"] = headers
        captured["timeout"] = timeout
        return _FakeResponse()

    monkeypatch.setattr(bff_main.httpx, "post", _fake_post)

    auth_context = AuthContext.from_claims(
        {"aud": BFF_AUD, "scp": "bff.access", "iss": ISSUER, "tid": TENANT},
        token_type="delegated",
        correlation_id="correlation-placeholder",
    )
    headers = bff_main._build_forward_headers(
        _request({"Authorization": "Bearer redacted-bff-audience-assertion"}),
        auth_context,
    )

    assert headers["Authorization"] == "Bearer redacted-exchanged-access-token"
    assert captured["url"] == TOKEN_URL
    assert captured["data"]["assertion"] == "redacted-bff-audience-assertion"
    assert captured["data"]["scope"] == f"{AGENT_AUD}/.default"


def test_agent_strict_chain_exchanges_inbound_token_before_mcp_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _strict_common_env(monkeypatch)
    monkeypatch.setenv("ALLOWED_AUDIENCES", AGENT_AUD)
    monkeypatch.setenv("REQUIRED_SCOPES", "agent.access")
    monkeypatch.setenv("BLUEPRINT_AUDIENCE", AGENT_AUD)
    monkeypatch.setenv("MCP_CHAIN_ENABLED", "true")
    monkeypatch.setenv("MCP_PROTECTED_API_BASE_URL", "https://mcp.example.invalid")
    monkeypatch.setenv("OBO_DOWNSTREAM_AUDIENCE", MCP_AUD)
    monkeypatch.setenv("OBO_REQUIRED_SCOPES", f"{MCP_AUD}/.default")

    _clear_package("agent_strict_obo_app")
    _bootstrap_package("agent_strict_obo_app", AGENT_PYTHON / "app")
    agent_auth = importlib.import_module("agent_strict_obo_app.auth")

    captured: dict[str, Any] = {}

    def _fake_post(url: str, *, data: dict[str, Any], headers: dict[str, str], timeout: float):
        captured["url"] = url
        captured["data"] = data
        captured["headers"] = headers
        captured["timeout"] = timeout
        return _FakeResponse()

    monkeypatch.setattr(obo_module.httpx, "post", _fake_post)

    auth_context = AuthContext.from_claims(
        {"aud": AGENT_AUD, "scp": "agent.access", "iss": ISSUER, "tid": TENANT},
        token_type="delegated",
        correlation_id="correlation-placeholder",
    )
    exchange = agent_auth.exchange_for_mcp(
        auth_context,
        authorization="Bearer redacted-agent-audience-assertion",
    )

    assert exchange.authorization == "Bearer redacted-exchanged-access-token"
    assert exchange.claims["aud"] == MCP_AUD
    assert captured["url"] == TOKEN_URL
    assert captured["data"]["assertion"] == "redacted-agent-audience-assertion"
    assert captured["data"]["scope"] == f"{MCP_AUD}/.default"


def test_bff_strict_chain_fails_fast_without_obo_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _strict_common_env(monkeypatch)
    monkeypatch.delenv("OBO_CLIENT_SECRET", raising=False)
    monkeypatch.setenv("ALLOWED_AUDIENCES", BFF_AUD)
    monkeypatch.setenv("REQUIRED_SCOPES", "bff.access")
    monkeypatch.setenv("CHAT_SESSION_CHAIN_ENABLED", "true")
    monkeypatch.setenv("AGENT_EXECUTION_BASE_URL", "https://agent.example.invalid")
    monkeypatch.setenv("OBO_REQUIRED_SCOPES", f"{AGENT_AUD}/.default")

    _clear_package("bff_missing_obo_app")
    _bootstrap_package("bff_missing_obo_app", BFF_PYTHON / "app")
    with pytest.raises(ValueError, match="OBO_CLIENT_SECRET"):
        importlib.import_module("bff_missing_obo_app.config").load_settings()


def test_agent_strict_chain_fails_fast_without_obo_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _strict_common_env(monkeypatch)
    monkeypatch.delenv("OBO_CLIENT_SECRET", raising=False)
    monkeypatch.setenv("ALLOWED_AUDIENCES", AGENT_AUD)
    monkeypatch.setenv("REQUIRED_SCOPES", "agent.access")
    monkeypatch.setenv("BLUEPRINT_AUDIENCE", AGENT_AUD)
    monkeypatch.setenv("MCP_CHAIN_ENABLED", "true")
    monkeypatch.setenv("MCP_PROTECTED_API_BASE_URL", "https://mcp.example.invalid")
    monkeypatch.setenv("OBO_DOWNSTREAM_AUDIENCE", MCP_AUD)
    monkeypatch.setenv("OBO_REQUIRED_SCOPES", f"{MCP_AUD}/.default")

    _clear_package("agent_missing_obo_app")
    _bootstrap_package("agent_missing_obo_app", AGENT_PYTHON / "app")
    with pytest.raises(ValueError, match="OBO_CLIENT_SECRET"):
        importlib.import_module("agent_missing_obo_app.config").load_settings()
