# Spec 006 — Tasks

**Spec:** 006-azure-deployment-baseline
**Milestone:** M6 — Azure deployment baseline
**Updated:** 2026-06-01
**Primary owners:** Tank (Infra/DevOps), Neo (Backend/Rename)
**Reviewers:** Morpheus (Architecture), Trinity (Security)

---

## Dependency Order

```
T00 (Neo: M6 rename) ──────────────────────────────────────────────────────────────┐
                                                                                    │
T11 (Morpheus review) ──┐                                                           │
T12 (Trinity review)  ──┤── (all clear) ──────────────────────────────────────────┼─→ IMPLEMENT
                                                                                    │
After T00 + T11 + T12 complete:                                                     │
  Tank stream:  T01 → T02 → T03 → T04 → T05 → T06 → T07 → T08 ◄──────────────────┘
  Neo stream:   T09 → T10

T11 and T12 run in parallel with each other. T00 can run concurrently with T11/T12.
T01 depends on T00 (path references) AND T11 (architecture review).
T06 depends on T00 (service name) AND T12 (strict mode review).
T09 depends on T00 (rename) AND T12 (security review).
```

---

## T00 — M6 Task 0: Rename agent-gateway → agent-execution

**Owner:** Neo
**Depends on:** Ashley approval of Agent Execution Service naming (pre-condition)
**Blocks:** T01, T03, T06, T09 (all tasks that reference paths or service names)

**Description:**
Apply the approved Agent Execution Service rename atomically before any M6 implementation code lands. This is a doc + code + config rename with zero functional change — it does not modify logic, only paths, names, and references.

**Scope of changes:**

1. **Filesystem rename** (do this first):
   - `apps/agent-gateway/` → `apps/agent-execution/`
   - `apps/agent-gateway/python-fastapi-agent-framework/` → `apps/agent-execution/python-fastapi/`
   - `.NET` and `node-placeholder` sub-dirs renamed analogously if present.

2. **Python imports and sys.path:**
   - Any `sys.path.insert(0, "apps/agent-gateway/...")` in test files → `apps/agent-execution/...`
   - Any `from apps.agent_gateway` import patterns updated.

3. **Docker Compose files** (all files):
   - `docker/docker-compose.yml`: service `agent-gateway:` → `agent-execution:`, `context: ../apps/agent-gateway/...` → `../apps/agent-execution/...`
   - `docker/docker-compose.single-tenant.yml`: service key `agent-gateway:` → `agent-execution:`
   - `docker/docker-compose.vendor-shaped.yml`: same
   - `docker/docker-compose.cross-tenant.local.yml`: same
   - `docker/docker-compose.tracing.yml`: same
   - `depends_on` blocks in `bff` service updated.

4. **`docker/README.md`:** All `agent-gateway` service name references updated.

5. **CI / scripts:** Any shell script, Makefile, or CI workflow referencing `apps/agent-gateway/` or `agent-gateway` service name updated.

6. **k8s manifest comments** in `docs/deployment/k8s/agent-gateway-deployment.yaml`: Comment header updated; filename may be renamed to `agent-execution-deployment.yaml` if the Morpheus T11 review recommends it.

7. **Spec and doc references:** Update path references in `.squad/specs/002-aks-entra-agent-id/` key files table (prose only; no functional artifact changes). Update `docs/agent-framework/`, `docs/architecture/`, `docs/identity/`, `docs/apim/` as specified in Morpheus v2 naming proposal (`.squad/decisions/inbox/morpheus-naming-proposal-pre-m6-v2.md` §5).

8. **ADRs:**
   - Create `.squad/architecture/decisions/003-agent-execution-naming.md` (full squad record).
   - Create `docs/adr/0008-agent-execution-naming.md` (public summary).
   - Add `Status: Superseded by ADR 0008` note to `.squad/architecture/decisions/001-agentic-layer-vs-agent-gateway-terminology.md`.
   - Add `Status: Superseded by ADR 0008` note to `docs/adr/0006-agentic-layer-vs-agent-gateway-terminology.md`.

**Acceptance:**
- `apps/agent-execution/` exists; `apps/agent-gateway/` does not exist.
- `docker compose -f docker/docker-compose.yml config --quiet` passes (service name `agent-execution` present).
- `python -m pytest` passes (229+ tests, zero failures).
- `terraform fmt -check -recursive` passes.
- No remaining references to `apps/agent-gateway/` or `agent-gateway` Compose service name in any file outside of historical spec log entries.

