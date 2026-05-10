# Spec 006 — Requirements

**Spec:** 006-azure-deployment-baseline
**Milestone:** M6 — Azure deployment baseline
**Updated:** 2026-06-01

---

## Functional Requirements

### FR-01 — Agent Execution Service rename (M6 Task 0)

The filesystem and Compose rename MUST be applied before any M6 implementation files reference the new path:

- `apps/agent-gateway/` → `apps/agent-execution/`
- `apps/agent-gateway/python-fastapi-agent-framework/` → `apps/agent-execution/python-fastapi/` (primary sub-path)
- Docker Compose service name `agent-gateway` → `agent-execution` in base, all overlays, and tracing overlay.
- All Python `import` statements, `sys.path` inserts, `__init__.py` references, and test fixture path references updated.
- All CI commands, Terraform resource references, k8s manifest comments, spec artifact references, and documentation path references updated.
- `python -m pytest` MUST pass (229+ tests) after rename with zero test failures.
- All `docker compose … config --quiet` checks MUST pass after rename.

### FR-02 — ACA Terraform environment

`infra/terraform/environments/single-tenant-aca/` MUST exist with:
- `main.tf` wiring: resource group → log analytics → app insights → container apps environment → three container apps (BFF, Agent Execution Service, MCP Protected API) → APIM → three managed identities.
- `variables.tf` with all inputs defined. All `default` values MUST use placeholder strings (`""`, `"placeholder"`, `"{tenant-id}"`) — no real values.
- `outputs.tf` with at minimum: `bff_url`, `agent_execution_url`, `mcp_protected_api_url`, `apim_gateway_url`, `bff_managed_identity_id`, `agent_execution_managed_identity_id`, `mcp_managed_identity_id`.
- `providers.tf` with `azurerm` (≥ 3.x) and `azuread` (≥ 2.x) providers; `subscription_id`, `tenant_id` read from variables — no inline literals.
- `terraform.tfvars.example` with ONLY brace-token placeholders.
- `terraform init -backend=false` and `terraform validate` MUST pass without live Azure credentials.
- `terraform fmt -check` MUST pass for the entire `infra/terraform/` tree.

### FR-03 — Container app module resource body

`infra/terraform/modules/container-app/main.tf` MUST contain an `azurerm_container_app` resource block with:
- `name`, `container_apps_environment_id`, `resource_group_name`, `revision_mode` wired from variables.
- `identity` block for user-assigned managed identity.
- `template.container` block with `name`, `image`, `cpu`, `memory` wired from variables (placeholder defaults).
- `ingress` block with `external_enabled`, `target_port` wired from variables.
- All sensitive fields (connection strings, secrets) expressed via `secret` block with placeholder values only.

### FR-04 — Application Insights module

`infra/terraform/modules/app-insights/` MUST be created with:
- `main.tf`: `azurerm_application_insights` resource block linked to a `log_analytics_workspace_id` variable. `application_type = "web"`. Workspace-based (not classic).
- `variables.tf`: `name`, `resource_group_name`, `location`, `log_analytics_workspace_id`, `tags`.
- `outputs.tf`: `instrumentation_key` (sensitive), `connection_string` (sensitive), `app_id`.

### FR-05 — APIM wiring for ACA backend

The APIM module MUST be updated or the `single-tenant-aca/main.tf` MUST wire:
- APIM backend URL set to the BFF container app FQDN output (placeholder in tfvars.example).
- APIM JWT policy reference to the ingress policy from Spec 004.
- APIM system-assigned managed identity skeleton (resource block present).

### FR-06 — Managed identity per container app

Three user-assigned managed identity resources MUST be scaffolded (one per service) in the `single-tenant-aca` environment:
- `managed_identity_bff`, `managed_identity_agent_execution`, `managed_identity_mcp_protected_api`.
- Each identity's `principal_id` MUST be an output.
- Role assignment blocks (e.g., Azure Key Vault Secrets User) MUST be present as placeholder comments or empty resource blocks — not applied without a live scope.

### FR-07 — Azure Monitor OTLP endpoint documented

Each service's `config/env/*.env.example` file MUST document the Azure Monitor OTLP endpoint variable:

```
# Azure Monitor OTLP endpoint (replace {region} with your Azure region, e.g. eastus)
# For local dev: leave unset or use OTEL_SDK_DISABLED=true
OTEL_EXPORTER_OTLP_ENDPOINT=https://{region}.otel.monitor.azure.com/v1/traces
```

No code change to `identity_lab_auth/telemetry.py` is required — the OTEL SDK consumes `OTEL_EXPORTER_OTLP_ENDPOINT` natively.

### FR-08 — `AUTH_MODE=strict` Compose overlay

