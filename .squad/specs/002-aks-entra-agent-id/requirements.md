# Spec 002 — Requirements

**Spec:** 002-aks-entra-agent-id  
**Milestone:** M5 — AKS + Entra Agent ID auth exploration  
**Updated:** 2026-05-14

---

## Functional Requirements

### FR-01 — Agent ID sidecar contract

The spec MUST define the three sidecar HTTP endpoints with documented input/output schemas:

1. `GET /Validate` — receives a bearer token (via `Authorization` header or sidecar context); returns validation result (accepted/rejected) and, on success, a sanitized claim set.
2. `GET /AuthorizationHeader/{apiName}` — returns a string suitable for direct use as an `Authorization` header value for the named downstream API. The string format is `Bearer <token>`.
3. `POST /DownstreamApi/{apiName}` — body contains the inbound bearer token context; performs Agent OBO exchange; returns sanitized downstream claims for the named API.

All sidecar endpoints in mock/offline mode MUST be exercisable without a real network connection to the sidecar process or to Entra ID.

### FR-02 — Blueprint audience validation (before Agent OBO)

Before any Agent OBO exchange, the agent-gateway MUST validate that the inbound token's audience matches the configured blueprint audience. Tokens with any other `aud` value MUST be rejected with HTTP 401 before the exchange is attempted.

**Placeholder blueprint audience:** `api://00000000-0000-0000-0000-000000000201/access_as_user`

### FR-03 — Offline Agent ID fixture set

Seven claim fixture files MUST be created under `tests/fixtures/sample-claims/` with the following names and semantics:

| Fixture | Semantic |
|---|---|
| `agent-blueprint-user-token` | Happy-path user token with correct blueprint `aud` and `scp`. |
| `agent-obo-mcp-token` | Agent OBO output: correct MCP `aud`, `appid` actor claim present. |
| `agent-wrong-audience` | `aud` does not match the blueprint; MUST be rejected before OBO. |
| `agent-missing-actor` | OBO-shaped token missing `appid`; MUST be rejected at MCP boundary. |
| `agent-app-only-blueprint` | No `scp`, no user subject; MUST be rejected for delegated endpoints. |
| `agent-untrusted-tenant` | `tid` not in trusted-tenants allowlist; MUST be rejected. |
| `agent-replay-stale` | `exp` is in the past; MUST be rejected as expired/stale. |

All fixture files MUST use only all-zero placeholder GUIDs. No real tenant IDs, subscription IDs, or real tokens.

### FR-04 — Negative test coverage

For each negative fixture, at least one offline pytest test MUST:

1. Load the fixture via the existing `load_fixture_claims` mechanism.
2. Pass it through the relevant validation boundary (audience check, actor check, exp check, tid check).
3. Assert that the validation raises an appropriate exception or returns a rejected/unauthorized result.

Tests MUST NOT make any network calls.

### FR-05 — Safe-claims allowlist extension

`config/claims/safe-claims-allowlist.json` MUST be updated to include `xms_act_fct`.

`DEFAULT_SAFE_CLAIM_KEYS` in `apps/shared/python/identity_lab_auth/claims.py` MUST be updated to include `xms_act_fct`.

The following claims MUST continue to be absent from the allowlist: `oid`, `sub`, `email`, `upn`, `name`, `preferred_username`, `family_name`, `given_name`.

A test MUST assert that `sanitize_claims()` drops `oid`/`sub` while preserving `appid` and `xms_act_fct`.

### FR-06 — Agent OBO sidecar mock boundary

A distinct `agent_obo` module or adapter MUST be designed (and stubbed/typed) with the following behaviour:

- **Blueprint audience validation:** Refuses to exchange any token whose `aud` does not match the configured blueprint audience. Raises `ValueError` on mismatch.
- **Localhost enforcement:** Sidecar URL MUST begin with `http://localhost` or `http://127.0.0.1`. Any other base URL MUST raise `ValueError` at construction time.
- **Zero network calls in offline mode:** When `AUTH_MODE=mock`, the sidecar mock boundary resolves calls from fixture claims only. No HTTP connections to any external endpoint.
- **Sanitized output:** All returned claim dicts MUST pass through `sanitize_claims()`. Raw token strings MUST NOT be returned.
- **Separation:** The agent OBO adapter MUST be a distinct code path from:
  - `obo.exchange_on_behalf_of()` (MCP user OBO, Spec 001/003).
  - Azure OpenAI/Foundry managed identity path (no shared state).

