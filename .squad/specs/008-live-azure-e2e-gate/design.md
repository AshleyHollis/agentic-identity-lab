# Spec 008 — Design

**Spec:** 008-live-azure-e2e-gate  
**Milestone:** M8  
**Updated:** 2026-05-10  
**Note:** Planning artifact only. No live Azure deployment or workflow implementation is performed by this spec.

---

## Architecture Overview

### Working live topology

```text
GitHub Actions
  |
  +--> m8-validate.yml            -> public-safe validation and policy scans only
  +--> m8-deploy.yml              -> protected deploy for IaC/config/image/app rollout
  +--> m8-smoke-trace.yml         -> protected smoke + Azure Monitor verification
  +--> m8-nightly-shutdown.yml    -> scheduled/manual cost-control actions
  +--> m8-start-resume.yml        -> optional manual bring-up workflow
  +--> m8-destroy.yml             -> optional manual full teardown (non-blocking enhancement)
  |
  v
Browser smoke driver (recommended: SPA/public client)
  -> APIM
  -> BFF
  -> Agent Execution Service
  -> MCP Protected API
  -> Azure Monitor / Application Insights verification
```

### Service path under test

```text
browser client
  -> APIM (delegated token preserved)
  -> BFF (validates inbound user token only)
  -> Agent Execution Service (only OBO boundary)
  -> MCP Protected API (accepts only downstream token)
```

### Naming boundary

- **Agent Execution Service** = the service under test in ACA/AKS that hosts agent execution.
- **AKS Agent Gateway / agentgateway.dev** = optional AKS-side gateway/proxy pattern from earlier milestones.
- M8 default path is **ACA + APIM** from Spec 006, not AKS Agent Gateway.

---

## Workflow Topology

| Workflow | Trigger | Protection | Purpose | Required guards |
|---|---|---|---|---|
| `m8-validate.yml` | `pull_request`, optional `workflow_dispatch` | public-safe only | lint/test/Terraform validate/policy scans | never requests live Azure approval or smoke |
| `m8-deploy.yml` | `workflow_dispatch` | protected GitHub Environment | IaC + config + image/app deployment | Azure OIDC, approval before apply, smoke only when `LIVE_AZURE_TESTS=true` |
| `m8-smoke-trace.yml` | `workflow_dispatch` or post-deploy call | protected GitHub Environment | browser smoke and trace verification | `LIVE_AZURE_TESTS=true`, delegated-flow only |
| `m8-nightly-shutdown.yml` | `schedule`, optional `workflow_dispatch` | dedicated scoped shutdown environment | nightly scale-down/stop/report | idempotent, non-destructive by default, dedicated shutdown identity only |
| `m8-start-resume.yml` | `workflow_dispatch`, optional schedule | dedicated scoped shutdown environment | bring scaled-down resources back online | idempotent, ready-state checks, dedicated shutdown identity only |
| `m8-destroy.yml` | `workflow_dispatch` | manually approved protected environment | optional full teardown enhancement | destructive operations require explicit approval; not required for M8 closeout unless T06 is explicitly implemented |

**Destroy-path scope note:** M8's required cost-control path is nightly stop/scale-down plus manual start/resume. `m8-destroy.yml` is optional and non-blocking for M8 closeout unless the team explicitly chooses to implement T06.

**Binding protection rule:** Deploy/apply and smoke workflows MUST use protected GitHub Environments with required reviewers. Public `push`/`pull_request` CI MUST remain validation-only and MUST NOT bypass these approval boundaries.

### Deploy workflow stages

The protected deploy workflow MUST follow this stage order:

1. validate inputs and confirm environment selection is placeholder-safe in code, real only in protected env settings
2. authenticate to Azure with OIDC
3. build/publish images if the deployment path uses ACR
4. create a Terraform plan artifact
5. require protected-environment approval before apply/deploy
6. apply IaC and configuration
7. deploy/update application containers
8. optionally invoke smoke/trace verification only when `LIVE_AZURE_TESTS=true`

### PR validation content

The PR validation workflow is intentionally separate from protected deployment and MUST contain:

- repo tests and lint/validation already used today
- Terraform formatting/init/validate
- workflow-policy checks for accidental live steps in public CI
- secret/identifier scans
- client token-handling checks where automation exists

No PR validation job may request `id-token: write`.

---

## Protected Environment and Identity Model

### GitHub permissions model

| Job type | Minimum GitHub permissions | Azure auth position |
|---|---|---|
| Public validation | `contents: read` | no live Azure auth |
| Deploy/apply | `contents: read`, `id-token: write` | OIDC federated identity |
| Smoke/trace | `contents: read`, `id-token: write` only if Azure verification requires it | protected environment only |
| Nightly shutdown/start-resume | `contents: read`, `id-token: write` | dedicated low-privilege shutdown principal (or equivalently constrained identity) required |