**Validation:**
```
python -m pytest
terraform -chdir=infra\terraform fmt -check -recursive
docker compose -f docker\docker-compose.yml config --quiet
docker compose -f docker\docker-compose.yml -f docker\docker-compose.tracing.yml config --quiet
```

---

## T11 — Architecture Review

**Owner:** Morpheus
**Depends on:** Spec 006 spec artifacts complete
**Blocks:** T01–T08 (Tank implementation stream)

**Description:**
Review `design.md` ADRs M6-01 (ACA default), M6-02 (OTLP endpoint swap), and the overall ACA topology, Terraform structure, and APIM wiring design. Confirm or amend before Tank begins implementation.

**Review checklist:**
- [ ] ADR-M6-01: ACA as default deployment path — confirm or amend.
- [ ] ADR-M6-02: OTLP endpoint swap (no code change) — confirm or amend.
- [ ] Terraform `single-tenant-aca` structure — confirm module wiring is sound.
- [ ] APIM backend URL output wiring — confirm the `fqdn` output approach is correct.
- [ ] Container app ingress: confirm external vs internal default (see research Q6).
- [ ] k8s-bootstrap namespace inconsistency (M5 T14 flag) — confirm defer to post-M6 or address in T00 k8s manifest update.
- [ ] Open questions Q1, Q2, Q4, Q6 from `research.md`.

**Acceptance:**
- Morpheus leaves a written decision note in `.progress.md` under "Log".
- Each ADR in `design.md` updated to "Accepted" or "Amended" status.
- Any required design amendments documented before T01 begins.

**Validation:** n/a (review task)

---

## T12 — Security Review

**Owner:** Trinity
**Depends on:** Spec 006 spec artifacts complete
**Blocks:** T06, T09, T10

**Description:**
Review `requirements.md` FR-08 through FR-10 (strict mode, managed identity, no mock in deployed), `design.md` security section, and managed identity ADR-M6-03. Confirm that:

- `AUTH_MODE=strict` enforcement is correctly specified and testable.
- Managed identity strategy (ADR-M6-03) is sound — user-assigned identities, role assignment scope.
- The OBO boundary at managed identity level is correctly separated (BFF: no OBO; Agent Execution Service: OBO; MCP: validate-only).
- `AUTH_MODE=mock` is unconditionally blocked in the deployment overlay.
- No real tenant IDs or secrets are present or could be accidentally introduced by the tasks.
- The `docker-compose.strict-aca.yml` overlay design correctly simulates deployed strict mode.
- NFR-01 (no secrets), NFR-02 (no terraform apply in CI), NFR-05 (public-safe) are implementable.
- Open questions Q3, Q5 from `research.md` are addressed.

**Acceptance:**
- Trinity leaves a written decision note in `.progress.md` under "Log".
- ADR-M6-03 updated to "Accepted" or "Amended" in `design.md`.
- Any security-required changes to requirements or design documented before T06/T09/T10 begin.

**Validation:** n/a (review task)

---

## T01 — Create single-tenant-aca Terraform Environment

**Owner:** Tank
**Depends on:** T00 (path references), T11 (architecture review)
**Blocks:** T03, T04, T05

**Description:**
Create `infra/terraform/environments/single-tenant-aca/` with all five files. Wire modules per the `main.tf` conceptual structure in `design.md`. All variable defaults are placeholders.

**Files to create:**
- `infra/terraform/environments/single-tenant-aca/main.tf`
- `infra/terraform/environments/single-tenant-aca/variables.tf`
- `infra/terraform/environments/single-tenant-aca/outputs.tf`
- `infra/terraform/environments/single-tenant-aca/providers.tf`
- `infra/terraform/environments/single-tenant-aca/terraform.tfvars.example`

**Key requirements (from FR-02):**
- `providers.tf`: azurerm ≥ 3.x, azuread ≥ 2.x. `subscription_id`, `tenant_id` from variables — no inline literals.
- `terraform.tfvars.example`: Only `{tenant-id}`, `{subscription-id}`, `{resource-group}` brace tokens.
- All `default` values in `variables.tf`: empty string `""` or placeholder.

**Note:** Do not add a real `.terraform.lock.hcl` if providers cannot be resolved without credentials. Run `init -backend=false` only.

**Validation:**
```
terraform -chdir=infra\terraform fmt -check -recursive
terraform -chdir=infra\terraform\environments\single-tenant-aca init -backend=false
terraform -chdir=infra\terraform\environments\single-tenant-aca validate
```

---

