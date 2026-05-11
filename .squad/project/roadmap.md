# Project Roadmap

Principles
- Prioritize a working local delegated-token story before any Azure deployment.
- Stay public-safe: no secrets, tenant IDs, or live tokens.
- Keep implementations minimal and extendable.

## Terminology (canonical — see ADR 0008)

| Term | Meaning | Filesystem path |
|------|---------|-----------------|
| **Agent Execution Service** | Lab's application-level agent execution service — hosts AI agents, enforces Entra Agent ID / OBO boundaries, code-first successor to PromptFlow | `apps/agent-execution/` |
| **Identity Lab Agent Execution Service** | Qualified display name used when org/lab context is useful | Same service as above |
| **AKS Agent Gateway** | Standalone agentgateway.dev infrastructure proxy running as an AKS pod sidecar | Deployed to AKS; not a local source directory |

> **Slug:** `agent-execution` (used in Terraform resource names, K8s labels, Docker image tags, and current local runtime wiring).  
> **Historical alias:** older ADRs/spec notes may still reference `agent-gateway` or `apps/agent-gateway/`; treat those as pre-M6 naming only.  
> **Prohibited terms in new prose:** "Agentic Layer" (superseded), unqualified "Agent Gateway" (collision with AKS Agent Gateway), unqualified "Agent Service" (collision with Azure AI Agent Service / Foundry).  
> **Historical note:** "Agentic Layer" was the canonical term from ADR 0006 (M5). ADR 0008 supersedes ADR 0006.

---

## Status Dashboard

> Last updated: 2026-07-07 · Maintained by Mouse + Tank

**▶ Current position: M9 live deploy approval + E2E tracking — readiness deploy/smoke/shutdown evidence exists, but final live browser/agent-browser E2E remains blocked until protected dispatch approval and closeout gates pass.**

> **Does everything eventually deploy to Azure and get verified end-to-end?**  
> **Yes.** The intended destination is a live Azure deployment (ACA + APIM) where a real browser session drives a delegated Entra token through APIM → BFF → Agent Execution Service → MCP Protected API and all hops are smoke-tested with real Entra tokens and traces visible in Azure Monitor.  
> The lab reaches that through staged gates:
>
> - **M6** established the *configuration and Terraform validation baseline* — infrastructure scaffolded, `AUTH_MODE=strict` verified, `terraform validate` passes. **No `terraform apply` was run; no live resources were created.** M6 proves the configuration is correct, not that the deployment works.
> - **M7 (Variant clients)** implements the client-side delegated flows (SPFx, SPA, SharePoint classic) offline/locally. M7 clients are *necessary inputs* to live E2E because they exercise delegated-token acquisition, but M7 alone does not prove live Azure deployment.
> - **M8 (Live Azure E2E gate scaffolding)** delivered protected workflow scaffolds and static/public-safe validation gates. M8 did not claim live Azure deployment.
> - **M9 (Live Azure E2E execution acceptance)** is the first milestone allowed to claim a configured protected environment was actually deployed and browser → APIM → BFF → Agent Execution Service → MCP was smoke-tested with real Entra tokens.
>
> **Public-repo constraint (permanent):** live credentials, tenant IDs, subscription IDs, and real Entra tokens must never be committed. M9 live execution must run opt-in against a private protected environment; its smoke-test scripts live in the repo but the secrets that drive them do not.

