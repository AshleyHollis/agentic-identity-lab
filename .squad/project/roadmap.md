# Project Roadmap

Principles
- Prioritize a working local delegated-token story before any Azure deployment.
- Stay public-safe: no secrets, tenant IDs, or live tokens.
- Keep implementations minimal and extendable.

## Terminology (canonical — see ADR 0006)

| Term | Meaning | Filesystem path |
|------|---------|-----------------|
| **Agentic Layer** | Lab's application-level agent orchestration service | `apps/agent-gateway/` *(legacy path; not renamed)* |
| **AKS Agent Gateway** | Standalone agentgateway.dev infrastructure proxy running as an AKS pod sidecar | Deployed to AKS; not a local source directory |

> "Agent gateway" (unqualified) is retired as a standalone term in new documentation.
> The Docker Compose service name `agent-gateway` is unchanged.

---

## Status Dashboard

> Last updated: 2026-05-14 · Maintained by Morpheus

**▶ Current position: Milestone 5 — AKS + Entra Agent ID auth exploration (spec promotion + terminology/tracing amendment)**

| # | Milestone | Spec | Status | Validation |
|---|-----------|------|--------|------------|
| M1 | Local token validation + OBO boundaries | [Spec 001](.squad\specs\001-token-validation-and-obo\README.md) | ✅ Complete | `python -m pytest` passed |
| M2 | Local delegated flow integration | [Spec 003](.squad\specs\003-local-delegated-flow-integration\README.md) | ✅ Complete | `python -m pytest` passed |
| M3 | APIM policy alignment | [Spec 004](.squad\specs\004-apim-policy-alignment\README.md) | ✅ Complete | pytest 56 passed; `terraform fmt` + `validate` passed |
| M4 | Local runtime ergonomics | [Spec 005](.squad\specs\005-local-runtime-ergonomics\README.md) | ✅ Complete | Compose configs passed; `python -m pytest` 65 passed |
| M5 | AKS + Entra Agent ID + observability | [Spec 002](.squad\specs\002-aks-entra-agent-id\README.md) | 🔄 In Progress | Spec promoted; pending T01–T03 review gates |
| M6 | Azure deployment baseline | *(spec not yet created)* | 📋 Roadmap | `terraform fmt` + `validate` |
| M7 | Variant client implementations | *(spec not yet created)* | 📋 Roadmap | variant tests + `python -m pytest` |

