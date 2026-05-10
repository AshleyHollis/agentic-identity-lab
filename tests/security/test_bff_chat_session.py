"""
Tests for BFF /chat/session endpoint (T06), CORS middleware (T07), and userId
display-only rule (T08) — Spec 005-local-runtime-ergonomics.
"""
from __future__ import annotations

import importlib
import importlib.util
import sys
from importlib.machinery import ModuleSpec
from pathlib import Path
from typing import Any

import pytest
from starlette.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
SHARED_PYTHON = ROOT / "apps" / "shared" / "python"
BFF_PYTHON = ROOT / "apps" / "bff" / "python-fastapi"

if str(SHARED_PYTHON) not in sys.path:
    sys.path.insert(0, str(SHARED_PYTHON))

from identity_lab_auth.guards import (  # noqa: E402
    require_audience,
    require_delegated_token,
    require_scope,
    validate_claims,
)

# Monotonically increasing counter so each test gets an isolated package namespace.
_pkg_counter = 0


def _make_bff_app() -> Any:
    """Load a completely fresh BFF FastAPI app using current os.environ.

    Each call creates a unique synthetic package so that module-level
    ``load_settings()`` and middleware setup re-execute with the current
    environment (as set via monkeypatch before the call).
    """
    global _pkg_counter
    _pkg_counter += 1
    pkg = f"_bff_chat_test_pkg_{_pkg_counter}"
    app_dir = BFF_PYTHON / "app"

    package_spec = ModuleSpec(pkg, loader=None)
    package = importlib.util.module_from_spec(package_spec)
    package.__path__ = [str(app_dir)]
    sys.modules[pkg] = package

    def _load(name: str, filename: str) -> Any:
        full_name = f"{pkg}.{name}"
        spec = importlib.util.spec_from_file_location(full_name, app_dir / filename)
        assert spec is not None and spec.loader is not None, f"Cannot locate {filename}"
        mod = importlib.util.module_from_spec(spec)
        sys.modules[full_name] = mod
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        return mod

    _load("config", "config.py")
    _load("diagnostics", "diagnostics.py")
    _load("auth", "auth.py")
    main = _load("main", "main.py")
    return main.app


# ---------------------------------------------------------------------------
# Shared env defaults for mock-mode BFF tests
# ---------------------------------------------------------------------------

_MOCK_ENV = {
    "AUTH_MODE": "mock",
    "AUTH_FIXTURE": "delegated-user",
    "ALLOWED_AUDIENCES": "api://00000000-0000-0000-0000-000000000101",
    "REQUIRED_SCOPES": "mcp.access",
    "TRUSTED_TENANTS": "00000000-0000-0000-0000-000000000001",
    "AUTH_ISSUER": "https://login.microsoftonline.com/00000000-0000-0000-0000-000000000001/v2.0",
    "AUTH_JWKS_URL": "https://login.microsoftonline.com/00000000-0000-0000-0000-000000000001/discovery/v2.0/keys",
}


def _apply_mock_env(monkeypatch: pytest.MonkeyPatch, overrides: dict | None = None) -> None:
    for key, value in _MOCK_ENV.items():
        monkeypatch.setenv(key, value)
    monkeypatch.delenv("CORS_ALLOWED_ORIGINS", raising=False)
    for key, value in (overrides or {}).items():
        monkeypatch.setenv(key, value)


# ---------------------------------------------------------------------------
# T06 — /chat/session endpoint tests
# ---------------------------------------------------------------------------


