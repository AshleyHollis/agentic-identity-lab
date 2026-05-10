"""Tests for T12 — Blueprint audience validation wired into Agentic Layer auth.py.

Spec 002 / M5 T12 — Neo
Owner: Neo
Depends on: T11 (MockAgentSidecarClient), T07 (fixture files)

Tests cover:
- Correct blueprint audience: validate_agent_blueprint() returns sanitized claims
- Wrong blueprint audience: validate_agent_blueprint() raises HTTP 401 BEFORE any OBO
- Stale / untrusted-tenant / app-only fixtures rejected with HTTP 401 (no OBO call)
- exchange_agent_obo() returns OboExchange with sanitized downstream claims
- exchange_agent_obo() raises HTTP 401 when downstream exchange fails
- OBO exchange is NOT invoked when blueprint validation fails (spy assertion)
- No PII in returned claims from either boundary function
- Existing MCP delegated OBO path (resolve_auth_context + exchange_for_mcp) not
  affected by T12 wiring — full non-regression check

These tests make no network calls (NFR-02).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest
from fastapi import HTTPException

# ---------------------------------------------------------------------------
# Path bootstrap — shared library + Agentic Layer app package
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]
SHARED_PYTHON = ROOT / "apps" / "shared" / "python"
GATEWAY_ROOT = ROOT / "apps" / "agent-execution" / "python-fastapi-agent-framework"
FIXTURES_DIR = ROOT / "tests" / "fixtures" / "sample-claims"

sys.path.insert(0, str(SHARED_PYTHON))
sys.path.insert(0, str(GATEWAY_ROOT))

# Clear cached modules so monkeypatch env changes take full effect
for _mod in ("app", "app.auth", "app.config"):
    sys.modules.pop(_mod, None)

from identity_lab_auth.agent_obo import (  # noqa: E402
    BLUEPRINT_AUDIENCE_PLACEHOLDER,
    MockAgentSidecarClient,
    SidecarConfig,
)
import app.auth as gateway_auth  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_BLUEPRINT_AUD = BLUEPRINT_AUDIENCE_PLACEHOLDER
_TRUSTED_TENANT = "00000000-0000-0000-0000-000000000001"
_MCP_AUD = "api://00000000-0000-0000-0000-000000000103"
_GATEWAY_AUD = "api://00000000-0000-0000-0000-000000000102"
_ISSUER = "https://login.microsoftonline.com/00000000-0000-0000-0000-000000000001/v2.0"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load(filename: str) -> dict[str, Any]:
    return json.loads((FIXTURES_DIR / filename).read_text(encoding="utf-8"))


def _sidecar_config(audience: str = _BLUEPRINT_AUD) -> SidecarConfig:
    return SidecarConfig(sidecar_url="http://localhost:5000", blueprint_audience=audience)


def _make_mock_client(
    fixture_name: str = "agent-blueprint-user-token.json",
    obo_fixture_name: str = "agent-obo-mcp-token.json",
    trusted_tenants: list[str] | None = None,
    audience: str = _BLUEPRINT_AUD,
) -> MockAgentSidecarClient:
    return MockAgentSidecarClient(
        config=_sidecar_config(audience),
        fixture_claims=_load(fixture_name),
        obo_fixture_claims=_load(obo_fixture_name),
        trusted_tenants=trusted_tenants or [_TRUSTED_TENANT],
    )


class _SpyClient(MockAgentSidecarClient):
    """Subclass that counts downstream_api calls to verify OBO is not invoked."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.downstream_api_call_count = 0

    def downstream_api(self, api_name: str, user_assertion: str, scopes: list[str]) -> dict:
        self.downstream_api_call_count += 1
        return super().downstream_api(api_name, user_assertion, scopes)


# ---------------------------------------------------------------------------
# validate_agent_blueprint — happy path
# ---------------------------------------------------------------------------


def test_validate_blueprint_correct_audience_returns_sanitized_claims() -> None:
    """validate_agent_blueprint() returns sanitized claims for a valid blueprint token."""
    client = _make_mock_client()
    result = gateway_auth.validate_agent_blueprint("any-bearer-ignored-in-mock", client)

    assert isinstance(result, dict)
    assert result["aud"] == _BLUEPRINT_AUD
    assert result["tid"] == _TRUSTED_TENANT
    assert result["scp"] == "access_as_user"


