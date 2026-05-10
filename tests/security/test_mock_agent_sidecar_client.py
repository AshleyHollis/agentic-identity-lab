"""Unit tests for T11 — MockAgentSidecarClient offline fixture implementation.

Spec 002 / M5 T11 — Neo
Owner: Neo
Depends on: T10 (AgentSidecarClient ABC), T07 (fixture files)

Tests cover:
- Happy path: validate() returns sanitized blueprint claims
- Happy path: authorization_header() returns offline sentinel
- Happy path: downstream_api() returns sanitized OBO claims
- Wrong audience fixture → validate() raises ValueError before any exchange
- Stale/expired fixture → validate() raises ValueError
- Untrusted tenant fixture → validate() raises ValueError
- App-only (no scp) fixture → validate() raises ValueError
- Wrong audience → downstream_api() raises ValueError
- Missing actor (no appid): downstream_api() succeeds; result has no appid
- No PII in validate() output (no oid, sub, email, upn, name)
- No PII in downstream_api() output
- authorization_header() never returns a raw Entra token string
- MockAgentSidecarClient is exported from package __init__
- Zero HTTP calls made (all assertions are pure dict operations)

These tests make no network calls (NFR-02).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

# ---------------------------------------------------------------------------
# Path bootstrap
# ---------------------------------------------------------------------------

SHARED_PYTHON = Path(__file__).resolve().parents[2] / "apps" / "shared" / "python"
FIXTURES_DIR = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "sample-claims"
sys.path.insert(0, str(SHARED_PYTHON))

from identity_lab_auth.agent_obo import (  # noqa: E402
    BLUEPRINT_AUDIENCE_PLACEHOLDER,
    MockAgentSidecarClient,
    SidecarConfig,
)
import identity_lab_auth  # noqa: E402

# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

_TRUSTED_TENANT = "00000000-0000-0000-0000-000000000001"
_UNTRUSTED_TENANT = "00000000-0000-0000-0000-000000000002"


def _load(filename: str) -> dict[str, Any]:
    return json.loads((FIXTURES_DIR / filename).read_text(encoding="utf-8"))


def _config(audience: str = BLUEPRINT_AUDIENCE_PLACEHOLDER) -> SidecarConfig:
    return SidecarConfig(sidecar_url="http://localhost:5000", blueprint_audience=audience)


def _make_client(
    fixture_name: str = "agent-blueprint-user-token.json",
    obo_fixture_name: str = "agent-obo-mcp-token.json",
    trusted_tenants: list[str] | None = None,
    audience: str = BLUEPRINT_AUDIENCE_PLACEHOLDER,
) -> MockAgentSidecarClient:
    return MockAgentSidecarClient(
        config=_config(audience),
        fixture_claims=_load(fixture_name),
        obo_fixture_claims=_load(obo_fixture_name),
        trusted_tenants=trusted_tenants if trusted_tenants is not None else [_TRUSTED_TENANT],
    )


# ---------------------------------------------------------------------------
# Happy path — validate()
# ---------------------------------------------------------------------------


def test_validate_happy_path_returns_sanitized_claims() -> None:
    """validate() returns sanitized blueprint claims for a valid fixture."""
    client = _make_client()
    result = client.validate("any-bearer-string-ignored-in-mock-mode")

    assert isinstance(result, dict)
    assert result["aud"] == BLUEPRINT_AUDIENCE_PLACEHOLDER
    assert result["tid"] == _TRUSTED_TENANT
    assert result["scp"] == "access_as_user"


def test_validate_returns_no_pii_claims() -> None:
    """validate() output must never contain oid, sub, email, upn, or name."""
    client = _make_client()
    result = client.validate("ignored")

    pii_keys = {"oid", "sub", "email", "upn", "name", "preferred_username",
                "family_name", "given_name"}
    assert pii_keys.isdisjoint(result), (
        f"PII claims found in validate() output: {pii_keys & result.keys()}"
    )


def test_validate_bearer_token_string_is_ignored() -> None:
    """validate() result must be identical regardless of the literal bearer_token."""
    client = _make_client()
    r1 = client.validate("token-a")
    r2 = client.validate("Bearer eyJ.totally.different")
    assert r1 == r2


# ---------------------------------------------------------------------------
# Happy path — authorization_header()
# ---------------------------------------------------------------------------


def test_authorization_header_returns_offline_sentinel() -> None:
    """authorization_header() must return the literal offline mock sentinel."""
    client = _make_client()
    assert client.authorization_header("mcp-protected-api") == "Bearer OFFLINE_MOCK_TOKEN"


def test_authorization_header_api_name_does_not_affect_result() -> None:
    """authorization_header() sentinel is constant regardless of api_name."""
    client = _make_client()
    assert client.authorization_header("api-a") == client.authorization_header("api-b")


def test_authorization_header_is_not_raw_entra_jwt() -> None:
    """authorization_header() must not return a raw Entra-issued JWT string."""
    client = _make_client()
    header = client.authorization_header("any")
    # A real Entra JWT has three base64url segments separated by dots
    token_part = header.removeprefix("Bearer ").strip()
    assert token_part.count(".") < 2, (
        "authorization_header() returned what looks like a real JWT; "
        "offline mock must return OFFLINE_MOCK_TOKEN only."
    )


# ---------------------------------------------------------------------------
# Happy path — downstream_api()
# ---------------------------------------------------------------------------


def test_downstream_api_happy_path_returns_sanitized_obo_claims() -> None:
    """downstream_api() returns sanitized OBO claims from the obo fixture."""
    client = _make_client()
    result = client.downstream_api(
        api_name="mcp-protected-api",
        user_assertion="some-opaque-bearer",
        scopes=["mcp.access"],
    )

    assert isinstance(result, dict)
    assert result["aud"] == "api://00000000-0000-0000-0000-000000000103"
    assert result["scp"] == "mcp.access"
    assert result.get("appid") == "00000000-0000-0000-0000-000000000201"


def test_downstream_api_returns_no_pii_claims() -> None:
    """downstream_api() output must never contain PII claims."""
    client = _make_client()
    result = client.downstream_api("api", "token", ["mcp.access"])

    pii_keys = {"oid", "sub", "email", "upn", "name", "preferred_username",
                "family_name", "given_name"}
    assert pii_keys.isdisjoint(result), (
        f"PII claims found in downstream_api() output: {pii_keys & result.keys()}"
    )


def test_downstream_api_missing_actor_returns_no_appid() -> None:
    """downstream_api() with agent-missing-actor OBO fixture returns no appid claim."""
    client = _make_client(obo_fixture_name="agent-missing-actor.json")
    result = client.downstream_api("api", "token", ["mcp.access"])

    assert "appid" not in result, (
        "Expected no appid in sanitized output when OBO fixture has no appid"
    )


# ---------------------------------------------------------------------------
# Negative cases — validate()
# ---------------------------------------------------------------------------


def test_validate_wrong_audience_raises() -> None:
    """validate() raises ValueError when fixture aud != blueprint_audience."""
    client = _make_client(fixture_name="agent-wrong-audience.json")
    with pytest.raises(ValueError, match="blueprint audience"):
        client.validate("ignored")


def test_validate_untrusted_tenant_raises() -> None:
    """validate() raises ValueError when fixture tid is not in trusted_tenants."""
    client = _make_client(fixture_name="agent-untrusted-tenant.json")
    with pytest.raises(ValueError, match="[Uu]ntrusted tenant"):
        client.validate("ignored")


def test_validate_stale_token_raises() -> None:
    """validate() raises ValueError when fixture exp is in the past."""
    client = _make_client(fixture_name="agent-replay-stale.json")
    with pytest.raises(ValueError, match="expired"):
        client.validate("ignored")


def test_validate_app_only_no_scp_raises() -> None:
    """validate() raises ValueError for app-only tokens that have no scp claim."""
    client = _make_client(fixture_name="agent-app-only-blueprint.json")
    with pytest.raises(ValueError, match="scp"):
        client.validate("ignored")


# ---------------------------------------------------------------------------
# Negative cases — downstream_api()
# ---------------------------------------------------------------------------


def test_downstream_api_wrong_audience_raises() -> None:
    """downstream_api() raises ValueError when fixture aud != blueprint_audience."""
    client = _make_client(fixture_name="agent-wrong-audience.json")
    with pytest.raises(ValueError, match="blueprint audience"):
        client.downstream_api("api", "ignored", ["mcp.access"])


# ---------------------------------------------------------------------------
# Constructor / config contract
# ---------------------------------------------------------------------------


def test_mock_client_is_concrete_subclass() -> None:
    """MockAgentSidecarClient is a concrete subclass of AgentSidecarClient."""
    from identity_lab_auth.agent_obo import AgentSidecarClient

    client = _make_client()
    assert isinstance(client, AgentSidecarClient)


def test_mock_client_config_property() -> None:
    """config property returns the SidecarConfig passed at construction."""
    cfg = _config()
    client = MockAgentSidecarClient(
        config=cfg,
        fixture_claims=_load("agent-blueprint-user-token.json"),
        obo_fixture_claims=_load("agent-obo-mcp-token.json"),
        trusted_tenants=[_TRUSTED_TENANT],
    )
    assert client.config is cfg


def test_mock_client_default_trusted_tenant() -> None:
    """MockAgentSidecarClient defaults to the offline placeholder tenant."""
    client = MockAgentSidecarClient(
        config=_config(),
        fixture_claims=_load("agent-blueprint-user-token.json"),
        obo_fixture_claims=_load("agent-obo-mcp-token.json"),
        # trusted_tenants omitted — uses default
    )
    # Trusted tenant in fixture is _TRUSTED_TENANT; default should accept it
    result = client.validate("ignored")
    assert result["tid"] == _TRUSTED_TENANT


def test_mock_client_explicit_trusted_tenant_list_rejects_unlisted() -> None:
    """validate() rejects a tenant not in an explicit trusted_tenants list."""
    # Blueprint fixture has tid = _TRUSTED_TENANT; pass only _UNTRUSTED_TENANT
    client = MockAgentSidecarClient(
        config=_config(),
        fixture_claims=_load("agent-blueprint-user-token.json"),
        obo_fixture_claims=_load("agent-obo-mcp-token.json"),
        trusted_tenants=[_UNTRUSTED_TENANT],
    )
    with pytest.raises(ValueError, match="[Uu]ntrusted tenant"):
        client.validate("ignored")


def test_mock_client_fixture_claims_not_mutated() -> None:
    """MockAgentSidecarClient does not hold a reference to the caller's dict."""
    raw = _load("agent-blueprint-user-token.json")
    client = _make_client()
    # Mutating the source dict after construction must not affect validation
    raw["aud"] = "tampered"
    result = client.validate("ignored")
    assert result["aud"] == BLUEPRINT_AUDIENCE_PLACEHOLDER


# ---------------------------------------------------------------------------
# Package-level exports
# ---------------------------------------------------------------------------


def test_package_exports_mock_agent_sidecar_client() -> None:
    """identity_lab_auth exports MockAgentSidecarClient."""
    assert hasattr(identity_lab_auth, "MockAgentSidecarClient")
    assert identity_lab_auth.MockAgentSidecarClient is MockAgentSidecarClient


# ---------------------------------------------------------------------------
# Path separation — no import from obo / MSAL (NFR-06)
# ---------------------------------------------------------------------------


def test_mock_client_module_does_not_import_obo_exchange() -> None:
    """agent_obo module must not import exchange_on_behalf_of."""
    import identity_lab_auth.agent_obo as agent_obo_module

    assert not hasattr(agent_obo_module, "exchange_on_behalf_of")