## T02 — Create app-insights Terraform Module

**Owner:** Tank
**Depends on:** T11 (architecture review)
**Blocks:** T01 (T01 references this module — coordinate ordering)

**Description:**
Create `infra/terraform/modules/app-insights/` with three files per FR-04. Use workspace-based Application Insights (`azurerm_application_insights` with `workspace_id`).

**Files to create:**
- `infra/terraform/modules/app-insights/main.tf`
- `infra/terraform/modules/app-insights/variables.tf`
- `infra/terraform/modules/app-insights/outputs.tf`

**Sensitive outputs:** `instrumentation_key` and `connection_string` must be marked `sensitive = true` in outputs.

**Note:** T02 should be completed before or in parallel with T01 since T01's `main.tf` references this module.

**Validation:**
```
terraform -chdir=infra\terraform fmt -check -recursive
```

---

## T03 — Add Container App Module Resource Body

**Owner:** Tank
**Depends on:** T01, T11
**Blocks:** T05

**Description:**
Replace the `# TODO` placeholder in `infra/terraform/modules/container-app/main.tf` with an `azurerm_container_app` resource block per the design. Update `variables.tf` and `outputs.tf` to add the new variables and outputs required by the resource block.

**Key variables to add:**
- `container_apps_environment_id` (string)
- `image` (string, default: `"mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"`)
- `cpu` (number, default: `0.25`)
- `memory` (string, default: `"0.5Gi"`)
- `managed_identity_id` (string)
- `external_enabled` (bool, default: `false`)
- `otel_endpoint` (string, default: `""`)

**Key outputs to add:**
- `fqdn` — container app FQDN (used by APIM module as `backend_url`)
- `identity_id` — managed identity principal ID

**Hard constraint:** `AUTH_MODE` is hardcoded to `"strict"` as an env var in the container template — it must NOT be a variable to prevent accidental mock deployment.

**Validation:**
```
terraform -chdir=infra\terraform fmt -check -recursive
terraform -chdir=infra\terraform\environments\single-tenant-aca validate
```

---

## T04 — Wire APIM Module for ACA Backend

**Owner:** Tank
**Depends on:** T01, T11
**Blocks:** T07 (final gate)

**Description:**
Update the `apim` or `apim-api` module (whichever is appropriate) to accept a `backend_url` variable that wires the APIM backend to the BFF container app FQDN. This variable is already present in the APIM module if it was scaffolded in M3/M4 — verify and wire if not already wired.

Confirm that:
- The APIM module references the ingress JWT policy XML from `infra/terraform/policies/apim/ingress-validate-user-token.xml`.
- APIM system-assigned managed identity skeleton is present in `main.tf` (an `identity { type = "SystemAssigned" }` block on the `azurerm_api_management` resource).

**Files to check/update:**
- `infra/terraform/modules/apim/main.tf`
- `infra/terraform/modules/apim/variables.tf`
- `infra/terraform/modules/apim-api/main.tf` (if backend_url is here)

**Validation:**
```
terraform -chdir=infra\terraform fmt -check -recursive
terraform -chdir=infra\terraform\environments\single-tenant-aca validate
```

---

## T05 — Wire Managed Identity Assignment per Container App

**Owner:** Tank
**Depends on:** T03
**Blocks:** T07

**Description:**
Confirm that each of the three container app module calls in `single-tenant-aca/main.tf` passes the correct `managed_identity_id` from the corresponding `managed_identity_*` module. Add `azurerm_role_assignment` placeholder blocks (commented out or as `# TODO` with explanation) for the post-M6 role assignments (e.g., Key Vault Secrets User, App Insights Publisher).

Role assignment placeholder format (commented block):
```hcl
# Role assignment — apply post-M6 with live subscription scope
# resource "azurerm_role_assignment" "agent_execution_obo" {
#   scope                = "/subscriptions/{subscription-id}/resourceGroups/{resource-group}"
#   role_definition_name = "Managed Identity Operator"
#   principal_id         = module.managed_identity_agent_execution.principal_id
# }
```

**Validation:**
```
terraform -chdir=infra\terraform fmt -check -recursive
terraform -chdir=infra\terraform\environments\single-tenant-aca validate
```

---

## T06 — Create docker-compose.strict-aca.yml Overlay

**Owner:** Tank
**Depends on:** T00 (service name `agent-execution` must exist in base), T12 (security review)
**Blocks:** T07

**Description:**
Create `docker/docker-compose.strict-aca.yml` per the design schema in `design.md`. All values use `{tenant-id}` and `{region}` placeholders. Add a prominent comment block at the top:

```yaml
# STRICT MODE OVERLAY — for local pre-deployment simulation of deployed AUTH_MODE=strict.
# AUTH_MODE=mock MUST NOT be used in deployed ACA environments.
# Replace {tenant-id} and {region} placeholders before testing against a real tenant.
# This overlay is for local validation only — no real credentials are committed here.
```

**Validation:**
```
docker compose -f docker\docker-compose.yml -f docker\docker-compose.strict-aca.yml config --quiet
```

---

## T07 — CI Validation Gates and No-Secret Scan

**Owner:** Tank
**Depends on:** T01, T02, T03, T04, T05, T06
**Blocks:** T08

**Description:**
Verify that the complete validation command sequence passes in a CI-safe manner (no live credentials). Document the full sequence in `infra/terraform/README.md` and optionally add or update a GitHub Actions workflow for Terraform validation.

**Command sequence to verify and document:**
```
# 1. Format check (entire infra tree)
terraform -chdir=infra\terraform fmt -check -recursive

# 2. ACA environment init + validate
terraform -chdir=infra\terraform\environments\single-tenant-aca init -backend=false
terraform -chdir=infra\terraform\environments\single-tenant-aca validate

# 3. Compose config checks (base + all overlays)
docker compose -f docker\docker-compose.yml config --quiet
docker compose -f docker\docker-compose.yml -f docker\docker-compose.single-tenant.yml config --quiet
docker compose -f docker\docker-compose.yml -f docker\docker-compose.vendor-shaped.yml config --quiet
docker compose -f docker\docker-compose.yml -f docker\docker-compose.cross-tenant.local.yml config --quiet
docker compose -f docker\docker-compose.yml -f docker\docker-compose.tracing.yml config --quiet
docker compose -f docker\docker-compose.yml -f docker\docker-compose.strict-aca.yml config --quiet

# 4. Python tests
python -m pytest

# 5. No-secret scan
# rg -r --include="*.tf" --include="*.yml" --include="*.yaml" --include="*.env*" \
#   "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}" \
#   infra/ docker/ config/ apps/ \
#   | grep -v "00000000-0000-0000-0000-" \
#   | grep -v ".terraform/"
# (no output expected — any match is a failure)
```

**Note:** If a GitHub Actions workflow already exists for Terraform validation, update it. If not, document the sequence in `infra/terraform/README.md` and note that a CI workflow addition is a post-M6 follow-on.

**Validation:**
All commands above exit 0.

---

## T08 — Update Deployment Documentation

**Owner:** Tank
**Depends on:** T07
**Blocks:** none (terminal in Tank stream)

**Description:**
Create `docs/deployment/aca/README.md` with:
1. Overview of the ACA deployment topology (diagram or table).
2. Managed identity model: which service has which identity, what OBO boundary each crosses.
3. Azure Monitor OTLP endpoint swap: explain the env var change from local Jaeger to Azure Monitor.
4. Step-by-step variable substitution guide for `terraform.tfvars.example`.
5. `AUTH_MODE=strict` deployment constraint documented explicitly.
6. Note: "No `terraform apply` is run from this public repository."
7. GitHub OIDC federated identity as the recommended CI/CD auth pattern (documented, not wired).

**File to create:**
- `docs/deployment/aca/README.md`

Mark as "ILLUSTRATIVE REFERENCE ONLY — see `infra/terraform/environments/single-tenant-aca/terraform.tfvars.example` for placeholder substitution guide."

**Validation:** Doc review — spot-check commands and placeholder patterns are correct.

---

## T09 — AUTH_MODE=strict Enforcement Verification

**Owner:** Neo
**Depends on:** T00 (rename, Python paths updated), T12 (security review)
**Blocks:** T10

**Description:**
Verify and test that all three Python FastAPI services (BFF, Agent Execution Service, MCP Protected API) correctly enforce `AUTH_MODE=strict`. If any gap is found, implement the minimal fix.

**Test scenarios to verify (one test per scenario minimum):**

1. **`X-Identity-Lab-Fixture` header is ignored in strict mode** — request with fixture header and no real JWT → 401 (not a mock auth success).
2. **Missing `AUTH_ISSUER` in strict mode → startup error** — service refuses to start without issuer configured.
3. **Missing `AUTH_JWKS_URL` in strict mode → startup error** — service refuses to start without JWKS URL.
4. **Mock token path unreachable in strict mode** — a mock token (fixture-format) must not pass strict validation.

