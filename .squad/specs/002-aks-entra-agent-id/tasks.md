# Spec 002 — Tasks

**Spec:** 002-aks-entra-agent-id  
**Milestone:** M5 — AKS + Entra Agent ID auth exploration  
**Updated:** 2026-05-14  
**Primary owners:** Morpheus, Tank, Trinity, Neo  
**Reviewers:** Morpheus (architecture), Trinity (security)

---

## Dependency Order

```
T01 (Morpheus spec review) ─────────────────────────────────────────────────────┐
T02 (Morpheus ADR decisions)  ──────────────────────────────────────────────────┤
T03 (Trinity security review) ──────────────────────────────────────────────────┤
                                                                                 ↓
                  ┌── T04 (Tank: AKS TF skeletons) → T05 (Tank: AKS manifests) ─┤
                  │                                                               │
                  ├── T06 (Trinity: safe-claims ext) → T07 (Trinity: fixtures)   │
                  │   → T08 (Trinity: neg tests) → T09 (Trinity: JWKS tests)     │
                  │                                                               │
                  ├── T10 (Neo: agent_obo interface) → T11 (Neo: mock impl)      │
                  │   → T12 (Neo: blueprint aud validation) → T13 (Neo: tests)   │
                  │                                                               │
                  └── T17 (Morpheus: tracing design review)                      │
                      → T18 (Neo: OTEL instrumentation) → T19 (Tank: Compose     │
                         tracing overlay) → T20 (Trinity: tracing security        │
                         review)                                                  │
                                                                                 ↓
                  T14 (Morpheus: arch review post-impl) ─────────────────────────┤
                  T15 (Trinity: security sign-off) ──────────────────────────────┤
                                                                                 ↓
                  T16 (Tank: AKS TF validation CI) ────────────── all complete ──┘
```

T01, T02, T03 are blocking review/decision tasks. No implementation begins until T02 and T03 are both complete.

T04–T13 and T17–T20 are parallel streams (Tank, Trinity, Neo, Morpheus) that can proceed after T02+T03 complete.

T14 and T15 are post-implementation review gates. T16 is final validation.

---

## T01 — Morpheus: Spec 002 Promotion Review

**Owner:** Morpheus  
**Depends on:** Spec 002 spec artifacts complete (this task set)  
**Blocks:** T02, T03  

**Description:**  
Review the promoted Spec 002 artifacts (`README.md`, `goals.md`, `research.md`, `requirements.md`, `design.md`, `tasks.md`, `state.json`, `.progress.md`). Confirm that the scope, ADR framing, and design decisions are architecturally sound before implementation begins. Flag any concerns on the AKS optional track decision and sidecar boundary design.

**Acceptance:**
- Morpheus records a written review note in `.progress.md` under "Log".
- Any required amendments to `design.md` or `requirements.md` are documented and applied before T02.

**Validation:** n/a (review task)

---

## T02 — Morpheus: Record ADR Decisions

**Owner:** Morpheus  
**Depends on:** T01  
**Blocks:** T04, T10 (implementation unblocked only after T02 + T03 both complete)  

**Description:**  
Record architectural decisions for:

- **ADR-M5-01:** AKS optional track vs ACA default track. Preferred: standalone `environments/aks/` (see `design.md`). Record acceptance or amendment.
- **ADR-M5-02:** Agent ID sidecar mock boundary approach. Preferred: in-process adapter with `AgentSidecarClient` ABC (see `design.md`). Record acceptance or amendment.

Record decisions in `design.md` (update ADR status from "Pending" to "Accepted" or "Amended") and leave a summary note in `.progress.md`.

**Acceptance:**
- ADR-M5-01 status updated in `design.md`.
- ADR-M5-02 status updated in `design.md`.
- Decision note in `.progress.md`.

**Validation:** n/a (decision task)

---

## T03 — Trinity: Security Review and ADR-M5-03 Decision

**Owner:** Trinity  
**Depends on:** T01  
**Blocks:** T06, T07, T08, T09 (Trinity stream), T10, T11, T12, T13 (Neo stream)  

**Description:**  
Security review of:

