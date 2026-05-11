# Azure Container Apps Deployment — Agent Identity Lab

> **ILLUSTRATIVE REFERENCE ONLY** — see `infra/terraform/environments/single-tenant-aca/terraform.tfvars.example`
> for placeholder substitution guide.
>
> **No `terraform apply` is run from this public repository.** All Terraform in this repo is
> validation-only (fmt + validate). Deploy using your own pipeline with real credentials supplied
> at runtime.

---

## Overview

M6 establishes Azure Container Apps (ACA) as the default deployment path for Agent Identity Lab
(ADR-M6-01). Three Python FastAPI services are deployed as separate container apps in a shared
ACA environment, fronted by Azure API Management (APIM).

### Topology

```
Internet
  │
  ▼
Azure APIM  ── ingress JWT validation (delegated user token)
             ── correlation ID injection
             ── Security C2: APIM MI never injected as Authorization header to BFF
  │ HTTPS (BFF container app FQDN)
  ▼
BFF Container App          — AUTH_MODE=strict, user-assigned managed identity
  │ HTTPS (Agent Execution FQDN, internal ACA networking)
  ▼
Agent Execution Service    — AUTH_MODE=strict, blueprint audience validation, OBO (post-M6)
                           — user-assigned managed identity
  │ HTTPS (MCP Protected API FQDN) + OBO token
  ▼
MCP Protected API          — AUTH_MODE=strict, OBO token validation
                           — user-assigned managed identity

Supporting:
  • Azure Log Analytics Workspace (workspace-based App Insights)
  • Azure Application Insights (OTLP ingestion — ADR-M6-02)
  • Azure Container Apps Environment (shared for all 3 services)
```

### AKS Optional Path

The AKS optional track from M5 (Spec 002) is preserved unchanged in
`infra/terraform/environments/aks/`. ACA is the M6 default; AKS is an advanced-track option.

---

## Managed Identity Model (ADR-M6-03)

User-assigned managed identities are provisioned per service (Option A — Trinity T12):

| Service | Identity Name | OBO Boundary | Role Assignments (post-M6) |
|---------|--------------|--------------|---------------------------|
| BFF | `*-id-bff` | None (validates inbound user tokens only) | Monitoring Metrics Publisher |
| Agent Execution Service | `*-id-agent-execution` | Performs OBO exchange (post-M6) | Monitoring Metrics Publisher, Managed Identity Operator |
| MCP Protected API | `*-id-mcp` | Validates OBO tokens only | Monitoring Metrics Publisher |

**Security Binding C2 (Trinity T12):** APIM's system-assigned managed identity (provisioned for
future Key Vault access) MUST NOT be injected as the `Authorization` header to BFF. The delegated
user token validated by APIM passes through to BFF unchanged.

Role assignment resources are commented-out placeholders in `single-tenant-aca/main.tf`.
Apply them post-M6 with a real subscription scope.

---

## Azure Monitor OTLP Endpoint Swap (ADR-M6-02)

All three services use the OpenTelemetry SDK configured with `OTEL_EXPORTER_OTLP_ENDPOINT`.

| Environment | OTEL_EXPORTER_OTLP_ENDPOINT value |
|-------------|----------------------------------|
| Local (Jaeger) | `http://otel-collector:4317` (via `docker-compose.tracing.yml`) |
| Deployed (Azure Monitor) | `https://{region}.otel.monitor.azure.com/v1/traces` |

This is a **config-only change** — no code change from M5 instrumentation. The SDK reads the
env var; swapping from local Jaeger to Azure Monitor requires only updating this variable.

`APPLICATIONINSIGHTS_CONNECTION_STRING` is available from the `app-insights` module output
(`connection_string`) for post-M6 enrichment (live metrics, availability tests) if needed.

---

## AUTH_MODE=strict Deployment Constraint

`AUTH_MODE=strict` is hardcoded in the `container-app` Terraform module template. It is **not
a variable** — this prevents accidental mock-mode deployment.

In strict mode:
- `X-Identity-Lab-Fixture` headers are ignored (no mock auth bypass).
- `AUTH_ISSUER` and `AUTH_JWKS_URL` must be set or the service refuses to start.
- Mock tokens are not accepted.

The `docker/docker-compose.strict-aca.yml` overlay simulates this locally for pre-deploy validation.

---

## Variable Substitution Guide