### Azure identity model

- Purpose-scoped identities are mandatory. Deploy/apply, smoke verification, and shutdown/start-resume MUST use separate OIDC principals, or an equivalently constrained model with explicit documented scope and denied capabilities.
- Shutdown/start-resume identity scope MUST be restricted to explicit lab stop/start/scale actions and MUST NOT have permissions for broad IaC deploy/apply/destroy operations.
- Scope RBAC to the dedicated lab resource group or narrower.
- Routine workflow principals MUST NOT use subscription-wide Owner access.
- If bootstrap RBAC changes are needed, treat them as a separate reviewed path, not part of normal M8 deploy.

---

## Resource Lifecycle Strategy

| Resource type | Default action | Alternate / notes | Reporting expectation |
|---|---|---|---|
| ACA-hosted BFF / Agent Execution / MCP apps | scale to zero / `minReplicas=0` nightly | keep max scale low for lab | report `scaled_to_zero` or `left_running` |
| APIM | leave running if SKU cannot stop cheaply | stop/start only when target tier supports it | report `stopped`, `left_running`, or `manual_follow_up_required` |
| Log Analytics | leave running | reduce retention and cap ingestion | report retention/cap posture, not stop |
| App Insights | leave running | align with low-retention / sampling strategy | report telemetry policy posture |
| ACR (if used) | leave running | retention cleanup for old images/tags | report cleanup policy and current mode |
| Optional AKS / Agent Gateway path | future/optional stop/start only if path is activated | not part of default M8 target | report as optional/future |
| Managed identities / role assignments | leave in place | control-plane objects only | report unchanged |
| Resource group / full environment | no nightly destroy by default | manual destroy/recreate workflow only | report `destroy_only` capability |

**Design rule:** every nightly run must emit a summary that classifies each targeted resource as `stopped`, `scaled_to_zero`, `left_running`, `destroy_only`, or `manual_follow_up_required`.

---

## Smoke and Trace Verification Design

### Canonical smoke driver

Use the M7 SPA/public client as the default automated browser driver because it is the easiest delegated-browser path to automate without SharePoint tenant coupling.

### Smoke assertions

A passing M8 smoke run should prove:

1. a real delegated browser sign-in succeeds
2. the request enters through APIM
3. APIM preserves the inbound `Authorization` header to the BFF
4. BFF validates the delegated token and forwards work without performing downstream OBO
5. Agent Execution Service performs the OBO exchange for MCP access
6. MCP Protected API rejects the original user token and accepts the proper downstream token
7. Azure Monitor / Application Insights shows correlated telemetry for the run

### Binding telemetry/KQL contract (required for implementation)

The smoke/trace implementation MUST ship a versioned KQL contract (saved queries or `.kql` files) and MUST fail the workflow if any contract step fails. This contract is implementation-binding and not illustrative.

**Required query surfaces (all must be covered):**

1. **requests:** `requests` and/or `AppRequests`
2. **dependencies:** `dependencies` and/or `AppDependencies`
3. **traces:** `traces` and/or `AppTraces`
4. **logs:** `AppTraces` and/or workspace log tables used by the environment (for example `ContainerAppConsoleLogs_CL`)

**Environment parameterization (public-safe):**

- lookback window (default example: `30m`)
- role/service filter list (`apim`, `bff`, `agent-execution`, `mcp-protected-api`)
- table profile selector (classic App Insights tables vs workspace-based tables)
- optional workspace/app selector supplied only at runtime in protected environments

### Positive chain query contract (required)

```kusto
let lookback = 30m;
let role_names = dynamic(["apim","bff","agent-execution","mcp-protected-api"]);
let req = union isfuzzy=true requests, AppRequests
    | where timestamp > ago(lookback)
    | where cloud_RoleName in (role_names)
    | project timestamp, tableName="requests", cloud_RoleName, operation_Id, operation_ParentId, name, resultCode;
let dep = union isfuzzy=true dependencies, AppDependencies
    | where timestamp > ago(lookback)
    | where cloud_RoleName in (role_names)
    | project timestamp, tableName="dependencies", cloud_RoleName, operation_Id, operation_ParentId, name, resultCode;
let trc = union isfuzzy=true traces, AppTraces
    | where timestamp > ago(lookback)
    | where cloud_RoleName in (role_names)
    | project timestamp, tableName="traces", cloud_RoleName, operation_Id, operation_ParentId, name, resultCode;
union req, dep, trc
| order by timestamp asc
```

Pass condition: correlated `operation_Id`/parent chain evidence exists across APIM -> BFF -> Agent Execution Service -> MCP for the smoke window.

### Negative leakage query contract (required)