1. **FR-05 (safe-claims allowlist extension):** Confirm that adding `xms_act_fct` to the allowlist does not introduce PII exposure. Confirm `xms_act_fct` claim shape (JSON object) is handled safely by `sanitize_claims()` — flag if `dict` type needs explicit handling.
2. **FR-06 (agent OBO mock boundary):** Confirm the `AgentSidecarClient` ABC design and MockAgentSidecarClient spec are safe: no token logging, no network calls, correct audience validation order.
3. **FR-09 (strict JWKS validation):** Confirm the algorithm allowlist and JWKS `kid`-miss-retry strategy are sound. Record **ADR-M5-03** decision (JWKS library and caching approach).
4. **Fixture negative case coverage (FR-03/FR-04):** Confirm the seven fixture names and their expected rejection reasons are complete. Add any missing negative case.
5. **Security design notes in `design.md` §Security Design Notes:** Confirm or amend each note.

**Acceptance:**
- Trinity records security review note in `.progress.md`.
- ADR-M5-03 status updated in `design.md` (from "Pending" to "Accepted" or "Amended").
- Any security-required amendments to `design.md` or `requirements.md` applied before implementation.
- `dict`-type handling for `xms_act_fct` in `sanitize_claims()` flagged as explicit implementation requirement if confirmed needed.

**Validation:** n/a (review task)

---

## T04 — Tank: AKS Terraform Module Skeletons

**Owner:** Tank  
**Depends on:** T02 + T03 complete  
**Blocks:** T05, T16  

**Description:**  
Create four Terraform skeleton directories with valid HCL structure per the layout in `design.md §AKS Terraform Skeleton Layout`:

1. `infra/terraform/modules/aks/` — `main.tf`, `variables.tf`, `outputs.tf`.
2. `infra/terraform/modules/workload-identity/` — `main.tf`, `variables.tf`, `outputs.tf`.
3. `infra/terraform/modules/k8s-bootstrap/` — `main.tf`, `variables.tf`, `outputs.tf`.
4. `infra/terraform/environments/aks/` — `main.tf`, `variables.tf`, `outputs.tf`, `terraform.tfvars.example`.

Resource bodies may be stubs (e.g., `resource "azurerm_kubernetes_cluster" "this" {}`), but HCL must be syntactically valid. All variable default values and `tfvars.example` values MUST be placeholder-only strings.

**Checklist:**
- No real tenant IDs, subscription IDs, client IDs, or secrets.
- All GUIDs use all-zero placeholder pattern.
- `terraform.tfvars.example` uses `{placeholder}` or all-zero GUIDs exclusively.
- AKS environment does not modify existing `single-tenant` or `vendor-shaped` environments.

**Validation:**
```
terraform -chdir=infra\terraform fmt -check -recursive
terraform -chdir=infra\terraform\environments\aks init -backend=false
terraform -chdir=infra\terraform\environments\aks validate
```

---

## T05 — Tank: Illustrative AKS Manifest Docs

**Owner:** Tank  
**Depends on:** T04  
**Blocks:** T14  

**Description:**  
Create `docs/deployment/k8s/` directory with:

1. `README.md` — context paragraph: illustrative reference only; not applied by CI or production automation; all names and IDs are placeholders.
2. `namespace.yaml` — namespace for agent workloads.
3. `service-account.yaml` — service account with workload identity annotations (`azure.workload.identity/client-id`, `azure.workload.identity/tenant-id`) using placeholder values.
4. `agent-gateway-deployment.yaml` — Deployment spec with:
   - agent-gateway container (placeholder image).
   - Entra Agent ID sidecar container (placeholder image, `localhost` port only).
   - Pod annotation `azure.workload.identity/use: "true"`.
   - Sidecar container exposes only `containerPort` on `127.0.0.1` binding.
5. `network-policy.yaml` — NetworkPolicy that:
   - Selects the agent-gateway pod by label.
   - Denies all ingress to the sidecar port except from the same pod (localhost only).
   - Includes a comment explaining the cross-pod prevention intent.

Each YAML file MUST include a comment at the top: `# ILLUSTRATIVE REFERENCE ONLY — not applied by CI or production automation`.

All names, image references, and IDs MUST be placeholder values (e.g., `your-registry.azurecr.io/agent-gateway:latest`, `00000000-0000-0000-0000-000000000000`).

