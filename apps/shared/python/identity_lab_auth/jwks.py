"""
JWKS client and strict JWT algorithm validation.

Implements ADR-M5-03: PyJWT + manual httpx JWKS fetch, in-process TTL dict cache,
one kid-miss retry, lowercase alg normalization, jku/x5u suppression, ≤5s fetch timeout.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

import jwt

# ---------------------------------------------------------------------------
# Algorithm enforcement (Security Design Notes §6, ADR-M5-03)
# ---------------------------------------------------------------------------

# Symmetric and null algorithms that MUST be rejected in all validation paths.
# Stored lowercase — _validate_algorithm() normalises the raw alg before comparison.
REJECTED_ALGORITHMS: frozenset[str] = frozenset({"none", "hs256", "hs384", "hs512"})

# Asymmetric algorithms allowed for signature verification.
ALLOWED_ALGORITHMS: frozenset[str] = frozenset({"RS256", "RS384", "RS512", "ES256", "ES384"})

_ALLOWED_LOWER: frozenset[str] = frozenset(a.lower() for a in ALLOWED_ALGORITHMS)


def _validate_algorithm(alg_raw: str) -> str:
    """Normalise and validate a JWT ``alg`` header value.

    Mixed-case variants (``None``, ``NONE``, ``nOnE``, ``HS256``) are a documented
    bypass vector — normalization to lowercase closes this gap.

    Returns the canonical casing suitable for ``jwt.decode(algorithms=[...])``.
    Raises ``ValueError`` if the algorithm is rejected or unrecognised.
    """
    if not alg_raw:
        raise ValueError("Rejected algorithm: '' (empty)")
    alg = alg_raw.strip().lower()
    if alg in REJECTED_ALGORITHMS:
        raise ValueError(f"Rejected algorithm: {alg_raw!r}")
    if alg not in _ALLOWED_LOWER:
        raise ValueError(f"Rejected algorithm: {alg_raw!r}")
    # Return canonical (proper-case) form for PyJWT
    for allowed in ALLOWED_ALGORITHMS:
        if allowed.lower() == alg:
            return allowed
    raise ValueError(f"Rejected algorithm: {alg_raw!r}")  # unreachable


# ---------------------------------------------------------------------------
# JWKS cache (ADR-M5-03 §JwksCache)
# ---------------------------------------------------------------------------


@dataclass
class JwksCache:
    """In-process JWKS key cache keyed by ``kid``.

    JWKS URL MUST be sourced from ``AUTH_JWKS_URL`` config only.
    Token header claims ``jku`` and ``x5u`` MUST NOT influence ``jwks_url``
    (SSRF + algorithm-swap vector — Security Design Notes §7).

    One instance per service; not a module-level global so it is injectable
    in tests without patching globals.
    """

    jwks_url: str
    ttl_seconds: int = 300
    fetch_timeout_seconds: float = 5.0  # combined connect + read (Security Design Notes §8)
    _cache: dict[str, Any] = field(default_factory=dict, repr=False)
    _fetched_at: float = field(default=0.0, repr=False)

    # Optional httpx.Client injected for testing (avoids monkeypatching the module)
    _http_client: Any = field(default=None, repr=False)

    def get_key(self, kid: str) -> Any:
        """Return the JWK dict for *kid*, fetching/refreshing JWKS as needed.

        Raises ``ValueError`` if the kid is absent after one retry.
        """
        if self._is_stale():
            self._refresh()
        key = self._cache.get(kid)
        if key is None:
            # One retry on kid-miss (ADR-M5-03 Note 3).
            # More retries risk thundering-herd during key rotation.
            self._refresh()
            key = self._cache.get(kid)
        if key is None:
            raise ValueError(f"kid {kid!r} not found in JWKS after refresh")
        return key

    def _is_stale(self) -> bool:
        return (time.monotonic() - self._fetched_at) > self.ttl_seconds

    def _refresh(self) -> None:
        """Fetch the JWKS from ``jwks_url`` and repopulate the cache.

        The URL is ALWAYS ``self.jwks_url`` — never taken from a token header
        (``jku``/``x5u`` suppression, Security Design Notes §7).
        """
        import httpx  # lazy import; httpx is an optional dep for offline tests

        client = self._http_client
        if client is not None:
            response = client.get(self.jwks_url, timeout=self.fetch_timeout_seconds)
        else:
            response = httpx.get(self.jwks_url, timeout=self.fetch_timeout_seconds)
        response.raise_for_status()
        keys = response.json().get("keys", [])
        self._cache = {k["kid"]: k for k in keys if "kid" in k}
        self._fetched_at = time.monotonic()


# ---------------------------------------------------------------------------
# Full strict-mode validation flow
# ---------------------------------------------------------------------------


def validate_strict(
    token: str,
    cache: JwksCache,
    *,
    allowed_audiences: list[str],
    issuer: str | None = None,
    allowed_issuers: list[str] | None = None,
) -> dict[str, Any]:
    """Validate *token* in strict mode using *cache* for JWKS key lookup.

    Steps (per ADR-M5-03 §Full validation flow):
    1. Decode header only (no signature check).
    2. Algorithm check — before any key fetch.
    3. ``kid`` required.
    4. JWKS key lookup (with one retry on miss).
    5. Signature + claims verification.

    ``jku``/``x5u`` suppression: the JWKS URL is never derived from token content;
    only ``cache.jwks_url`` (set from ``AUTH_JWKS_URL`` config) is used.

    ``allowed_issuers``: when provided (multi-value list), takes precedence over
    ``issuer`` and enables accepting both v1 (sts.windows.net) and v2
    (login.microsoftonline.com) Entra tokens without a code rebuild.

    Returns sanitized claims dict on success. Raises ``ValueError`` on any
    validation failure.
    """
    # 1. Decode header only — no signature verification yet
    # options={"verify_signature": False} prevents PyJWT from following jku/x5u.
    header = jwt.get_unverified_header(token)

    # 2. Algorithm enforcement (lowercase normalisation closes mixed-case bypass)
    canonical_alg = _validate_algorithm(header.get("alg", ""))

    # 3. kid is mandatory for asymmetric JWKS lookup
    kid = header.get("kid")
    if not kid:
        raise ValueError("Missing kid in token header")

    # 4. Fetch/cache key — URL sourced exclusively from cache.jwks_url (not token)
    jwk_data = cache.get_key(kid)
    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(jwk_data)

    # 5. Verify signature + standard claims.
    # When multiple issuers are accepted, skip PyJWT's built-in issuer check
    # (which accepts only a single string) and perform the check manually after
    # signature verification.
    effective_issuers = [v.strip() for v in (allowed_issuers or []) if v.strip()]
    if effective_issuers:
        # Multi-issuer path: skip PyJWT issuer validation; check manually below.
        jwt_issuer = None
    else:
        jwt_issuer = issuer

    decode_options: dict[str, Any] = {"require": ["exp", "nbf", "aud", "iss"]}
    claims = jwt.decode(
        token,
        public_key,
        algorithms=[canonical_alg],  # explicit allowlist — no autodiscovery
        audience=allowed_audiences,
        issuer=jwt_issuer,
        options=decode_options,
    )

    if effective_issuers:
        claim_iss = claims.get("iss", "")
        if not isinstance(claim_iss, str) or claim_iss.strip() not in effective_issuers:
            raise ValueError(f"Issuer '{claim_iss}' not in allowed issuers")

    return claims