> **Note:** Spec-first gate applies — a spec directory and task list must exist under `.squad\specs\` before implementation begins for any milestone.

---

## Milestone 1 — Local token validation + OBO boundaries (Spec 001)

**Goal:** Establish offline-safe JWT validation scaffolding and explicit OBO boundaries across BFF / Agentic Layer → MCP protected API.  
**Owner agents:** Morpheus (architecture), Trinity (security), Neo (backend)  
**Impact:** High  
**Status:** ✅ Complete

### ✅ Done by end of M1 — what works

| Capability | Details |
|-----------|---------|
| Offline JWT validation | `identity_lab_auth` validates JWTs from fixture files without any network call to Entra ID. |
| PII suppression | `sanitize_claims()` strips `oid`, `sub`, `email`, `upn`, `name`, `preferred_username` on every path. |
| OBO boundary defined | The Agentic Layer must exchange the inbound token for an MCP-audience token before calling the MCP protected API. Forwarding the original token is blocked. |
| `/whoami` endpoints | All services return only safe, sanitized claim metadata. Raw tokens are never returned. |
| Negative cases pass | Wrong audience, missing scope, and expired token all result in 401 rejections with no token leakage. |
| `python -m pytest` | Initial auth unit test suite passes. |

**Key files:**
- `apps/shared/python/identity_lab_auth/*`
- `apps/bff/python-fastapi/app/auth.py`
- `apps/agent-gateway/python-fastapi-agent-framework/app/auth.py` *(Agentic Layer)*
- `apps/mcp-protected-api/python-fastapi/app/auth.py`
- `tests/fixtures/sample-claims/*`
- `config/env/*.env.example`

---

## Milestone 2 — Local delegated flow integration (Spec 003)

**Goal:** Prove request flow from BFF / Agentic Layer into MCP protected API using mock OBO exchange and integration tests.  
**Owner agents:** Neo, Trinity  
**Impact:** High  
**Status:** ✅ Complete

### ✅ Done by end of M2 — what works

| Capability | Details |
|-----------|---------|
| End-to-end local flow | A test client can drive a request through BFF → Agentic Layer → MCP protected API entirely offline. |
| Mock OBO exchange | The OBO exchange resolves from fixture claims with zero network calls. The Agentic Layer does not invent or bypass tokens. |
| Delegated token integrity | The original inbound token is never forwarded to the MCP API; only the OBO-exchanged token (MCP-audience) is used. |
| Integration tests | `tests/integration/` tests verify the full delegated chain from end to end with mock tokens. |
| `python -m pytest` | All tests pass including integration tests. |

**Key files:**
- `apps/agent-gateway/python-fastapi-agent-framework/app/*` *(Agentic Layer)*
- `apps/mcp-protected-api/python-fastapi/app/*`
- `tests/integration/*`
- `.squad/specs/003-local-delegated-flow-integration/*`

---

## Milestone 3 — APIM policy alignment (documentation + examples) (Spec 004)

**Goal:** Align APIM ingress/egress policy examples with validated token/audience rules and OBO boundary rules.  
**Owner agents:** Morpheus, Trinity, Tank  
**Impact:** Medium  
**Status:** ✅ Complete

### ✅ Done by end of M3 — what works

| Capability | Details |
|-----------|---------|
| APIM policy documentation | `docs/apim/` shows correct audience enforcement for inbound user tokens for BFF and Agentic Layer boundaries. |
| OBO boundary in policies | Policy examples make explicit that APIM must not replace delegated tokens with managed identity; OBO happens in the Agentic Layer, not at APIM. |
| Terraform policy validation | `infra/terraform/policies/` is format-checked and validates without live Azure credentials. |
| Policy integration tests | Tests assert audience rules, OBO boundary rules, and that policies reject wrong-audience tokens. |
| `terraform fmt` + `validate` | Pass for APIM modules. |

**Key files:** `docs/apim/*`, `infra/terraform/policies/*`, `tests/integration/python/test_apim_*.py`, `.squad/specs/004-apim-policy-alignment/*`

---

## Milestone 4 — Local runtime ergonomics (Spec 005)

**Goal:** Ensure Docker Compose and env examples support the offline token flow for BFF / Agentic Layer / MCP.  
**Owner agents:** Tank, Neo  
**Impact:** Medium  
**Status:** ✅ Complete

### ✅ Done by end of M4 — what works

| Capability | Details |
|-----------|---------|
| `docker compose up` | All services start: BFF, Agentic Layer, MCP Protected API. |
| Offline token flow | `.env.example` files guide developers through offline token flow configuration with no Azure credentials. |
| New-developer experience | A new contributor can `docker compose up` and run `python -m pytest` with no live Azure credentials and no manual setup beyond `.env` copy. |
| Compose validation | Base and overlay Compose config checks pass; no missing service definitions. |
| 65+ tests pass | Full offline/Compose-mode `python -m pytest` suite passes. |

**Key files:** `docker/docker-compose.yml`, `config/env/*.env.example`, `apps/bff/python-fastapi/app/*`

---

## Milestone 5 — AKS + Entra Agent ID + Observability

**Goal:** Validate an optional AKS path for Microsoft Entra Agent ID auth in agent/MCP workloads, building on the local mock/OBO foundation. Establish end-to-end tracing (OpenTelemetry + Jaeger) across all mock and AKS flows. Resolve terminology ambiguity between the Agentic Layer and the AKS Agent Gateway.  
**Owner agents:** Morpheus (Lead/Architect), Tank (Infra), Trinity (Security), Neo (Backend)  
**Impact:** High  
**Status:** 🔄 In Progress — Spec 002 promoted to tasks-ready; terminology + tracing amendment applied; implementation blocked pending T01–T03 review gates.

### ✅ Done by end of M5 — what works

| Capability | Details |
|-----------|---------|
| **Terminology** | "Agentic Layer" = lab's orchestration service (`apps/agent-gateway/`). "AKS Agent Gateway" = agentgateway.dev infrastructure proxy sidecar. ADRs 0006 + 0007 recorded. |
| **AKS Terraform skeletons** | `infra/terraform/modules/aks/`, `workload-identity/`, `k8s-bootstrap/`, and `environments/aks/` exist with valid HCL; `terraform fmt -check` and `validate` pass with no live credentials. |
| **Agent ID sidecar mock boundary** | `AgentSidecarClient` ABC and `MockAgentSidecarClient` implemented. In-process mock resolves from fixture claims, makes zero HTTP calls, enforces localhost-only sidecar URL. |
| **Blueprint audience validation** | Agentic Layer validates inbound token `aud` against the configured blueprint audience before any Agent OBO exchange; wrong-audience tokens are rejected with 401. |
| **Agent ID fixture set** | Seven fixture files in `tests/fixtures/sample-claims/`: happy-path user token, Agent OBO MCP token, wrong-audience, missing-actor, app-only-blueprint, untrusted-tenant, replay-stale. All use all-zero placeholder GUIDs. |
| **Negative case tests** | Offline pytest tests for all five negative fixtures; each asserts correct rejection without network calls. |
| **`xms_act_fct` safe-claims** | `config/claims/safe-claims-allowlist.json` and `DEFAULT_SAFE_CLAIM_KEYS` updated for `xms_act_fct`; PII suppression (`oid`, `sub`, etc.) preserved. |
| **Strict JWKS validation** | `alg:none` and `HS*` rejected at header stage; `kid` required; TTL cache with `kid`-miss retry; strict mode ignores fixture header. Offline tests for each rejection case. |
| **Illustrative AKS manifests** | `docs/deployment/k8s/` contains `namespace.yaml`, `service-account.yaml`, `agent-gateway-deployment.yaml`, `network-policy.yaml` — all labelled "ILLUSTRATIVE REFERENCE ONLY". |
| **Three M5 ADRs** | ADR-M5-01 (AKS optional track), ADR-M5-02 (sidecar mock boundary), ADR-M5-03 (JWKS strategy) recorded in `design.md`. |
| **End-to-end tracing (mock flows)** | OpenTelemetry SDK instruments BFF, Agentic Layer, and MCP Protected API. Jaeger all-in-one runs in Docker Compose. Contributors open `localhost:16686` to see the full request chain as visual spans. |
| **AKS Agent Gateway tracing design** | agentgateway.dev's native OTLP → Jaeger pipeline documented; Jaeger UI shows `list_tools`/`call_tool` spans when AKS flows are exercised. |
| **W3C TraceContext propagation** | `traceparent`/`tracestate` forwarded on all inter-service HTTP calls. |
| **No PII in traces** | Span attribute allowlist enforced; `oid`, `sub`, raw tokens never in spans. |
| **65+ tests pass** | `python -m pytest` passes from M4 baseline plus new M5 tests. |
| **No secrets committed** | No real GUIDs, tenant IDs, kubeconfigs, or tokens anywhere in committed files. |

**Key files:**
- `.squad\specs\002-aks-entra-agent-id\*` (spec artifacts)
- `.squad\architecture\decisions\001-agentic-layer-vs-agent-gateway-terminology.md`
- `.squad\architecture\decisions\002-end-to-end-tracing-strategy.md`
- `docs\adr\0006-agentic-layer-vs-agent-gateway-terminology.md`
- `docs\adr\0007-end-to-end-tracing-strategy.md`
- `apps\shared\python\identity_lab_auth\agent_obo.py` (T10 — not yet created)
- `apps\shared\python\identity_lab_auth\telemetry.py` (T18 — not yet created)
- `tests\fixtures\sample-claims\agent-*.json` (T07 — not yet created)
- `infra\terraform\modules\aks\`, `workload-identity\`, `k8s-bootstrap\` (T04 — not yet created)
- `infra\terraform\environments\aks\` (T04 — not yet created)
- `docs\deployment\k8s\*` (T05 — not yet created)
- `docker\docker-compose.yml` or overlay — Jaeger service (tracing — not yet created)

**Validation targets:**
```
python -m pytest
terraform -chdir=infra\terraform fmt -check -recursive
terraform -chdir=infra\terraform\environments\aks validate
```

---

## Milestone 6 — Azure deployment baseline

**Goal:** Implement minimal Terraform wiring for APIM + Container Apps with managed identity ready for OBO (no secrets committed). Migrate tracing backend to Azure Monitor (OTLP endpoint swap).  
**Owner agents:** Tank, Morpheus  
**Impact:** Medium-High  
**Status:** 📋 Roadmap (spec not yet created)

### ✅ Done by end of M6 — what works

| Capability | Details |
|-----------|---------|
| **Azure deployment** | Terraform deploys APIM + Container Apps to Azure for the `single-tenant` environment. No `terraform apply` in CI — CI validates only. |
| **Managed identity** | Workload identity and managed identity wired for OBO; no secrets or kubeconfigs committed. |
| **Deployed delegated flow** | Full request chain works in Azure: browser → APIM → BFF → Agentic Layer → MCP protected API. |
| **Smoke tests** | Smoke tests run against deployed endpoint from a CI/CD pipeline (no live secret in repo). |
| **Azure Monitor tracing** | `OTEL_EXPORTER_OTLP_ENDPOINT` set to Azure Monitor OTLP ingestion URL; end-to-end traces visible in Azure portal. No code change from M5 instrumentation. |
| **`terraform fmt` + `validate`** | Pass for all environments. |

**Key files:** `infra/terraform/modules/*`, `infra/terraform/environments/*`

---

## Milestone 7 — Variant client implementations

**Goal:** Implement first UI clients (SPFx, SharePoint classic, SPA) that exercise delegated flows.  
**Owner agents:** Mouse, Neo  
**Impact:** Medium  
**Status:** 📋 Roadmap (spec not yet created)

### ✅ Done by end of M7 — what works

| Capability | Details |
|-----------|---------|
| **SPFx web part** | SPFx web part acquires a delegated token from Entra ID via MSAL and calls BFF with the correct audience. |
| **SharePoint classic integration** | SharePoint classic page integration works through the same BFF delegated flow. |
| **SPA (public client)** | Single-page app uses PKCE flow, acquires delegated token, calls BFF. |
| **Token handling documented** | Each variant's token acquisition, audience, and OBO hand-off is documented with a diagram. |
| **Variant-specific tests** | Variant integration tests pass; all flows verified with `python -m pytest`. |
| **Trace visualization** | All three client variants generate trace spans visible in the Jaeger UI (or Azure Monitor in deployed mode). |

**Key files:** `apps/sharepoint-*`, `apps/spfx-webpart`, `apps/spa-public-client`

---

## Cross-cutting: End-to-End Tracing

> **ADR:** `docs/adr/0007-end-to-end-tracing-strategy.md` · Full record: `.squad/architecture/decisions/002-end-to-end-tracing-strategy.md`

| Phase | What is traceable | Visualization |
|-------|------------------|--------------| 
| M5 (local/mock) | BFF → Agentic Layer → MCP Protected API (mock flows) | Jaeger UI `localhost:16686` (Docker Compose) |
| M5 (AKS flows) | AKS Agent Gateway proxy spans (`list_tools`, `call_tool`) | Same Jaeger UI via agentgateway.dev native integration |
| M6 (Azure) | Full deployed chain including APIM | Azure Monitor (OTLP endpoint — config-only swap) |
| M7 (clients) | All variant client → BFF spans | Azure Monitor or Jaeger |

**Invariants (all phases):**
- W3C TraceContext (`traceparent`/`tracestate`) propagated on all inter-service HTTP calls.
- Span attributes follow `sanitize_claims()` rules: `oid`, `sub`, `email`, `upn`, raw tokens **never** in spans.
- `OTEL_SDK_DISABLED=true` (or no-op exporter) in unit-test runs; tracing does not require a running Jaeger instance in offline pytest.