**Validation:** YAML syntax check (manual or `python -c "import yaml; yaml.safe_load(open(...))"` for each file). No automated CI target — doc review only.

---

## T06 — Trinity: Safe-Claims Allowlist Extension

**Owner:** Trinity  
**Depends on:** T03 (security review confirms `xms_act_fct` is safe)  
**Blocks:** T07  

**Description:**  
Extend the safe-claims allowlist to include `xms_act_fct`:

1. Add `"xms_act_fct"` to `config/claims/safe-claims-allowlist.json` `allowlist` array.
2. Add `"xms_act_fct"` to `DEFAULT_SAFE_CLAIM_KEYS` in `apps/shared/python/identity_lab_auth/claims.py`.
3. If T03 identified that `sanitize_claims()` drops `dict`-typed values (the `xms_act_fct` claim is a JSON object), update `_sanitize_value()` in `claims.py` to handle `dict` inputs safely — convert to a string representation or pass through as-is up to a safe size limit (e.g., 512 chars as JSON string). Do NOT log or expose nested PII.
4. Add a test asserting that `sanitize_claims()`:
   - Includes `xms_act_fct` when present.
   - Drops `oid` and `sub` even when present.
   - Handles `xms_act_fct` as a dict without raising.

**Files to change:**
- `config/claims/safe-claims-allowlist.json`
- `apps/shared/python/identity_lab_auth/claims.py`
- New or extended test under `tests/security/` or `tests/unit/`

**Validation:**
```
python -m pytest
```

---

## T07 — Trinity: Agent ID Fixture Files

**Owner:** Trinity  
**Depends on:** T06  
**Blocks:** T08  

**Description:**  
Create seven JSON fixture files under `tests/fixtures/sample-claims/` per the claim content specified in `design.md §Offline Fixture Design`:

1. `agent-blueprint-user-token.json`
2. `agent-obo-mcp-token.json`
3. `agent-wrong-audience.json`
4. `agent-missing-actor.json`
5. `agent-app-only-blueprint.json`
6. `agent-untrusted-tenant.json`
7. `agent-replay-stale.json`

**Constraints:**
- All GUIDs MUST be all-zero placeholders from the placeholder table in `design.md`.
- No `oid`, `sub`, `email`, `upn`, `name`, or `preferred_username` in any fixture.
- `exp` values: use `1893456000` for valid fixtures (far-future placeholder); use `1600000000` for the replay/stale fixture (past).
- `xms_act_fct` in `agent-obo-mcp-token.json` MUST be a JSON object: `{"appid": "00000000-0000-0000-0000-000000000201"}`.

**Validation:** Manual JSON syntax check + `python -c "import json; json.load(open('<file>'))"` for each file.

---

## T08 — Trinity: Negative Test Coverage

**Owner:** Trinity  
**Depends on:** T07  
**Blocks:** T13 (Neo integration tests — may proceed in parallel after T07)  

**Description:**  
Write offline pytest tests for each negative fixture in `tests/security/test_agent_id_fixtures.py` (or equivalent):

| Test | Fixture | Expected outcome |
|---|---|---|
| `test_wrong_audience_rejected` | `agent-wrong-audience` | `ValueError` or 401 at audience check |
| `test_missing_actor_rejected_at_mcp` | `agent-missing-actor` | `ValueError` at MCP boundary actor check |
| `test_app_only_blueprint_rejected` | `agent-app-only-blueprint` | `ValueError` — no `scp`, delegated endpoint |
| `test_untrusted_tenant_rejected` | `agent-untrusted-tenant` | `ValueError` at trusted-tenant check |
| `test_stale_token_rejected` | `agent-replay-stale` | `ValueError` at `exp` check |
| `test_blueprint_user_token_accepted` | `agent-blueprint-user-token` | Accepted; sanitized claims returned |
| `test_obo_mcp_token_accepted` | `agent-obo-mcp-token` | Accepted; `appid` and `xms_act_fct` in output |

All tests MUST be offline (no network calls). Use the mock boundary from T11 once available; stub inline if T11 is not yet merged.

**Validation:**
```
python -m pytest tests/security/test_agent_id_fixtures.py -v
python -m pytest
```

---

## T09 — Trinity: Strict JWKS Validation Tests

