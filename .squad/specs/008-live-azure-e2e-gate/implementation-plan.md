# Spec 008 — M8 Implementation Kickoff Package (T00)

**Spec:** 008-live-azure-e2e-gate  
**Milestone:** M8  
**Owner:** Tank (Azure / Terraform / DevOps)  
**Status:** T00 complete — implementation contract finalized  
**Updated:** 2026-05-10

---

## 1) Workflow contract (final names, boundaries, handoffs)

M8 workflow set is fixed to the following names and responsibilities:

| Workflow | Trigger | Public/Protected | Core responsibility | Primary downstream handoff |
|---|---|---|---|---|
| `m8-validate.yml` | `pull_request`, optional `workflow_dispatch` | Public-safe | Validation only (tests, Terraform validate, policy scans) | T02 baseline and policy gate evidence |
| `m8-deploy.yml` | `workflow_dispatch` | Protected Environment | IaC plan/apply + app/config/image rollout | Deploy outputs/metadata to smoke workflow |
| `m8-smoke-trace.yml` | `workflow_dispatch` or deploy-call | Protected Environment | Live delegated smoke + telemetry contract verification | T07/T08 security and trace evidence |
| `m8-nightly-shutdown.yml` | `schedule`, optional `workflow_dispatch` | Protected Environment (shutdown scope) | Idempotent nightly stop/scale-down and action summary | T05 cost-control reporting |
| `m8-start-resume.yml` | `workflow_dispatch`, optional schedule | Protected Environment (shutdown scope) | Idempotent bring-up from scaled/stopped state | T04 readiness confirmation |
| `m8-destroy.yml` (optional) | `workflow_dispatch` only | Protected Environment + explicit approval | Manual destroy/recreate only when explicitly enabled | Optional T06 + T09 destroy guidance |

**Binding rules**
- Public CI remains validation-only; no live Azure deploy/apply/destroy/auth.
- `LIVE_AZURE_TESTS=true` is only valid in protected live workflows (deploy smoke stage and smoke-trace workflow).
- ACA is the default deployment target; AKS/Agent Gateway remains optional/future.

---

## 2) Job boundary contract by workflow

### `m8-validate.yml` (T02)
1. `repo-validation` — existing test/lint/compose/terraform validate checks.
2. `policy-guardrails` — fail on live behavior in public workflows, non-placeholder IDs, or unsafe defaults.
3. `publish-validation-summary` — non-secret summary artifact/log only.

**Outputs (non-secret):**
- `validation_passed` (`true|false`)
- `policy_guardrails_passed` (`true|false`)

### `m8-deploy.yml` (T03)
1. `preflight` — input validation and run contract checks.
2. `azure-auth-deploy` — OIDC login with deploy identity.
3. `build-publish` — optional ACR image build/push path.
4. `terraform-plan` — plan artifact creation.
5. `protected-apply` — environment-gated apply/deploy stage.
6. `deploy-summary` — emit non-secret deploy metadata for smoke handoff.
7. `invoke-smoke` (conditional) — only if `live_azure_tests == 'true'`.

**Inputs:**
- `environment_slug` (placeholder-like slug, e.g. `agentidlab-live`)
- `live_azure_tests` (default `false`)
- `run_apply` (default `true`)
- `image_tag` (optional)

**Outputs (non-secret):**
- `deploy_status`
- `deployment_label`
- `resource_group_placeholder`
- `smoke_ready` (`true|false`)

### `m8-smoke-trace.yml` (T07/T08)
1. `preflight-smoke` — enforce protected env + `LIVE_AZURE_TESTS=true`.
2. `azure-auth-smoke` — OIDC login with smoke identity.
3. `browser-smoke` — canonical SPA delegated path run.
4. `trace-contract` — run positive+negative KQL contract checks.
5. `smoke-summary` — publish sanitized pass/fail and trace-check status.

**Inputs:**
- `environment_slug`
- `deployment_label` (optional, from deploy workflow)
- `live_azure_tests` (must be `true`)
- `kql_lookback` (default `30m`)

**Outputs (non-secret):**
- `smoke_passed`
- `trace_contract_passed`
- `leakage_findings_count`

### `m8-nightly-shutdown.yml` (T05)
1. `preflight-shutdown` — target scoping and idempotency checks.
2. `azure-auth-shutdown` — OIDC login with shutdown identity.
3. `shutdown-actions` — scale-to-zero/stop supported resources.
4. `shutdown-report` — classification summary by resource type.

**Outputs (non-secret):**
- `shutdown_status`
- `resource_action_summary`

### `m8-start-resume.yml` (T04)
1. `preflight-start` — target scoping and current-state check.
2. `azure-auth-shutdown-scope` — same low-privilege lifecycle identity scope.
3. `start-actions` — resume/start/scale-up actions.
4. `start-report` — readiness + action summary.

**Outputs (non-secret):**
- `resume_status`
- `ready_state_summary`

### `m8-destroy.yml` (optional T06)
1. `preflight-destroy` — explicit manual intent confirmation.
2. `azure-auth-deploy-scope` — approved identity for destructive operations.
3. `destroy-apply` — destroy/recreate execution.
4. `destroy-report` — explicit destruction and recovery notes.

**Outputs (non-secret):**
- `destroy_status`
- `recreate_required`

---

## 3) Workflow dependency and handoff contract (T00 → downstream)

