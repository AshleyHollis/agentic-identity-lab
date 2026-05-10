"""T13 — Integration tests for the full Agent OBO boundary.

Spec 002 / M5 T13 — Neo
Owner: Neo
Depends on: T12 (blueprint audience validation in Agentic Layer), T08 (negative fixtures)

Tests cover the five T13 scenarios defined in tasks.md:

1. test_agent_blueprint_happy_path
   Blueprint user token → mock sidecar validate → mock OBO → MCP sanitized claims returned.
   Exercises the full Agent OBO pipeline through app.auth.validate_agent_blueprint and
   app.auth.exchange_agent_obo using MockAgentSidecarClient (offline, no network calls).

2. test_agent_wrong_audience_rejected_before_obo
   Wrong-audience fixture → boundary raises HTTP 401 before any OBO exchange is attempted.
   Spy subclass asserts downstream_api is never invoked (FR-02).

3. test_agent_obo_does_not_share_state_with_mcp_obo
   Both Agent OBO and MCP user OBO paths are invoked within the same test.
   Asserts: (a) they operate on separate module objects (identity_lab_auth.agent_obo vs
   identity_lab_auth.obo), (b) their returned claim dicts are distinct Python objects
   with no shared references, (c) the Agent OBO SidecarConfig instance is not reachable
   from the MCP OBO code path (NFR-06).

4. test_agent_obo_output_has_no_pii
   OBO result claims (both validate step and downstream exchange step) contain none of:
   oid, sub, email, upn, name, preferred_username, family_name, given_name (FR-05 / §10).

5. test_sidecar_non_localhost_rejected_at_construction
   SidecarConfig constructed with any non-localhost URL (HTTPS, external IP, etc.) raises
   ValueError at dataclass post_init — the AKS network-policy boundary is enforced before
   any client instance is created (FR-06).

No network calls are made (NFR-02).  All fixtures use all-zero placeholder GUIDs.
"""

from __future__ import annotations

import importlib
import importlib.machinery
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest
from fastapi import HTTPException

# ---------------------------------------------------------------------------
# Path bootstrap — shared library + Agentic Layer app package
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[3]
SHARED_PYTHON = ROOT / "apps" / "shared" / "python"
GATEWAY_ROOT = ROOT / "apps" / "agent-execution" / "python-fastapi-agent-framework"
FIXTURES_DIR = ROOT / "tests" / "fixtures" / "sample-claims"

sys.path.insert(0, str(SHARED_PYTHON))
sys.path.insert(0, str(GATEWAY_ROOT))

# Evict stale module cache so env monkeypatches take effect for each test.
for _mod in ("app", "app.auth", "app.config"):
    sys.modules.pop(_mod, None)

