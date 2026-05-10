# Spec 002 — Research

**Spec:** 002-aks-entra-agent-id  
**Milestone:** M5 — AKS + Entra Agent ID auth exploration  
**Updated:** 2026-05-14

---

## 1. Source Material

All research is based on publicly available material. No tenant-specific content, credentials, or internal documentation is referenced.

- **Primary:** Christian Posta's Entra Agent ID on Kubernetes series (https://blog.christianposta.com/entra-agent-id-agw/) — covers fundamentals, OBO token exchange, Kubernetes sidecar deployment, workload identity federation, and AgentGateway + MCP/LLM scenarios.
- **Microsoft Entra Agent ID** public product documentation (no internal or tenant-specific pages referenced).
- **Entra Workload Identity Federation** public docs (Azure AD → Kubernetes OIDC trust).
- **Microsoft identity platform: OAuth 2.0 On-Behalf-Of flow** (standard OBO documentation).

---

## 2. Agent ID Token Model

### 2.1 Blueprint vs Agent Identity

- A **blueprint** defines a class of agent. It is represented as an Entra app registration.
- An **agent identity** is a specific deployment of a blueprint, mapped to a Kubernetes service account.
- The blueprint audience follows the pattern `api://<blueprint-app-id>/access_as_user` (placeholder: `api://00000000-0000-0000-0000-000000000201/access_as_user`).
- Blueprint authentication against Entra uses **workload identity federation** (Kubernetes service account OIDC token), avoiding client secrets entirely.

### 2.2 Agent OBO Token Exchange

- The user presents a token whose audience is the blueprint: `aud = api://00000000-0000-0000-0000-000000000201/access_as_user`.
- The Agent ID sidecar performs OBO: user remains the **subject** (`sub`); the agent/blueprint becomes the **actor** (`appid`, `xms_act_fct`).
- The resulting Agent OBO token targets the MCP protected API audience: `aud = api://00000000-0000-0000-0000-000000000103`.
- The Agent OBO token must include `scp` for the downstream MCP operation (e.g., `mcp.access`).

### 2.3 Claim Anatomy

**Blueprint user token (inbound to sidecar):**

```json
{
  "aud": "api://00000000-0000-0000-0000-000000000201/access_as_user",
  "iss": "https://login.microsoftonline.com/00000000-0000-0000-0000-000000000001/v2.0",
  "tid": "00000000-0000-0000-0000-000000000001",
  "azp": "00000000-0000-0000-0000-000000000010",
  "scp": "access_as_user",
  "ver": "2.0"
}
```

**Agent OBO MCP token (output from sidecar exchange):**

```json
{
  "aud": "api://00000000-0000-0000-0000-000000000103",
  "iss": "https://login.microsoftonline.com/00000000-0000-0000-0000-000000000001/v2.0",
  "tid": "00000000-0000-0000-0000-000000000001",
  "appid": "00000000-0000-0000-0000-000000000201",
  "xms_act_fct": {"appid": "00000000-0000-0000-0000-000000000201"},
  "scp": "mcp.access",
  "ver": "2.0"
}
```

All GUIDs above are all-zero placeholder values. `oid`/`sub` are intentionally omitted from the sanitized output.

---

## 3. Agent ID Sidecar Pattern

### 3.1 Sidecar Architecture

- The Entra Agent ID SDK runs as a **sidecar container** alongside the agent workload in the same Kubernetes pod.
- The sidecar exposes a **localhost HTTP API** on a fixed port (e.g., `http://localhost:4000`).
- The agent app calls the sidecar rather than performing its own token acquisition.
- **Network policies must restrict** sidecar port access to `localhost` only — no cross-pod access.

### 3.2 Sidecar Endpoints (per Posta series / Entra Agent ID public docs)

