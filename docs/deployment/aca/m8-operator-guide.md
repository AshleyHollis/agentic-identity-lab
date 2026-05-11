# M8 Live Operations Operator Guide (ACA default)

This runbook documents Spec 008 / T09 operations for the protected live lab path.

## Safety and scope

- ACA is the default runtime target.
- Public CI stays validation-only; do not run live deploy/smoke/shutdown from `push` or `pull_request`.
- Live workflows run only from protected GitHub Environments with required reviewers.
- Use OIDC + managed identity placeholders only; do not commit real IDs, tenant values, tokens, or secrets.

## Protected workflow sequence

1. **Deploy/update**: `.github/workflows/m8-deploy-live.yml`
   - `workflow_dispatch` only, protected environment `lab-live-azure-deploy`.
   - Smoke is opt-in and gated by `live_azure_tests=true`.
2. **Start/resume**: `.github/workflows/m8-start-resume.yml`
   - Uses lifecycle identity in `lab-live-azure-ops`.
   - Idempotently restores ACA `minReplicas` from `0` to `1`.
3. **Smoke + trace**: `.github/workflows/m8-smoke-trace.yml`
   - Enforces `live_azure_tests=true`.
   - Runs static harness + KQL contract checks, then optional protected live verification.
4. **Nightly shutdown**: `.github/workflows/m8-nightly-shutdown.yml`
   - Scheduled/manual non-destructive scale-down posture.
   - Emits `stopped`, `scaled_to_zero`, `left_running`, `destroy_only`, `manual_follow_up_required`.

## RBAC and identity boundaries (binding)

- Deploy and smoke identities must be separate.
- Lifecycle identity is stop/start/scale focused.
- Lifecycle identity must not perform broad deploy/apply/destroy.
- Identity scope must be scoped to the lab resource group (or narrower), not subscription-wide Owner.
- Protected environments:
  - `lab-live-azure-deploy` -> `AZURE_CLIENT_ID_DEPLOY`
  - `lab-live-azure-smoke` -> `AZURE_CLIENT_ID_SMOKE`
  - `lab-live-azure-ops` -> `AZURE_CLIENT_ID_SHUTDOWN`

## Cost model by resource type

| Resource type | Nightly behavior | Billing expectation |
|---|---|---|
| ACA apps (BFF, Agent Execution, MCP) | scale to zero (`minReplicas=0`) | Compute can drop near zero when idle; control-plane/log costs can remain |
| APIM | left running by default; tier-specific stop/start only when explicitly supported | Often still billable even when traffic is low; classify explicitly in summary |
| Log Analytics workspace | left running | Billable by ingestion + retention |
| App Insights | left running | Billable by telemetry ingestion/retention |
| ACR (if used) | left running; apply image/tag retention hygiene | Registry storage remains billable |
| Managed identities / role assignments | left running | Control-plane objects; minimal direct runtime cost |
| Optional AKS / Agent Gateway path | optional/future only; no default M8 shutdown action | If enabled later, node/control-plane costs can remain unless explicitly stopped |
| Resource group/environment | no nightly delete | Destroy/recreate only in optional manual T06 path |

## What stays running vs scales to zero

- **Scales to zero**: ACA app replicas via nightly shutdown workflow.
- **Usually stays running/billable**: APIM (tier-dependent), Log Analytics, App Insights, ACR, identities/RBAC bindings.
- **Not in scheduled path**: destructive delete operations.

## Optional destroy/recreate path (T06, not implemented by default)

If T06 is later implemented:

- Keep it manual-only with explicit approval.
- Use separate destructive scope and recovery documentation.
- Treat as `destroy_only` in operator summaries.
- Expect redeploy/reconfiguration and possible data/config loss unless backups/state are handled outside this repo.

## Safe smoke/trace invocation and leakage checks

### Public-safe static validation (no live Azure)

```bash
python tools/ci/public_safe_validation.py
python tools/telemetry/validate_m8_kql_contract.py
python tools/ci/m8_smoke_trace_contract.py validate --workflow-file .github/workflows/m8-smoke-trace.yml --positive-kql tools/telemetry/kql/m8-positive-chain.kql --negative-kql tools/telemetry/kql/m8-negative-leakage.kql
```

### Protected live smoke (operator-approved only)

- Trigger `m8-smoke-trace.yml` with:
  - `live_azure_tests=true`
  - `run_live_azure_checks=true` only when live checks are explicitly approved.
  - `browser_transport=playwright` (default), `agent-browser` (accepted-risk), or `manual-artifact` (human MFA + redacted artifact)
- Keep artifacts sanitized; do not upload token-bearing HAR/trace/log files.

### Telemetry privacy rules

- Never print or persist `Authorization`, `Cookie`, `Set-Cookie`, raw JWTs, or token-like strings.
- Never log PII claims (`oid`, `sub`, `email`, `upn`, `preferred_username`).
- Treat raw `tracestate` as unsafe unless scrubbed.
- Negative KQL (`m8-negative-leakage.kql`) must return zero rows; any row is a failure.

## M9 external setup checklist (unblocks Spec 009 T01/T02)

### 1) Create protected GitHub Environments and reviewer gates

- `lab-live-azure-deploy`
- `lab-live-azure-smoke`
- `lab-live-azure-ops`

Status (Spec 009, 2026-05-10): environment shells exist in `AshleyHollis/agentic-identity-lab`; reviewer gates are configured on all three environments for one-human lab operation (`required_reviewers` configured, `prevent_self_review=false`, `wait_timer=0`).