**Owner:** Trinity  
**Depends on:** T03 (ADR-M5-03 decision), T06  
**Blocks:** T15  

**Description:**  
Write offline pytest tests for strict JWKS validation in `tests/security/test_jwks_strict.py` (or equivalent):

| Test | Scenario | Expected outcome |
|---|---|---|
| `test_alg_none_rejected` | JWT header `"alg": "none"` | `ValueError("Rejected algorithm: none")` |
| `test_hs256_rejected` | JWT header `"alg": "HS256"` | `ValueError` — symmetric algorithm rejected |
| `test_hs512_rejected` | JWT header `"alg": "HS512"` | `ValueError` |
| `test_missing_kid_rejected` | No `kid` in JWT header | `ValueError("Missing kid")` |
| `test_unknown_kid_rejected` | `kid` not in JWKS | `ValueError` — kid not found after retry |
| `test_fixture_header_ignored_in_strict_mode` | `X-Identity-Lab-Fixture` header + `AUTH_MODE=strict` | Header has no effect; validation proceeds normally |
| `test_valid_rs256_structure_accepted` | Valid header structure with `RS256` and `kid` | No algorithm rejection (signature validation mocked offline) |

Tests MUST use offline stubs for JWKS fetching; no real OIDC endpoints contacted.

**Validation:**
```
python -m pytest tests/security/test_jwks_strict.py -v
python -m pytest
```

---

## T10 — Neo: `AgentSidecarClient` Interface and Module Stub

**Owner:** Neo  
**Depends on:** T02 + T03 complete  
**Blocks:** T11  

**Description:**  
Create `apps/shared/python/identity_lab_auth/agent_obo.py` as a module stub with:

1. `AgentSidecarClient` ABC (per `design.md §Agent OBO Sidecar Mock Boundary Design`).
2. A `SidecarConfig` dataclass with `sidecar_url: str` and `blueprint_audience: str`.
3. Constructor-level localhost enforcement: raise `ValueError` if `sidecar_url` does not start with `http://localhost` or `http://127.0.0.1`.
4. Update `apps/shared/python/identity_lab_auth/__init__.py` to export `AgentSidecarClient` and `SidecarConfig`.

**No `MockAgentSidecarClient` implementation yet** — that is T11. This task is interface + config validation only.

**Files to create/change:**
- `apps/shared/python/identity_lab_auth/agent_obo.py`
- `apps/shared/python/identity_lab_auth/__init__.py`

**Validation:**
```
python -m pytest
```

---

## T11 — Neo: `MockAgentSidecarClient` Implementation

**Owner:** Neo  
**Depends on:** T10, T07 (fixtures available)  
**Blocks:** T12  

**Description:**  
Implement `MockAgentSidecarClient(AgentSidecarClient)` in `apps/shared/python/identity_lab_auth/agent_obo.py`:

- Constructor accepts `fixture_claims: dict` (blueprint user token fixture) and `obo_fixture_claims: dict` (OBO MCP token fixture).
- `validate(bearer_token)`: ignores the literal bearer string (offline mock); validates `fixture_claims["aud"]` against `blueprint_audience`; validates `tid` against `trusted_tenants`; validates `exp`; returns `sanitize_claims(fixture_claims)`.
- `authorization_header(api_name)`: returns `"Bearer OFFLINE_MOCK_TOKEN"`. Never makes HTTP calls.
- `downstream_api(api_name, user_assertion, scopes)`: validates `user_assertion` audience against `blueprint_audience` (best-effort string check); returns `sanitize_claims(obo_fixture_claims)`.
- All returned dicts pass through `sanitize_claims()`. No raw token strings in output.

**Validation:**
```
python -m pytest
```

---

## T12 — Neo: Blueprint Audience Validation in Agentic Layer

**Owner:** Neo  
**Depends on:** T11  
**Blocks:** T13  

**Description:**  
Wire the blueprint audience validation into `apps/agent-gateway/python-fastapi-agent-framework/app/auth.py` (or an appropriate dependency) so that:

1. A request bearing a token with `aud != BLUEPRINT_AUDIENCE` is rejected before any OBO exchange.
2. The validation uses the `AgentSidecarClient.validate()` method (mock in test; real in future).
3. An integration test confirms that the existing MCP delegated OBO path is not affected.