### FR-07 — AKS Terraform skeletons

Four Terraform skeleton directories MUST exist with valid HCL structure (variables, outputs, main — even if resource bodies are stubs):

1. `infra/terraform/modules/aks/` — AKS cluster module (variables: location, resource group, node pool config, OIDC issuer flag).
2. `infra/terraform/modules/workload-identity/` — Workload identity module (variables: federated credential issuer, subject, blueprint client ID placeholder).
3. `infra/terraform/modules/k8s-bootstrap/` — Kubernetes bootstrap (namespace, service account, RBAC stubs).
4. `infra/terraform/environments/aks/` — AKS environment overlay (calls AKS modules; all variable values are placeholder-only).

`terraform fmt -check -recursive` and `terraform validate` MUST pass for the AKS overlay without live credentials.

All `*.tfvars.example` files MUST use only placeholder values. No real tenant IDs, subscription IDs, or access keys.

### FR-08 — Illustrative AKS manifest docs

Under `docs/deployment/k8s/` (create directory if absent), MUST exist:

1. `namespace.yaml` — illustrative namespace definition for agent workloads.
2. `service-account.yaml` — service account with workload identity annotation (`azure.workload.identity/client-id`, `azure.workload.identity/tenant-id`) using placeholder values.
3. `agent-gateway-deployment.yaml` — illustrative pod spec with agent-gateway container and Entra Agent ID sidecar container. Sidecar exposes only localhost port. Includes `azure.workload.identity/use: "true"` pod annotation.
4. `network-policy.yaml` — network policy restricting sidecar port to localhost only; prevents cross-pod access to the sidecar endpoint.

All YAML files MUST be clearly labelled as illustrative/reference (comment at top of each file). All namespace names, image references, and IDs MUST be placeholder values.

### FR-09 — Strict JWT/JWKS validation design

The design MUST specify:

- Rejection of `alg: none` at header validation stage.
- Rejection of any `HS*` algorithm at header validation stage.
- Requirement for a matching `kid` in the JWKS response before signature verification.
- Preservation of all existing claim checks: `aud`, `iss`, `tid`, `exp`, `nbf`, `scp`.
- Strict mode MUST ignore the `X-Identity-Lab-Fixture` header.
- JWKS caching: in-process TTL cache; on `kid` miss, one retry with a fresh JWKS fetch; no blocking on cache population.

Offline pytest tests MUST cover each rejection case by crafting a minimal fixture header and asserting `ValueError` or `401` result.

### FR-10 — Three ADR decisions before implementation

Before any implementation task begins, Morpheus and Trinity MUST record decisions on:

| ADR | Question | Owner |
|---|---|---|
| ADR-M5-01 | AKS optional track vs ACA default track | Morpheus |
| ADR-M5-02 | Agent ID sidecar mock boundary vs real SDK / direct MSAL | Morpheus + Trinity |
| ADR-M5-03 | JWKS client library and key-rotation / caching strategy | Trinity |

Decisions are recorded in `design.md` and acknowledged in `.progress.md` before T-Implementation tasks are unblocked.

---

## Non-Functional Requirements

### NFR-01 — Public safety

No real GUIDs, tenant IDs, subscription IDs, kubeconfigs, client secrets, tokens, or certificates committed anywhere. All-zero placeholder GUIDs (`00000000-0000-0000-0000-00000000NNNN`) and `{placeholder}` template tokens only.

### NFR-02 — Offline testability

All offline pytest tests run without:
- Network access to Entra ID or any OIDC endpoint.
- A running Kubernetes cluster or AKS environment.
- Any environment variable pointing to a live tenant.

### NFR-03 — No regression

`python -m pytest` MUST continue to pass (65 tests minimum from M4 baseline) after all changes in this spec.

### NFR-04 — Terraform validation only

No Terraform module in this spec performs a `terraform apply` or `terraform plan` against a live Azure subscription in CI. CI is validation-only (`fmt -check` + `validate`).

### NFR-05 — Implementation gate

Implementation tasks (T05–T16) MUST NOT begin until:
- Morpheus records ADR decisions (T02).
- Trinity records security review (T03).
- Both are acknowledged in `.progress.md`.

### NFR-06 — Separation of identity paths