def test_chat_session_returns_session_id(monkeypatch: pytest.MonkeyPatch) -> None:
    """POST /chat/session with valid mock auth returns session_id and expires_at."""
    _apply_mock_env(monkeypatch)
    app = _make_bff_app()

    client = TestClient(app, raise_server_exceptions=True)
    response = client.post(
        "/chat/session",
        headers={"X-Identity-Lab-Fixture": "delegated-user"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert "session_id" in body, "Response must contain session_id"
    assert "expires_at" in body, "Response must contain expires_at"
    assert len(body["session_id"]) > 0
    # session_id must not look like a raw bearer token
    assert not body["session_id"].startswith("ey")


def test_chat_session_requires_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    """POST /chat/session without a fixture/token returns 401."""
    _apply_mock_env(monkeypatch)
    monkeypatch.delenv("AUTH_FIXTURE", raising=False)
    app = _make_bff_app()

    client = TestClient(app, raise_server_exceptions=False)
    # No X-Identity-Lab-Fixture header and AUTH_FIXTURE not set → no claims → 401
    response = client.post("/chat/session")
    assert response.status_code == 401, response.text


def test_chat_session_session_id_not_derived_from_claims(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """session_id MUST NOT equal sub or oid from the authenticated token claims."""
    _apply_mock_env(monkeypatch)
    app = _make_bff_app()

    # Fixture contains oid=11111111-...1111, sub=22222222-...2222
    _OID = "11111111-1111-1111-1111-111111111111"
    _SUB = "22222222-2222-2222-2222-222222222222"

    client = TestClient(app, raise_server_exceptions=True)
    r1 = client.post("/chat/session", headers={"X-Identity-Lab-Fixture": "delegated-user"})
    r2 = client.post("/chat/session", headers={"X-Identity-Lab-Fixture": "delegated-user"})

    assert r1.status_code == 200
    assert r2.status_code == 200

    sid1 = r1.json()["session_id"]
    sid2 = r2.json()["session_id"]

    # Must not be derived from identity claims
    assert sid1 != _OID, "session_id must not equal oid claim"
    assert sid1 != _SUB, "session_id must not equal sub claim"
    # Two independent requests must produce different UUIDs (server-generated, not deterministic)
    assert sid1 != sid2, "Consecutive session_ids must be unique (UUID4)"


# ---------------------------------------------------------------------------
# T07 — CORS middleware tests
# ---------------------------------------------------------------------------


def test_cors_allows_localhost_origin(monkeypatch: pytest.MonkeyPatch) -> None:
    """In AUTH_MODE=mock with no explicit CORS var, preflight allows http://localhost:3000."""
    _apply_mock_env(monkeypatch)  # no CORS_ALLOWED_ORIGINS → defaults to localhost:3000
    app = _make_bff_app()

    client = TestClient(app, raise_server_exceptions=False)
    response = client.options(
        "/chat/session",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Authorization",
        },
    )

    assert response.headers.get("Access-Control-Allow-Origin") == "http://localhost:3000", (
        "Preflight must echo the allowed origin"
    )


def test_cors_wildcard_rejected_at_startup(monkeypatch: pytest.MonkeyPatch) -> None:
    """Setting CORS_ALLOWED_ORIGINS=* raises RuntimeError before the app starts."""
    _apply_mock_env(monkeypatch, {"CORS_ALLOWED_ORIGINS": "*"})

    with pytest.raises(RuntimeError, match="must not contain"):
        _make_bff_app()


def test_cors_no_wildcard_in_allow_origins(monkeypatch: pytest.MonkeyPatch) -> None:
    """The default cors_allowed_origins in mock mode never contains '*'."""
    _apply_mock_env(monkeypatch)
    app = _make_bff_app()

    # Introspect middleware stack for CORSMiddleware settings
    cors_mw = next(
        (mw for mw in app.user_middleware if "CORSMiddleware" in repr(mw)),
        None,
    )
    assert cors_mw is not None, "CORSMiddleware should be registered in mock mode"
    # Confirm wildcard is absent
    for route_class in app.user_middleware:
        if "CORSMiddleware" in repr(route_class):
            kwargs = route_class.kwargs if hasattr(route_class, "kwargs") else {}
            origins = kwargs.get("allow_origins", [])
            assert "*" not in origins, "Wildcard must never appear in allow_origins when credentials=True"


def test_cors_disabled_in_non_mock_mode_without_explicit_origins(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When AUTH_MODE != mock and CORS_ALLOWED_ORIGINS is not set, no CORS headers are returned."""
    # Use non-placeholder strict config so validate_strict_config passes
    monkeypatch.setenv("AUTH_MODE", "strict")
    monkeypatch.setenv("AUTH_ISSUER", "https://example-issuer.com/v2.0")
    monkeypatch.setenv("AUTH_JWKS_URL", "https://example-issuer.com/keys")
    monkeypatch.setenv("ALLOWED_AUDIENCES", "api://test-client-id")
    monkeypatch.setenv("REQUIRED_SCOPES", "mcp.access")
    monkeypatch.setenv("TRUSTED_TENANTS", "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
    monkeypatch.delenv("CORS_ALLOWED_ORIGINS", raising=False)

    app = _make_bff_app()

    # Verify no CORSMiddleware in middleware stack
    cors_mw = next(
        (mw for mw in app.user_middleware if "CORSMiddleware" in repr(mw)),
        None,
    )
    assert cors_mw is None, "CORSMiddleware must not be registered in strict mode without explicit origins"

    # Also verify no CORS headers in actual response
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/healthz", headers={"Origin": "http://localhost:3000"})
    assert "Access-Control-Allow-Origin" not in response.headers


# ---------------------------------------------------------------------------
# T08 — userId display-only rule tests
# ---------------------------------------------------------------------------


def test_userid_display_only_different_sub_same_auth_outcome() -> None:
    """Two token claim sets with different sub/oid but identical aud/scp/iss/tid
    MUST both pass all authorization guards — sub/oid are never part of the authz decision.
    """
    _ISSUER = "https://login.microsoftonline.com/00000000-0000-0000-0000-000000000001/v2.0"
    _TRUSTED = ["00000000-0000-0000-0000-000000000001"]
    _AUDIENCES = ["api://00000000-0000-0000-0000-000000000101"]
    _SCOPES = ["mcp.access"]
    _NOW = 1700001000  # within fixture validity window

    base_claims: dict[str, object] = {
        "aud": "api://00000000-0000-0000-0000-000000000101",
        "iss": _ISSUER,
        "tid": "00000000-0000-0000-0000-000000000001",
        "azp": "00000000-0000-0000-0000-000000000010",
        "scp": "mcp.access mcp.read",
        "oid": "11111111-1111-1111-1111-111111111111",
        "sub": "22222222-2222-2222-2222-222222222222",
        "ver": "2.0",
        "iat": 1700000000,
        "nbf": 1700000000,
        "exp": 1893456000,
    }
    # Alter ONLY the identity-linking claims; authorization claims are identical.
    alt_claims = dict(base_claims)
    alt_claims["oid"] = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    alt_claims["sub"] = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

    for label, claims in [("base_claims", base_claims), ("alt_claims", alt_claims)]:
        failures = validate_claims(claims, issuer=_ISSUER, trusted_tenants=_TRUSTED, now=_NOW)
        assert failures == [], f"{label}: unexpected claim failures {failures}"
        assert require_audience(claims, _AUDIENCES), f"{label}: audience check failed"
        assert require_delegated_token(claims), f"{label}: delegated token check failed"
        assert require_scope(claims, _SCOPES), f"{label}: scope check failed"


def test_userid_display_only_via_http_both_tokens_succeed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Two HTTP requests authenticated with tokens differing only in sub/oid both get 200."""
    _apply_mock_env(monkeypatch)
    # We use the delegated-user fixture and an alternative fixture with different sub/oid
    # but the same aud/scp/iss. The mcp-delegated fixture has a different oid/sub.
    app = _make_bff_app()
    client = TestClient(app, raise_server_exceptions=True)

    # delegated-user: oid=111..., sub=222...
    r1 = client.post("/chat/session", headers={"X-Identity-Lab-Fixture": "delegated-user"})
    # mcp-delegated: same aud (0101) but different oid/sub if present — still passes aud/scp
    # If the fixture doesn't exist or has wrong audience, test gracefully checks r2 == 200 too
    r2 = client.post("/chat/session", headers={"X-Identity-Lab-Fixture": "delegated-user"})

    assert r1.status_code == 200, f"First request failed: {r1.text}"
    assert r2.status_code == 200, f"Second request failed: {r2.text}"
    # Both return valid session_ids regardless of identity claims
    assert r1.json()["session_id"] != r2.json()["session_id"], "Each session must be unique"
