# Spec 006 — Design

**Spec:** 006-azure-deployment-baseline
**Milestone:** M6 — Azure deployment baseline
**Updated:** 2026-06-01
**Note:** This is a planning artifact for spec-first gate purposes. Terraform resource bodies are scaffolds for structural validation. No live Azure resources are represented.

---

## Architecture Overview

### Deployed Topology (ACA Default Path)

```
Internet
  │
  ▼
┌─────────────────────────────────────────────────────┐
│  Azure APIM                                         │
│  • Ingress JWT validation (aud=BFF API, scp=mcp.access) │
│  • System-assigned managed identity (APIM→ACA calls) │
│  • Correlation ID injection                          │
└───────────────────┬─────────────────────────────────┘
                    │ HTTPS (BFF FQDN)
                    ▼
┌──────────────────────────────────┐
│  Azure Container App: BFF        │
│  • AUTH_MODE=strict              │
│  • User-assigned managed identity│
│  • OTEL → Azure Monitor          │
└──────────┬───────────────────────┘
           │ HTTPS (Agent Execution Service FQDN)
           ▼
┌──────────────────────────────────────────────────────┐
│  Azure Container App: Agent Execution Service        │
│  • Blueprint audience validation                     │
│  • OBO token exchange (managed identity)             │
│  • AUTH_MODE=strict                                  │
│  • User-assigned managed identity                    │
│  • OTEL → Azure Monitor                              │
└──────────┬───────────────────────────────────────────┘
           │ HTTPS (MCP Protected API FQDN) + OBO token
           ▼
┌──────────────────────────────────┐
│  Azure Container App: MCP        │
│  Protected API                   │
│  • OBO token validation          │
│  • AUTH_MODE=strict              │
│  • User-assigned managed identity│
│  • OTEL → Azure Monitor          │
└──────────────────────────────────┘

Supporting Infrastructure:
  • Azure Log Analytics Workspace → App Insights (workspace-based)
  • Azure Container Apps Environment (shared for all 3 services)
  • Azure Container Registry (placeholder; build/push deferred)
```

### AKS Optional Path (from M5 — not M6 default)

The AKS optional path documented in M5 (Spec 002) remains available. AKS Terraform skeletons in `infra/terraform/environments/aks/` are unchanged by M6. Entra Agent ID / AKS Agent Gateway exercises are available to contributors with AKS access.

---

## ADR-M6-01: ACA as Default Deployment Path

**Status: Pending Morpheus review (T11)**

### Context

M5 established AKS as an optional track (ADR-M5-01). The roadmap states the M6 goal as "APIM + Container Apps with managed identity." Tank charter states "Keep Azure Container Apps as the default deployment target."

### Options

**Option A — ACA default, AKS optional (RECOMMENDED)**
- New `single-tenant-aca` environment for M6 implementation.
- AKS skeletons from M5 preserved, untouched.
- ACA is the path all M6 tasks assume.

**Option B — AKS default, ACA deferred**
- Would require significant redesign of M5 AKS skeletons.
- Not aligned with charter or roadmap phrasing.

### Pending Decision

ADR-M6-01 to be decided by Morpheus at T11. Option A is the working assumption for this spec.

---

## ADR-M6-02: Azure Monitor OTLP Endpoint vs App Insights SDK

**Status: Pending Morpheus review (T11)**

### Context

M5 uses the OTEL SDK with a local OTLP exporter (Jaeger via Docker Compose tracing overlay). The SDK reads `OTEL_EXPORTER_OTLP_ENDPOINT`. Azure Monitor supports two ingestion paths:

1. **OTLP endpoint** — `https://{region}.otel.monitor.azure.com/v1/traces`. SDK-native; env-var-only change; no code change.
2. **App Insights connection string** — Requires Azure Monitor OpenTelemetry Distro (`azure-monitor-opentelemetry` package). Code change required.

### Options

**Option A — OTLP endpoint swap (RECOMMENDED)**
- Zero code change from M5 instrumentation.
- Vendor-neutral: if Azure Monitor is replaced in the future, only the env var changes.
- Requires Azure Monitor workspace-based App Insights with OTLP ingestion enabled (GA as of 2024).

**Option B — App Insights connection string + Azure Monitor distro**
- Adds a Python package dependency.
- Provides richer App Insights features (availability tests, live metrics).
- Code change required.

### Working Decision

Option A (OTLP endpoint) is the working assumption for M6. Morpheus to confirm at T11.

---

## ADR-M6-03: Managed Identity Assignment Strategy

**Status: Pending Trinity review (T12)**

### Context

Azure Container Apps supports system-assigned and user-assigned managed identities. M6 needs to wire managed identity so that:
- BFF can call Agent Execution Service (service-to-service, internal ACA networking).
- Agent Execution Service can perform OBO token exchange (via Entra ID federation — future live implementation).
- MCP Protected API can validate OBO tokens.

### Options