These tests may already exist (M5 covered JWKS strict mode in T09). Verify coverage; add tests only where gaps exist. Do not modify existing passing tests.

**Files to check/update:**
- `apps/bff/python-fastapi/app/config.py` — `AUTH_MODE=strict` startup guard
- `apps/agent-execution/python-fastapi/app/config.py` — same
- `apps/mcp-protected-api/python-fastapi/app/config.py` — same
- `tests/security/` — verify or add tests for the above scenarios

**Validation:**
```
python -m pytest
```

---

## T10 — Azure Monitor OTLP Env Var Documentation

**Owner:** Neo
**Depends on:** T09
**Blocks:** none (terminal in Neo stream)

**Description:**
Add `OTEL_EXPORTER_OTLP_ENDPOINT` placeholder to each service's `config/env/*.env.example` file per FR-07. Also add a comment explaining the local-vs-deployed distinction.

**Comment block to add to each `.env.example`:**
```
# --- Azure Monitor tracing (deployed environments) ---
# For local development: leave OTEL_EXPORTER_OTLP_ENDPOINT unset or set OTEL_SDK_DISABLED=true
# For deployed ACA: set to your Azure Monitor OTLP ingestion endpoint (replace {region})
# This is a config-only swap from the local Jaeger exporter — no code change required.
OTEL_EXPORTER_OTLP_ENDPOINT=https://{region}.otel.monitor.azure.com/v1/traces
```

**Files to update:**
- `config/env/bff.env.example`
- `config/env/agent-execution.env.example` *(renamed from `agent-gateway.env.example` in T00)*
- `config/env/mcp-protected-api.env.example`

**Validation:**
```
python -m pytest
docker compose -f docker\docker-compose.yml config --quiet
```

---

## Summary Table

| ID | Title | Owner | Depends On | Blocks | Validation |
|----|-------|-------|-----------|--------|------------|
| T00 | M6 rename: agent-gateway → agent-execution | Neo | Ashley approval | T01, T06, T09 | pytest, compose config, tf fmt |
| T11 | Architecture review | Morpheus | spec complete | T01–T08 | n/a |
| T12 | Security review | Trinity | spec complete | T06, T09, T10 | n/a |
| T01 | Create single-tenant-aca TF environment | Tank | T00, T11 | T03, T04, T05 | tf fmt, init, validate |
| T02 | Create app-insights TF module | Tank | T11 | T01 | tf fmt |
| T03 | Add container-app module resource body | Tank | T01, T11 | T05 | tf fmt, validate |
| T04 | Wire APIM module for ACA backend | Tank | T01, T11 | T07 | tf fmt, validate |
| T05 | Wire managed identity per container app | Tank | T03 | T07 | tf fmt, validate |
| T06 | Create docker-compose.strict-aca.yml | Tank | T00, T12 | T07 | compose config |
| T07 | CI validation gates + no-secret scan | Tank | T01–T06 | T08 | all validation commands |
| T08 | Update ACA deployment documentation | Tank | T07 | — | doc review |
| T09 | AUTH_MODE=strict verification (Python) | Neo | T00, T12 | T10 | pytest |
| T10 | Azure Monitor OTLP env var documentation | Neo | T09 | — | pytest, compose config |

---

## M6 Gate Criteria

All of the following must be true before M6 is marked complete:

- [ ] T00 complete — rename applied, all tests pass (229+), compose config passes, tf fmt passes
- [ ] T11 complete — Morpheus architecture sign-off with ADR decisions recorded in `.progress.md`
- [ ] T12 complete — Trinity security sign-off recorded in `.progress.md`
- [ ] `infra/terraform/environments/single-tenant-aca/` exists and `terraform validate` passes
- [ ] `infra/terraform/modules/app-insights/` exists and `terraform fmt -check` passes
- [ ] `infra/terraform/modules/container-app/main.tf` has a real resource body (not `# TODO`)
- [ ] `docker/docker-compose.strict-aca.yml` exists and `config --quiet` passes
- [ ] `python -m pytest` passes (229+ tests, no regressions)
- [ ] No real tenant IDs, subscription IDs, client IDs, secrets, or tokens committed
- [ ] `AUTH_MODE=strict` verified in all three Python services
- [ ] `OTEL_EXPORTER_OTLP_ENDPOINT` documented in all three `.env.example` files
- [ ] `docs/deployment/aca/README.md` exists with correct placeholder guidance
- [ ] AKS environment `terraform validate` still passes (NFR-06)
