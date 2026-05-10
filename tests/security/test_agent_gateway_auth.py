from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi import HTTPException

ROOT = Path(__file__).resolve().parents[2]
SHARED_PYTHON = ROOT / "apps" / "shared" / "python"
GATEWAY_ROOT = ROOT / "apps" / "agent-execution" / "python-fastapi-agent-framework"

sys.path.insert(0, str(SHARED_PYTHON))
sys.path.insert(0, str(GATEWAY_ROOT))
for module_name in ("app", "app.auth", "app.config"):
    sys.modules.pop(module_name, None)

from identity_lab_auth.claims import SAFE_CLAIM_KEYS  # noqa: E402

import app.auth as gateway_auth  # noqa: E402

GATEWAY_AUD = "api://00000000-0000-0000-0000-000000000102"
MCP_AUD = "api://00000000-0000-0000-0000-000000000103"
ISSUER = "https://login.microsoftonline.com/00000000-0000-0000-0000-000000000001/v2.0"
TRUSTED_TENANTS = "00000000-0000-0000-0000-000000000001"


def _configure_env(
    monkeypatch: pytest.MonkeyPatch,
    *,
    fixture: str,
    allowed_audiences: str = GATEWAY_AUD,
    required_scopes: str = "mcp.access,mcp.write",
    obo_audience: str = MCP_AUD,
    obo_scopes: str = "mcp.write",
) -> None:
    monkeypatch.setenv("AUTH_MODE", "mock")
    monkeypatch.setenv("AUTH_FIXTURE", fixture)
    monkeypatch.setenv("AUTH_ISSUER", ISSUER)
    monkeypatch.setenv("TRUSTED_TENANTS", TRUSTED_TENANTS)
    monkeypatch.setenv("ALLOWED_AUDIENCES", allowed_audiences)
    monkeypatch.setenv("REQUIRED_SCOPES", required_scopes)
    monkeypatch.setenv("OBO_DOWNSTREAM_AUDIENCE", obo_audience)
    monkeypatch.setenv("OBO_REQUIRED_SCOPES", obo_scopes)


def test_gateway_auth_builds_obo_exchange(monkeypatch: pytest.MonkeyPatch) -> None:
    _configure_env(monkeypatch, fixture="delegated-gateway")
    context = gateway_auth.resolve_auth_context({})

    assert context.authenticated
    assert context.authorized
    assert context.claims["aud"] == GATEWAY_AUD
    assert set(context.claims).issubset(SAFE_CLAIM_KEYS)
    assert "sub" not in context.claims
    assert "oid" not in context.claims

    obo_exchange = gateway_auth.exchange_for_mcp(context)
    assert obo_exchange.claims["aud"] == MCP_AUD
    assert obo_exchange.claims["aud"] != context.claims["aud"]
    assert set(obo_exchange.claims).issubset(SAFE_CLAIM_KEYS)
    assert "sub" not in obo_exchange.claims
    assert "oid" not in obo_exchange.claims
    assert obo_exchange.authorization != "Bearer inbound-token"
    assert "inbound-token" not in obo_exchange.authorization


def test_gateway_rejects_wrong_audience(monkeypatch: pytest.MonkeyPatch) -> None:
    _configure_env(monkeypatch, fixture="wrong-audience")
    with pytest.raises(HTTPException) as excinfo:
        gateway_auth.resolve_auth_context({})

    assert excinfo.value.status_code == 401


def test_gateway_rejects_missing_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    _configure_env(monkeypatch, fixture="delegated-gateway", required_scopes="mcp.write")
    with pytest.raises(HTTPException) as excinfo:
        gateway_auth.resolve_auth_context({})

    assert excinfo.value.status_code == 403


def test_gateway_rejects_app_only_token(monkeypatch: pytest.MonkeyPatch) -> None:
    _configure_env(monkeypatch, fixture="app-only-gateway")
    with pytest.raises(HTTPException) as excinfo:
        gateway_auth.resolve_auth_context({})

    assert excinfo.value.status_code == 403