`docker/docker-compose.strict-aca.yml` MUST exist with:
- `AUTH_MODE=strict` for all three services.
- `AUTH_ISSUER=https://login.microsoftonline.com/{tenant-id}/v2.0` for all three services.
- `AUTH_JWKS_URL=https://login.microsoftonline.com/{tenant-id}/discovery/v2.0/keys` for all three services.
- `OTEL_EXPORTER_OTLP_ENDPOINT=https://{region}.otel.monitor.azure.com/v1/traces` for all three services.
- `docker compose -f docker\docker-compose.yml -f docker\docker-compose.strict-aca.yml config --quiet` MUST pass.

### FR-09 — `AUTH_MODE=strict` Python verification

All three Python FastAPI services MUST be verified to enforce strict mode:
- `X-Identity-Lab-Fixture` header MUST be ignored / rejected when `AUTH_MODE=strict`.
- `AUTH_ISSUER` and `AUTH_JWKS_URL` MUST be required (startup error if absent in strict mode).
- No mock token path MUST be reachable in strict mode.
- Tests verifying each constraint MUST pass as part of `python -m pytest`.

### FR-10 — No mock mode in deployed environments

The deployment overlay and documentation MUST make explicit:
- Deployed environments (ACA) MUST use `AUTH_MODE=strict`.
- `AUTH_MODE=mock` MUST NOT be used in any deployed container app environment variable.
- This constraint MUST be documented in `docker/docker-compose.strict-aca.yml` as a comment and in the deployment docs.

### FR-11 — CI validation gates

A documented CI-safe command sequence MUST exist (`.github/workflows/` or documented in `infra/terraform/README.md`) that:
1. Runs `terraform fmt -check -recursive` for the entire infra tree.
2. Runs `terraform init -backend=false` and `terraform validate` for `single-tenant-aca`.
3. Runs all Compose `config --quiet` checks (base + overlays + strict-aca).
4. Runs a no-secret scan (e.g., `git grep` or `rg` for patterns matching real GUID formats, subscription IDs, or `secret` values).
5. Runs `python -m pytest`.

All commands MUST pass with exit code 0 without live Azure credentials.

### FR-12 — Deployment documentation

`docs/deployment/aca/` MUST exist with at minimum:
- `README.md` explaining the ACA deployment topology, managed identity model, and OTLP tracing swap.
- All content marked "ILLUSTRATIVE REFERENCE ONLY" with a clear note that no `terraform apply` is run from this repository.
- Step-by-step manual deployment notes (placeholder variable substitution guide).

---

## Non-Functional Requirements

### NFR-01 — No secrets or real IDs committed

All placeholder values MUST use only:
- Brace-token placeholders: `{tenant-id}`, `{subscription-id}`, `{resource-group}`, `{tenant_id}`, `{region}`
- All-zero GUIDs: `00000000-0000-0000-0000-000000000000`
- Descriptive strings: `placeholder`, `PLACEHOLDER`, `your-value-here`

Real tenant IDs, subscription IDs, client IDs, client secrets, kubeconfigs, tokens, or certificates MUST NOT appear in any committed file.

### NFR-02 — No `terraform apply` in public CI

No GitHub Actions workflow MUST execute `terraform apply` or `terraform destroy` against any live Azure environment. CI validates only.

### NFR-03 — Python tests remain green

`python -m pytest` MUST pass with no regressions after all changes. Any new strict-mode tests MUST be green.

### NFR-04 — Terraform format compliant

`terraform fmt -check -recursive` MUST pass for the entire `infra/terraform/` tree after all M6 Terraform changes.

### NFR-05 — Public-safe at all times

Every commit in M6 MUST satisfy the no-secret constraint (NFR-01) at the time of commit. No intermediate commit may introduce real credentials even temporarily.

### NFR-06 — AKS optional path preserved

The M5 AKS Terraform skeletons (`infra/terraform/environments/aks/`, `infra/terraform/modules/aks/`, etc.) MUST remain valid and unmodified by M6 changes. `terraform validate` for the AKS environment MUST continue to pass.

### NFR-07 — Agent Execution Service naming consistency

After T00, the term "Agent Execution Service" (slug `agent-execution`) MUST be used consistently across all new and updated files. Legacy references in existing M1–M5 spec artifacts are updated in T00 where they appear in path references; prose amendments to older specs are documented but not required to be exhaustive in M6.

---

## Constraints

- No live Azure deployment is authorized from this spec or from any public CI workflow.
- `AUTH_MODE=mock` is not an acceptable setting for deployed container apps.
- The AKS optional path remains available from M5; M6 does not gate on it.
- The `container-app` module resource body added in M6 is a skeleton for Terraform validation — it does not represent production-ready HCL (resource configurations like autoscaling, secrets rotation, and Dapr are deferred).
- M6 does not implement the runtime OBO call path using managed identity (that requires live Azure credentials and a deployed Entra app registration — deferred to post-M6 implementation work done outside the public repo).
