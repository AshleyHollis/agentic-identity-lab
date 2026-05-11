from __future__ import annotations

import importlib
import importlib.machinery
import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
SHARED_PYTHON = ROOT / "apps" / "shared" / "python"
BFF_PYTHON = ROOT / "apps" / "bff" / "python-fastapi"
AGENT_PYTHON = ROOT / "apps" / "agent-execution" / "python-fastapi-agent-framework"
ISSUER = "https://login.microsoftonline.com/00000000-0000-0000-0000-000000000001/v2.0"
TRUSTED_TENANT = "00000000-0000-0000-0000-000000000001"

if str(SHARED_PYTHON) not in sys.path:
    sys.path.insert(0, str(SHARED_PYTHON))


def _bootstrap_package(name: str, package_path: Path) -> None:
    spec = importlib.machinery.ModuleSpec(name, loader=None, is_package=True)
    module = importlib.util.module_from_spec(spec)
    module.__path__ = [str(package_path)]
    sys.modules[name] = module


def _clear_package(name: str) -> None:
    for module_name in list(sys.modules):
        if module_name == name or module_name.startswith(f"{name}."):
            sys.modules.pop(module_name, None)


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict[str, Any]):
        self.status_code = status_code
        self._payload = payload

    def json(self) -> dict[str, Any]:
        return self._payload


def test_chat_session_invokes_agent_chain_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUTH_MODE", "mock")
    monkeypatch.setenv("AUTH_FIXTURE", "delegated-user")
    monkeypatch.setenv("AUTH_ISSUER", ISSUER)
    monkeypatch.setenv("AUTH_JWKS_URL", "https://login.microsoftonline.com/common/discovery/v2.0/keys")
    monkeypatch.setenv("TRUSTED_TENANTS", TRUSTED_TENANT)
    monkeypatch.setenv("ALLOWED_AUDIENCES", "api://00000000-0000-0000-0000-000000000101")
    monkeypatch.setenv("REQUIRED_SCOPES", "mcp.access")
    monkeypatch.setenv("CHAT_SESSION_CHAIN_ENABLED", "true")
    monkeypatch.setenv("AGENT_EXECUTION_BASE_URL", "http://agent-execution:8080")
    monkeypatch.setenv("AGENT_EXECUTION_INVOKE_PATH", "/agent/invoke")
    monkeypatch.setenv("DOWNSTREAM_TIMEOUT_SECONDS", "5")

    _clear_package("bff_chain_app")
    _bootstrap_package("bff_chain_app", BFF_PYTHON / "app")
    bff_main = importlib.import_module("bff_chain_app.main")

    captured: dict[str, Any] = {}

    def _fake_post(url: str, *, json: dict[str, Any], headers: dict[str, str], timeout: float):
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        captured["timeout"] = timeout
        return _FakeResponse(200, {"status": "accepted"})

    monkeypatch.setattr(bff_main.httpx, "post", _fake_post)

    response = TestClient(bff_main.app).post(
        "/chat/session",
        headers={
            "X-Identity-Lab-Fixture": "delegated-user",
            "Authorization": "Bearer inbound-user-token",
            "traceparent": "00-11111111111111111111111111111111-2222222222222222-01",
        },
        json={"display_name": "Safe Display Name"},
    )

    assert response.status_code == 200, response.text
    assert captured["url"] == "http://agent-execution:8080/agent/invoke"
    assert captured["headers"]["Authorization"] == "Bearer inbound-user-token"
    assert captured["headers"]["traceparent"].startswith("00-")
    assert captured["json"]["payload"]["operation"] == "chat_session"
    assert "display_name" not in str(captured["json"]).lower()


def test_agent_invoke_calls_mcp_authorization_check_when_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AUTH_MODE", "mock")
    monkeypatch.setenv("AUTH_FIXTURE", "delegated-gateway")
    monkeypatch.setenv("AUTH_ISSUER", ISSUER)
    monkeypatch.setenv("AUTH_JWKS_URL", "https://login.microsoftonline.com/common/discovery/v2.0/keys")
    monkeypatch.setenv("TRUSTED_TENANTS", TRUSTED_TENANT)
    monkeypatch.setenv("ALLOWED_AUDIENCES", "api://00000000-0000-0000-0000-000000000102")
    monkeypatch.setenv("REQUIRED_SCOPES", "mcp.access,mcp.write")
    monkeypatch.setenv("OBO_DOWNSTREAM_AUDIENCE", "api://00000000-0000-0000-0000-000000000103")
    monkeypatch.setenv("OBO_REQUIRED_SCOPES", "mcp.write")
    monkeypatch.setenv("MCP_CHAIN_ENABLED", "true")
    monkeypatch.setenv("MCP_PROTECTED_API_BASE_URL", "http://mcp-protected-api:8080")
    monkeypatch.setenv("MCP_AUTHORIZATION_CHECK_PATH", "/tools/authorization-check")
    monkeypatch.setenv("DOWNSTREAM_TIMEOUT_SECONDS", "5")

    _clear_package("agent_chain_app")
    _bootstrap_package("agent_chain_app", AGENT_PYTHON / "app")
    agent_main = importlib.import_module("agent_chain_app.main")

    captured: dict[str, Any] = {}

    def _fake_post(url: str, *, json: dict[str, Any], headers: dict[str, str], timeout: float):
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        captured["timeout"] = timeout
        return _FakeResponse(200, {"authorized": True, "correlation_id": "corr-downstream"})

    monkeypatch.setattr(agent_main.httpx, "post", _fake_post)

    response = TestClient(agent_main.app).post(
        "/agent/invoke",
        headers={
            "X-Identity-Lab-Fixture": "delegated-gateway",
            "Authorization": "Bearer inbound-user-token",
            "traceparent": "00-11111111111111111111111111111111-2222222222222222-01",
        },
        json={"payload": {"message": "hello"}},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["chain_exercised"] is True
    assert body["mcp_authorized"] is True
    assert body["mcp_correlation_id"] == "corr-downstream"
    assert captured["url"] == "http://mcp-protected-api:8080/tools/authorization-check"
    assert captured["headers"]["Authorization"] == "Bearer obo-token"
    assert captured["json"] == {}
