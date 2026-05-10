# Spec 009: Live Azure Execution and Evidence

**Status:** Spec-ready; live execution blocked pending approval and reviewer gates  
**Milestone:** M9  
**Spec Phase:** spec.feature — protected live execution planning  
**Created:** 2026-05-10  
**Updated:** 2026-05-10  
**Requested by:** Ashley Hollis  
**Owners:** Tank, Neo, Mouse, Trinity, Morpheus  
**Impact:** High

---

## Summary

M9 turns the M8 protected scaffolds into the first claimable live Azure deployment and end-to-end verification milestone.

The verified live path is:

```text
browser client -> APIM -> BFF -> Agent Execution Service -> MCP Protected API -> Azure Monitor / Application Insights
```

M9 remains opt-in and protected. Public CI stays offline/static. This spec does not run Azure deployments, dispatch workflows, read `.env` files, or record real tenant, subscription, endpoint, token, certificate, or secret values.

---

## What works at the end of M9

- ACA + APIM lab resources are deployed/updated by protected GitHub Actions only.
- BFF, Agent Execution Service, and MCP Protected API run with `AUTH_MODE=strict`.
- A real browser smoke acquires a delegated Entra token from an approved client variant and calls APIM.
- APIM validates and forwards only to BFF; BFF does not perform MCP OBO.
- Agent Execution Service performs the MCP-audience OBO exchange.
- MCP Protected API rejects the original user/BFF-audience token and accepts only the MCP-audience delegated token.
- Azure Monitor / Application Insights positive KQL proves the correlated chain.
- Negative KQL returns zero leakage rows for tokens, auth headers, endpoint/account metadata, forbidden PII claims, and unsafe `tracestate`.
- Cost controls are verified before closeout.

---

## Required Azure resources

- Resource group for the lab boundary.
- Azure Container Registry.
- Azure Container Apps environment.
- Container Apps for BFF, Agent Execution Service, and MCP Protected API.
- Azure API Management instance/routes/policies.
- Application Insights and Log Analytics workspace.
- Runtime managed identities.
- Purpose-scoped GitHub OIDC/federated identities for deploy, smoke, and lifecycle operations.
- Entra app registrations/scopes configured outside the repo.

---

## Required protected placeholders

Protected GitHub Environments:

- `lab-live-azure-deploy`
- `lab-live-azure-smoke`
- `lab-live-azure-ops`

Placeholder secret/variable names only:

- `AZURE_CLIENT_ID_DEPLOY`, `AZURE_CLIENT_ID_SMOKE`, `AZURE_CLIENT_ID_SHUTDOWN`
- `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`
- `AZURE_LOCATION`, `AZURE_RESOURCE_GROUP_NAME`
- `AZURE_APIM_NAME`, `AZURE_CONTAINER_APP_ENV_NAME`, `AZURE_CONTAINER_REGISTRY_NAME`
- `LIVE_APIM_BASE_URL`, `LIVE_READINESS_URL`
- `LIVE_SMOKE_CLIENT_ID`, `LIVE_AUTHORITY_HOST`, `LIVE_SMOKE_SCOPES`
- `LIVE_BFF_AUDIENCE`, `LIVE_AGENT_EXECUTION_AUDIENCE`, `LIVE_MCP_AUDIENCE`
- `APPLICATIONINSIGHTS_CONNECTION_STRING` or approved managed identity equivalent
- `APIM_SUBSCRIPTION_KEY` if the selected APIM route requires one

Do not commit or print real values.

---

## Workflow order after approval

1. Static/public-safe validation.
2. `.github\workflows\m8-live-oidc-contract.yml`.
3. `.github\workflows\m8-deploy-live.yml` with approved mutation toggles.
4. `.github\workflows\m8-start-resume.yml` if needed.
5. `.github\workflows\m8-smoke-trace.yml` with `LIVE_AZURE_TESTS=true`.
6. Positive and negative Azure Monitor / App Insights KQL verification.
7. Redacted evidence package review.
8. `.github\workflows\m8-nightly-shutdown.yml` or approved manual ops shutdown.
9. Optional teardown only if explicitly approved.

---

## Artifacts

| Artifact | Description |
|---|---|
| `goals.md` | Goals and done criteria |
| `research.md` | Baseline and imported readiness/security findings |
| `requirements.md` | Functional, security, observability, and cost requirements |
| `design.md` | Architecture, evidence model, workflow order, and ADRs |
| `tasks.md` | Review-gated task graph |
| `state.json` | Machine-readable status |
| `.progress.md` | Progress tracking |

---

## Checkpoint

[CHECKPOINT] User approval, protected GitHub Environment configuration, and Tank/Trinity/Morpheus reviewer gates are required before live deployment dispatch or live success claims.
