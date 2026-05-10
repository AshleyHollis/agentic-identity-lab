# Spec 002 — Design

**Spec:** 002-aks-entra-agent-id  
**Milestone:** M5 — AKS + Entra Agent ID auth exploration  
**Updated:** 2026-05-15 (Amendment 001)

---

## Terminology Definitions

*(Added: Amendment 001, 2026-05-15 — see also `README.md §Terminology`)*

To prevent confusion between the lab's own services and the AKS Agent Gateway, this document uses the following terms consistently (per ADR 0006):

| Term | Meaning in this document |
|------|--------------------------|
| **Agentic Layer** | The lab's app-level orchestration service at `apps/agent-gateway/` (legacy filesystem path; not renamed). The application identity and OBO boundary. |
| **AKS Agent Gateway** | The agentgateway.dev open-source proxy deployed in AKS as infrastructure; NOT the Agentic Layer |
| **Entra Agent ID sidecar** | The Entra Agent ID SDK container running in the same pod as the Agentic Layer in AKS |

The `apps/agent-gateway/` directory and Docker Compose service name `agent-gateway` are legacy paths preserved for backward compatibility. All prose references use **Agentic Layer**.

---

## ADR-M5-01 — AKS Optional Track vs ACA Default Track

**Status:** ✅ Accepted (Morpheus — 2026-05-14)

**Decision:** Option A — standalone `environments/aks/` directory. ACA remains the default (`single-tenant`); AKS is strictly opt-in with a separate, independently validatable environment overlay.

**Rationale:** Keeps ACA and AKS concerns fully separated; AKS overlay validates independently without touching the existing `single-tenant` environment.

**Question:** Should the AKS deployment path be a standalone environment (`environments/aks/`) or a feature-flag overlay on the existing `single-tenant` environment?

**Options evaluated:**

| Option | Approach | Pros | Cons |
|---|---|---|---|
| A | Standalone `environments/aks/` directory | Clear separation; ACA remains untouched | Slight duplication of shared vars |
| B | Feature-flag overlay on `single-tenant` | Minimal new files | AKS and ACA concerns mix; harder to validate in isolation |
| C | Separate `aks` workspace with shared modules | Maximum isolation | Higher complexity for a first skeleton |

**Preferred (pending confirmation):** Option A — standalone `environments/aks/` directory. This keeps the ACA default (`single-tenant`) completely unmodified, and the AKS overlay can be validated independently (`terraform validate -chdir=infra/terraform/environments/aks`). ACA remains the default; AKS is strictly opt-in.

**Decision:** _To be recorded by Morpheus in `.progress.md`._

---

## ADR-M5-02 — Agent ID Sidecar Mock Boundary vs Real SDK / Direct MSAL

**Status:** ✅ Accepted (Morpheus + Trinity — 2026-05-14)

**Decision:** Option A — in-process adapter with `AgentSidecarClient` ABC, swappable for a real HTTP adapter in future live-test opt-in. The interface is designed for drop-in replacement without modifying the Agentic Layer's call sites.

**Rationale:** Zero external dependencies in offline mode; preserves offline safety while making the real AKS Agent Gateway sidecar drop-in ready when Trinity approves live testing.

**Question:** In mock/offline mode, should the Agent OBO sidecar boundary be (A) an in-process Python adapter that resolves from fixture claims, (B) a real localhost HTTP stub process, or (C) direct MSAL calls in tests?

**Options evaluated:**

| Option | Approach | Pros | Cons |
|---|---|---|---|
| A | In-process adapter — reads fixture claims, no HTTP | Zero external dependencies; fast; fully offline | Does not exercise real HTTP sidecar protocol |
| B | Localhost HTTP stub (e.g., `httpretty`, `responses`, `pytest-httpserver`) | Validates HTTP contract offline | More setup; still needs fixture data |
| C | Direct MSAL (`msal.ConfidentialClientApplication.acquire_token_on_behalf_of`) | Uses real library | Requires live Entra credentials; breaks offline constraint |

**Preferred (pending confirmation):** Option A for offline/mock mode with the interface designed to be swappable for Option B in a future live-test opt-in. The agent OBO boundary module exposes a protocol/ABC (`AgentSidecarClient`) that the in-process mock and a future real HTTP adapter both implement. This preserves offline safety while making the real sidecar drop-in ready.

**Decision:** _To be recorded by Morpheus + Trinity in `.progress.md`._