**Note:** This task wires the boundary in code but does not call a real sidecar. The MockAgentSidecarClient from T11 is used in tests. The real HTTP call path is explicitly gated behind a future environment flag.

**Validation:**
```
python -m pytest
```

---

## T13 — Neo: Integration Tests for Agent OBO Boundary

**Owner:** Neo  
**Depends on:** T12, T08  
**Blocks:** T14  

**Description:**  
Write integration tests in `tests/integration/` (or `tests/security/`) for the full Agent OBO boundary:

1. `test_agent_blueprint_happy_path` — blueprint user token → mock sidecar validate → mock OBO → MCP sanitized claims returned.
2. `test_agent_wrong_audience_rejected_before_obo` — wrong-audience fixture → boundary raises before any OBO exchange.
3. `test_agent_obo_does_not_share_state_with_mcp_obo` — both paths are invoked; assert they use different module instances and return distinct claim sets.
4. `test_agent_obo_output_has_no_pii` — OBO result claims contain no `oid`, `sub`, `email`, `upn`, `name`.
5. `test_sidecar_non_localhost_rejected_at_construction` — `SidecarConfig` with external URL raises `ValueError`.

**Validation:**
```
python -m pytest
```

---

## T14 — Morpheus: Post-Implementation Architecture Review

**Owner:** Morpheus  
**Depends on:** T04, T05, T12, T13, T18, T19 complete  
**Blocks:** T15, T16  

**Description:**  
Review the implemented:

- AKS Terraform module skeletons (T04): confirm structure, variable naming, and `tfvars.example` safety.
- AKS manifest docs (T05): confirm illustrative labelling and network policy correctness.
- `AgentSidecarClient` interface and mock boundary (T10–T12): confirm the ABC design, localhost enforcement, and separation from MCP OBO.

Record findings and final architecture approval in `.progress.md`.

**Validation:** n/a (review task)

---

## T15 — Trinity: Post-Implementation Security Sign-Off

**Owner:** Trinity  
**Depends on:** T06, T08, T09, T13, T14  
**Blocks:** T16  

**Description:**  
Final security review confirming:

1. `sanitize_claims()` correctly handles `xms_act_fct` as a dict without PII leakage.
2. All seven negative fixture tests pass and cover the intended rejection reasons.
3. Strict JWKS tests cover `alg:none`, `HS*`, missing `kid`, and fixture-header suppression.
4. No raw token strings appear in logs, responses, or test output.
5. Agent OBO path has zero shared state with MCP user OBO or Azure OpenAI/Foundry managed identity.
6. No real GUIDs, secrets, or tokens committed anywhere.

Record sign-off in `.progress.md`. Flag any remaining blockers before T16.

**Validation:**
```
python -m pytest
```

---

## T16 — Tank: AKS Terraform Validation in CI / Final Validation

**Owner:** Tank  
**Depends on:** T14, T15  
**Blocks:** M5 complete  

**Description:**  
Run final validation across all M5 targets:

```
terraform -chdir=infra\terraform fmt -check -recursive
terraform -chdir=infra\terraform\environments\aks init -backend=false
terraform -chdir=infra\terraform\environments\aks validate
python -m pytest
```

Confirm no-secret scan passes: search for real GUID patterns, bearer strings, and kubeconfig markers in all new and modified files.

Record final validation results in `.progress.md` and update `state.json` status to `tasks-complete` (still pending coordinator roadmap closure).

**Validation:**
```
terraform -chdir=infra\terraform fmt -check -recursive
terraform -chdir=infra\terraform\environments\aks validate
python -m pytest
```

---

## T17 — Morpheus: Tracing Design Review

*(Added: Amendment 001, 2026-05-15)*

**Owner:** Morpheus  
**Depends on:** T02 + T03 complete  
**Blocks:** T18, T19  

**Description:**  
Review the end-to-end tracing design in `design.md §End-to-End Tracing Design`. Confirm:

1. The span model is architecturally correct for both the mock flow and the AKS flow.
2. The W3C `traceparent` propagation approach is consistent with the AKS Agent Gateway's OTEL integration.
3. The `docker-compose.tracing.yml` overlay specification is safe and does not introduce new secrets or external dependencies beyond the OTEL/Jaeger images.
4. Span attribute names (`auth.mode`, `auth.audience`, `auth.outcome`, `obo.hop`) are non-overlapping with standard OTEL semantic conventions and do not expose PII.
5. Static vs dynamic tracing config split is appropriate.