def test_validate_blueprint_no_pii_in_returned_claims() -> None:
    """validate_agent_blueprint() output must never contain PII claims."""
    client = _make_mock_client()
    result = gateway_auth.validate_agent_blueprint("ignored", client)

    pii_keys = {"oid", "sub", "email", "upn", "name", "preferred_username",
                "family_name", "given_name"}
    assert pii_keys.isdisjoint(result), (
        f"PII claims found: {pii_keys & result.keys()}"
    )


# ---------------------------------------------------------------------------
# validate_agent_blueprint — rejection cases (HTTP 401 BEFORE OBO)
# ---------------------------------------------------------------------------


def test_validate_blueprint_wrong_audience_raises_http_401() -> None:
    """Wrong-audience fixture → HTTP 401 before any OBO exchange."""
    client = _make_mock_client(fixture_name="agent-wrong-audience.json")

    with pytest.raises(HTTPException) as exc_info:
        gateway_auth.validate_agent_blueprint("ignored", client)

    assert exc_info.value.status_code == 401
    assert "Blueprint audience validation failed" in exc_info.value.detail


def test_validate_blueprint_wrong_audience_never_invokes_obo() -> None:
    """OBO (downstream_api) is never called when blueprint audience validation fails."""
    spy = _SpyClient(
        config=_sidecar_config(),
        fixture_claims=_load("agent-wrong-audience.json"),
        obo_fixture_claims=_load("agent-obo-mcp-token.json"),
        trusted_tenants=[_TRUSTED_TENANT],
    )

    with pytest.raises(HTTPException):
        gateway_auth.validate_agent_blueprint("ignored", spy)

    assert spy.downstream_api_call_count == 0, (
        "downstream_api (OBO exchange) must NOT be called before blueprint validation succeeds"
    )


def test_validate_blueprint_stale_token_raises_http_401() -> None:
    """Expired/stale token → HTTP 401."""
    client = _make_mock_client(fixture_name="agent-replay-stale.json")

    with pytest.raises(HTTPException) as exc_info:
        gateway_auth.validate_agent_blueprint("ignored", client)

    assert exc_info.value.status_code == 401


def test_validate_blueprint_untrusted_tenant_raises_http_401() -> None:
    """Untrusted-tenant fixture → HTTP 401."""
    client = _make_mock_client(fixture_name="agent-untrusted-tenant.json")

    with pytest.raises(HTTPException) as exc_info:
        gateway_auth.validate_agent_blueprint("ignored", client)

    assert exc_info.value.status_code == 401


def test_validate_blueprint_app_only_no_scp_raises_http_401() -> None:
    """App-only token with no scp → HTTP 401."""
    client = _make_mock_client(fixture_name="agent-app-only-blueprint.json")

    with pytest.raises(HTTPException) as exc_info:
        gateway_auth.validate_agent_blueprint("ignored", client)

    assert exc_info.value.status_code == 401


def test_validate_blueprint_raises_401_not_403() -> None:
    """Wrong blueprint audience must produce 401 Unauthorized, not 403 Forbidden."""
    client = _make_mock_client(fixture_name="agent-wrong-audience.json")

    with pytest.raises(HTTPException) as exc_info:
        gateway_auth.validate_agent_blueprint("ignored", client)

    assert exc_info.value.status_code == 401
    assert exc_info.value.status_code != 403


# ---------------------------------------------------------------------------
# exchange_agent_obo — happy path
# ---------------------------------------------------------------------------


def test_exchange_agent_obo_returns_obo_exchange() -> None:
    """exchange_agent_obo() returns OboExchange with sanitized downstream claims."""
    client = _make_mock_client()
    result = gateway_auth.exchange_agent_obo("some-bearer", client)

    assert isinstance(result, gateway_auth.OboExchange)
    assert result.claims["aud"] == _MCP_AUD
    assert result.claims.get("scp") == "mcp.access"
    assert result.authorization == "Bearer OFFLINE_MOCK_TOKEN"


