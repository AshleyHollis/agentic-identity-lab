# ADR-003: JWKS Client Library and Key-Rotation / Caching Strategy

> **Status:** Accepted
> **Date:** 2026-05-15
> **Deciders:** Trinity (Security/Identity), Ashley Hollis (Product Owner)
> **Phase:** security
> **Impact:** High — applies to all services performing strict JWT validation against Entra ID JWKS endpoints; any future service that validates JWTs in `AUTH_MODE=strict` must follow this decision.

## Context

Spec 002 introduces strict JWT/JWKS validation (`AUTH_MODE=strict`) for the lab's identity flows. This requires:

1. A Python library to decode JWT headers and verify signatures against JWKS public keys.
2. A caching strategy for JWKS key material that is safe under key rotation, resilient to `kid` changes, and resistant to algorithm-confusion and SSRF attacks.

Three candidate libraries were evaluated. The choice has security implications beyond performance:

- **Algorithm confusion** (CVE-2022-29217 in `python-jose`): A library that does not enforce the caller's algorithm allowlist can be tricked into accepting tokens signed with a weaker algorithm.
- **SSRF via `jku`/`x5u`**: Some JOSE libraries follow the JWT header's `jku` (JWK Set URL) or `x5u` (X.509 URL) claims to fetch keys. An attacker who can craft a token header can direct the server to fetch an attacker-controlled URL.
- **Stale key material**: Without a `kid`-miss-retry strategy, a newly rotated key will cause all validations to fail until the TTL expires.

This is a cross-cutting concern: the `JwksCache` and algorithm enforcement logic will be shared across the Agent Execution Service, BFF, and MCP Protected API in `apps/shared/python/identity_lab_auth/`.

## Ranked priorities

1. **No algorithm confusion** — the library and call pattern must make it impossible to accept a token with an attacker-chosen algorithm.
2. **No SSRF** — JWKS URL must come exclusively from server config; token-header claims must not influence the fetch URL.
3. **Key rotation safety** — a rotated key must become usable within one TTL cycle without service restart.
4. **Testability** — the caching layer must be injectable so unit tests can exercise `kid`-miss and cache-population paths without a live OIDC endpoint.
5. **Ecosystem fit** — prefer libraries already present (directly or transitively) in the FastAPI ecosystem to avoid adding heavyweight dependencies.

## Options considered

### Option A: `PyJWT` + manual `httpx` JWKS fetch ✅ (Selected)

Use `PyJWT` for JWT header decode and signature verification. Fetch JWKS manually via `httpx` with an explicit URL from `AUTH_JWKS_URL` config. Maintain an in-process `dict` cache keyed by `kid`, with a configurable TTL (default 300 s).

**Security properties:**
- Algorithm enforcement is caller-controlled: `jwt.decode(token, key, algorithms=["RS256"])`. No library-level algorithm autodiscovery.
- `jku`/`x5u` header claims are never followed — the fetch URL is hardcoded to `AUTH_JWKS_URL`.
- No known algorithm confusion CVEs in maintained release line.

**Key-rotation behaviour:**
1. On `kid` miss in cache → invalidate entire cache, re-fetch JWKS once.
2. If `kid` still absent after refresh → raise `ValueError("kid not found in JWKS after refresh")`.
3. On TTL expiry (300 s default) → refresh lazily on next request.

**Pros:**
- `PyJWT` is a transitive dependency of `python-jose`, `authlib`, and `fastapi-jwt-auth` — likely already present.
- Transparent algorithm enforcement; the caller's `algorithms=` list is the only list that matters.
- `httpx` is already used for outbound HTTP in the lab's services.
- Cache logic is simple `dict` + `time.monotonic()`; no extra library required.
- Fully testable by injecting a `JwksCache` instance with a stub `httpx.Client`.

**Cons:**
- Manual JWKS parsing (extracting RSA/EC keys from JWK set) requires `PyJWT`'s `PyJWKClient` helper or equivalent.
- Must explicitly disable any `PyJWT` modes that follow `jku`/`x5u` (use `options={"verify_signature": True}` and never call `PyJWKClient` with `headers=True`).

### Option B: `joserfc`

