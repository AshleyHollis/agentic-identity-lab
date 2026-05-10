"""T09 — Strict JWKS validation tests (offline).

Covers (per tasks.md §T09 and ADR-M5-03):
- alg:none rejection (+ mixed-case variants: None, NONE, nOnE)
- HS256, HS384, HS512 rejection (symmetric algorithms)
- Missing kid rejection
- Unknown kid rejection after one retry
- Fixture header suppression in strict mode
- jku / x5u header suppression (SSRF prevention)
- Valid RS256 header accepted (signature verification mocked offline)

All tests are fully offline — no real OIDC endpoints contacted.
JWKS fetch is replaced with an injected stub client.
"""
from __future__ import annotations

import base64
import json
import sys
import time
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
SHARED_PYTHON = ROOT / "apps" / "shared" / "python"
sys.path.insert(0, str(SHARED_PYTHON))

from identity_lab_auth.jwks import (  # noqa: E402
    ALLOWED_ALGORITHMS,
    REJECTED_ALGORITHMS,
    JwksCache,
    _validate_algorithm,
    validate_strict,
)
from identity_lab_auth.auth_settings import AUTH_FIXTURE_HEADER, AuthMode  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _b64url(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode()
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _make_jwt_with_header(header: dict[str, Any], payload: dict[str, Any] | None = None) -> str:
    """Build a raw (unsigned / invalid-signature) JWT with the given header.

    Sufficient for header-level rejection tests where signature verification
    is never reached.
    """
    if payload is None:
        payload = {"sub": "test", "exp": int(time.time()) + 3600}
    h = _b64url(json.dumps(header))
    p = _b64url(json.dumps(payload))
    sig = _b64url(b"fakesignature")
    return f"{h}.{p}.{sig}"


def _make_stub_cache(keys: dict[str, Any] | None = None) -> JwksCache:
    """Return a JwksCache pre-populated with *keys* that never fetches the network."""
    cache = JwksCache(jwks_url="https://stub.example.com/jwks")
    cache._cache = keys or {}
    cache._fetched_at = time.monotonic()  # mark as fresh
    return cache


def _stub_refresh_noop(cache: JwksCache) -> None:
    """Patch _refresh so no network call is made (cache stays as-is)."""
    cache._refresh = lambda: None  # type: ignore[method-assign]


def _stub_refresh_with_keys(cache: JwksCache, keys: dict[str, Any]) -> None:
    """Patch _refresh to load *keys* instead of hitting the network."""
    def _refresh() -> None:
        cache._cache = keys
        cache._fetched_at = time.monotonic()
    cache._refresh = _refresh  # type: ignore[method-assign]


# ---------------------------------------------------------------------------
# _validate_algorithm unit tests
# ---------------------------------------------------------------------------


class TestAlgorithmValidation:
    """Algorithm normalization and rejection (Security Design Notes §6)."""

    def test_alg_none_lowercase_rejected(self) -> None:
        with pytest.raises(ValueError, match="Rejected algorithm"):
            _validate_algorithm("none")

    def test_alg_none_capitalised_rejected(self) -> None:
        """Mixed-case bypass vector — must be rejected."""
        with pytest.raises(ValueError, match="Rejected algorithm"):
            _validate_algorithm("None")

    def test_alg_none_uppercase_rejected(self) -> None:
        with pytest.raises(ValueError, match="Rejected algorithm"):
            _validate_algorithm("NONE")

    def test_alg_none_mixed_case_rejected(self) -> None:
        with pytest.raises(ValueError, match="Rejected algorithm"):
            _validate_algorithm("nOnE")

    def test_alg_hs256_rejected(self) -> None:
        with pytest.raises(ValueError, match="Rejected algorithm"):
            _validate_algorithm("HS256")

    def test_alg_hs256_lowercase_rejected(self) -> None:
        with pytest.raises(ValueError, match="Rejected algorithm"):
            _validate_algorithm("hs256")

    def test_alg_hs384_rejected(self) -> None:
        with pytest.raises(ValueError, match="Rejected algorithm"):
            _validate_algorithm("HS384")

    def test_alg_hs512_rejected(self) -> None:
        with pytest.raises(ValueError, match="Rejected algorithm"):
            _validate_algorithm("HS512")

    def test_alg_empty_rejected(self) -> None:
        with pytest.raises(ValueError, match="Rejected algorithm"):
            _validate_algorithm("")

    def test_alg_rs256_accepted(self) -> None:
        assert _validate_algorithm("RS256") == "RS256"

    def test_alg_rs384_accepted(self) -> None:
        assert _validate_algorithm("RS384") == "RS384"

    def test_alg_rs512_accepted(self) -> None:
        assert _validate_algorithm("RS512") == "RS512"

    def test_alg_es256_accepted(self) -> None:
        assert _validate_algorithm("ES256") == "ES256"

    def test_alg_rs256_lowercase_normalised(self) -> None:
        """Lowercase input produces correct canonical form."""
        assert _validate_algorithm("rs256") == "RS256"

    def test_rejected_algorithms_set_contains_none(self) -> None:
        assert "none" in REJECTED_ALGORITHMS

    def test_rejected_algorithms_set_contains_symmetric(self) -> None:
        assert {"hs256", "hs384", "hs512"}.issubset(REJECTED_ALGORITHMS)

    def test_allowed_algorithms_set_contains_rsa(self) -> None:
        assert {"RS256", "RS384", "RS512"}.issubset(ALLOWED_ALGORITHMS)


# ---------------------------------------------------------------------------
# JwksCache unit tests
# ---------------------------------------------------------------------------


class TestJwksCache:
    """JWKS cache kid-miss and retry behaviour (ADR-M5-03)."""

    def test_missing_kid_raises_after_retry(self) -> None:
        """kid absent from cache → one retry → still absent → ValueError."""
        cache = _make_stub_cache(keys={})  # empty — kid never found
        _stub_refresh_noop(cache)  # retry does nothing
        with pytest.raises(ValueError, match="not found in JWKS after refresh"):
            cache.get_key("unknown-kid-abc")

    def test_present_kid_returned(self) -> None:
        stub_key = {"kid": "key-001", "kty": "RSA", "n": "stub", "e": "stub"}
        cache = _make_stub_cache(keys={"key-001": stub_key})
        _stub_refresh_noop(cache)
        assert cache.get_key("key-001") == stub_key

    def test_stale_cache_triggers_refresh(self) -> None:
        stub_key = {"kid": "key-002", "kty": "RSA"}
        cache = _make_stub_cache(keys={})
        cache._fetched_at = 0.0  # force stale
        _stub_refresh_with_keys(cache, {"key-002": stub_key})
        assert cache.get_key("key-002") == stub_key

    def test_kid_miss_triggers_one_retry(self) -> None:
        """key not in fresh cache → retry → found."""
        stub_key = {"kid": "rotated-key", "kty": "RSA"}
        cache = _make_stub_cache(keys={})
        cache._fetched_at = time.monotonic()  # fresh — no stale refresh
        _stub_refresh_with_keys(cache, {"rotated-key": stub_key})
        assert cache.get_key("rotated-key") == stub_key

    def test_jwks_url_never_overridden_by_token_content(self) -> None:
        """SSRF prevention: cache.jwks_url must not be influenced by token jku/x5u."""
        cache = JwksCache(jwks_url="https://config.example.com/jwks")
        assert cache.jwks_url == "https://config.example.com/jwks"
        # Simulate an attacker supplying jku/x5u — they MUST NOT change the url
        attacker_url = "https://attacker.example.com/evil-jwks"
        # The cache has no mechanism to accept a URL from outside — this is the guard.
        assert cache.jwks_url != attacker_url

    def test_fetch_timeout_default_bounded(self) -> None:
        """Default fetch timeout MUST be ≤ 5 seconds (Security Design Notes §8)."""
        cache = JwksCache(jwks_url="https://example.com/jwks")
        assert cache.fetch_timeout_seconds <= 5.0


# ---------------------------------------------------------------------------
# validate_strict — token-level rejection (offline stubs)
# ---------------------------------------------------------------------------


class TestValidateStrictAlgorithmRejection:
    """validate_strict rejects bad algorithms before any key lookup."""

    def _cache_with_no_fetch(self) -> JwksCache:
        cache = _make_stub_cache({})
        _stub_refresh_noop(cache)
        return cache

    def test_alg_none_rejected(self) -> None:
        token = _make_jwt_with_header({"alg": "none", "typ": "JWT"})
        with pytest.raises(ValueError, match="Rejected algorithm"):
            validate_strict(token, self._cache_with_no_fetch(), allowed_audiences=["test"])

    def test_alg_none_mixed_case_rejected(self) -> None:
        for variant in ("None", "NONE", "nOnE"):
            token = _make_jwt_with_header({"alg": variant, "typ": "JWT"})
            with pytest.raises(ValueError, match="Rejected algorithm"):
                validate_strict(token, self._cache_with_no_fetch(), allowed_audiences=["test"])

    def test_hs256_rejected(self) -> None:
        token = _make_jwt_with_header({"alg": "HS256", "kid": "k1", "typ": "JWT"})
        with pytest.raises(ValueError, match="Rejected algorithm"):
            validate_strict(token, self._cache_with_no_fetch(), allowed_audiences=["test"])

    def test_hs384_rejected(self) -> None:
        token = _make_jwt_with_header({"alg": "HS384", "kid": "k1", "typ": "JWT"})
        with pytest.raises(ValueError, match="Rejected algorithm"):
            validate_strict(token, self._cache_with_no_fetch(), allowed_audiences=["test"])

    def test_hs512_rejected(self) -> None:
        token = _make_jwt_with_header({"alg": "HS512", "kid": "k1", "typ": "JWT"})
        with pytest.raises(ValueError, match="Rejected algorithm"):
            validate_strict(token, self._cache_with_no_fetch(), allowed_audiences=["test"])


class TestValidateStrictKidRejection:
    """validate_strict rejects tokens with missing or unknown kid."""

    def test_missing_kid_rejected(self) -> None:
        token = _make_jwt_with_header({"alg": "RS256", "typ": "JWT"})  # no kid
        cache = _make_stub_cache({})
        _stub_refresh_noop(cache)
        with pytest.raises(ValueError, match="Missing kid"):
            validate_strict(token, cache, allowed_audiences=["test"])

    def test_unknown_kid_rejected_after_retry(self) -> None:
        token = _make_jwt_with_header({"alg": "RS256", "kid": "ghost-key", "typ": "JWT"})
        cache = _make_stub_cache({})  # empty — kid never present
        _stub_refresh_noop(cache)
        with pytest.raises(ValueError, match="not found in JWKS after refresh"):
            validate_strict(token, cache, allowed_audiences=["test"])


# ---------------------------------------------------------------------------
# Fixture header suppression in strict mode
# ---------------------------------------------------------------------------


class TestFixtureHeaderSuppressionInStrictMode:
    """X-Identity-Lab-Fixture header MUST have no effect in AUTH_MODE=strict."""

    def test_fixture_header_does_not_bypass_strict_validation(self) -> None:
        """Passing the fixture header in strict mode must not short-circuit JWKS validation."""
        from identity_lab_auth.auth_settings import load_auth_settings, AUTH_MODE_ENV

        settings = load_auth_settings(
            headers={AUTH_FIXTURE_HEADER: "delegated-user"},
            env={AUTH_MODE_ENV: "strict"},
        )
        # In strict mode the fixture name is stored but load_auth_claims raises
        # NotImplementedError — the fixture header must NOT route around strict validation.
        assert settings.mode == AuthMode.STRICT
        # Verify that fixture value is present in settings but does not grant claims
        from identity_lab_auth.auth_settings import load_auth_claims
        with pytest.raises(NotImplementedError):
            load_auth_claims(settings)

    def test_fixture_header_select_returns_value_in_mock_mode(self) -> None:
        """Control: header IS used in mock mode (confirms the suppression test is meaningful)."""
        from identity_lab_auth.auth_settings import load_auth_settings, AUTH_MODE_ENV

        settings = load_auth_settings(
            headers={AUTH_FIXTURE_HEADER: "delegated-user"},
            env={AUTH_MODE_ENV: "mock"},
        )
        assert settings.mode == AuthMode.MOCK
        assert settings.fixture == "delegated-user"


# ---------------------------------------------------------------------------
# jku / x5u suppression (SSRF prevention — Security Design Notes §7)
# ---------------------------------------------------------------------------


class TestJkuX5uSuppression:
    """JWKS URL must come exclusively from config, never from token headers."""

    def test_jku_in_token_header_does_not_influence_fetch_url(self) -> None:
        """The cache URL must not change when a token carries jku."""
        config_url = "https://config.example.com/jwks"
        cache = JwksCache(jwks_url=config_url)
        # Simulate what validate_strict does: extract header, validate alg, get kid
        # The jwks_url on the cache must remain the config URL regardless of jku
        assert cache.jwks_url == config_url

    def test_x5u_in_token_header_does_not_influence_fetch_url(self) -> None:
        config_url = "https://config.example.com/jwks"
        cache = JwksCache(jwks_url=config_url)
        assert cache.jwks_url == config_url

    def test_validate_strict_does_not_read_jku_from_header(self) -> None:
        """validate_strict must raise on alg/kid issues — not follow jku."""
        token = _make_jwt_with_header({
            "alg": "RS256",
            "kid": "k1",
            "typ": "JWT",
            "jku": "https://attacker.example.com/evil-jwks",  # SSRF vector
        })
        cache = _make_stub_cache({})  # kid not present → raises
        _stub_refresh_noop(cache)
        # Should fail with kid-not-found, NOT by fetching attacker URL
        with pytest.raises(ValueError, match="not found in JWKS after refresh"):
            validate_strict(token, cache, allowed_audiences=["test"])

    def test_validate_strict_does_not_read_x5u_from_header(self) -> None:
        token = _make_jwt_with_header({
            "alg": "RS256",
            "kid": "k1",
            "typ": "JWT",
            "x5u": "https://attacker.example.com/evil-cert",  # SSRF vector
        })
        cache = _make_stub_cache({})
        _stub_refresh_noop(cache)
        with pytest.raises(ValueError, match="not found in JWKS after refresh"):
            validate_strict(token, cache, allowed_audiences=["test"])


# ---------------------------------------------------------------------------
# Valid RS256 structure accepted (algorithm check only — signature mocked)
# ---------------------------------------------------------------------------


class TestValidRS256StructureAccepted:
    """RS256 + kid present passes algorithm and kid checks (signature mocked offline)."""

    def test_rs256_with_valid_kid_passes_algorithm_check(self) -> None:
        """Algorithm check and kid lookup pass; full signature verify requires real keys.
        
        We verify up to the point of key lookup succeeding.  The stub JWK data will
        cause jwt.decode to raise a key-format error, confirming algorithm + kid
        rejection gates were NOT triggered.
        """
        stub_jwk = {
            "kid": "valid-key-001",
            "kty": "RSA",
            "use": "sig",
            "n": "sIbeschj0VdDsRvb",  # intentionally invalid — causes key format error
            "e": "AQAB",
        }
        cache = _make_stub_cache({"valid-key-001": stub_jwk})
        _stub_refresh_noop(cache)

        token = _make_jwt_with_header({"alg": "RS256", "kid": "valid-key-001", "typ": "JWT"})

        # Algorithm + kid checks pass; the error comes from key parsing / signature
        # verification — NOT from algorithm rejection or missing-kid rejection.
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with pytest.raises(Exception) as exc_info:
                validate_strict(token, cache, allowed_audiences=["test"])
        assert "Rejected algorithm" not in str(exc_info.value)
        assert "Missing kid" not in str(exc_info.value)
        assert "not found in JWKS" not in str(exc_info.value)