| Endpoint | Method | Purpose |
|---|---|---|
| `/Validate` | GET | Validates the bearer token in the request context from the sidecar's trust model. |
| `/AuthorizationHeader/{apiName}` | GET | Returns a ready-to-use `Authorization: Bearer <token>` header string for the named API. |
| `/DownstreamApi/{apiName}` | POST | Performs Agent OBO exchange and returns the downstream token (or token claims) for the named API. |

In mock/offline mode, these calls must be interceptable by a test double that never makes real HTTP calls.

### 3.3 Localhost Enforcement

The sidecar URL must:
- Begin with `http://localhost` or `http://127.0.0.1` in all non-production modes.
- Be rejected at configuration time if a non-localhost URL is provided (guards against mis-wiring to an external endpoint).

---

## 4. AKS + Workload Identity Architecture

### 4.1 Cluster Requirements

- AKS cluster with **OIDC issuer enabled** (`--enable-oidc-issuer`).
- **Azure AD Workload Identity** add-on installed (`--enable-workload-identity`).
- OIDC issuer URL exported for use in federated credential configuration.

### 4.2 Service Account Binding

- Each agent workload has a dedicated Kubernetes service account.
- Service account annotated with `azure.workload.identity/client-id: <placeholder>` and `azure.workload.identity/tenant-id: <placeholder>`.
- Pod spec annotated with `azure.workload.identity/use: "true"`.
- A federated identity credential on the blueprint's Entra app registration trusts `<oidc-issuer>/sub/system:serviceaccount:<namespace>:<sa-name>`.

### 4.3 Identity Separation

| Identity path | Mechanism | Audience |
|---|---|---|
| Blueprint (agent) auth | Workload identity federation (OIDC) | Entra Agent ID / blueprint app |
| User-delegated MCP OBO | Inbound user token → Agent OBO | `api://mcp-app-id` |
| Azure OpenAI / Foundry | Managed identity (separate MSI) | `cognitiveservices.azure.com` |
| MCP user OBO (Spec 001) | MSAL OBO, separate token | `api://mcp-app-id` |

These paths must not share tokens or be conflated in service configuration.

---

## 5. Strict JWT / JWKS Validation Research

### 5.1 Algorithm Safety

- **`alg: none`** MUST be rejected — a JWT with no signature is trivially forgeable.
- **`HS*` algorithms** (HMAC-SHA: `HS256`, `HS384`, `HS512`) MUST be rejected — symmetric algorithms require a shared secret; Entra ID tokens use RS256/RS384/ES256.
- Accepted algorithms: `RS256`, `RS384`, `RS512`, `ES256`, `ES384` (asymmetric only).

### 5.2 JWKS Key Matching

- Every real Entra ID JWT carries a `kid` (key ID) header claim.
- Validation MUST find the matching `kid` in the JWKS response before verifying the signature.
- Tokens with no `kid`, or with a `kid` absent from the JWKS, MUST be rejected.

### 5.3 Caching Strategy Options

Three approaches were evaluated:

| Option | Library | Cache | Key rotation |
|---|---|---|---|
| A | `PyJWT` + manual JWKS fetch | In-process TTL dict | Retry with fresh JWKS on `kid` miss |
| B | `joserfc` | In-process LRU | Same as A |
| C | `python-jose` | In-process | No explicit rotation hook |

**Preferred (ADR-M5-03 candidate):** Option A — `PyJWT` is already a transitive dependency in the Python ecosystem used by FastAPI; manual JWKS caching with an explicit `kid`-miss refresh is the most transparent and testable pattern. Decision to be confirmed in ADR-M5-03.

### 5.4 Strict-Mode Fixture Header Suppression

In `AUTH_MODE=strict`, the `X-Identity-Lab-Fixture` header MUST be ignored; the header has no effect on token selection or validation. This prevents fixture-bypass attacks in deployed environments.

---

## 6. Existing State Audit

### 6.1 Shared Auth Library (Spec 001 foundation)

