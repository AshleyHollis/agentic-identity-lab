# Tasks — Spec 009

| Task ID | Title | Owner | Dependencies | Status |
|---|---|---|---|---|
| T00 | Spec/ADR planning package | Morpheus | M8 closed | ✅ Complete |
| T01 | Protected environment gate audit | Tank | T00 | ✅ Complete (required environment shells exist; reviewer gate configured for authenticated lab operator; env placeholders remain external) |
| T02 | OIDC federation verification | Tank | T01 | ✅ Complete for zero-mutation readiness (deploy/smoke/ops Entra apps + exact federated subjects verified; protected GitHub environment identity secrets repaired from matching federated apps; deterministic lab RG now set (`rg-agent-identity-lab-dev-aca`, `eastus`), RG-scoped RBAC bound for deploy/smoke/ops, RG/location vars set, and deterministic `ACA_APP_NAMES` + `APIM_SERVICE_NAME` set across protected environments; optional lifecycle/smoke runtime vars remain later-stage blockers) |
| T03 | Security gate review | Trinity | T00-T02 | ✅ Complete (accepted blocked state) |
| T04 | Zero-mutation deploy rehearsal | Tank | T02, T03 | ✅ Complete (protected OIDC contract and deploy-live dry-run passed with mutation flags disabled and `live_azure_tests=false`) |
| T05 | Lifecycle readiness rehearsal | Tank | T02, T03, T04 | ✅ Complete (protected start/resume and nightly shutdown dry-runs passed) |
| T06 | Live smoke contract rehearsal | Neo / Mouse | T03, T04 | ✅ Complete (protected smoke/trace contract-only rehearsal passed; live check job skipped) |
| T07 | Approved first live mutation window | Tank | T04-T06, user approval | ✅ Complete (protected run `redacted-live-deploy-run` passed image publish, Terraform apply, and ACA image rollout with live mutation approval) |
| T08 | Runtime configuration verification | Tank / Neo | T07 | ✅ Complete (ACA/APIM runtime posture verified; strict auth/App Insights/runtime ports confirmed; run `redacted-readiness-smoke-run` also verified live runtime telemetry) |
| T09 | Browser / agent-browser smoke execution | Mouse / Neo | T08 | Blocked / waiting: latest protected deploy failed before apply because BFF_AUDIENCE is unset; agent-browser smoke failed because M9_AGENT_BROWSER_COMMAND is unset; they must still prove Graph/bootstrap permission, protected OBO credentials, and real delegated browser/agent-browser E2E |
| T10 | Positive KQL chain verification | Neo | T09 | ✅ Complete for readiness-generated live traces (protected Azure Monitor KQL verification in run `redacted-readiness-smoke-run` observed BFF, Agent Execution, and MCP roles) |
| T11 | Negative leakage verification | Trinity / Neo | T09 | ✅ Complete for readiness-generated live telemetry (protected run `redacted-readiness-smoke-run` hard-failed on leakage rows and passed with zero forbidden token/PII hits) |
| T12 | Redacted evidence package | Morpheus / Trinity | T10, T11 | In progress (readiness evidence exists; public-safe manual artifact template is ready; final package must add the live browser/agent-browser E2E proof without IDs, endpoints, tokens, cookies, usernames, raw claims, screenshots, HAR, raw traces, or raw KQL rows) |
| T13 | Cost-control shutdown verification | Tank | T09 | ✅ Complete (protected shutdown run `redacted-shutdown-run`; all ACA apps min replicas restored to 0) |
| T14 | Deployment readiness review | Tank | T01-T08, T13 | In progress / blocked on the latest protected deploy missing BFF_AUDIENCE, agent-browser command configuration, then live E2E proof, protected OBO credential setup, live browser/agent-browser E2E evidence, and shutdown verification for that run; not blocked on automating Entra MFA |
| T15 | Security/evidence review | Trinity | T03, T11, T12 | In progress (elevated-access/secret-handling review passed with controls; final E2E evidence review remains pending) |
| T16 | Architecture closeout review | Morpheus | T12-T15 | Pending (acceptance bar amended: manual MFA is allowed; controlled agent-browser is accepted; blocked until real live E2E evidence + reviewer gates) |
| T17 | Final M9 closeout | Morpheus | T16 | Pending |

## Pre-live validation commands

```powershell
python tools\ci\public_safe_validation.py
python tools\telemetry\validate_m8_kql_contract.py
python tools\ci\m8_browser_smoke_harness.py --mode static
python tools\ci\m8_smoke_trace_contract.py validate --workflow-file .github\workflows\m8-smoke-trace.yml --positive-kql tools\telemetry\kql\m8-positive-chain.kql --negative-kql tools\telemetry\kql\m8-negative-leakage.kql
```

## Amended M9 acceptance

M9 is complete only after a protected live run demonstrates the full browser/agent-browser path through APIM, BFF, Agent Execution Service, and MCP with a real delegated token. Manual Entra MFA is acceptable for the human-operated sign-in step. Agent-browser use is accepted risk only with controls: protected environment approval, ephemeral browser state, no persisted cookies/tokens/storage, redacted logs/evidence, positive trace/log proof, negative leakage proof, and verified shutdown/scale-down after the run. Existing readiness telemetry remains prerequisite evidence, not full E2E completion.

## Live block

T07 and later live-mutation tasks require explicit protected workflow inputs and environment approval. Ashley's standing directive is to continue through deployment and end-to-end verification while attempting access first; live mutations still must remain inside protected GitHub Environment gates and redacted evidence rules. For M9 closeout, Entra MFA may remain manual-only and does not have to be solved for automation. A controlled agent-browser path is accepted risk when it improves live E2E verification, provided no browser state, cookies, tokens, usernames, raw claims, endpoints, screenshots, HAR files, raw traces, or raw KQL rows are committed or published.

## External setup prerequisite for T01/T02

The following must be completed outside the repository before T04/T05/T06 can proceed:

1. ✅ Created `lab-live-azure-deploy`, `lab-live-azure-smoke`, and `lab-live-azure-ops`.
2. ✅ Configure GitHub Environment reviewer gate for one-human lab operation (authenticated repo owner set as required reviewer with `prevent_self_review=false`, zero-wait posture; Trinity accepted T02 reviewer gate/env inventory readiness).
3. ◐ Add required environment-scoped placeholders (secrets and vars only; no real values in repo/logs). Core identity secrets are configured; RG/location vars are configured; deterministic runtime names `ACA_APP_NAMES` and `APIM_SERVICE_NAME` are configured; optional lifecycle/smoke runtime vars (`APIM_STOP_SUPPORTED`, `M8_READINESS_URL`, and smoke runtime vars) remain pending for post-T04 stages.
4. ✅ Configure Entra federated credentials for GitHub OIDC environment subjects:
   - `repo:<ORG_OR_USER>/<REPO>:environment:lab-live-azure-deploy`
   - `repo:<ORG_OR_USER>/<REPO>:environment:lab-live-azure-smoke`
   - `repo:<ORG_OR_USER>/<REPO>:environment:lab-live-azure-ops`
5. ✅ Re-run zero-mutation validations and protected OIDC contract workflow. T04 succeeded after publishing workflow files to `main`, granting the deploy workflow's reusable smoke call `id-token: write`, repairing tenant/subscription environment secrets from the authenticated Azure context, and resetting deploy/smoke/ops client-ID secrets from Entra app registrations with matching federated subjects.