Required reviewers for each environment:

- `Tank`
- `Trinity`
- `Morpheus`

### 2) Add environment-scoped placeholders only (no real values in repo/logs)

Secrets:

- `AZURE_CLIENT_ID_DEPLOY`
- `AZURE_CLIENT_ID_SMOKE`
- `AZURE_CLIENT_ID_SHUTDOWN`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`
- `M9_PLAYWRIGHT_CHAT_URL` (required for `playwright` and `agent-browser` transports)
- `M9_PLAYWRIGHT_ACCESS_TOKEN` (required for `playwright`; optional for `agent-browser` and `manual-artifact`)
- `M9_AGENT_BROWSER_COMMAND` (required for `agent-browser` transport)
- `LIVE_BFF_OBO_CLIENT_SECRET` (BFF confidential client secret for OBO to Agent Execution Service)
- `LIVE_AGENT_EXECUTION_OBO_CLIENT_SECRET` (Agent Execution Service confidential client secret for OBO to MCP)
- `APPLICATIONINSIGHTS_CONNECTION_STRING` (or approved managed identity equivalent)
- `APIM_SUBSCRIPTION_KEY` (only if route requires it)

Variables:

- `AZURE_LOCATION`
- `AZURE_RESOURCE_GROUP_NAME`
- `AZURE_APIM_NAME`
- `AZURE_CONTAINER_APP_ENV_NAME`
- `AZURE_CONTAINER_REGISTRY_NAME`
- `LIVE_APIM_BASE_URL`
- `LIVE_READINESS_URL`
- `LIVE_SMOKE_CLIENT_ID`
- `LIVE_AUTHORITY_HOST`
- `LIVE_SMOKE_SCOPES`
- `LIVE_BFF_AUDIENCE`
- `LIVE_AGENT_EXECUTION_AUDIENCE`
- `LIVE_MCP_AUDIENCE`
- `AZURE_RESOURCE_GROUP`
- `M9_BROWSER_TRANSPORT`
- `M9_BROWSER_EVIDENCE_JSON` (required for `manual-artifact` transport)
- `M9_AGENT_BROWSER_TIMEOUT_SECONDS` (optional for `agent-browser` transport)
- `APIM_RESOURCE_GROUP`
- `ACA_APP_NAMES`
- `APIM_SERVICE_NAME`
- `APIM_STOP_SUPPORTED`
- `M8_READINESS_URL`

### 3) Configure Entra federated credentials (placeholder subject contract)

- Deploy identity subject: `repo:<ORG_OR_USER>/<REPO>:environment:lab-live-azure-deploy`
- Smoke identity subject: `repo:<ORG_OR_USER>/<REPO>:environment:lab-live-azure-smoke`
- Lifecycle identity subject: `repo:<ORG_OR_USER>/<REPO>:environment:lab-live-azure-ops`
- Audience: `api://AzureADTokenExchange`

Lifecycle identity scope must remain stop/start/scale only (no deploy/apply/destroy/delete).

### 4) Validation sequence (zero-mutation first)

1. `python tools\ci\m9_github_environment_check.py --repo <ORG_OR_USER>/<REPO> --mode zero-mutation`
2. `python tools\ci\m9_github_environment_check.py --repo <ORG_OR_USER>/<REPO> --mode lifecycle-runtime`
3. `python tools\ci\m9_github_environment_check.py --repo <ORG_OR_USER>/<REPO> --mode smoke-runtime`
4. `python tools\ci\public_safe_validation.py`
5. `python tools\telemetry\validate_m8_kql_contract.py`
6. `python tools\ci\m8_browser_smoke_harness.py --mode static`
7. `python tools\ci\m8_smoke_trace_contract.py validate --workflow-file .github\workflows\m8-smoke-trace.yml --positive-kql tools\telemetry\kql\m8-positive-chain.kql --negative-kql tools\telemetry\kql\m8-negative-leakage.kql`
8. Dispatch `.github\workflows\m8-live-oidc-contract.yml` (read-only checks only)
9. Dispatch `.github\workflows\m8-deploy-live.yml` with:
   - `run_apply=false`
   - `run_config_rollout=false`
   - `run_app_rollout=false`
   - `execute_live_mutations=false`
   - `live_azure_tests=false`

### 5) Strict delegated Entra bootstrap + consent (run in protected deploy boundary)

- `m8-deploy-live.yml` now runs `tools/ci/m9_entra_app_bootstrap.py` before Terraform apply.
- The bootstrap idempotently ensures app registrations/scopes for:
  - BFF resource API
  - Agent Execution Service resource API
  - MCP resource API
  - Smoke public client app
- It writes real `api://<client-id>` audiences/scopes into `live.auto.tfvars` and pre-authorizes:
  - smoke client -> BFF scope
  - BFF -> Agent delegated scopes
  - Agent -> MCP delegated scopes
- Admin consent must be granted for required delegated permissions in the tenant (once per tenant).

## Safe next action to reach first live E2E

Run a protected manual `m8-deploy-live.yml` dispatch with:

- `run_apply=false`
- `run_config_rollout=false`
- `run_app_rollout=false`
- `execute_live_mutations=false`
- `live_azure_tests=false`

This is the zero-mutation confidence run to verify protected environment bindings, OIDC identity wiring, and M9 preflight checks before any approved live mutation.