- `apps/shared/python/identity_lab_auth/claims.py` — `sanitize_claims()`, `DEFAULT_SAFE_CLAIM_KEYS`, `load_safe_claims_allowlist()`.
- `apps/shared/python/identity_lab_auth/obo.py` — `exchange_on_behalf_of()` (mock OBO boundary for MCP user delegated path).
- `apps/shared/python/identity_lab_auth/auth_settings.py` — `AuthMode`, `AuthSettings`, fixture selection, strict-mode config validation.
- `config/claims/safe-claims-allowlist.json` — currently contains: `aud`, `iss`, `tid`, `azp`, `appid`, `scp`, `roles`, `exp`, `nbf`, `iat`, `ver`. Needs `xms_act_fct` added.

### 6.2 Existing Fixtures

Current fixtures in `tests/fixtures/sample-claims/`:

| File | Covers |
|---|---|
| `delegated-user.json` | BFF/gateway user delegated path |
| `delegated-gateway.json` | Gateway delegated path |
| `mcp-delegated.json` | MCP delegated (Spec 001/003) |
| `mcp-app-only.json` | App-only MCP token (negative) |
| `app-only.json` | Generic app-only |
| `app-only-gateway.json` | Gateway app-only |
| `wrong-audience.json` | Wrong audience (existing negative) |
| `untrusted-tenant.json` | Untrusted tenant (existing negative) |
| `expired-token.json` | Expired (existing negative) |
| `not-yet-valid.json` | nbf in future (existing negative) |
| `iat-in-future.json` | iat in future |
| `mcp-missing-scope.json` | Missing scope |
| `issuer-mismatch.json` | Issuer mismatch |

**Gap:** No Agent ID / Agent OBO specific fixtures exist. Seven new fixtures are required (see goals.md §2).

### 6.3 Terraform State

- `infra/terraform/modules/` contains: `apim`, `apim-api`, `app-service`, `azure-openai`, `container-app`, `container-apps-env`, `container-registry`, `entra-api-scope`, `entra-app-registration`, `entra-cross-tenant-notes`, `entra-service-principal`, `key-vault`, `log-analytics`, `managed-identity`, `resource-group`.
- **Gaps for M5:** No `aks`, `workload-identity`, or `k8s-bootstrap` modules exist. No `environments/aks/` overlay exists.

### 6.4 Docs State

- `docs/deployment/` contains `aks-optional.md` (high-level reference notes).
- **Gap:** No illustrative Kubernetes manifest files for the sidecar pattern.

---

## 7. Open Questions / ADR Inputs

| # | Question | Tracking |
|---|---|---|
| Q1 | Should the AKS environment overlay be a standalone environment or a feature flag on `single-tenant`? | ADR-M5-01 |
| Q2 | Should the sidecar mock boundary be an in-process Python adapter or a real localhost HTTP stub? | ADR-M5-02 |
| Q3 | Which JWKS client library and what TTL/rotation strategy? | ADR-M5-03 |
| Q4 | Is `xms_act_fct` the stable claim name across all Entra Agent ID token variants? | Research task — Trinity |
| Q5 | Should Agent OBO fixture tokens include a simulated `act` claim in addition to `xms_act_fct`? | Design task — Trinity + Neo |

---

## 8. Terminology Disambiguation and AKS Agent Gateway Tracing

*(Added: Amendment 001, 2026-05-15)*

### 8.1 Naming Disambiguation

The lab uses "agent-gateway" as the directory and service name for its FastAPI orchestration service (`apps/agent-gateway/python-fastapi-agent-framework`). This name collides in reader perception with the standalone agentgateway.dev open-source project. To avoid ambiguity, this spec adopts the following terminology (see also `README.md §Terminology`, ADR 0006):

| Term | Meaning |
|------|---------|
| **Agentic Layer** | The lab's app-level orchestration service at `apps/agent-gateway/` (legacy path; not renamed) |
| **AKS Agent Gateway** | The agentgateway.dev open-source proxy, deployed in AKS as infrastructure |

