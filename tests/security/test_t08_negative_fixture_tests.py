"""T08 — Negative fixture tests for Agent ID / Agent OBO claim fixtures.

Spec 002 / M5 / FR-04.  Five offline pytest tests, one per negative fixture
from T07, each loading the fixture via ``load_fixture_claims`` and passing it
through the relevant validation boundary.  Every test asserts the token is
rejected for the correct documented reason.

No network calls are made.  All fixtures use all-zero placeholder GUIDs.
AUTH_MODE is not read; the tests operate directly on claim dicts.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SHARED_PYTHON = ROOT / "apps" / "shared" / "python"
sys.path.insert(0, str(SHARED_PYTHON))

from identity_lab_auth.agent_obo import BLUEPRINT_AUDIENCE_PLACEHOLDER  # noqa: E402
from identity_lab_auth.auth_settings import load_fixture_claims  # noqa: E402
from identity_lab_auth.guards import (  # noqa: E402
    require_actor_appid,
    require_audience,
    require_delegated_token,
    validate_claims,
)

FIXTURES_DIR = ROOT / "tests" / "fixtures" / "sample-claims"

# The single trusted tenant used across all non-untrusted-tenant fixtures.
TRUSTED_TENANT = "00000000-0000-0000-0000-000000000001"

# Blueprint audience that inbound tokens MUST match before any Agent OBO exchange.
BLUEPRINT_AUD = BLUEPRINT_AUDIENCE_PLACEHOLDER  # api://00000000-0000-0000-0000-000000000201/access_as_user


def _load(name: str) -> dict:  # type: ignore[type-arg]
    claims = load_fixture_claims(name, FIXTURES_DIR)
    assert claims is not None, f"Fixture '{name}' not found in {FIXTURES_DIR}"
    return claims


# ---------------------------------------------------------------------------
# 1. Wrong audience — rejected before Agent OBO exchange (FR-02, FR-04)
# ---------------------------------------------------------------------------


def test_wrong_audience_rejected_before_obo() -> None:
    """agent-wrong-audience: aud mismatch MUST reject before any OBO exchange.

    The fixture carries the BFF audience instead of the blueprint audience.
    ``require_audience`` at the Agentic Layer gateway MUST return False so that
    the OBO exchange is never attempted (FR-02).
    """
    claims = _load("agent-wrong-audience")

    accepted = require_audience(claims, BLUEPRINT_AUD)

    assert accepted is False, (
        f"Expected audience check to reject aud={claims.get('aud')!r}; "
        f"blueprint audience is {BLUEPRINT_AUD!r}"
    )


# ---------------------------------------------------------------------------
# 2. Missing actor / appid — rejected at MCP boundary (FR-04)
# ---------------------------------------------------------------------------


def test_missing_actor_rejected_at_mcp_boundary() -> None:
    """agent-missing-actor: OBO-shaped token without appid MUST be rejected.

    The MCP protected API requires ``appid`` on Agent OBO tokens to prove the
    token was issued by the registered agent application.  A token that passes
    the delegated-scope check but carries no ``appid`` MUST be rejected by
    ``require_actor_appid`` at the MCP boundary.
    """
    claims = _load("agent-missing-actor")

    # Pre-condition: the fixture must be missing appid.
    assert claims.get("appid") is None, (
        "Pre-condition violated: agent-missing-actor fixture should have no 'appid' claim"
    )

    # The fixture IS delegated (has scp) — it would pass the scope check.
    assert require_delegated_token(claims) is True, (
        "Pre-condition violated: agent-missing-actor should be delegated-shaped (has scp)"
    )

    # MCP boundary actor check MUST reject the token.
    actor_ok = require_actor_appid(claims)

    assert actor_ok is False, (
        "MCP boundary: agent OBO token without 'appid' MUST be rejected"
    )


# ---------------------------------------------------------------------------
# 3. App-only blueprint token — rejected for delegated endpoints (FR-04)
# ---------------------------------------------------------------------------


def test_app_only_blueprint_rejected_for_delegated_endpoints() -> None:
    """agent-app-only-blueprint: token without scp MUST be rejected.

    The fixture has the correct blueprint audience and an appid but no ``scp``
    claim (app-only shape, no user context).  Delegated endpoints MUST reject
    it via ``require_delegated_token``.
    """
    claims = _load("agent-app-only-blueprint")

    # Pre-condition: correct blueprint audience present, no scp.
    assert claims.get("aud") == BLUEPRINT_AUD, (
        "Pre-condition violated: agent-app-only-blueprint should have blueprint aud"
    )
    assert claims.get("scp") is None, (
        "Pre-condition violated: agent-app-only-blueprint must have no scp"
    )

    delegated = require_delegated_token(claims)

    assert delegated is False, (
        "Delegated endpoint: app-only token (no scp) MUST be rejected by require_delegated_token"
    )


# ---------------------------------------------------------------------------
# 4. Untrusted tenant — rejected by tenant allowlist check (FR-04)
# ---------------------------------------------------------------------------


def test_untrusted_tenant_rejected() -> None:
    """agent-untrusted-tenant: tid not in allowlist MUST be rejected.

    The fixture carries tid=00000000-0000-0000-0000-000000000002, which is not
    in the trusted-tenant allowlist.  ``validate_claims`` MUST report
    'untrusted_tenant' in its failure list.
    """
    claims = _load("agent-untrusted-tenant")

    # Pre-condition: tenant is distinct from the trusted one.
    assert claims.get("tid") != TRUSTED_TENANT, (
        "Pre-condition violated: agent-untrusted-tenant must carry an untrusted tid"
    )

    failures = validate_claims(
        claims,
        issuer=None,  # skip issuer check — this test isolates the tid check
        trusted_tenants=[TRUSTED_TENANT],
        now=time.time(),
    )

    assert "untrusted_tenant" in failures, (
        f"Expected 'untrusted_tenant' in validate_claims failures; "
        f"got {failures!r}  (tid={claims.get('tid')!r})"
    )


# ---------------------------------------------------------------------------
# 5. Replay / stale token — rejected as expired (FR-04)
# ---------------------------------------------------------------------------


def test_replay_stale_token_rejected_as_expired() -> None:
    """agent-replay-stale: past exp MUST be rejected as token_expired.

    The fixture sets exp=1600000000 (2020-09-13 UTC), which is always in the
    past.  With clock_skew_seconds=0, ``validate_claims`` MUST report
    'token_expired'.
    """
    claims = _load("agent-replay-stale")

    # Pre-condition: exp is demonstrably in the past.
    exp = claims.get("exp")
    assert isinstance(exp, int) and exp < int(time.time()), (
        f"Pre-condition violated: exp={exp!r} is not in the past"
    )

    failures = validate_claims(
        claims,
        issuer=None,  # skip issuer check — this test isolates the exp check
        trusted_tenants=None,  # skip tenant check — isolate exp check
        clock_skew_seconds=0,
        now=time.time(),
    )

    assert "token_expired" in failures, (
        f"Expected 'token_expired' in validate_claims failures; "
        f"got {failures!r}  (exp={exp!r})"
    )