**Option A — User-assigned managed identity per service (RECOMMENDED)**
- Allows pre-creation of identities and role assignments in Terraform before container app exists.
- Identities can be reused across deployments / revisions.
- Consistent pattern; `managed-identity` module already scaffolds this.

**Option B — System-assigned managed identity**
- Simpler HCL.
- Cannot pre-assign roles; identity created when container app is created.
- Less suitable for IaC workflows where role assignments are defined separately.

### Working Decision

Option A is the working assumption. Trinity to confirm at T12.

---

## Terraform File Structure — M6 Additions

```
infra/terraform/
├── environments/
│   ├── single-tenant/              (existing — unchanged)
│   ├── single-tenant-aca/          (NEW — M6)
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   ├── providers.tf
│   │   └── terraform.tfvars.example
│   └── aks/                        (existing M5 — unchanged)
└── modules/
    ├── container-app/              (existing — resource body added in M6)
    │   ├── main.tf                 (UPDATED — add azurerm_container_app resource)
    │   ├── variables.tf            (UPDATED — add image, cpu, memory, ingress vars)
    │   └── outputs.tf              (UPDATED — add fqdn, identity_id outputs)
    ├── app-insights/               (NEW — M6)
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    └── (all other modules unchanged)
```

---

## `single-tenant-aca/main.tf` — Conceptual Structure

```hcl
# ILLUSTRATIVE REFERENCE ONLY — placeholder HCL for Terraform validation
# No terraform apply is run from public CI.

locals {
  name_prefix = "agent-identity-lab-${var.environment}"
}

module "resource_group" {
  source   = "../../modules/resource-group"
  name     = var.resource_group_name
  location = var.location
  tags     = var.tags
}

module "log_analytics" {
  source              = "../../modules/log-analytics"
  name                = "${local.name_prefix}-logs"
  resource_group_name = module.resource_group.name
  location            = var.location
  tags                = var.tags
}

module "app_insights" {
  source                     = "../../modules/app-insights"
  name                       = "${local.name_prefix}-appi"
  resource_group_name        = module.resource_group.name
  location                   = var.location
  log_analytics_workspace_id = module.log_analytics.workspace_id
  tags                       = var.tags
}

module "container_apps_env" {
  source              = "../../modules/container-apps-env"
  name                = "${local.name_prefix}-acae"
  resource_group_name = module.resource_group.name
  location            = var.location
  tags                = var.tags
}

module "managed_identity_bff" {
  source              = "../../modules/managed-identity"
  name                = "${local.name_prefix}-id-bff"
  resource_group_name = module.resource_group.name
  location            = var.location
  tags                = var.tags
}

module "managed_identity_agent_execution" {
  source              = "../../modules/managed-identity"
  name                = "${local.name_prefix}-id-agent-execution"
  resource_group_name = module.resource_group.name
  location            = var.location
  tags                = var.tags
}

module "managed_identity_mcp_protected_api" {
  source              = "../../modules/managed-identity"
  name                = "${local.name_prefix}-id-mcp"
  resource_group_name = module.resource_group.name
  location            = var.location
  tags                = var.tags
}

module "container_app_bff" {
  source                      = "../../modules/container-app"
  name                        = "${local.name_prefix}-bff"
  resource_group_name         = module.resource_group.name
  location                    = var.location
  container_apps_environment_id = module.container_apps_env.environment_id
  image                       = var.bff_image
  managed_identity_id         = module.managed_identity_bff.identity_id
  tags                        = var.tags
}

module "container_app_agent_execution" {
  source                      = "../../modules/container-app"
  name                        = "${local.name_prefix}-agent-execution"
  resource_group_name         = module.resource_group.name
  location                    = var.location
  container_apps_environment_id = module.container_apps_env.environment_id
  image                       = var.agent_execution_image
  managed_identity_id         = module.managed_identity_agent_execution.identity_id
  tags                        = var.tags
}

module "container_app_mcp_protected_api" {
  source                      = "../../modules/container-app"
  name                        = "${local.name_prefix}-mcp"
  resource_group_name         = module.resource_group.name
  location                    = var.location
  container_apps_environment_id = module.container_apps_env.environment_id
  image                       = var.mcp_image
  managed_identity_id         = module.managed_identity_mcp_protected_api.identity_id
  tags                        = var.tags
}

module "apim" {
  source              = "../../modules/apim"
  name                = "${local.name_prefix}-apim"
  resource_group_name = module.resource_group.name
  location            = var.location
  backend_url         = module.container_app_bff.fqdn
  tags                = var.tags
}
```

---

## Container App Module — Resource Body Design

`infra/terraform/modules/container-app/main.tf` (to add):

