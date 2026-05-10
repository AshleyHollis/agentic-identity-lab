# Spec 002 — Goals

**Spec:** 002-aks-entra-agent-id  
**Milestone:** M5 — AKS + Entra Agent ID auth exploration (expanded to implementation track)  
**Updated:** 2026-05-14

---

## Primary Goal

Promote Spec 002 from a draft/research placeholder into a fully implementation-ready spec so that the AKS + Microsoft Entra Agent ID auth work can proceed under a defined contract, fixture set, safe-claims boundary, and explicit ADR decisions — without any live tenant credentials committed to the repository.

---

## Success Criteria

### 1 — Agent ID sidecar contract is defined and testable offline

The three sidecar endpoints are documented with input/output schemas:

- `GET /Validate` — validates the inbound bearer token in the sidecar's context.
- `GET /AuthorizationHeader/{apiName}` — returns a ready-to-use `Authorization: Bearer` header value for the named API.
- `POST /DownstreamApi/{apiName}` — triggers an Agent OBO exchange and returns downstream token claims.

Offline tests cover each endpoint behaviour using fixture claims only; no real HTTP calls to the sidecar or to Entra ID.

### 2 — Agent ID fixture set is complete

Seven offline JSON claim fixtures exist under `tests/fixtures/sample-claims/`:

| Fixture name | Purpose |
|---|---|
| `agent-blueprint-user-token` | Valid user token scoped to the blueprint audience; happy path for sidecar ingress. |
| `agent-obo-mcp-token` | Agent OBO output token for MCP; includes `appid` actor claim. |
| `agent-wrong-audience` | User token with `aud` not matching the blueprint; must be rejected. |
| `agent-missing-actor` | OBO-shaped token with no `appid`/actor claim; must be rejected at MCP boundary. |
| `agent-app-only-blueprint` | App-only token (no `scp`, no user subject) against the blueprint audience; must be rejected for delegated endpoints. |
| `agent-untrusted-tenant` | Token from a `tid` not in the trusted-tenants allowlist; must be rejected. |
| `agent-replay-stale` | Token with `exp` in the past and `iat` more than the allowed clock skew ago; must be rejected. |

### 3 — Safe-claims allowlist covers non-PII actor metadata

`config/claims/safe-claims-allowlist.json` and `DEFAULT_SAFE_CLAIM_KEYS` in `apps/shared/python/identity_lab_auth/claims.py` include `xms_act_fct` in addition to the already-present `appid`.

PII suppression rule continues to hold: `oid`, `sub`, `email`, `upn`, `name`, and `preferred_username` are never in the allowlist and are never surfaced in sanitized output.

### 4 — Agent OBO sidecar mock boundary is specified

A distinct `agent_obo` abstraction (or sidecar mock boundary) is designed to:

- Validate the inbound blueprint audience before any exchange is attempted.
- Enforce a localhost-only sidecar URL (reject any non-localhost target).
- Make zero network calls in offline/mock mode.
- Return only sanitized output claims (through the safe-claims allowlist).
- Remain entirely separate from the MCP user OBO path (Spec 001/003) and Azure OpenAI/Foundry managed identity.

### 5 — AKS Terraform skeletons validate

Four Terraform skeletons exist with valid HCL structure:

- `infra/terraform/modules/aks/`
- `infra/terraform/modules/workload-identity/`
- `infra/terraform/modules/k8s-bootstrap/`
- `infra/terraform/environments/aks/`

`terraform fmt -check -recursive` and `terraform validate` pass for the AKS overlay without live credentials. All variables and outputs are placeholder-only.

### 6 — Illustrative AKS manifests exist in docs

Reference-only YAML manifests under `docs/deployment/k8s/` illustrate:

- Namespace and service account with workload identity annotation.
- Agent Execution Service deployment with an Entra Agent ID sidecar container.
- Network policy restricting sidecar access to localhost only (blocking cross-pod access).

These files are explicitly marked as illustrative/reference; they are not applied by CI.

### 7 — Strict JWT/JWKS validation design is documented and testable

The design specifies:

- Reject tokens with `alg: none` or any `HS*` algorithm.
- Require a matching `kid` in the JWKS response before signature verification.
- Preserve all existing claim checks (`aud`, `iss`, `tid`, `exp`, `nbf`, `scp`).
- Ignore `X-Identity-Lab-Fixture` header in `AUTH_MODE=strict`.
- JWKS caching strategy with TTL, key rotation support, and no blocking on cache miss.

Offline tests cover each rejection case using crafted fixture headers.

### 8 — Three ADRs are decided before implementation begins

| ADR | Decision required |
|---|---|
| ADR-M5-01 | AKS optional track vs ACA default track |
| ADR-M5-02 | Agent ID sidecar mock boundary vs real SDK / direct MSAL |
| ADR-M5-03 | JWKS client library and key-rotation / caching strategy |

### 9 — No secrets committed

No real tenant IDs, subscription IDs, kubeconfigs, client secrets, tokens, or certificates appear anywhere in this spec or in any file created or modified by this spec.

### 10 — End-to-end tracing design is complete for mock and AKS flows

*(Added: Amendment 001, 2026-05-15)*

An end-to-end distributed tracing design exists covering every hop in both the local mock flow and the future AKS flow:

- **Mock flow spans:** browser/client → BFF → Agent Execution Service → MCP protected API
- **AKS flow spans:** browser/client → AKS Agent Gateway → Agent Execution Service (in AKS) → Entra Agent ID sidecar → APIM → OBO exchange → MCP protected API

The design specifies:
- OpenTelemetry (OTEL) as the instrumentation standard; Jaeger as the visualization backend (consistent with AKS Agent Gateway's tracing integration).
- Propagated `traceparent`/`tracestate` headers across all service boundaries.
- Correlation ID strategy: one `trace_id` spans the full request chain; each service boundary adds a child span.
- Span attribute expectations: request path, auth mode (`mock`/`strict`), audience, outcome (`accepted`/`rejected`), OBO hop markers.
- Static tracing config (global) for the mock flow; dynamic tracing config (per-listener) reserved for the AKS Agent Gateway integration.
- A mock-flow tracing fixture: a minimal `docker-compose.tracing.yml` overlay that spins up Jaeger alongside the existing services so users can visualize request movement through the lab stack without any Azure deployment.

Tracing tasks (T17–T20) are added to `tasks.md` but remain blocked behind the same review gates (T02 + T03) as all other implementation tasks.

---

## Non-Goals

- Running against a live Azure tenant or real AKS cluster.
- Full production-grade AKS deployment (M6+).
- Entra Agent ID SDK wiring in runtime code (deferred to implementation phase after review gate).
- Azure OpenAI/Foundry managed identity integration path.
- M6 ACA deployment baseline or M7 client variants.

---

## Amendments

| # | Date | Changed By | Summary | Status |
|---|------|-----------|---------|--------|
| 001 | 2026-05-15 | spec-feature (Ashley Hollis) | Added Success Criterion 10 — End-to-end tracing design (mock + AKS, OTEL/Jaeger, T17–T20). Implementation remains blocked pending T03. | Approved |
| 001-correction | 2026-05-15 | spec-feature (Ashley Hollis) | Terminology corrected per ADR 0006: "local app gateway" → **Agentic Layer**; "standalone Agent Gateway" → **AKS Agent Gateway**. | Applied |
| 002 | 2026-05-10 | Morpheus (Ashley Hollis approval) | Naming amendment: "Agentic Layer" → **Agent Execution Service** per ADR 0008. Success criteria and flow descriptions updated. | Applied — pre-M6 |