**Key rule:** the AKS Agent Gateway is not the lab's Agentic Layer. In the AKS scenario, the AKS Agent Gateway sits in front of the Agentic Layer as an ingress/MCP proxy; the Agentic Layer and MCP protected API remain the lab's application identity boundary.

### 8.2 AKS Agent Gateway Tracing (agentgateway.dev)

Source: https://agentgateway.dev/docs/standalone/main/reference/observability/traces/

The AKS Agent Gateway integrates with **Jaeger** as the tracing platform via an **OpenTelemetry (OTEL)** pipeline. This is relevant to M5 because:

1. **OTEL is the standard.** The lab should adopt OTEL for all instrumentation so that traces from the lab's FastAPI services can be correlated with spans emitted by the AKS Agent Gateway when it is present.

2. **Two tracing configuration modes:**
   - **Static tracing:** Configured globally in `config.tracing`; applies to all routes. Suitable for the mock flow (all lab services use one static config).
   - **Dynamic tracing:** Configured per listener (`frontendPolicies.tracing`). Supports CEL expressions for dynamic span attributes (e.g., `request.path`, `jwt.sub`), per-listener service name resource attributes, per-listener sampling overrides, and choice of OTEL protocol (HTTP or gRPC). Relevant when the AKS Agent Gateway is present in the AKS flow.

3. **Jaeger UI:** Exposes trace visualization at `http://localhost:16686`. Traces include `list_tools` and `call_tool` spans for MCP operations.

4. **Span attributes of interest:**
   - `service.name` — resource attribute set at tracer provider level; appears in Jaeger's service dropdown.
   - CEL-evaluated span attributes: `request.path`, auth outcome, audience, OBO hop markers.
   - `randomSampling` / `clientSampling` — per-policy overrides; sampling is disabled by default.

5. **Infrastructure for mock tracing:** A Jaeger instance can be spun up with Docker Compose (OTel collector on `localhost:4317`, Jaeger agent on `localhost:14268`, Jaeger UI on `localhost:16686`). The lab can add a `docker-compose.tracing.yml` overlay alongside the existing Compose stack for local E2E trace visualization without any Azure deployment.

### 8.3 End-to-End Trace Flow (Mock)

```
[Browser/Client]
    │ traceparent header
    ▼
[BFF — FastAPI]
    │ propagate traceparent
    ▼
[Agentic Layer — FastAPI]
    │ propagate traceparent; OBO boundary span
    ▼
[MCP Protected API — FastAPI]
    │ response span
```

### 8.4 End-to-End Trace Flow (AKS)

```
[Browser/Client]
    │ traceparent header
    ▼
[AKS Agent Gateway — agentgateway.dev]
    │ propagate traceparent; dynamic tracing span
    ▼
[Agentic Layer — deployed in AKS pod]
    │ propagate traceparent; blueprint audience validation span
    ▼
[Entra Agent ID Sidecar — localhost only]
    │ OBO exchange span (sidecar internal)
    ▼
[APIM — Azure API Management]
    │ policy span (external; not instrumented by lab)
    ▼
[MCP Protected API]
```

All spans within the lab's Python services use OTEL SDK (`opentelemetry-sdk`, `opentelemetry-instrumentation-fastapi`). Correlation is maintained via W3C `traceparent` header propagation.

---

## Amendments

| # | Date | Changed By | Summary | Status |
|---|------|-----------|---------|--------|
| 001 | 2026-05-15 | spec-feature (Ashley Hollis) | Added Section 8 — terminology disambiguation, AKS Agent Gateway tracing reference (OTEL/Jaeger), E2E trace flow diagrams for mock and AKS. | Approved |
| 001-correction | 2026-05-15 | spec-feature (Ashley Hollis) | Terminology corrected per ADR 0006: "local app gateway" → **Agentic Layer**; "standalone Agent Gateway" → **AKS Agent Gateway**. | Applied |