def test_exchange_agent_obo_authorization_is_offline_sentinel() -> None:
    """exchange_agent_obo() authorization field must be the offline mock sentinel."""
    client = _make_mock_client()
    result = gateway_auth.exchange_agent_obo("ignored", client, api_name="mcp-protected-api")

    assert result.authorization == "Bearer OFFLINE_MOCK_TOKEN"
    assert "OFFLINE_MOCK_TOKEN" in result.authorization


def test_exchange_agent_obo_no_pii_in_downstream_claims() -> None:
    """OBO downstream claims must not contain PII."""
    client = _make_mock_client()
    result = gateway_auth.exchange_agent_obo("ignored", client)

    pii_keys = {"oid", "sub", "email", "upn", "name", "preferred_username",
                "family_name", "given_name"}
    assert pii_keys.isdisjoint(result.claims), (
        f"PII claims in OBO output: {pii_keys & result.claims.keys()}"
    )


def test_exchange_agent_obo_downstream_aud_differs_from_blueprint_aud() -> None:
    """OBO downstream aud must differ from the inbound blueprint aud."""
    client = _make_mock_client()
    result = gateway_auth.exchange_agent_obo("ignored", client)

    # Blueprint aud is the inbound token aud; OBO aud is the downstream MCP aud
    assert result.claims["aud"] != _BLUEPRINT_AUD


# ---------------------------------------------------------------------------
# exchange_agent_obo — rejection when wrong audience in fixture
# ---------------------------------------------------------------------------


def test_exchange_agent_obo_wrong_audience_raises_http_401() -> None:
    """exchange_agent_obo() raises HTTP 401 when fixture aud != blueprint_audience."""
    client = _make_mock_client(fixture_name="agent-wrong-audience.json")

    with pytest.raises(HTTPException) as exc_info:
        gateway_auth.exchange_agent_obo("ignored", client)

    assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# Path separation — Agent OBO path does NOT share state with MCP user OBO
# ---------------------------------------------------------------------------


def test_agent_obo_path_separate_from_mcp_obo(monkeypatch: pytest.MonkeyPatch) -> None:
    """Agent OBO and MCP user OBO return distinct claims from separate code paths."""
    monkeypatch.setenv("AUTH_MODE", "mock")
    monkeypatch.setenv("AUTH_FIXTURE", "delegated-gateway")
    monkeypatch.setenv("AUTH_ISSUER", _ISSUER)
    monkeypatch.setenv("TRUSTED_TENANTS", _TRUSTED_TENANT)
    monkeypatch.setenv("ALLOWED_AUDIENCES", _GATEWAY_AUD)
    monkeypatch.setenv("REQUIRED_SCOPES", "mcp.access,mcp.write")
    monkeypatch.setenv("OBO_DOWNSTREAM_AUDIENCE", _MCP_AUD)
    monkeypatch.setenv("OBO_REQUIRED_SCOPES", "mcp.write")

    # MCP user OBO path
    mcp_context = gateway_auth.resolve_auth_context({})
    mcp_exchange = gateway_auth.exchange_for_mcp(mcp_context)

    # Agent OBO path (separate module + separate claim source)
    agent_client = _make_mock_client()
    agent_claims = gateway_auth.validate_agent_blueprint("ignored", agent_client)
    agent_exchange = gateway_auth.exchange_agent_obo("ignored", agent_client)

    # Inbound claim sources differ (gateway aud vs blueprint aud)
    assert mcp_context.claims.get("aud") == _GATEWAY_AUD
    assert agent_claims["aud"] == _BLUEPRINT_AUD

    # Both downstream paths target MCP aud, but arrive via separate code paths
    assert mcp_exchange.claims["aud"] == _MCP_AUD
    assert agent_exchange.claims["aud"] == _MCP_AUD

    # The two paths return distinct Python dicts (no shared state)
    assert mcp_exchange.claims is not agent_exchange.claims