| # | Milestone | Spec | Status | Validation |
|---|-----------|------|--------|------------|
| M1 | Local token validation + OBO boundaries | [Spec 001](.squad\specs\001-token-validation-and-obo\README.md) | ✅ Complete | `python -m pytest` passed |
| M2 | Local delegated flow integration | [Spec 003](.squad\specs\003-local-delegated-flow-integration\README.md) | ✅ Complete | `python -m pytest` passed |
| M3 | APIM policy alignment | [Spec 004](.squad\specs\004-apim-policy-alignment\README.md) | ✅ Complete | pytest 56 passed; `terraform fmt` + `validate` passed |
| M4 | Local runtime ergonomics | [Spec 005](.squad\specs\005-local-runtime-ergonomics\README.md) | ✅ Complete | Compose configs passed; `python -m pytest` 65 passed |
| M5 | AKS + Entra Agent ID + observability | [Spec 002](.squad\specs\002-aks-entra-agent-id\README.md) | ✅ Complete | `python -m pytest` 229 passed; Terraform fmt/init/validate passed; Compose tracing config passed |
| M6 | Azure deployment baseline *(config + Terraform validation only — no live apply)* | [Spec 006](.squad\specs\006-azure-deployment-baseline\README.md) | ✅ Complete | pytest 235 passed; `terraform fmt/init/validate` passed; Compose strict-aca + tracing configs passed; no-secret scan passed |
| M7 | Variant client implementations *(offline delegated flows; prepares clients for M8 E2E)* | [Spec 007](.squad\specs\007-variant-client-implementations\README.md) | ✅ Complete and closed (T09/T10 accepted after A-01 remediation; T13 closeout complete) | Python full suite 246 passed; focused T09 re-review tests 19 passed; focused T10 security tests 91 passed; SPA/classic/SPFx validations + compose config passed |
| M8 | Live Azure E2E verification *(opt-in; requires configured private environment)* | [Spec 008](.squad\specs\008-live-azure-e2e-gate\README.md) | ✅ Complete and closed (T15) | `state.json` parse passed; `python tools/ci/public_safe_validation.py` passed; `python tools/telemetry/validate_m8_kql_contract.py` passed; focused `tests/security/test_m8_public_safe_validation.py` passed; no live Azure execution claimed in this session |
| M9 | Live Azure E2E execution acceptance *(protected deploy + browser smoke + KQL proof)* | [Spec 009](.squad\specs\009-live-azure-execution-and-evidence\README.md) | 🟡 In progress; final E2E blocked/waiting | Readiness deploy/smoke/shutdown evidence exists; current protected deploy/smoke dispatches are waiting for approval. Do not close until real delegated browser/agent-browser E2E, positive/negative KQL for that run, shutdown, and Tank/Trinity/Morpheus review gates pass. |