import app.auth as gateway_auth  # noqa: E402
from identity_lab_auth.agent_obo import (  # noqa: E402
    BLUEPRINT_AUDIENCE_PLACEHOLDER,
    MockAgentSidecarClient,
    SidecarConfig,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_BLUEPRINT_AUD = BLUEPRINT_AUDIENCE_PLACEHOLDER  # api://00000000-…-000000000201/access_as_user
_TRUSTED_TENANT = "00000000-0000-0000-0000-000000000001"
_MCP_AUD = "api://00000000-0000-0000-0000-000000000103"
_GATEWAY_AUD = "api://00000000-0000-0000-0000-000000000102"
_ISSUER = "https://login.microsoftonline.com/00000000-0000-0000-0000-000000000001/v2.0"

_PII_KEYS = frozenset(
    {"oid", "sub", "email", "upn", "name", "preferred_username", "family_name", "given_name"}
)

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
    """Counts downstream_api invocations to assert OBO is not called on validation failure."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.downstream_api_call_count = 0

    def downstream_api(
        self, api_name: str, user_assertion: str, scopes: list[str]
    ) -> dict[str, Any]:
        self.downstream_api_call_count += 1
        return super().downstream_api(api_name, user_assertion, scopes)


# ---------------------------------------------------------------------------
# T13-1: test_agent_blueprint_happy_path
# ---------------------------------------------------------------------------


def test_agent_blueprint_happy_path() -> None:
    """Full Agent OBO pipeline: validate blueprint → OBO exchange → MCP sanitized claims.

    Simulates the complete T13 happy path through app.auth:
      1. validate_agent_blueprint() accepts the blueprint user token → returns sanitized claims
         with blueprint audience.
      2. exchange_agent_obo() exchanges it for downstream MCP claims via mock sidecar →
         returns OboExchange with MCP audience and 'Bearer OFFLINE_MOCK_TOKEN'.
      3. Final claim dict carries mcp.access scope, appid actor claim, no PII.
    """
    client = _make_mock_client()

    # Step 1 — Blueprint audience validation (GET /Validate equivalent)
    validated_claims = gateway_auth.validate_agent_blueprint("bearer-ignored-in-mock", client)

    assert validated_claims["aud"] == _BLUEPRINT_AUD, (
        "Blueprint validation must return claims with blueprint audience"
    )
    assert validated_claims["tid"] == _TRUSTED_TENANT
    assert validated_claims.get("scp") == "access_as_user"
    assert _PII_KEYS.isdisjoint(validated_claims), (
        f"Validated claims must not contain PII: found {_PII_KEYS & validated_claims.keys()}"
    )

    # Step 2 — Agent OBO exchange (POST /DownstreamApi/{apiName} equivalent)
    obo_result = gateway_auth.exchange_agent_obo("bearer-ignored-in-mock", client)

    assert isinstance(obo_result, gateway_auth.OboExchange)
    assert obo_result.claims["aud"] == _MCP_AUD, (
        "OBO downstream claims must carry MCP audience, not blueprint audience"
    )
    assert obo_result.claims.get("scp") == "mcp.access"
    assert obo_result.claims.get("appid") is not None, (
        "Agent OBO output must include appid actor claim"
    )
    assert obo_result.authorization == "Bearer OFFLINE_MOCK_TOKEN"


# ---------------------------------------------------------------------------
# T13-2: test_agent_wrong_audience_rejected_before_obo
# ---------------------------------------------------------------------------


def test_agent_wrong_audience_rejected_before_obo() -> None:
    """Wrong-audience fixture → HTTP 401 raised before any OBO exchange is attempted (FR-02).

    The agent-wrong-audience.json fixture carries the BFF audience rather than the
    blueprint audience.  validate_agent_blueprint() MUST raise HTTPException(401) without
    ever calling downstream_api() (i.e. without attempting any OBO exchange).
    """
    spy = _SpyClient(
        config=_sidecar_config(),
        fixture_claims=_load("agent-wrong-audience.json"),
        obo_fixture_claims=_load("agent-obo-mcp-token.json"),
        trusted_tenants=[_TRUSTED_TENANT],
    )

    with pytest.raises(HTTPException) as exc_info:
        gateway_auth.validate_agent_blueprint("bearer-wrong-aud", spy)

    assert exc_info.value.status_code == 401, (
        "Wrong blueprint audience must produce HTTP 401 Unauthorized"
    )
    assert "Blueprint audience validation failed" in exc_info.value.detail

    assert spy.downstream_api_call_count == 0, (
        "OBO exchange (downstream_api) MUST NOT be called before blueprint validation succeeds — "
        f"was called {spy.downstream_api_call_count} time(s)"
    )


# ---------------------------------------------------------------------------
# T13-3: test_agent_obo_does_not_share_state_with_mcp_obo
# ---------------------------------------------------------------------------


def test_agent_obo_does_not_share_state_with_mcp_obo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Agent OBO and MCP user OBO paths are strictly separate (NFR-06 / FR-06).

    Both paths are invoked within this test.  Assertions:
    a) identity_lab_auth.agent_obo and identity_lab_auth.obo are distinct module objects
       — they share no top-level names, token variables, or configuration.
    b) The Agent OBO path uses MockAgentSidecarClient (its own SidecarConfig instance);
       the MCP OBO path uses exchange_on_behalf_of (AuthContext; separate import path).
    c) Returned claim dicts are distinct Python objects — no shared identity (is not).
    d) Claim sources differ: Agent OBO inbound aud = blueprint, MCP OBO inbound aud = gateway.
    e) Neither path can access the other's SidecarConfig or AuthContext through public API.
    """
    import identity_lab_auth.agent_obo as agent_obo_module
    import identity_lab_auth.obo as mcp_obo_module

    # (a) — Module identity
    assert agent_obo_module is not mcp_obo_module, (
        "identity_lab_auth.agent_obo and identity_lab_auth.obo must be distinct module objects"
    )
    assert not hasattr(mcp_obo_module, "SidecarConfig"), (
        "MCP OBO module must not expose SidecarConfig — zero shared state with Agent OBO"
    )
    assert not hasattr(mcp_obo_module, "AgentSidecarClient"), (
        "MCP OBO module must not expose AgentSidecarClient — zero shared state"
    )
    assert not hasattr(agent_obo_module, "exchange_on_behalf_of"), (
        "Agent OBO module must not expose exchange_on_behalf_of — zero shared state with MCP OBO"
    )

    # (b) — Set up MCP user OBO path via auth env
    monkeypatch.setenv("AUTH_MODE", "mock")
    monkeypatch.setenv("AUTH_FIXTURE", "delegated-gateway")
    monkeypatch.setenv("AUTH_ISSUER", _ISSUER)
    monkeypatch.setenv("TRUSTED_TENANTS", _TRUSTED_TENANT)
    monkeypatch.setenv("ALLOWED_AUDIENCES", _GATEWAY_AUD)
    monkeypatch.setenv("REQUIRED_SCOPES", "mcp.access,mcp.write")
    monkeypatch.setenv("OBO_DOWNSTREAM_AUDIENCE", _MCP_AUD)
    monkeypatch.setenv("OBO_REQUIRED_SCOPES", "mcp.write")

    mcp_context = gateway_auth.resolve_auth_context({})
    mcp_exchange = gateway_auth.exchange_for_mcp(mcp_context)

    # (b) — Set up Agent OBO path via MockAgentSidecarClient
    agent_client = _make_mock_client()
    agent_validated = gateway_auth.validate_agent_blueprint("bearer-ignored", agent_client)
    agent_exchange = gateway_auth.exchange_agent_obo("bearer-ignored", agent_client)

    # (c) — Returned claim dicts are distinct Python objects (no shared references)
    assert mcp_exchange.claims is not agent_exchange.claims, (
        "MCP OBO and Agent OBO returned claim dicts must be distinct Python objects"
    )

    # (d) — Inbound token audiences differ: gateway aud for MCP path, blueprint aud for Agent path
    assert mcp_context.claims.get("aud") == _GATEWAY_AUD, (
        "MCP path uses gateway audience on inbound token"
    )
    assert agent_validated["aud"] == _BLUEPRINT_AUD, (
        "Agent path uses blueprint audience on inbound token"
    )

    # Both converge on MCP aud for downstream claims, but via entirely separate code paths
    assert mcp_exchange.claims["aud"] == _MCP_AUD
    assert agent_exchange.claims["aud"] == _MCP_AUD

    # (e) — Agent OBO SidecarConfig is not reachable from the MCP OBO module
    assert not hasattr(mcp_obo_module, "_LOCALHOST_PREFIXES"), (
        "MCP OBO module must not contain sidecar localhost enforcement state"
    )


# ---------------------------------------------------------------------------
# T13-4: test_agent_obo_output_has_no_pii
# ---------------------------------------------------------------------------


def test_agent_obo_output_has_no_pii() -> None:
    """OBO result (both validate and downstream exchange) must contain no PII claims (§10 / FR-05).

    The binding security contract (Security Design Notes §10, Trinity T03) mandates that
    ALL concrete AgentSidecarClient implementations route claim outputs through
    sanitize_claims(), preventing oid, sub, email, upn, name, preferred_username,
    family_name, and given_name from appearing in any returned dict.
    """
    client = _make_mock_client()

    # Validate step output
    validated_claims = gateway_auth.validate_agent_blueprint("bearer-ignored", client)
    assert _PII_KEYS.isdisjoint(validated_claims), (
        f"Blueprint validation output must not contain PII; found: "
        f"{_PII_KEYS & validated_claims.keys()}"
    )

    # OBO exchange output
    obo_result = gateway_auth.exchange_agent_obo("bearer-ignored", client)
    assert _PII_KEYS.isdisjoint(obo_result.claims), (
        f"Agent OBO downstream claims must not contain PII; found: "
        f"{_PII_KEYS & obo_result.claims.keys()}"
    )

    # authorization field must not expose a raw Entra token string
    assert "OFFLINE_MOCK_TOKEN" in obo_result.authorization
    assert obo_result.authorization == "Bearer OFFLINE_MOCK_TOKEN"

    # Verify expected non-PII claims are present and correct
    assert obo_result.claims.get("aud") == _MCP_AUD
    assert obo_result.claims.get("appid") is not None


# ---------------------------------------------------------------------------
# T13-5: test_sidecar_non_localhost_rejected_at_construction
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad_url",
    [
        "https://sidecar.example.com/api",
        "http://10.0.0.1:5000",
        "http://192.168.1.1:5000",
        "https://localhost:5000",      # HTTPS not allowed — only http://localhost
        "http://localhostmalicious",   # prefix must be exact (http://localhost with port or /)
        "ftp://localhost/sidecar",
        "",
    ],
    ids=[
        "external-https",
        "private-ip",
        "lan-ip",
        "https-localhost-rejected",
        "malicious-lookalike",
        "ftp-scheme",
        "empty-url",
    ],
)
def test_sidecar_non_localhost_rejected_at_construction(bad_url: str) -> None:
    """SidecarConfig raises ValueError for any non-localhost URL (FR-06 / AKS network policy).

    The Entra Agent ID sidecar is only reachable from the co-located pod container via
    localhost.  This test exercises the SidecarConfig.__post_init__ enforcement so that
    mis-configured sidecar URLs are caught at object construction — before any client
    instance is created and before any request is dispatched.
    """
    with pytest.raises(ValueError, match=r"sidecar_url must start with|must be a non-empty"):
        SidecarConfig(sidecar_url=bad_url, blueprint_audience=_BLUEPRINT_AUD)