```kusto
let lookback = 30m;
let role_names = dynamic(["apim","bff","agent-execution","mcp-protected-api"]);
let forbidden = dynamic([
  "authorization","bearer ","eyj","cookie","set-cookie","access_token","refresh_token","id_token",
  "\"oid\"","\"sub\"","\"email\"","\"upn\"","\"preferred_username\"","tracestate"
]);
let req = union isfuzzy=true requests, AppRequests
    | where timestamp > ago(lookback) and cloud_RoleName in (role_names)
    | extend signal="requests", payload=tostring(pack_all());
let dep = union isfuzzy=true dependencies, AppDependencies
    | where timestamp > ago(lookback) and cloud_RoleName in (role_names)
    | extend signal="dependencies", payload=tostring(pack_all());
let trc = union isfuzzy=true traces, AppTraces
    | where timestamp > ago(lookback) and cloud_RoleName in (role_names)
    | extend signal="traces", payload=tostring(pack_all());
let logs = union isfuzzy=true AppTraces, ContainerAppConsoleLogs_CL
    | where timestamp > ago(lookback)
    | extend signal="logs", payload=tostring(pack_all());
union req, dep, trc, logs
| where tolower(payload) has_any (forbidden)
| project timestamp, signal, cloud_RoleName, operation_Id, payload
```

Fail condition: any returned row. The pipeline MUST hard-fail if leakage rows are found.

### Required leakage-ban keys and patterns

The negative contract MUST explicitly fail on evidence of:

- raw tokens/JWT-like values (`Bearer`, `eyJ`, auth/token/cookie material)
- `Authorization` header values (not key-only presence)
- claim keys/values: `oid`, `sub`, `email`, `upn`, `preferred_username`
- unsafe `tracestate` content (presence or user/token-bearing values)

### Required implementation artifacts (future implementation, not live querying in this spec revision)

- saved KQL files for positive and negative contracts (versioned in repo)
- a script/runner that executes the saved KQL contract with environment-supplied parameters
- a CI/static test that validates contract coverage includes requests/dependencies/traces/logs and all forbidden key patterns
- workflow wiring so smoke/deploy trace-verification jobs fail on contract failure

### Telemetry safety rules

- Never emit `Authorization`, `Cookie`, `Set-Cookie`, or token-bearing query values to logs, traces, or workflow summaries.
- Never emit PII claim values such as `oid`, `sub`, `email`, `upn`, `preferred_username`, `name`, `given_name`, or `family_name`.
- Treat raw `tracestate` as unsafe unless it is explicitly scrubbed.
- Keep existing sanitization and strict-mode expectations intact.

---

## Required Validation Gates

Before M8 implementation can be considered complete, the workflow family must include or preserve:

1. workflow policy scan for accidental live steps in public CI
2. secret / identifier scan
3. client token-handling scan
4. delegated-auth negative tests
5. OBO-boundary tests
6. telemetry leakage tests with KQL/workbook support
7. artifact hygiene checks for screenshots/HAR/traces/log uploads

These validation gates are part of the planned architecture, not optional post-hoc hardening.

---

## ADR-M8-01: Opt-in live gate boundary

**Status:** Ready for review

### Options

- **Option A (RECOMMENDED):** Live Azure deployment and smoke workflows are `workflow_dispatch` / protected schedule only and never default public CI.
- Option B: Live workflows run on `push` to `main` when secrets exist.

### Working decision

Option A. This keeps the repo public-safe and prevents accidental live spend.

---

## ADR-M8-02: Pipeline-first deployment model

**Status:** Ready for review

### Options

- **Option A (RECOMMENDED):** GitHub Actions performs build/publish, IaC apply, config rollout, and smoke orchestration via protected environment + OIDC.
- Option B: Manual local CLI is primary; GitHub Actions is secondary.

### Working decision

Option A. It improves repeatability, audibility, and contributor clarity.

---

## ADR-M8-03: Low-cost operating model

**Status:** Ready for review

### Options

- **Option A (RECOMMENDED):** Manual start/resume + nightly stop/scale-down + optional manual destroy for non-stoppable expensive resources.
- Option B: Always-on lab environment.
- Option C: Destroy/recreate everything every night.

### Working decision

Option A. It balances contributor convenience with meaningful cost control and avoids forcing full redeploy for every morning use.

---

## ADR-M8-04: Live trace verification and telemetry safety

**Status:** Ready for review

### Options

- **Option A (RECOMMENDED):** Azure Monitor / Application Insights verification with explicit no-token/no-PII telemetry constraints and saved positive/negative KQL recipe.
- Option B: Rely on application logs only.

### Working decision

Option A. M8 exists partly to prove live observability, not just functional success.

---

## Environment / Naming Examples

To avoid blocking on private naming decisions, the spec uses example names only:

- GitHub Environment: `lab-live-azure`
- Workflow input environment slug: `agentidlab-live`
- Resource prefix example: `agentidlab-live-{region}`

These are descriptive placeholders, not committed real environment identifiers.