> **Note:** Spec-first gate applies — a spec directory and task list must exist under `.squad\specs\` before implementation begins for any milestone.  
> **M8 note:** M8 remains opt-in by design. Public CI cannot hold the secrets required for live deployment. In this closeout session, live workflows remained scaffolds and were **not** executed against Azure.
> **M9 note:** Spec 009 now has readiness deploy/smoke/shutdown evidence and elevated-access controls, but final live E2E is still blocked/waiting on protected dispatch approval plus reviewer gates. No final live browser/agent-browser success is claimed.

---

## Milestone 1 — Local token validation + OBO boundaries (Spec 001)

**Goal:** Establish offline-safe JWT validation scaffolding and explicit OBO boundaries across BFF / Agent Execution Service → MCP protected API.  
**Owner agents:** Morpheus (architecture), Trinity (security), Neo (backend)  
**Impact:** High  
**Status:** ✅ Complete

### ✅ Done by end of M1 — what works

| Capability | Details |
|-----------|---------|
| Offline JWT validation | `identity_lab_auth` validates JWTs from fixture files without any network call to Entra ID. |
| PII suppression | `sanitize_claims()` strips `oid`, `sub`, `email`, `upn`, `name`, `preferred_username` on every path. |
| OBO boundary defined | The Agent Execution Service must exchange the inbound token for an MCP-audience token before calling the MCP protected API. Forwarding the original token is blocked. |
| `/whoami` endpoints | All services return only safe, sanitized claim metadata. Raw tokens are never returned. |
| Negative cases pass | Wrong audience, missing scope, and expired token all result in 401 rejections with no token leakage. |
| `python -m pytest` | Initial auth unit test suite passes. |

**Key files:**
- `apps/shared/python/identity_lab_auth/*`
- `apps/bff/python-fastapi/app/auth.py`
- `apps/agent-execution/python-fastapi-agent-framework/app/auth.py`
- `apps/mcp-protected-api/python-fastapi/app/auth.py`
- `tests/fixtures/sample-claims/*`
- `config/env/*.env.example`

---

## Milestone 2 — Local delegated flow integration (Spec 003)

**Goal:** Prove request flow from BFF / Agent Execution Service into MCP protected API using mock OBO exchange and integration tests.  
**Owner agents:** Neo, Trinity  
**Impact:** High  
**Status:** ✅ Complete

### ✅ Done by end of M2 — what works

| Capability | Details |
|-----------|---------|
| End-to-end local flow | A test client can drive a request through BFF → Agent Execution Service → MCP protected API entirely offline. |
| Mock OBO exchange | The OBO exchange resolves from fixture claims with zero network calls. The Agent Execution Service does not invent or bypass tokens. |
| Delegated token integrity | The original inbound token is never forwarded to the MCP API; only the OBO-exchanged token (MCP-audience) is used. |
| Integration tests | `tests/integration/` tests verify the full delegated chain from end to end with mock tokens. |
| `python -m pytest` | All tests pass including integration tests. |

**Key files:**
- `apps/agent-execution/python-fastapi-agent-framework/app/*`
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
| APIM policy documentation | `docs/apim/` shows correct audience enforcement for inbound user tokens for BFF and Agent Execution Service boundaries. |
| OBO boundary in policies | Policy examples make explicit that APIM must not replace delegated tokens with managed identity; OBO happens in the Agent Execution Service, not at APIM. |
| Terraform policy validation | `infra/terraform/policies/` is format-checked and validates without live Azure credentials. |
| Policy integration tests | Tests assert audience rules, OBO boundary rules, and that policies reject wrong-audience tokens. |
| `terraform fmt` + `validate` | Pass for APIM modules. |

**Key files:** `docs/apim/*`, `infra/terraform/policies/*`, `tests/integration/python/test_apim_*.py`, `.squad/specs/004-apim-policy-alignment/*`

---

## Milestone 4 — Local runtime ergonomics (Spec 005)

**Goal:** Ensure Docker Compose and env examples support the offline token flow for BFF / Agent Execution Service / MCP.  
**Owner agents:** Tank, Neo  
**Impact:** Medium  
**Status:** ✅ Complete

### ✅ Done by end of M4 — what works

| Capability | Details |
|-----------|---------|
| `docker compose up` | All services start: BFF, Agent Execution Service, MCP Protected API. |
| Offline token flow | `.env.example` files guide developers through offline token flow configuration with no Azure credentials. |
| New-developer experience | A new contributor can `docker compose up` and run `python -m pytest` with no live Azure credentials and no manual setup beyond `.env` copy. |
| Compose validation | Base and overlay Compose config checks pass; no missing service definitions. |
| 65+ tests pass | Full offline/Compose-mode `python -m pytest` suite passes. |

**Key files:** `docker/docker-compose.yml`, `config/env/*.env.example`, `apps/bff/python-fastapi/app/*`

---

## Milestone 5 — AKS + Entra Agent ID + Observability

**Goal:** Validate an optional AKS path for Microsoft Entra Agent ID auth in agent/MCP workloads, building on the local mock/OBO foundation. Establish end-to-end tracing (OpenTelemetry + Jaeger) across all mock and AKS flows. Adopt "Agent Execution Service" as the canonical successor term to "Agentic Layer" (naming amendment — pre-M6 approved).  
**Owner agents:** Morpheus (Lead/Architect), Tank (Infra), Trinity (Security), Neo (Backend)  
**Impact:** High  
**Status:** ✅ Complete — all Spec 002 tasks T01–T20 complete; architecture/security sign-offs accepted; final validation passed.

### ✅ Done by end of M5 — what works

| Capability | Details |
|-----------|---------|
| **Terminology (M5)** | "Agentic Layer" = lab's orchestration service during M5 implementation (`apps/agent-gateway/`). "AKS Agent Gateway" = agentgateway.dev infrastructure proxy sidecar. ADRs 0006 + 0007 recorded. *(Note: "Agentic Layer" is superseded by "Agent Execution Service" per ADR 0008, adopted pre-M6.)* |
| **AKS Terraform skeletons** | `infra/terraform/modules/aks/`, `workload-identity/`, `k8s-bootstrap/`, and `environments/aks/` exist with valid HCL; `terraform fmt -check` and `validate` pass with no live credentials. |
| **Agent ID sidecar mock boundary** | `AgentSidecarClient` ABC and `MockAgentSidecarClient` implemented. In-process mock resolves from fixture claims, makes zero HTTP calls, enforces localhost-only sidecar URL. |
| **Blueprint audience validation** | Agent Execution Service validates inbound token `aud` against the configured blueprint audience before any Agent OBO exchange; wrong-audience tokens are rejected with 401. |
| **Agent ID fixture set** | Seven fixture files in `tests/fixtures/sample-claims/`: happy-path user token, Agent OBO MCP token, wrong-audience, missing-actor, app-only-blueprint, untrusted-tenant, replay-stale. All use all-zero placeholder GUIDs. |
| **Negative case tests** | Offline pytest tests for all five negative fixtures; each asserts correct rejection without network calls. |
| **`xms_act_fct` safe-claims** | `config/claims/safe-claims-allowlist.json` and `DEFAULT_SAFE_CLAIM_KEYS` updated for `xms_act_fct`; PII suppression (`oid`, `sub`, etc.) preserved. |
| **Strict JWKS validation** | `alg:none` and `HS*` rejected at header stage; `kid` required; TTL cache with `kid`-miss retry; strict mode ignores fixture header. Offline tests for each rejection case. |
| **Illustrative AKS manifests** | `docs/deployment/k8s/` contains `namespace.yaml`, `service-account.yaml`, `agent-gateway-deployment.yaml`, `network-policy.yaml` — all labelled "ILLUSTRATIVE REFERENCE ONLY". |
| **Three M5 ADRs** | ADR-M5-01 (AKS optional track), ADR-M5-02 (sidecar mock boundary), ADR-M5-03 (JWKS strategy) recorded in `design.md`. |
| **End-to-end tracing (mock flows)** | OpenTelemetry SDK instruments BFF, Agent Execution Service, and MCP Protected API. Jaeger all-in-one runs in Docker Compose. Contributors open `localhost:16686` to see the full request chain as visual spans. |
| **AKS Agent Gateway tracing design** | agentgateway.dev's native OTLP → Jaeger pipeline documented; Jaeger UI shows `list_tools`/`call_tool` spans when AKS flows are exercised. |
| **W3C TraceContext propagation** | `traceparent`/`tracestate` forwarded on all inter-service HTTP calls. |
| **No PII in traces** | Span attribute allowlist enforced; `oid`, `sub`, raw tokens never in spans. |
| **Full Python suite passes** | `python -m pytest` passes: 229 tests. |
| **No secrets committed** | No real GUIDs, tenant IDs, kubeconfigs, or tokens anywhere in committed files. |

**Key files:**
- `.squad\specs\002-aks-entra-agent-id\*` (spec artifacts)
- `.squad\architecture\decisions\001-agentic-layer-vs-agent-gateway-terminology.md` *(superseded — historical record)*
- `.squad\architecture\decisions\004-agent-execution-service-naming.md` *(pre-M6 naming ADR)*
- `.squad\architecture\decisions\002-end-to-end-tracing-strategy.md`
- `docs\adr\0006-agentic-layer-vs-agent-gateway-terminology.md` *(superseded — historical record)*
- `docs\adr\0008-agent-execution-service-naming.md` *(pre-M6 naming ADR — public counterpart)*
- `docs\adr\0007-end-to-end-tracing-strategy.md`
- `apps\shared\python\identity_lab_auth\agent_obo.py`
- `apps\shared\python\identity_lab_auth\telemetry.py`
- `tests\fixtures\sample-claims\agent-*.json`
- `infra\terraform\modules\aks\`, `workload-identity\`, `k8s-bootstrap\`
- `infra\terraform\environments\aks\`
- `docs\deployment\k8s\*`
- `docker\docker-compose.tracing.yml`, `docker\otel-collector-config.yaml`

**Validation targets:**
```
python -m pytest
terraform -chdir=infra\terraform fmt -check -recursive
terraform -chdir=infra\terraform\environments\aks init -backend=false
terraform -chdir=infra\terraform\environments\aks validate
docker compose -f docker\docker-compose.yml -f docker\docker-compose.tracing.yml config --quiet
```

---

## Milestone 6 — Azure deployment baseline *(configuration + Terraform validation only)*

**Goal:** Implement minimal Terraform wiring for APIM + Container Apps with managed identity ready for OBO (no secrets committed). Migrate tracing backend to Azure Monitor (OTLP endpoint swap). Apply Agent Execution Service rename (M6 Task 0).  
**Owner agents:** Tank (Lead/Infra), Neo (Backend/Rename)  
**Reviewers:** Morpheus, Trinity  
**Impact:** High  
**Status:** ✅ Complete — [Spec 006](.squad\specs\006-azure-deployment-baseline\README.md) closed. All T00–T13 tasks complete; Morpheus + Trinity post-implementation reviews accepted; final closeout validation passed 2026-06-01.

> **Scope clarification — what M6 is and is not:**  
> M6 proves that the Azure deployment *configuration* is correct. It **does not** run `terraform apply`, create live Azure resources, or smoke-test a deployed endpoint. `terraform validate` passing means the HCL is structurally sound and all required inputs are typed correctly — it is not evidence that a working deployment exists. Live deployment and E2E smoke-testing are the M8 gate.

### ✅ Done by end of M6 — what works

| Capability | Details |
|-----------|---------|
| **Agent Execution Service rename** | `apps/agent-gateway/` → `apps/agent-execution/`; Compose service `agent-gateway` → `agent-execution`. All imports, CI commands, specs, and docs updated. 229+ tests pass. |
| **ACA Terraform skeleton** | `infra/terraform/environments/single-tenant-aca/` scaffolded: APIM + Container Apps + App Insights + managed identities. `terraform fmt/validate` passes. No `terraform apply` in CI. |
| **Managed identity scaffolded** | User-assigned managed identity per service (BFF, Agent Execution Service, MCP Protected API). OBO boundary design preserved from M1/M2. |
| **Azure Monitor tracing** | `OTEL_EXPORTER_OTLP_ENDPOINT` documented in `.env.example` files as Azure Monitor OTLP placeholder. Config-only swap from M5 Jaeger instrumentation — no code change. |
| **`AUTH_MODE=strict` enforced** | All three Python services verified to reject fixture headers and require real JWKS in strict mode. `docker-compose.strict-aca.yml` overlay validates. |
| **CI validation gates** | `terraform fmt` + `init -backend=false` + `validate`, all Compose `config --quiet` checks, `python -m pytest`, no-secret scan — all pass without live credentials. |
| **ACA deployment docs** | `docs/deployment/aca/README.md` with topology, managed identity model, OTLP swap, and variable substitution guide. Marked ILLUSTRATIVE. |

**Key files:** `infra/terraform/modules/*`, `infra/terraform/environments/single-tenant-aca/`, `apps/agent-execution/`, `docker/docker-compose.strict-aca.yml`, `docs/deployment/aca/`

---

## Milestone 7 — Variant client implementations *(offline delegated flows)*

**Goal:** Implement first UI clients (SPFx, SharePoint classic, SPA) that exercise delegated flows offline/locally.  
**Owner agents:** Mouse, Neo  
**Impact:** High  
**Status:** ✅ Complete and closed (2026-06-02) — [Spec 007](.squad\specs\007-variant-client-implementations\README.md)

> **Scope clarification — what M7 is and is not:**  
> M7 clients prove delegated token acquisition from the browser side. Flows are exercised locally/offline (or against a mock BFF) and validated with `python -m pytest`. M7 does **not** by itself prove live Azure deployment — even when all M7 tests pass, the chain browser → APIM → BFF → Agent Execution Service → MCP Protected API has not been smoke-tested against real Azure infrastructure. That verification is the M8 gate.  
> M7 is a *necessary prerequisite* for M8: without working client implementations that can acquire real Entra delegated tokens, there is nothing to drive the M8 E2E smoke test.

### ✅ Done by end of M7 — what works

| Capability | Details |
|-----------|---------|
| **SPFx web part** | SPFx web part acquires a delegated token from Entra ID via `AadHttpClient` and calls BFF `/chat/session` with the correct audience. Token managed by SPFx runtime — not in localStorage. |
| **SharePoint classic integration** | Classic loader script acquires delegated token via pluggable token provider (`_spPageContextInfo.aadTokenProviderFactory`); calls BFF. Token used in-memory only. |
| **SPA (public client)** | React/Vite SPA uses MSAL PKCE flow (`cacheLocation: sessionStorage`), acquires delegated token, calls BFF `/chat/session`. |
| **Identity invariant enforced** | `userId` in any body field is display/context only — code comments + negative tests confirm BFF rejects requests with `userId` but no/invalid bearer token (401). |
| **Token handling documented** | Each variant's token acquisition, cache strategy, and BFF handoff documented with Mermaid diagram. Token security section in each variant README. |
| **No-token-persistence validated** | Per-variant test/assertion: SPA uses `sessionStorage` (not `localStorage`); classic loader uses in-memory only; SPFx web part calls no storage API. |
| **Variant-specific tests** | Negative tests (no-token-persistence, no-userId-auth-fallback) pass; `python -m pytest` passes (235+ tests). |
| **Trace visualization** | All three client variants generate W3C TraceContext `traceparent` spans; visible in local Jaeger (`localhost:16686`) or Azure Monitor when deployed. |

**Key files:** `apps/sharepoint-*`, `apps/spfx-webpart`, `apps/spa-public-client`

### Final M7 validation summary

- Full Python regression (T08 baseline): `python -m pytest` → **246 passed**.
- Focused T09 re-review: `python -m pytest tests/security/test_m7_variant_identity_boundaries.py tests/security/test_bff_chat_session.py` → **19 passed**; `cd apps/spfx-webpart/identity-chat-webpart && npm run build && npm test` → **pass**.
- Focused T10 re-review: `python -m pytest tests/security/test_bff_chat_session.py tests/security/test_m7_variant_identity_boundaries.py tests/security/test_jwks_strict.py tests/security/test_telemetry.py` → **91 passed**; `cd apps/spfx-webpart/identity-chat-webpart && npm run build && npm test` → **pass**.
- Cross-variant validation remained green from T08: SPA/classic/SPFx validations passed, `docker compose -f docker/docker-compose.yml config --quiet` passed, and public-safe scan passed.
- Live Azure E2E was intentionally **not run in M7**; this remains the M8 opt-in gate.

---

## Milestone 8 — Live Azure E2E verification *(opt-in; requires configured private environment)*

**Goal:** Deploy the M6-validated configuration to a real Azure environment and smoke-test the complete chain — browser → APIM → BFF → Agent Execution Service → MCP Protected API — with real Entra delegated tokens. Validate that traces appear in Azure Monitor end-to-end.  
**Owner agents:** Tank (Infra/Deploy), Trinity (Security validation), Morpheus (Architecture sign-off)  
**Reviewers:** All  
**Impact:** High — this is the milestone that answers "does it actually work in Azure?"  
**Status:** ✅ Complete and closed (T15)

> **Opt-in by design:** M8 cannot run from public CI. It requires a private environment holding real credentials (subscription ID, tenant ID, Entra app registrations, client secrets or federated credentials). These values must never be committed. M8 smoke-test scripts will live in this repository; the secrets-holding environment configuration does not.  
> **Prerequisites:** M6 (Terraform config validated) + M7 (working client-side delegated token acquisition) must both be complete before M8 can be meaningfully executed.

### ✅ Done by end of M8 — what works now

| Capability | Details |
|-----------|---------|
| **Protected live workflow scaffolds** | `m8-live-oidc-contract.yml`, `m8-deploy-live.yml`, `m8-start-resume.yml`, `m8-nightly-shutdown.yml`, and `m8-smoke-trace.yml` are in place with protected-environment/OIDC boundaries and opt-in live gates. |
| **Public-safe validation gates** | CI and local checks enforce placeholder-only identifiers, no unsafe live defaults, principal-scope boundaries, and telemetry leakage coverage (`tools/ci/public_safe_validation.py`, `tools/telemetry/validate_m8_kql_contract.py`). |
| **Canonical smoke/trace contract wiring** | Browser harness and KQL contract validators are wired for static/offline validation with hard-fail semantics represented for leakage checks. |
| **Operator documentation** | ACA operator runbook documents deploy/start/smoke/shutdown sequence, cost model, and optional T06 destroy posture (`docs/deployment/aca/m8-operator-guide.md`). |
| **Closeout task reconciliation** | Required path statuses are complete/accepted through T15; T06 is explicitly optional, not implemented, and non-blocking. |

**Validation summary (closeout):**
- `python -c "import json; json.load(open(r'.squad\\specs\\008-live-azure-e2e-gate\\state.json', encoding='utf-8')); print('state.json parse ok')"`
- `python tools/ci/public_safe_validation.py`
- `python tools/telemetry/validate_m8_kql_contract.py`
- `python -m pytest -q tests/security/test_m8_public_safe_validation.py`

**Key files:** `.github/workflows/m8-*.yml`, `tools/ci/public_safe_validation.py`, `tools/telemetry/validate_m8_kql_contract.py`, `docs/deployment/aca/m8-operator-guide.md`

> **Live execution note:** No live Azure deployment, workflow dispatch, start/stop operation, or smoke trace run was executed or claimed during this closeout session.

---

## Milestone 9 — Live Azure E2E execution acceptance *(protected environment only)*

**Goal:** Execute the first claimable live Azure deployment and browser smoke for browser → APIM → BFF → Agent Execution Service → MCP Protected API, then prove identity-boundary and telemetry-safety acceptance with Azure Monitor / Application Insights KQL.  
**Owner agents:** Tank (Infra/Deploy), Trinity (Security validation), Morpheus (Architecture sign-off), Neo (App/runtime fixes), Mouse (Browser smoke)  
**Impact:** High — live identity, protected environments, OIDC, and telemetry leakage prevention.  
**Status:** 🟡 In progress / final E2E blocked-waiting — [Spec 009](.squad\specs\009-live-azure-execution-and-evidence\README.md) exists; M9 MUST NOT claim closeout until protected deploy/smoke approval, real delegated browser/agent-browser E2E, positive/negative KQL, shutdown, and Tank/Trinity/Morpheus reviews are accepted.

### Required M9 security gates and execution contract

- Protected GitHub Environments only; public CI remains validation-only and never requests Azure tokens.
- Separate purpose-scoped OIDC identities for deploy/apply, smoke/trace verification, and lifecycle operations, or a documented equivalently constrained model.
- `AUTH_MODE=strict` for every live service; fixture/mock-token paths blocked.
- APIM validates issuer/audience/scope and preserves the delegated bearer token only to the BFF.
- BFF validates the inbound user token and never performs MCP OBO.
- Agent Execution Service is the only MCP OBO boundary.
- MCP Protected API rejects the original user token and accepts only the downstream MCP-audience token.
- Workflow logs, traces, summaries, artifacts, and KQL result exports contain no raw tokens, live endpoint values, account metadata, or PII claim keys/values.
- KQL acceptance requires positive role/operation correlation and negative zero-row leakage proof across requests, dependencies, traces, and logs.
- Required resources: resource group, ACR, ACA environment/apps for BFF / Agent Execution Service / MCP Protected API, APIM, managed identities, App Insights, and Log Analytics.
- Required protected environments: `lab-live-azure-deploy`, `lab-live-azure-smoke`, and `lab-live-azure-ops`.
- Required order: static validation → OIDC contract → zero-mutation deploy rehearsal → approved live deploy → start/resume if needed → browser smoke/trace → positive/negative KQL → redacted evidence review → shutdown/scale-down verification.
- Mandatory cost controls: ACA scale-down where compatible, nightly shutdown, documented APIM/App Insights/Log Analytics/ACR residual costs, and optional teardown only by explicit manual approval.

**Planning artifact:** `.squad\specs\009-live-azure-execution-and-evidence\`

---

> **ADR:** `docs/adr/0007-end-to-end-tracing-strategy.md` · Full record: `.squad/architecture/decisions/002-end-to-end-tracing-strategy.md`

| Phase | What is traceable | Visualization |
|-------|------------------|--------------| 
| M5 (local/mock) | BFF → Agent Execution Service → MCP Protected API (mock flows) | Jaeger UI `localhost:16686` (Docker Compose) |
| M5 (AKS flows) | AKS Agent Gateway proxy spans (`list_tools`, `call_tool`) | Same Jaeger UI via agentgateway.dev native integration |
| M6 (config baseline) | Full deployed chain topology designed and OTLP config documented — **not yet running live** | Azure Monitor (OTLP endpoint — config-only swap) |
| M7 (clients) | All variant client → BFF spans (offline/local) | Jaeger (local) or Azure Monitor (if deployed) |
| M8 (live E2E — opt-in) | Protected workflow scaffolds and telemetry contracts validated statically/offline; live execution remains operator-invoked only | Azure Monitor / Application Insights contract wiring validated; live evidence requires separate protected run |
| M9 (live execution + evidence) | Planned protected live deploy, browser smoke, positive chain KQL, and negative leakage KQL | Azure Monitor / Application Insights; public evidence must be redacted |

**Invariants (all phases):**
- W3C TraceContext (`traceparent`/`tracestate`) propagated on all inter-service HTTP calls.
- Span attributes follow `sanitize_claims()` rules: `oid`, `sub`, `email`, `upn`, `preferred_username`, `name`, `given_name`, `family_name`, raw tokens **never** in spans.
- `OTEL_SDK_DISABLED=true` (or no-op exporter) in unit-test runs; tracing does not require a running Jaeger instance in offline pytest.

