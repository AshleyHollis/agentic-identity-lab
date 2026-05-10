from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHARED_PYTHON = ROOT / "apps" / "shared" / "python"
sys.path.append(str(SHARED_PYTHON))

from identity_lab_auth.guards import (  # noqa: E402
    AuthContext,
    require_audience,
    require_delegated_token,
    require_scope,
    validate_claims,
)
from identity_lab_auth.token_type import classify_claims_token_type  # noqa: E402

FIXTURES_DIR = ROOT / "tests" / "fixtures" / "sample-claims"
ISSUER = "https://login.microsoftonline.com/00000000-0000-0000-0000-000000000001/v2.0"
TRUSTED_TENANTS = ["00000000-0000-0000-0000-000000000001"]
NOW = 1700001000


def _load_fixture(name: str) -> dict[str, object]:
    payload = (FIXTURES_DIR / f"{name}.json").read_text(encoding="utf-8")
    return json.loads(payload)


def test_require_audience_enforces_matches() -> None:
    claims = _load_fixture("delegated-user")
    assert require_audience(claims, ["api://00000000-0000-0000-0000-000000000101"])
    assert not require_audience(claims, ["api://00000000-0000-0000-0000-000000000999"])


def test_require_scope_rejects_missing_scope() -> None:
    claims = _load_fixture("delegated-user")
    assert require_scope(claims, ["mcp.access"])
    assert not require_scope(claims, ["mcp.write"])


def test_app_only_rejected_for_delegated_paths() -> None:
    claims = _load_fixture("app-only")
    assert classify_claims_token_type(claims) == "app-only"
    assert not require_delegated_token(claims)


def test_auth_context_strips_subject_claims() -> None:
    claims = _load_fixture("delegated-user")
    context = AuthContext.from_claims(claims, token_type="bearer")
    assert "sub" not in context.claims
    assert "oid" not in context.claims
    assert context.scopes == ["mcp.access", "mcp.read"]


def test_validate_claims_accepts_valid_claims() -> None:
    claims = _load_fixture("delegated-user")
    failures = validate_claims(
        claims,
        issuer=ISSUER,
        trusted_tenants=TRUSTED_TENANTS,
        now=NOW,
    )
    assert failures == []


def test_validate_claims_rejects_untrusted_tenant() -> None:
    claims = _load_fixture("untrusted-tenant")
    failures = validate_claims(
        claims,
        issuer=ISSUER,
        trusted_tenants=TRUSTED_TENANTS,
        now=NOW,
    )
    assert "untrusted_tenant" in failures


def test_validate_claims_rejects_expired_token() -> None:
    claims = _load_fixture("expired-token")
    failures = validate_claims(
        claims,
        issuer=ISSUER,
        trusted_tenants=TRUSTED_TENANTS,
        now=NOW,
    )
    assert "token_expired" in failures


def test_validate_claims_rejects_not_yet_valid_token() -> None:
    claims = _load_fixture("not-yet-valid")
    failures = validate_claims(
        claims,
        issuer=ISSUER,
        trusted_tenants=TRUSTED_TENANTS,
        now=NOW,
    )
    assert "token_not_yet_valid" in failures


def test_validate_claims_rejects_future_iat() -> None:
    claims = _load_fixture("iat-in-future")
    failures = validate_claims(
        claims,
        issuer=ISSUER,
        trusted_tenants=TRUSTED_TENANTS,
        now=NOW,
    )
    assert "token_issued_in_future" in failures


def test_validate_claims_rejects_issuer_mismatch() -> None:
    claims = _load_fixture("issuer-mismatch")
    failures = validate_claims(
        claims,
        issuer=ISSUER,
        trusted_tenants=TRUSTED_TENANTS,
        now=NOW,
    )
    assert "invalid_issuer" in failures