Record review decision in `.progress.md`.

**Validation:** n/a (review task)

---

## T18 — Neo: OTEL Instrumentation for Mock Flow

*(Added: Amendment 001, 2026-05-15)*

**Owner:** Neo  
**Depends on:** T17  
**Blocks:** T14, T20  

**Description:**  
Specify (and stub, if T02+T03 complete) OTEL instrumentation for the lab's Python services in mock flow:

1. Add `opentelemetry-sdk`, `opentelemetry-instrumentation-fastapi`, `opentelemetry-exporter-otlp-proto-grpc` to `apps/shared/python/` or per-service `requirements*.txt`.
2. Create a shared `identity_lab_auth/telemetry.py` stub that:
   - Initialises `TracerProvider` with OTLP gRPC exporter when `OTEL_EXPORTER_OTLP_ENDPOINT` is set.
   - Defaults to `NoOpTracerProvider` when the env var is unset (preserves offline/test behaviour).
   - Exports a `get_tracer(name: str)` helper.
3. In each FastAPI service's startup: call `setup_telemetry()` if not already called.
4. Add `instrument_fastapi(app)` call using `FastAPIInstrumentor` so HTTP spans are created automatically.
5. Add custom span attributes per `design.md §Required Span Attributes` at the OBO boundary and auth validation boundary.
6. Ensure `OTEL_SDK_DISABLED=true` is set in `config/env/*.env.example` test profiles.

**Files to change:**
- `apps/shared/python/identity_lab_auth/telemetry.py` (new)
- Per-service `requirements.txt` files
- Relevant `app/main.py` or `app/__init__.py` in each service

**Validation:**
```
python -m pytest   # OTEL must not affect test correctness
```

---

## T19 — Tank: Docker Compose Tracing Overlay

*(Added: Amendment 001, 2026-05-15)*

**Owner:** Tank  
**Depends on:** T17  
**Blocks:** T14, T20  

**Description:**  
Create `docker/docker-compose.tracing.yml` per `design.md §OTEL Infrastructure`:

1. `otel-collector` service — `otel/opentelemetry-collector-contrib:latest`; ports `4317` (gRPC) and `4318` (HTTP); mounts a companion `docker/otel-collector-config.yaml`.
2. `jaeger` service — `jaegertracing/all-in-one:latest`; ports `16686` (UI) and `14268` (HTTP collector); `COLLECTOR_OTLP_ENABLED=true`.
3. `docker/otel-collector-config.yaml` — minimal config routing OTLP gRPC → Jaeger exporter.

All image tags MUST be pinned to a specific version (not `latest`) in the final artifact for reproducibility. All values MUST be placeholder-safe (no secrets, no tenant IDs).

Each file MUST include a comment: `# ILLUSTRATIVE REFERENCE ONLY — adjust image versions and ports for production`.

**Files to create:**
- `docker/docker-compose.tracing.yml`
- `docker/otel-collector-config.yaml`

**Validation:**
```
docker compose -f docker/docker-compose.yml -f docker/docker-compose.tracing.yml config --quiet
```

---

## T20 — Trinity: Tracing Security Review

*(Added: Amendment 001, 2026-05-15)*

**Owner:** Trinity  
**Depends on:** T18, T19  
**Blocks:** T15  

**Description:**  
Security review of the tracing implementation:

1. Confirm no span attribute exposes PII — `auth.audience`, `auth.outcome`, `obo.hop` contain only non-PII values. `oid`, `sub`, `email`, `upn` MUST NOT appear as span attributes.
2. Confirm raw bearer tokens are never attached to spans or logs at the OTEL instrumentation layer.
3. Confirm the OTEL SDK is disabled in offline test runs (`OTEL_SDK_DISABLED=true`) and that no trace data is sent during `pytest`.
4. Confirm the Jaeger and OTEL collector images in the Compose overlay do not introduce new data egress paths in a local dev scenario.
5. Confirm the `docker-compose.tracing.yml` overlay does not expose new ports that conflict with other lab services.