**Pros:** JOSE RFC-compliant; no known CVEs.
**Cons:** Smaller community (< 1M monthly downloads vs PyJWT's 50M+); custom LRU cache adds complexity; no clear security advantage over Option A.
**Score:** Priority 5 (ecosystem fit) ❌ — not a common transitive dependency.

### Option C: `python-jose` ❌ (Eliminated)

**CVE-2022-29217:** Algorithm confusion vulnerability — an attacker can craft a token with `alg: RS256` but present an HMAC key, causing some `python-jose` usage patterns to accept it.
**No `kid`-miss rotation hook** — stale keys require manual cache invalidation.
**Eliminated** on Priority 1 (no algorithm confusion).

## Decision

We chose **Option A**: `PyJWT` + manual `httpx` JWKS fetch with an in-process TTL dict cache.

### Implementation specification

#### Algorithm enforcement

```python
ALLOWED_ALGORITHMS = {"RS256", "RS384", "RS512", "ES256", "ES384"}
REJECTED_ALGORITHMS = {"none", "hs256", "hs384", "hs512"}  # lowercase — see Note 1

def _validate_algorithm(alg_raw: str) -> str:
    """Normalize and validate JWT algorithm header."""
    alg = alg_raw.strip().lower()  # Note 1: always normalize to lowercase
    if alg in REJECTED_ALGORITHMS or alg not in {a.lower() for a in ALLOWED_ALGORITHMS}:
        raise ValueError(f"Rejected algorithm: {alg_raw!r}")
    # Return the canonical casing for PyJWT
    for allowed in ALLOWED_ALGORITHMS:
        if allowed.lower() == alg:
            return allowed
    raise ValueError(f"Rejected algorithm: {alg_raw!r}")
```

**Note 1:** `alg` MUST be lowercased before rejection comparison. A header of `alg: None`, `alg: NONE`, or `alg: nOnE` MUST all be rejected identically to `alg: none`. Mixed-case variants are a documented bypass vector; normalization closes this.

#### JWKS URL source

```python
# MUST be sourced exclusively from config — never from token header
jwks_url: str = settings.auth_jwks_url  # from AUTH_JWKS_URL env var

# MUST NOT do:
# jwks_url = jwt_header.get("jku")   ← SSRF vector — prohibited
# jwks_url = jwt_header.get("x5u")   ← SSRF vector — prohibited
```

#### JwksCache

```python
@dataclass
class JwksCache:
    """In-process JWKS key cache. One instance per service (not module-level global)."""
    jwks_url: str
    ttl_seconds: int = 300   # configurable via AUTH_JWKS_CACHE_TTL_SECONDS
    fetch_timeout_seconds: float = 5.0  # Note 2
    _cache: dict[str, Any] = field(default_factory=dict)
    _fetched_at: float = field(default=0.0)

    def get_key(self, kid: str) -> Any:
        if self._is_stale():
            self._refresh()
        key = self._cache.get(kid)
        if key is None:
            self._refresh()          # one retry on kid-miss (Note 3)
            key = self._cache.get(kid)
        if key is None:
            raise ValueError(f"kid {kid!r} not found in JWKS after refresh")
        return key

    def _is_stale(self) -> bool:
        return (time.monotonic() - self._fetched_at) > self.ttl_seconds

    def _refresh(self) -> None:
        # httpx fetch with bounded timeout (Note 2)
        response = httpx.get(self.jwks_url, timeout=self.fetch_timeout_seconds)
        response.raise_for_status()
        keys = response.json().get("keys", [])
        self._cache = {k["kid"]: k for k in keys if "kid" in k}
        self._fetched_at = time.monotonic()
```

**Note 2:** `httpx` MUST set a combined connect + read timeout ≤ 5 seconds. An unreachable JWKS endpoint must raise `ValueError` (not hang), so the upstream request returns HTTP 401 promptly.

**Note 3:** One retry on `kid` miss is sufficient. Two retries introduce a thundering-herd risk during key rotation where all in-flight requests simultaneously re-fetch. The retry is only triggered by an absent `kid`, not by TTL expiry.

#### Full validation flow (strict mode)

```python
def validate_strict(token: str, cache: JwksCache, settings: StrictSettings) -> dict:
    # 1. Decode header only (no signature check yet)
    header = jwt.get_unverified_header(token)

    # 2. Algorithm check (before any key fetch)
    canonical_alg = _validate_algorithm(header.get("alg", ""))

    # 3. kid required
    kid = header.get("kid")
    if not kid:
        raise ValueError("Missing kid in token header")

    # 4. Fetch/cache key
    jwk_data = cache.get_key(kid)
    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(jwk_data)

    # 5. Verify signature + claims
    claims = jwt.decode(
        token,
        public_key,
        algorithms=[canonical_alg],  # explicit — no autodiscovery
        audience=settings.allowed_audiences,
        options={"require": ["exp", "nbf", "aud", "iss"]},
    )

    # 6. Additional claim checks (iss, tid, scp)
    _validate_iss(claims, settings.issuer)
    _validate_tid(claims, settings.trusted_tenants)
    _validate_scp(claims, settings.required_scopes)

    return claims
```

### Offline test requirements

Tests for strict JWKS validation (T09) MUST:

1. Cover `alg:none` rejection (including `None`, `NONE` mixed-case variants).
2. Cover `HS256`, `HS384`, `HS512` rejection.
3. Cover missing `kid` rejection.
4. Cover `kid` miss after one retry (simulate via `JwksCache` with empty key set).
5. Cover fixture-header suppression in strict mode: pass `X-Identity-Lab-Fixture` header in a strict-mode context; assert it has no effect on validation outcome.
6. All tests MUST pass without any network calls (inject a `JwksCache` with a patched `_refresh` that reads from a local fixture JWK set).

## Consequences

**Positive:**
- Algorithm confusion attacks are prevented by explicit `algorithms=` parameter in every `jwt.decode()` call.
- SSRF via `jku`/`x5u` is prevented by never deriving the JWKS URL from token content.
- Key rotation latency is bounded: at most one TTL cycle (300 s) plus one retry fetch (< 5 s).
- The `JwksCache` is injectable, making all cache scenarios testable offline.

**Negative / costs:**
- Manual JWKS key parsing adds ~20 lines of boilerplate vs. some higher-level libraries.
- Services must import `PyJWT` explicitly; this is a new `requirements.txt` entry if not already transitive.

**Neutral / informational:**
- `python-jose` is eliminated permanently for this lab. If `python-jose` appears as a transitive dependency of another library, it MUST NOT be used for token verification — only `PyJWT` for that purpose.
- The `JwksCache.ttl_seconds` default of 300 s is intentionally conservative. Entra ID rotates signing keys infrequently (weeks), so 5-minute TTL is more than sufficient for freshness.

## Implementation notes

**M5 scope (Spec 002 — T09/T12):**
- Implement `JwksCache` and `_validate_algorithm` in `apps/shared/python/identity_lab_auth/jwks.py` (new file).
- Write offline tests under `tests/security/test_strict_jwks_validation.py`.
- Update `apps/shared/python/identity_lab_auth/__init__.py` to export `JwksCache`, `validate_strict`.

**Files to create/modify:**
- `apps/shared/python/identity_lab_auth/jwks.py` — new (T09/T12)
- `apps/shared/python/requirements.txt` — add `PyJWT>=2.8` and `httpx>=0.27` if not already present (T09)
- `tests/security/test_strict_jwks_validation.py` — new (T09)

## Review checkpoints

- [ ] T09 implementation: `test_strict_jwks_validation.py` covers all five rejection cases (alg:none mixed-case, HS*, missing-kid, kid-miss-retry, fixture-header suppression).
- [ ] T12 implementation: `JwksCache` used consistently across all strict-mode token validation entry points; no direct `python-jose` imports for validation.
- [ ] T15 (Trinity post-impl security sign-off): Confirm `jku`/`x5u` suppression is present in final implementation; confirm `alg` lowercasing is tested.
- [ ] Re-review trigger: if any new JOSE CVE is published against `PyJWT` or `httpx`, this ADR must be reviewed before the next milestone.

## References

- Spec 002 — Strict JWKS validation design: `.squad/specs/002-aks-entra-agent-id/design.md §Strict JWT / JWKS Validation Design`
- Spec 002 ADR-M5-03 in-spec record: `.squad/specs/002-aks-entra-agent-id/design.md §ADR-M5-03`
- CVE-2022-29217 (python-jose algorithm confusion): https://github.com/advisories/GHSA-ffqj-6fqr-9h24
- PyJWT documentation: https://pyjwt.readthedocs.io/en/stable/
- RFC 7517 (JWK) / RFC 7518 (JWA) / RFC 7519 (JWT)
- OWASP JWT cheat sheet: https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html
- Related ADR: `docs/adr/0008-jwks-client-caching-strategy.md` (public-docs counterpart — to be created by Tank/Neo at implementation start)
- Requested by: Ashley Hollis — T03 security gate, Spec 002 M5