The Agent OBO path MUST NOT share token variables, module imports, or configuration state with:
- The MCP user OBO path (`obo.exchange_on_behalf_of()`).
- Azure OpenAI/Foundry managed identity auth.
- Any direct MSAL call that bypasses the sidecar mock boundary interface.

### NFR-07 — Tracing observability

*(Added: Amendment 001, 2026-05-15)*

End-to-end distributed tracing MUST be designed (and a mock-flow implementation MUST be specified in `design.md`) using:
- OpenTelemetry (OTEL) SDK for all Python service instrumentation.
- W3C `traceparent` header propagation across all service boundaries.
- Jaeger as the visualization backend, consistent with the AKS Agent Gateway's tracing integration.

The tracing design MUST NOT require a live Azure environment or AKS cluster. A `docker-compose.tracing.yml` overlay MUST be specified so users can run Jaeger locally alongside the existing lab services.

---

## Functional Requirements (Amendment 001)

### FR-11 — Terminology clarity

*(Added: Amendment 001, 2026-05-15)*

All spec artifacts MUST use consistent terminology per ADR 0006 and the definitions in `README.md §Terminology`:

- "Agentic Layer" refers exclusively to the lab's application-level orchestration service at `apps/agent-gateway/` (legacy path; not renamed in the filesystem or Docker Compose).
- "AKS Agent Gateway" refers exclusively to the agentgateway.dev open-source proxy deployed in AKS.
- Artifacts MUST NOT use the retired term "local app gateway" or unqualified "agent gateway" in prose that could be confused with either canonical term.
- AKS manifest docs MUST use "Agentic Layer deployment" when describing the lab's FastAPI container, not "agent-gateway deployment".

### FR-12 — End-to-end tracing design

*(Added: Amendment 001, 2026-05-15)*

The design MUST specify end-to-end distributed tracing covering both the mock flow and the AKS flow:

1. **Span/trace model:**
   - One `trace_id` spans the full request chain from client to MCP protected API.
   - Each service boundary (BFF, Agentic Layer, MCP protected API) adds a child span.
   - In the AKS flow, the AKS Agent Gateway adds a parent span before the Agentic Layer span.
   - The Entra Agent ID sidecar OBO exchange is recorded as a child span of the Agentic Layer span.

2. **Propagation:** W3C `traceparent` and `tracestate` headers MUST be forwarded at every hop. No service MAY drop the trace context header without recording a span.

3. **Span attribute requirements:**
   - `auth.mode` — value of `AUTH_MODE` env var (`mock` / `strict`).
   - `auth.audience` — the `aud` value from the validated token.
   - `auth.outcome` — `accepted` or `rejected`.
   - `obo.hop` — present on the OBO exchange span; value `agent_obo` or `user_obo` to distinguish paths.
   - `http.route` and `http.method` — standard OTEL HTTP attributes.

4. **Mock-flow tracing infrastructure:**
   - A `docker/docker-compose.tracing.yml` overlay MUST be specified (not required to be implemented until T18) that adds Jaeger to the existing Compose stack.
   - The Jaeger UI MUST be accessible at `http://localhost:16686` when the overlay is active.
   - OTEL collector endpoint: `http://localhost:4317` (gRPC).

5. **AKS Agent Gateway tracing integration (AKS flow only):**
   - Static tracing config MUST be specified in the AKS manifest docs so the AKS Agent Gateway sends spans to the same OTEL collector.
   - Dynamic tracing (CEL span attributes) is documented as the preferred AKS configuration per the agentgateway.dev reference.

6. **No tracing in offline/unit tests:** OTEL instrumentation MUST be no-op or disabled in pytest runs. Tests MUST NOT depend on a running Jaeger instance.

---

## Amendments

| # | Date | Changed By | Summary | Status |
|---|------|-----------|---------|--------|
| 001 | 2026-05-15 | spec-feature (Ashley Hollis) | Added FR-11 (terminology), FR-12 (E2E tracing), NFR-07 (tracing observability). Implementation remains blocked pending T03. | Approved |
| 001-correction | 2026-05-15 | spec-feature (Ashley Hollis) | Terminology corrected per ADR 0006: "local app gateway" → **Agentic Layer**; "standalone Agent Gateway" → **AKS Agent Gateway**. FR-11 rewritten with canonical terms. | Applied |