---

## ADR-M5-03 — JWKS Client Library and Key-Rotation / Caching Strategy

**Status:** ✅ Accepted (Trinity — 2026-05-15)

**Decision:** Option A — `PyJWT` + manual `httpx` JWKS fetch, in-process TTL dict keyed by `kid`, 300-second default TTL (configurable via `AUTH_JWKS_CACHE_TTL_SECONDS`), one `kid`-miss retry with full cache invalidation, then hard fail.

**Rationale:**
- `PyJWT` is actively maintained and widely adopted in the FastAPI/Python ecosystem.
- Manual JWKS fetch via `httpx` gives explicit control over algorithm enforcement and timeout (no SSRF risk when URL is sourced strictly from config).
- The TTL + `kid`-miss-retry pattern is transparent and testable without additional mocking layers.
- `python-jose` carries CVE-2022-29217 (algorithm confusion) — eliminated.
- `joserfc` lacks the community adoption and ecosystem precedent to prefer over PyJWT for this use case.

**Full cross-cutting decision:** See `.squad/architecture/decisions/003-jwks-client-caching-strategy.md`.

**Question:** Which Python JWKS client library should be used, and what caching / key-rotation strategy should be enforced?

**Options evaluated:**

| Option | Library | Cache approach | Key rotation | Security notes |
|---|---|---|---|---|
| A ✅ | `PyJWT` + manual `httpx` JWKS fetch | In-process TTL dict (default 300 s, configurable) | On `kid` miss: invalidate cache, re-fetch once, then hard fail | Actively maintained; no known algorithm confusion CVEs; full control over `jku`/`x5u` suppression |
| B | `joserfc` | Custom LRU | Same as A | Viable but smaller community; no clear security advantage over PyJWT |
| C ❌ | `python-jose` | In-process | No explicit `kid`-miss rotation hook | CVE-2022-29217 (algorithm confusion); eliminated |

**Security constraints (Trinity — mandatory for T09/T12 implementation):**

1. **JWKS URL source:** The JWKS URL MUST be sourced exclusively from `AUTH_JWKS_URL` config. Token header claims `jku` and `x5u` MUST be ignored; any library mode that reads them MUST be disabled.
2. **Algorithm case normalization:** The `alg` header value MUST be normalized to lowercase before comparison against `REJECTED_ALGORITHMS` and `ALLOWED_ALGORITHMS`. A token with `alg: None` or `alg: NONE` MUST be rejected identically to `alg: none`.
3. **JWKS fetch timeout:** `httpx` JWKS fetch MUST set a connect + read timeout no greater than 5 seconds to prevent slow-server DoS.
4. **Cache isolation:** The in-process JWKS cache MUST be per-service-instance (no shared mutable global accessible across test cases). Tests that exercise cache behavior MUST inject a fresh `JwksCache` instance.
5. **No blocking on cache population:** Cache is populated lazily on first validation; startup MUST NOT fail if the JWKS endpoint is unreachable.

---

## Agent ID Sidecar Contract

### Endpoint Schemas

#### `GET /Validate`

**Request:** Inbound `Authorization: Bearer <token>` header.

**Response (200 OK — valid):**
```json
{
  "valid": true,
  "claims": {
    "aud": "api://00000000-0000-0000-0000-000000000201/access_as_user",
    "iss": "https://login.microsoftonline.com/00000000-0000-0000-0000-000000000001/v2.0",
    "tid": "00000000-0000-0000-0000-000000000001",
    "azp": "00000000-0000-0000-0000-000000000010",
    "scp": "access_as_user",
    "appid": "00000000-0000-0000-0000-000000000201",
    "ver": "2.0"
  }
}
```

**Response (401 Unauthorized — invalid):**
```json
{"valid": false, "reason": "token_expired | wrong_audience | untrusted_tenant | missing_scope | alg_rejected"}
```

All claim values in the `claims` field pass through `sanitize_claims()`. `oid` and `sub` are never present.

#### `GET /AuthorizationHeader/{apiName}`

**Request:** Path param `apiName` (e.g., `mcp-protected-api`). Sidecar resolves an existing token for the named API from its internal token cache (or triggers acquisition).

**Response (200 OK):**
```json
{
  "header": "Bearer <token-string-omitted-in-offline-mode>"
}
```

In offline/mock mode the `header` value is a synthetic placeholder string: `Bearer OFFLINE_MOCK_TOKEN`.

