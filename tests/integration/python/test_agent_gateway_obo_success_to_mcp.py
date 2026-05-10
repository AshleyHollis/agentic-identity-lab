from __future__ import annotations

import importlib
import importlib.machinery
import importlib.util
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[3]
SHARED_PYTHON = ROOT / "apps" / "shared" / "python"
GATEWAY_PYTHON = ROOT / "apps" / "agent-execution" / "python-fastapi-agent-framework"
MCP_PYTHON = ROOT / "apps" / "mcp-protected-api" / "python-fastapi"

sys.path.append(str(SHARED_PYTHON))

FIXTURE_HEADER = "X-Identity-Lab-Fixture"
ISSUER = "https://login.microsoftonline.com/00000000-0000-0000-0000-000000000001/v2.0"
TRUSTED_TENANTS = "00000000-0000-0000-0000-000000000001"
GATEWAY_AUD = "api://00000000-0000-0000-0000-000000000102"
MCP_AUD = "api://00000000-0000-0000-0000-000000000103"


def _bootstrap_package(name: str, package_path: Path) -> None:
    spec = importlib.machinery.ModuleSpec(name, loader=None, is_package=True)
    module = importlib.util.module_from_spec(spec)
    module.__path__ = [str(package_path)]
    sys.modules[name] = module


def _clear_package(name: str) -> None:
    for module_name in list(sys.modules):
        if module_name == name or module_name.startswith(f"{name}."):
            sys.modules.pop(module_name, None)


def _load_gateway_auth(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AUTH_MODE", "mock")
    monkeypatch.setenv("AUTH_FIXTURE", "delegated-gateway")
    monkeypatch.setenv("AUTH_ISSUER", ISSUER)
    monkeypatch.setenv("TRUSTED_TENANTS", TRUSTED_TENANTS)
    monkeypatch.setenv("ALLOWED_AUDIENCES", GATEWAY_AUD)
    monkeypatch.setenv("REQUIRED_SCOPES", "mcp.access,mcp.write")
    monkeypatch.setenv("OBO_DOWNSTREAM_AUDIENCE", MCP_AUD)
    monkeypatch.setenv("OBO_REQUIRED_SCOPES", "mcp.write")
    _clear_package("gateway_app")
    _bootstrap_package("gateway_app", GATEWAY_PYTHON / "app")
    return importlib.import_module("gateway_app.auth")


def _load_mcp_app(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AUTH_MODE", "mock")
    monkeypatch.setenv("AUTH_ISSUER", ISSUER)
    monkeypatch.setenv("TRUSTED_TENANTS", TRUSTED_TENANTS)
    monkeypatch.setenv("ALLOWED_AUDIENCES", MCP_AUD)
    monkeypatch.setenv("REQUIRED_SCOPES", "mcp.access,mcp.write")
    monkeypatch.setenv("ENABLE_DEBUG_CLAIMS", "false")
    _clear_package("mcp_app")
    _bootstrap_package("mcp_app", MCP_PYTHON / "app")
    return importlib.import_module("mcp_app.main"), importlib.import_module("mcp_app.auth")


def test_gateway_obo_claims_are_accepted_by_mcp_tools(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gateway_auth = _load_gateway_auth(monkeypatch)
    gateway_context = gateway_auth.resolve_auth_context({})
    obo_exchange = gateway_auth.exchange_for_mcp(gateway_context)

    mcp_main, mcp_auth = _load_mcp_app(monkeypatch)
    mcp_context = mcp_auth.AuthContext.from_claims(
        obo_exchange.claims,
        token_type="delegated",
        correlation_id=gateway_context.correlation_id,
    )
    mcp_main.app.dependency_overrides[mcp_auth.get_auth_context] = lambda: mcp_context
    try:
        response = TestClient(mcp_main.app).post(
            "/tools/authorization-check",
            headers={"Authorization": obo_exchange.authorization},
        )
    finally:
        mcp_main.app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["authorized"] is True
    assert payload["token_type"] == "delegated"
    assert payload["claims"]["aud"] == MCP_AUD
    assert payload["claims"]["scp"] == "mcp.write"
    assert "sub" not in payload["claims"]
    assert "oid" not in payload["claims"]
    assert obo_exchange.authorization != "Bearer inbound-token"


def test_mcp_rejects_inbound_gateway_token_without_obo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mcp_main, _ = _load_mcp_app(monkeypatch)
    response = TestClient(mcp_main.app).post(
        "/tools/authorization-check",
        headers={FIXTURE_HEADER: "delegated-gateway"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_audience"