1. Copy `infra/terraform/environments/single-tenant-aca/terraform.tfvars.example`
   to `terraform.tfvars` (not committed — add to `.gitignore`).

2. Replace placeholders:

   | Placeholder | Replace with |
   |-------------|-------------|
   | `{subscription-id}` | Your Azure subscription GUID |
   | `{tenant-id}` | Your Entra tenant GUID |
   | `{region}` | Azure region for OTLP endpoint (e.g., `eastus`) |
   | image variables | Real ACR image refs (`acrname.azurecr.io/service:tag`) |

3. Supply `terraform.tfvars` to your pipeline — never commit it.

---

## Validation Commands (CI-safe, no credentials required)

```bash
# Format check
terraform -chdir=infra/terraform fmt -check -recursive

# Download provider plugin (no backend, no credentials)
terraform -chdir=infra/terraform/environments/single-tenant-aca init -backend=false

# Schema validation (no Azure connection)
terraform -chdir=infra/terraform/environments/single-tenant-aca validate

# Compose config checks
docker compose -f docker/docker-compose.yml config --quiet
docker compose -f docker/docker-compose.yml -f docker/docker-compose.tracing.yml config --quiet
docker compose -f docker/docker-compose.yml -f docker/docker-compose.strict-aca.yml config --quiet
```

---

## Recommended CI/CD Auth Pattern

Use **GitHub OIDC federated identity** (Workload Identity Federation) to authenticate to Azure
from GitHub Actions without storing long-lived credentials:

```yaml
- uses: azure/login@v2
  with:
    client-id: ${{ secrets.AZURE_CLIENT_ID }}
    tenant-id: ${{ secrets.AZURE_TENANT_ID }}
    subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
```

Configure federated credentials on the deployment service principal to trust your repository's
OIDC issuer. Long-lived secrets (`AZURE_CLIENT_SECRET`) should not be used.

This pattern is documented here; it is not wired in this public repository's CI.

---

## M8 live operations workflow contract (protected, public-safe)

M8 adds workflow scaffolds for protected live operations without embedding real IDs/secrets:

- `.github/workflows/m8-live-oidc-contract.yml` (T01)
- `.github/workflows/m8-deploy-live.yml` (T03)
- `.github/workflows/m8-start-resume.yml` (T04)
- `.github/workflows/m8-nightly-shutdown.yml` (T05)
- `.github/workflows/m8-smoke-trace.yml` (T07)
- `docs/deployment/aca/m8-operator-guide.md` (T09 operator runbook)

### Protected environments

Use protected GitHub Environments with required reviewers, for example:

- `lab-live-azure-deploy`
- `lab-live-azure-smoke`
- `lab-live-azure-ops` (shutdown/start-resume)

### Required placeholder secrets/vars

Configure these in protected GitHub Environments (placeholder names only in repo):

- Secrets: `AZURE_CLIENT_ID_DEPLOY`, `AZURE_CLIENT_ID_SMOKE`, `AZURE_CLIENT_ID_SHUTDOWN`,
  `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`
- Variables: `AZURE_RESOURCE_GROUP`, `ACA_APP_NAMES`, `APIM_SERVICE_NAME`,
  optional `APIM_RESOURCE_GROUP`, optional `M8_READINESS_URL`, optional `APIM_STOP_SUPPORTED`

### Scope boundaries

- Deploy and smoke identities must be separate from lifecycle identity, or equivalently constrained.
- Lifecycle identity is stop/start/scale focused and must not perform broad deploy/apply/destroy.
- Deploy-live smoke stage is opt-in (`live_azure_tests=true`) and only runs in protected manual scope.
- Canonical smoke/trace workflow (`m8-smoke-trace.yml`) enforces `live_azure_tests=true`, runs static wiring checks (`tools/ci/m8_browser_smoke_harness.py`), validates KQL contract coverage, and supports protected live browser transports (`playwright`, accepted-risk `agent-browser`, or `manual-artifact`) with hard-fail leakage evaluation.
- Scheduled shutdown path is non-destructive and reports classifications (`stopped`,
  `scaled_to_zero`, `left_running`, `destroy_only`, `manual_follow_up_required`).

### Operator runbook

Use `docs/deployment/aca/m8-operator-guide.md` for:

- deploy/start-resume/smoke/nightly execution order
- resource cost model and what remains billable
- protected environment + RBAC identity boundaries
- optional destroy/recreate posture (T06 if later implemented)
- safe smoke/trace and KQL leakage invocation rules