#### `POST /DownstreamApi/{apiName}`

**Request body:**
```json
{
  "userAssertion": "<inbound-bearer-token>",
  "scopes": ["mcp.access"]
}
```

**Response (200 OK):**
```json
{
  "claims": {
    "aud": "api://00000000-0000-0000-0000-000000000103",
    "iss": "https://login.microsoftonline.com/00000000-0000-0000-0000-000000000001/v2.0",
    "tid": "00000000-0000-0000-0000-000000000001",
    "appid": "00000000-0000-0000-0000-000000000201",
    "xms_act_fct": {"appid": "00000000-0000-0000-0000-000000000201"},
    "scp": "mcp.access",
    "ver": "2.0"
  }
}
```

Response claims pass through `sanitize_claims()`. The raw token string is never returned.

---

## Agent OBO Sidecar Mock Boundary Design

### Interface (ABC)

```python
# apps/shared/python/identity_lab_auth/agent_obo.py (stub — implementation deferred)
from abc import ABC, abstractmethod
from typing import Any

class AgentSidecarClient(ABC):
    """Boundary between agent-gateway and Entra Agent ID sidecar."""

    @abstractmethod
    def validate(self, bearer_token: str) -> dict[str, Any]:
        """Validate bearer token; return sanitized claims or raise ValueError."""
        ...

    @abstractmethod
    def authorization_header(self, api_name: str) -> str:
        """Return 'Authorization: Bearer <token>' string for the named API."""
        ...

    @abstractmethod
    def downstream_api(self, api_name: str, user_assertion: str, scopes: list[str]) -> dict[str, Any]:
        """Perform Agent OBO exchange; return sanitized downstream claims."""
        ...
```

### MockAgentSidecarClient Behaviour

- Constructed with a `fixture_claims: dict` loaded from the fixture file.
- `validate()`: checks `aud` against `blueprint_audience`; checks `tid` against `trusted_tenants`; checks `exp`; returns `sanitize_claims(fixture_claims)` or raises `ValueError`.
- `authorization_header()`: returns the literal string `"Bearer OFFLINE_MOCK_TOKEN"`.
- `downstream_api()`: validates `user_assertion` audience, then returns `sanitize_claims(obo_fixture_claims)` from the loaded OBO fixture.
- Makes **zero HTTP calls**.
- Sidecar URL is validated on construction: `http://localhost` or `http://127.0.0.1` only.

### Blueprint Audience Validation

```python
# Pseudocode — not implementation
BLUEPRINT_AUDIENCE = "api://00000000-0000-0000-0000-000000000201/access_as_user"

def _validate_blueprint_audience(claims: dict, expected: str) -> None:
    if claims.get("aud") != expected:
        raise ValueError(f"Expected blueprint audience {expected!r}; got {claims.get('aud')!r}")
```

### Separation from MCP User OBO

| Concern | Module | Auth path |
|---|---|---|
| MCP user OBO (Spec 001/003) | `identity_lab_auth.obo.exchange_on_behalf_of` | User token → MCP audience |
| Agent OBO (this spec) | `identity_lab_auth.agent_obo.AgentSidecarClient` | Blueprint user token → MCP audience via sidecar |
| Azure OpenAI/Foundry | Separate managed identity path (no shared import) | `cognitiveservices.azure.com` audience |

---

## Offline Fixture Design

### Placeholder GUID Assignments