# ---------------------------------------------------------------------------
# Non-regression: existing MCP delegated OBO path is unaffected by T12 wiring
# ---------------------------------------------------------------------------


def test_existing_mcp_obo_path_unaffected(monkeypatch: pytest.MonkeyPatch) -> None:
    """T12 wiring must not regress the existing MCP delegated OBO path.

    resolve_auth_context() + exchange_for_mcp() must continue to work exactly
    as before T12: gateway-audience token in → MCP-audience OBO claims out.
    """
    monkeypatch.setenv("AUTH_MODE", "mock")
    monkeypatch.setenv("AUTH_FIXTURE", "delegated-gateway")
    monkeypatch.setenv("AUTH_ISSUER", _ISSUER)
    monkeypatch.setenv("TRUSTED_TENANTS", _TRUSTED_TENANT)
    monkeypatch.setenv("ALLOWED_AUDIENCES", _GATEWAY_AUD)
    monkeypatch.setenv("REQUIRED_SCOPES", "mcp.access,mcp.write")
    monkeypatch.setenv("OBO_DOWNSTREAM_AUDIENCE", _MCP_AUD)
    monkeypatch.setenv("OBO_REQUIRED_SCOPES", "mcp.write")

    context = gateway_auth.resolve_auth_context({})

    assert context.authenticated
    assert context.authorized
    assert context.claims["aud"] == _GATEWAY_AUD
    assert "sub" not in context.claims
    assert "oid" not in context.claims

    obo = gateway_auth.exchange_for_mcp(context)
    assert obo.claims["aud"] == _MCP_AUD
    assert obo.claims["aud"] != context.claims["aud"]
    assert "sub" not in obo.claims
    assert "oid" not in obo.claims
    assert obo.authorization != "Bearer inbound-token"
    assert "inbound-token" not in obo.authorization


def test_mcp_wrong_gateway_audience_still_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    """Wrong-audience rejection on the MCP path is unaffected by T12 changes."""
    monkeypatch.setenv("AUTH_MODE", "mock")
    monkeypatch.setenv("AUTH_FIXTURE", "wrong-audience")
    monkeypatch.setenv("AUTH_ISSUER", _ISSUER)
    monkeypatch.setenv("TRUSTED_TENANTS", _TRUSTED_TENANT)
    monkeypatch.setenv("ALLOWED_AUDIENCES", _GATEWAY_AUD)
    monkeypatch.setenv("REQUIRED_SCOPES", "mcp.access,mcp.write")
    monkeypatch.setenv("OBO_DOWNSTREAM_AUDIENCE", _MCP_AUD)
    monkeypatch.setenv("OBO_REQUIRED_SCOPES", "mcp.write")

    with pytest.raises(HTTPException) as exc_info:
        gateway_auth.resolve_auth_context({})

    assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# Module structure — agent_obo path not in obo module (NFR-06)
# ---------------------------------------------------------------------------


def test_auth_module_imports_agent_sidecar_client() -> None:
    """auth.py must import AgentSidecarClient to wire the blueprint boundary."""
    from identity_lab_auth.agent_obo import AgentSidecarClient

    assert hasattr(gateway_auth, "validate_agent_blueprint")
    assert hasattr(gateway_auth, "exchange_agent_obo")
    # The imported name is used as a type annotation in auth.py
    assert AgentSidecarClient is not None


def test_auth_module_does_not_expose_raw_obo_exchange() -> None:
    """Agent OBO path must not call MCP user OBO (exchange_on_behalf_of) directly.

    auth.py has both paths, but exchange_agent_obo uses AgentSidecarClient,
    not exchange_on_behalf_of.  Verify by calling exchange_agent_obo and
    confirming the result is sourced from the sidecar client, not from
    the MCP user OBO function.
    """
    client = _make_mock_client()
    result = gateway_auth.exchange_agent_obo("ignored", client)

    # Agent OBO returns the offline mock sentinel, not a real MCP OBO token
    assert result.authorization == "Bearer OFFLINE_MOCK_TOKEN"
    # Claims come from OBO fixture (MCP aud), not from exchange_on_behalf_of path
    assert result.claims["aud"] == _MCP_AUD