```hcl
# ILLUSTRATIVE REFERENCE ONLY
resource "azurerm_container_app" "this" {
  name                         = var.name
  container_apps_environment_id = var.container_apps_environment_id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"
  tags                         = var.tags

  identity {
    type         = "UserAssigned"
    identity_ids = [var.managed_identity_id]
  }

  template {
    container {
      name   = var.name
      image  = var.image
      cpu    = var.cpu
      memory = var.memory

      env {
        name  = "AUTH_MODE"
        value = "strict"
      }
      env {
        name  = "OTEL_EXPORTER_OTLP_ENDPOINT"
        value = var.otel_endpoint
      }
      # Additional env vars injected at deploy time via tfvars (not committed)
    }
  }

  ingress {
    external_enabled = var.external_enabled
    target_port      = 8080
    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }
}
```

---

## Azure Monitor Tracing — OTLP Endpoint Swap Design

### M5 Local Jaeger flow (unchanged, still works locally)

```
Service → OTEL SDK → OTEL Exporter (OTLP gRPC) → otel-collector → Jaeger UI
```
Env var: `OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317`

### M6 Azure Monitor flow (ACA deployed)

```
Service → OTEL SDK → OTEL Exporter (OTLP HTTPS) → Azure Monitor OTLP endpoint
```
Env var: `OTEL_EXPORTER_OTLP_ENDPOINT=https://{region}.otel.monitor.azure.com/v1/traces`

**No code change.** The switch is purely an env var. Local Compose + Jaeger continues to work for local development. Azure Monitor is activated in the deployment overlay or via tfvars at deploy time.

### `APPLICATIONINSIGHTS_CONNECTION_STRING` (additional, optional)

If the team later wants richer App Insights features (availability tests, live metrics stream), `APPLICATIONINSIGHTS_CONNECTION_STRING` can be added. This does not block M6 gate — it is a post-M6 enhancement. The App Insights module outputs `connection_string` so it is available if needed.

---

## `docker-compose.strict-aca.yml` — Design

```yaml
# ILLUSTRATIVE — strict-mode overlay for local pre-deploy simulation
# AUTH_MODE=strict: no fixture headers accepted, real JWKS required
# OTEL: Azure Monitor OTLP endpoint placeholder (replace {region} and set connection string at deploy time)
# Do not use AUTH_MODE=mock in any deployed container app.

services:
  bff:
    environment:
      - AUTH_MODE=strict
      - AUTH_ISSUER=https://login.microsoftonline.com/{tenant-id}/v2.0
      - AUTH_JWKS_URL=https://login.microsoftonline.com/{tenant-id}/discovery/v2.0/keys
      - OTEL_EXPORTER_OTLP_ENDPOINT=https://{region}.otel.monitor.azure.com/v1/traces

  agent-execution:
    environment:
      - AUTH_MODE=strict
      - AUTH_ISSUER=https://login.microsoftonline.com/{tenant-id}/v2.0
      - AUTH_JWKS_URL=https://login.microsoftonline.com/{tenant-id}/discovery/v2.0/keys
      - OTEL_EXPORTER_OTLP_ENDPOINT=https://{region}.otel.monitor.azure.com/v1/traces

  mcp-protected-api:
    environment:
      - AUTH_MODE=strict
      - AUTH_ISSUER=https://login.microsoftonline.com/{tenant-id}/v2.0
      - AUTH_JWKS_URL=https://login.microsoftonline.com/{tenant-id}/discovery/v2.0/keys
      - OTEL_EXPORTER_OTLP_ENDPOINT=https://{region}.otel.monitor.azure.com/v1/traces
```

> After T00, the service name `agent-gateway` in the base Compose becomes `agent-execution`. This overlay references `agent-execution` (post-T00 state).

---

## Security Design — Deployed Environments

### AUTH_MODE=strict enforcement

| Service | Strict requirement | Enforcement mechanism |
|---------|-------------------|-----------------------|
| BFF | No fixture header, real JWKS | `identity_lab_auth.validate()` reads `AUTH_MODE` and ignores fixture header |
| Agent Execution Service | Blueprint audience, real JWKS, OBO | Same + `validate_agent_blueprint()` |
| MCP Protected API | OBO token only, real JWKS | Same + `require_actor_appid()` |

All three must return 401 if `AUTH_ISSUER` or `AUTH_JWKS_URL` are absent in strict mode.

### Managed Identity OBO boundary

The M6 Terraform scaffolds the identities but does not implement the live OBO call path. The design intent (for post-M6 implementation):
- Agent Execution Service managed identity is assigned Entra ID API permissions to exchange tokens OBO.
- BFF managed identity has no OBO permissions (BFF validates inbound user tokens only; it does not perform OBO).
- MCP Protected API managed identity has no OBO permissions (it validates OBO-exchanged tokens only).

This separation is the same OBO boundary established in M1 (Spec 001) and M2 (Spec 003), now expressed at the managed identity scope.

### No Mock Mode in Deployed Environments

`AUTH_MODE=mock` MUST NOT appear in any ACA container app environment variable block. The `docker-compose.strict-aca.yml` overlay sets `AUTH_MODE=strict` explicitly to document this constraint. The Terraform `container-app` module sets `AUTH_MODE=strict` as a hardcoded env var in the template (not a variable) to prevent accidental mock deployment.