| Placeholder | Role |
|---|---|
| `00000000-0000-0000-0000-000000000001` | Trusted tenant ID |
| `00000000-0000-0000-0000-000000000002` | Untrusted tenant ID (negative fixture) |
| `00000000-0000-0000-0000-000000000010` | Inbound client (user's app / AZP) |
| `00000000-0000-0000-0000-000000000103` | MCP protected API app ID / audience suffix |
| `00000000-0000-0000-0000-000000000201` | Blueprint app ID |

Blueprint audience: `api://00000000-0000-0000-0000-000000000201/access_as_user`  
MCP audience: `api://00000000-0000-0000-0000-000000000103`

### Fixture Claim Content

**`agent-blueprint-user-token.json`:**
```json
{
  "aud": "api://00000000-0000-0000-0000-000000000201/access_as_user",
  "iss": "https://login.microsoftonline.com/00000000-0000-0000-0000-000000000001/v2.0",
  "tid": "00000000-0000-0000-0000-000000000001",
  "azp": "00000000-0000-0000-0000-000000000010",
  "scp": "access_as_user",
  "ver": "2.0",
  "iat": 1700000000,
  "nbf": 1700000000,
  "exp": 1893456000
}
```

**`agent-obo-mcp-token.json`:**
```json
{
  "aud": "api://00000000-0000-0000-0000-000000000103",
  "iss": "https://login.microsoftonline.com/00000000-0000-0000-0000-000000000001/v2.0",
  "tid": "00000000-0000-0000-0000-000000000001",
  "appid": "00000000-0000-0000-0000-000000000201",
  "xms_act_fct": {"appid": "00000000-0000-0000-0000-000000000201"},
  "scp": "mcp.access",
  "ver": "2.0",
  "iat": 1700000000,
  "nbf": 1700000000,
  "exp": 1893456000
}
```

**`agent-wrong-audience.json`:** Same as blueprint user token but `aud` set to `api://00000000-0000-0000-0000-000000000101` (BFF audience — wrong).

**`agent-missing-actor.json`:** OBO-shaped token (MCP aud) with no `appid` claim.

**`agent-app-only-blueprint.json`:** Blueprint aud, no `scp`, no user subject context — app-only shape.

**`agent-untrusted-tenant.json`:** Valid blueprint aud but `tid = 00000000-0000-0000-0000-000000000002` (untrusted).

**`agent-replay-stale.json`:** Blueprint aud, valid claims, but `exp = 1600000000` (past).

---

## Strict JWT / JWKS Validation Design

### Algorithm Allowlist

```python
ALLOWED_ALGORITHMS = {"RS256", "RS384", "RS512", "ES256", "ES384"}
REJECTED_ALGORITHMS = {"none", "HS256", "HS384", "HS512"}
```

Validation flow (strict mode):

1. Decode JWT header (no signature verification).
2. Extract `alg` and `kid`.
3. If `alg in REJECTED_ALGORITHMS` or `alg not in ALLOWED_ALGORITHMS` → raise `ValueError("Rejected algorithm: {alg}")`.
4. If `kid` is absent → raise `ValueError("Missing kid in token header")`.
5. Fetch JWKS (from cache or remote). Find matching key by `kid`.
6. If no matching key → clear cache, re-fetch once. If still no match → raise `ValueError("kid not found in JWKS")`.
7. Verify signature with matching key.
8. Validate claims: `exp`, `nbf`, `aud`, `iss`, `tid`, `scp`.

### Strict-Mode Fixture Header Suppression

```python
# In AUTH_MODE=strict, fixture header is ignored entirely:
if auth_mode == AuthMode.STRICT:
    fixture_name = None  # X-Identity-Lab-Fixture header has no effect
```

This guard is tested offline by passing a fixture header in a strict-mode context and asserting it has no effect on validation outcome.

### JWKS Cache Design

```python
# Pseudocode — not implementation
@dataclass
class JwksCache:
    ttl_seconds: int = 300
    _cache: dict[str, Any] = field(default_factory=dict)
    _fetched_at: float = 0.0

    def get_key(self, kid: str, jwks_url: str) -> Any:
        if self._is_stale():
            self._refresh(jwks_url)
        key = self._cache.get(kid)
        if key is None:
            self._refresh(jwks_url)  # one retry on kid miss
            key = self._cache.get(kid)
        if key is None:
            raise ValueError(f"kid {kid!r} not found in JWKS after refresh")
        return key
```

---

## AKS Terraform Skeleton Layout

```
infra/terraform/
├── modules/
│   ├── aks/
│   │   ├── main.tf          # AKS cluster resource stub
│   │   ├── variables.tf     # cluster_name, location, resource_group_name, node_count, oidc_issuer_enabled
│   │   └── outputs.tf       # cluster_id, oidc_issuer_url, kube_config (placeholder output only)
│   ├── workload-identity/
│   │   ├── main.tf          # Federated identity credential stub
│   │   ├── variables.tf     # blueprint_client_id, oidc_issuer, subject, audience
│   │   └── outputs.tf       # federated_credential_id
│   └── k8s-bootstrap/
│       ├── main.tf          # Namespace + service account + RBAC stubs
│       ├── variables.tf     # namespace, service_account_name, blueprint_client_id
│       └── outputs.tf       # namespace, service_account_name
└── environments/
    └── aks/
        ├── main.tf          # Calls aks, workload-identity, k8s-bootstrap modules
        ├── variables.tf     # All variables (no defaults with real values)
        ├── outputs.tf       # Placeholder outputs
        └── terraform.tfvars.example  # All placeholder values only
```

---

## AKS Manifest Layout (docs — illustrative only)

```
docs/deployment/k8s/
├── README.md                      # Context: illustrative only; not applied by CI
├── namespace.yaml
├── service-account.yaml
├── agent-gateway-deployment.yaml  # Agentic Layer (`apps/agent-gateway/`) + Entra Agent ID sidecar container (illustrative)
└── network-policy.yaml
```

All files marked at top: `# ILLUSTRATIVE REFERENCE ONLY — not applied by CI or production automation`.

---

## Security Design Notes (Trinity)

*(Notes 1–5 confirmed at T03 review — 2026-05-15. Notes 6–10 added at T03 review.)*

1. **No token logging.** Raw bearer strings must never appear in logs, structured output, or HTTP response bodies — only sanitized claim dicts. This applies equally to span attributes in the OTEL tracing path.
2. **PII suppression.** `oid`, `sub`, `email`, `upn`, `name`, `preferred_username`, `given_name`, `family_name` are suppressed at the `sanitize_claims()` boundary in all paths. The safe-claims allowlist is the authoritative source; no claim key outside the allowlist may be forwarded to any external system.
3. **`xms_act_fct` dict handling — CONFIRMED REQUIRED (T06 implementation gate).** `xms_act_fct` is a JSON object (`{"appid": "<uuid>"}`) in Entra OBO tokens. The existing `_sanitize_value()` function returns `None` for `dict` inputs (falls through to the final `return None`), which would silently drop the claim even after it is added to the allowlist. T06 MUST extend `_sanitize_value()` to handle `dict` type by either (a) recursively sanitizing only string-valued scalar keys, or (b) serialising to a bounded JSON string (≤ 512 chars). A test MUST assert that `sanitize_claims({"xms_act_fct": {"appid": "x"}, "oid": "y"})` returns `{"xms_act_fct": ...}` without `"oid"`.
4. **No cross-tenant tokens.** `/common/` or `/organizations/` issuers are rejected at the `iss` validation stage (pre-existing rule from Spec 001; must be preserved in the Agent OBO path). The Agent OBO boundary MUST inherit this check; it MUST NOT bypass `tid` validation for sidecar-originated tokens.
5. **Sidecar network policy.** Kubernetes network policy must deny all ingress to the sidecar port except from the co-located agent container (same pod, `localhost`). This is the only layer preventing cross-pod exfiltration of Agent ID tokens in the AKS environment.
6. **Algorithm normalization (T09 implementation gate).** The JWT `alg` header MUST be lowercased before comparison with `REJECTED_ALGORITHMS` / `ALLOWED_ALGORITHMS`. A header of `alg: None`, `alg: NONE`, or `alg: nOnE` MUST all be rejected identically to `alg: none`. Tests for `alg:none` rejection MUST include mixed-case variants.
7. **JWKS URL source integrity (T09/T12 implementation gate).** The JWKS URL MUST be sourced exclusively from the `AUTH_JWKS_URL` environment variable / config. The JWT header claims `jku` (JWK Set URL) and `x5u` (X.509 URL) MUST be explicitly ignored — any `PyJWT` decode mode that follows these claims MUST be disabled. Failure to suppress `jku`/`x5u` creates a server-side request forgery (SSRF) and algorithm-swap attack vector.
8. **JWKS fetch timeout.** The `httpx` client used for JWKS fetches MUST configure a combined connect + read timeout ≤ 5 seconds. An unreachable JWKS endpoint must produce a `ValueError` (not an indefinite hang) so that upstream HTTP 401 is returned promptly.
9. **Fixture name suppression in strict-mode spans (T20 tracing security gate).** Per TR-04.2 (trinity-tank-tracing-input), the `identity_lab.fixture_name` span attribute MUST be set to an empty string or omitted entirely when `AUTH_MODE=strict`. The fixture header value MUST NOT appear in any span, log, or structured output in strict mode. This mirrors the strict-mode fixture suppression already specified in `auth_settings.py` and this design doc.
10. **AgentSidecarClient implementation contract.** All concrete implementations of `AgentSidecarClient` (including any future real HTTP adapter) MUST route all claim outputs through `sanitize_claims()` before returning. The ABC docstrings MUST document this as a contract obligation, not merely an implementation choice, so future implementers do not inadvertently expose raw Entra token claims.

---

## End-to-End Tracing Design

*(Added: Amendment 001, 2026-05-15)*

### Overview

All Python services in the lab's application stack MUST be instrumented with the OpenTelemetry (OTEL) SDK. The AKS Agent Gateway (agentgateway.dev) emits OTEL spans natively. Both sets of spans are sent to the same OTEL collector and visualized in Jaeger.

**Reference:** https://agentgateway.dev/docs/standalone/main/reference/observability/traces/

### OTEL Infrastructure (Mock Flow — Docker Compose)

A `docker/docker-compose.tracing.yml` overlay adds Jaeger to the existing lab Compose stack:

```yaml
# docker/docker-compose.tracing.yml
# ILLUSTRATIVE — not production config; all values are placeholders
services:
  otel-collector:
    image: otel/opentelemetry-collector-contrib:latest
    ports:
      - "4317:4317"   # gRPC — OTEL SDK endpoint
      - "4318:4318"   # HTTP — alternative
    volumes:
      - ./otel-collector-config.yaml:/etc/otel-collector-config.yaml
    command: ["--config=/etc/otel-collector-config.yaml"]

  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"  # Jaeger UI
      - "14268:14268"  # Jaeger HTTP collector
    environment:
      - COLLECTOR_OTLP_ENABLED=true
```

Usage: `docker compose -f docker/docker-compose.yml -f docker/docker-compose.tracing.yml up`

> **T19 implementer note:** The base Compose stack uses the named network `agentic-identity-lab`
> (see `docker-compose.yml` `networks.default.name`). The tracing overlay MUST join this network
> so that `bff`, `agent-gateway`, and `mcp-protected-api` can resolve `otel-collector:4317` by
> Docker DNS. Add `networks: default: external: true  name: agentic-identity-lab` to
> `docker-compose.tracing.yml`, or let Docker Compose merge the network automatically when both
> files are passed to `docker compose -f … -f … up`.

### Span Model

```
trace_id: <uuid>
│
├─ span: bff.request                [BFF FastAPI]
│  ├─ identity_lab.auth_mode: mock
│  ├─ http.route: /api/...
│  └─ span: agentic-layer.request       [Agentic Layer]
│     ├─ identity_lab.aud: api://...-0201/access_as_user
│     ├─ identity_lab.authorized: true
│     └─ span: agentic-layer.obo.exchange  [OBO boundary]
│        ├─ identity_lab.obo_hop: agent_obo
│        └─ span: mcp-api.request       [MCP Protected API]
│           └─ identity_lab.authorized: true
```

AKS flow: the BFF originates the trace root and injects `traceparent` into requests routed through
the AKS Agent Gateway. The AKS Agent Gateway creates its own child span before forwarding to the
Agentic Layer (in AKS the BFF span is visible as the remote parent in the gateway's span).

```
trace_id: <uuid>
│
└─ span: aks-agent-gateway.request         [AKS Agent Gateway — agentgateway.dev, dynamic tracing]
   └─ span: agentic-layer.request          [Agentic Layer in AKS pod]
      ├─ span: sidecar.validate            [Entra Agent ID sidecar — GET /Validate]
      ├─ span: sidecar.downstream-api      [Entra Agent ID sidecar — POST /DownstreamApi/{apiName}]
      │    └─ identity_lab.obo_hop: agent_obo
      └─ span: mcp-api.request
```

### Required Span Attributes

All lab-specific span attributes MUST use the `identity_lab.*` namespace to avoid collision with
OpenTelemetry semantic conventions. The `identity_lab.fixture_name` attribute is the authoritative
precedent set by T03 security review §9; all lab attributes follow the same prefix.

| Attribute key | Service | Value / notes |
|---|---|---|
| `service.name` | All | `bff`, `agent-gateway`, `mcp-protected-api`, `aks-agent-gateway` |
| `identity_lab.auth_mode` | Agentic Layer, BFF | Value of `AUTH_MODE` env var (`mock` / `strict`) |
| `identity_lab.aud` | Agentic Layer | `aud` claim from validated token |
| `identity_lab.authorized` | Agentic Layer, MCP API | Boolean — `true` or `false` |
| `identity_lab.obo_hop` | OBO exchange span | `agent_obo` or `user_obo` |
| `identity_lab.fixture_name` | All (mock only) | `X-Identity-Lab-Fixture` header value; MUST be blank/omitted in `AUTH_MODE=strict` (T03 §9) |
| `http.route` | All FastAPI services | Standard OTEL HTTP semconv |
| `http.method` | All FastAPI services | Standard OTEL HTTP semconv |
| `http.status_code` | All FastAPI services | Standard OTEL HTTP semconv |

> **service.name note:** The canonical lab service term is "Agentic Layer" (per ADR-001), but
> `service.name` is set to `agent-gateway` to match the Docker Compose service name. This makes
> Jaeger service dropdowns consistent with `docker compose ps` output. The AKS Agent Gateway
> (agentgateway.dev) uses `aks-agent-gateway` to disambiguate from the lab service.

> **FR-12 alignment:** FR-12 lists logical attribute names (`auth.mode`, `auth.audience`,
> `auth.outcome`, `obo.hop`). This table supersedes those logical names with their implementation
> identifiers under the `identity_lab.*` namespace.

### Propagation

All services MUST propagate W3C `traceparent` and `tracestate` headers:
- **Inbound:** Extract `traceparent` from every incoming HTTP request.
- **Outbound:** Inject `traceparent` into every downstream HTTP call.
- The AKS Agent Gateway propagates `traceparent` automatically per the agentgateway.dev tracing configuration.

### Static vs Dynamic Tracing Configuration

| Context | Config type | Notes |
|---|---|---|
| Mock flow (Docker Compose) | Static | All services share one OTEL collector endpoint (`localhost:4317`) |
| AKS flow — lab services | Static | OTEL collector endpoint is a Kubernetes service (e.g., `otel-collector:4317`) |
| AKS flow — AKS Agent Gateway | Dynamic | Per-listener `frontendPolicies.tracing`; CEL span attributes for `request.path`, `request.method` etc.; `randomSampling` enabled. **`jwt.sub` and `jwt.oid` MUST NOT be used as CEL expressions — PII prohibition (T03 §9, ADR-002).** |

### Visualization Goal

At the end of M5, a developer MUST be able to:

1. Start the lab with `docker compose -f docker/docker-compose.yml -f docker/docker-compose.tracing.yml up`.
2. Make a request through the BFF to the MCP protected API.
3. Open `http://localhost:16686`, select service `agentic-layer`, click **Find Traces**.
4. See a complete trace with spans for: BFF → Agentic Layer (auth outcome + audience) → OBO boundary → MCP protected API.
5. Expand any span to see `identity_lab.auth_mode`, `identity_lab.authorized`, `identity_lab.obo_hop` attributes.

### Test Isolation

- OTEL instrumentation MUST be no-op (disabled or stubbed) in `pytest` runs.
- Tests MUST NOT depend on a Jaeger instance. Use `OTEL_SDK_DISABLED=true` or equivalent in the test env.
- Tracing config MUST NOT affect correctness of identity validation logic.

---

## Amendments

| # | Date | Changed By | Summary | Status |
|---|------|-----------|---------|--------|
| 001 | 2026-05-15 | spec-feature (Ashley Hollis) | Added Terminology Definitions section; updated AKS manifest layout to use Agentic Layer naming; added End-to-End Tracing Design (OTEL/Jaeger, span model, static/dynamic config, visualization goal). Implementation remains blocked pending T03. | Approved |
| 001-correction | 2026-05-15 | spec-feature (Ashley Hollis) | Terminology corrected per ADR 0006: "local app gateway" → **Agentic Layer**; "standalone Agent Gateway" → **AKS Agent Gateway**. Span `service.name` values updated to `agentic-layer` / `aks-agent-gateway`. | Applied |
| T17-review | 2026-05-27 | Morpheus | T17 architecture review. Four amendments applied: (1) Docker network note for tracing overlay; (2) span names updated to dot-separated convention and `agentic-layer.obo.exchange` replacing `agent_obo.exchange`; (3) Required Span Attributes table converted to `identity_lab.*` namespace per T03 §9; (4) PII error removed — `jwt.sub` CEL example replaced with `request.path`/`request.method` and prohibition note added. `service.name` for lab service set to `agent-gateway` (Compose name) with architecture note. Verdict: AMENDED → ACCEPTED. T18 and T19 unblocked. | Applied |