Record sign-off in `.progress.md`.

**Validation:** n/a (review task)

---

## Summary Table

| ID | Title | Owner | Depends On | Stream |
|----|-------|-------|-----------|--------|
| T01 | Spec promotion review | Morpheus | spec artifacts complete | Review |
| T02 | Record ADR-M5-01 + ADR-M5-02 decisions | Morpheus | T01 | Review |
| T03 | Security review + ADR-M5-03 | Trinity | T01 | Review |
| T04 | AKS TF module skeletons | Tank | T02+T03 | Tank |
| T05 | Illustrative AKS manifest docs | Tank | T04 | Tank |
| T06 | Safe-claims allowlist extension | Trinity | T03 | Trinity |
| T07 | Agent ID fixture files | Trinity | T06 | Trinity |
| T08 | Negative fixture tests | Trinity | T07 | Trinity |
| T09 | Strict JWKS validation tests | Trinity | T03, T06 | Trinity |
| T10 | `AgentSidecarClient` interface stub | Neo | T02+T03 | Neo |
| T11 | `MockAgentSidecarClient` implementation | Neo | T10, T07 | Neo |
| T12 | Blueprint audience validation in gateway | Neo | T11 | Neo |
| T13 | Integration tests for Agent OBO boundary | Neo | T12, T08 | Neo |
| T14 | Post-impl architecture review | Morpheus | T04, T05, T12, T13, T18, T19 | Review |
| T15 | Post-impl security sign-off | Trinity | T06–T09, T13, T14, T20 | Review |
| T16 | Final validation + AKS TF CI | Tank | T14, T15 | Tank |
| T17 | Tracing design review | Morpheus | T02+T03 | Review |
| T18 | OTEL instrumentation (mock flow) | Neo | T17 | Neo |
| T19 | Docker Compose tracing overlay | Tank | T17 | Tank |
| T20 | Tracing security review | Trinity | T18, T19 | Review |

## M5 Gate Criteria

All of the following must be true before M5 is marked complete:

- [ ] ADR-M5-01, ADR-M5-02, ADR-M5-03 decisions recorded by Morpheus and Trinity
- [ ] Seven Agent ID fixtures committed with all-zero placeholder GUIDs
- [ ] All negative fixture tests pass offline
- [ ] `xms_act_fct` in safe-claims allowlist; `sanitize_claims()` handles dict type
- [ ] `AgentSidecarClient` ABC and `MockAgentSidecarClient` implemented
- [ ] Blueprint audience validated before any OBO exchange
- [ ] Agent OBO path has zero shared state with MCP user OBO
- [ ] Strict JWKS tests: `alg:none`, `HS*`, missing `kid`, fixture-header suppression
- [ ] AKS Terraform skeletons pass `fmt -check` and `validate`
- [ ] Illustrative AKS manifest docs exist with illustrative labelling and use "Agentic Layer" terminology (per ADR 0006)
- [ ] `python -m pytest` passes (65+ tests baseline)
- [ ] No real GUIDs, tenant IDs, tokens, secrets, or kubeconfigs committed
- [ ] Morpheus post-impl architecture sign-off recorded
- [ ] Trinity post-impl security sign-off recorded
- [ ] E2E tracing design reviewed (T17 — Morpheus)
- [ ] OTEL instrumentation specified for mock flow (T18 — Neo)
- [ ] `docker-compose.tracing.yml` overlay specified (T19 — Tank)
- [ ] Tracing security review complete (T20 — Trinity)
- [ ] Amendment 001 reviewed and approved by Morpheus + Trinity

---

## Amendments

| # | Date | Changed By | Summary | Status |
|---|------|-----------|---------|--------|
| 001 | 2026-05-15 | spec-feature (Ashley Hollis) | Added T17–T20 (tracing stream); updated dependency diagram; updated T14/T15 depends-on to include T18/T19/T20; added tracing gate criteria; added terminology note for T05 manifest docs. Implementation remains blocked pending T03. | Approved |
| 001-correction | 2026-05-15 | spec-feature (Ashley Hollis) | Terminology corrected per ADR 0006: "local app gateway" → **Agentic Layer**; "standalone Agent Gateway" → **AKS Agent Gateway**. Gate checklist item for T05 updated. | Applied |