| Upstream | Handoff artifact/contract | Consumed by |
|---|---|---|
| T00 kickoff package | This file defines names/jobs/inputs/outputs/resource model/OIDC contract | T01, T02, T04, T05, T07, T08 |
| `m8-validate.yml` | Validation + policy gate status | T02 gate for deploy readiness |
| `m8-deploy.yml` | Deploy metadata (`deployment_label`, smoke-ready state) | T03 -> T07 smoke/trace |
| `m8-smoke-trace.yml` | Smoke + telemetry contract result | T07/T08 acceptance, T13/T14 review evidence |
| `m8-nightly-shutdown.yml` | Resource lifecycle action summary | T05 and T09 cost documentation |
| `m8-start-resume.yml` | Ready-state confirmation | T04 and operator guidance in T09 |
| `m8-destroy.yml` (optional) | Destroy/recreate evidence and boundary notes | Optional T06 and conditional T09 addendum |

---

## 4) Resource lifecycle matrix (binding for M8 docs/workflows)

| Resource type | Deploy/update | Start/resume | Nightly shutdown stop/scale-down | Smoke/trace expectation | Destroy/recreate | Notes |
|---|---|---|---|---|---|---|
| ACA apps (BFF, Agent Execution, MCP) | Deploy/update via IaC + app rollout | Scale from zero/min baseline | Set `minReplicas=0` (or equivalent) nightly | Full service chain required | Optional/manual only | Default M8 runtime target |
| APIM | Deploy/update config via protected pipeline | Start only if tier supports stop/start | Stop when supported; else leave running and report | Must show ingress hop in trace chain | Optional/manual only | Tier-dependent stoppability |
| Log Analytics Workspace | Provision/update via IaC | N/A | No stop; manage retention/caps | Query source for trace contract | Destroy only via manual path | Control cost via retention/cap, not stop |
| App Insights (workspace-based) | Provision/update via IaC | N/A | No stop; keep running with low-cost posture | Required for correlation + leakage checks | Destroy only via manual path | Enforce no-token/no-PII telemetry |
| ACR (if used) | Build/push/tag management | N/A | Not stoppable; retention cleanup | Supports deploy image provenance | Destroy optional/manual | Use cleanup policy for stale tags |
| Optional AKS / Agent Gateway (future path) | Optional/future only | Optional start path if enabled | Optional stop path if enabled | Optional/future trace node | Optional/manual | Must remain explicitly distinct from Agent Execution Service |
| Managed identities / RBAC bindings | Managed in protected provisioning path | N/A | No nightly change | Enables OIDC auth model | Destroy only if environment destroyed | Keep least privilege and purpose scope |

**Required nightly reporting classes:** `stopped`, `scaled_to_zero`, `left_running`, `destroy_only`, `manual_follow_up_required`.

---

## 5) Protected GitHub Environment + OIDC contract (high level)

### Protected environment boundary
- Live deploy/smoke/start/shutdown/destroy workflows run only in protected GitHub Environments with required reviewers.
- Public CI workflows must never request protected approvals, Azure live auth, or live test execution.

### Purpose-scoped identities (least privilege)
- **Deploy identity:** deploy/apply/update scope only; no broad subscription Owner usage.
- **Smoke identity:** only rights needed for smoke execution and telemetry query verification.
- **Shutdown/start-resume identity:** explicit stop/start/scale scope only; cannot perform broad deploy/apply/destroy.
- Equivalent constrained models are acceptable only if they enforce the same denied capabilities.

### `LIVE_AZURE_TESTS` contract
- Default remains false/unset in public CI.
- `LIVE_AZURE_TESTS=true` is required for live smoke steps and only permitted in protected live workflows.

---

## 6) Public-safe placeholders for workflow variables and secrets

No live IDs or secrets are committed. Use placeholders only in repo examples.

### Environment variables (non-secret identifiers; placeholders only)
- `AZURE_TENANT_ID=<tenant-guid-placeholder>`
- `AZURE_SUBSCRIPTION_ID=<subscription-guid-placeholder>`
- `AZURE_RESOURCE_GROUP=<rg-name-placeholder>`
- `AZURE_LOCATION=<azure-region-placeholder>`
- `ACA_ENVIRONMENT_NAME=<aca-env-placeholder>`
- `APIM_SERVICE_NAME=<apim-name-placeholder>`
- `LOG_ANALYTICS_WORKSPACE_ID=<workspace-id-placeholder>`
- `APPLICATIONINSIGHTS_RESOURCE_ID=<appinsights-id-placeholder>`
- `LIVE_AZURE_TESTS=false` (default in public CI)

### Secrets (protected GitHub Environment only; placeholders only)
- `AZURE_CLIENT_ID_DEPLOY=<client-id-placeholder>`
- `AZURE_CLIENT_ID_SMOKE=<client-id-placeholder>`
- `AZURE_CLIENT_ID_SHUTDOWN=<client-id-placeholder>`
- `AZURE_TENANT_ID=<tenant-guid-placeholder>`
- `AZURE_SUBSCRIPTION_ID=<subscription-guid-placeholder>`
- `M8_TEST_USER_USERNAME=<test-user-placeholder>` (if automated browser sign-in is approved)
- `M8_TEST_USER_PASSWORD=<test-password-placeholder>` (if automated browser sign-in is approved)

### Optional inputs for workflows
- `environment_slug=agentidlab-live`
- `live_azure_tests=false`
- `run_apply=true`
- `image_tag=<image-tag-placeholder>`
- `kql_lookback=30m`

---

## 7) Downstream execution order after T00

Required path (unchanged):
`T00 -> T01 -> T02 -> T03 -> T04 -> T05 -> T07 -> T08 -> T09 -> T13 -> T14 -> T15`

Optional branch:
`T01 -> T06` (non-blocking unless explicitly implemented)

T00 is complete when this contract is the implementation source of truth for T01–T05/T07/T08.
