# Spec 006 — Goals

**Spec:** 006-azure-deployment-baseline
**Milestone:** M6 — Azure deployment baseline
**Updated:** 2026-06-01
**Lead owners:** Tank (Infra), Neo (Backend/Rename)

---

## Primary Goal

Establish a validated, public-safe Azure deployment baseline for the Identity Lab: BFF, Agent Execution Service, and MCP Protected API deployed to Azure Container Apps (ACA) behind APIM, with managed identity wired for OBO readiness, and Azure Monitor replacing local Jaeger as the tracing backend. All infrastructure is scaffold-only; CI validates but never applies.

---

## Success Criteria

### 1 — M6 Task 0: Agent Execution Service rename is complete

The filesystem rename `apps/agent-gateway/` → `apps/agent-execution/` and Compose service rename `agent-gateway` → `agent-execution` are applied atomically as the first M6 commit:

- All Python imports updated.
- All Compose file references updated (base + all overlays + tracing overlay).
- All CI commands, Makefile/scripts, and spec/doc path references updated.
- `python -m pytest` passes (229+ tests) after rename.
- `terraform fmt -check -recursive` passes.
- All Compose `config --quiet` checks pass.

### 2 — ACA Terraform environment scaffolded and validating

`infra/terraform/environments/single-tenant-aca/` exists with:
- `main.tf` wiring resource group, Log Analytics, App Insights, container apps environment, BFF container app, Agent Execution Service container app, MCP Protected API container app, APIM, and managed identities.
- `variables.tf` with all inputs defined; all defaults are placeholders or empty strings.
- `outputs.tf` with service URLs and managed identity principal IDs as outputs.
- `providers.tf` with `azurerm` and `azuread` providers; no live credentials.
- `terraform.tfvars.example` with only `{tenant-id}`, `{subscription-id}`, `{resource-group}` brace tokens — no real values.
- `terraform init -backend=false` and `terraform validate` pass without live Azure credentials.

### 3 — APIM + ACA wired in skeleton

The APIM module is updated or extended so that the single-tenant-aca environment wires:
- APIM pointing at ACA backend URLs (placeholder outputs from container app modules).
- Ingress JWT policy references preserved from Spec 004.
- APIM system-assigned managed identity skeleton (resource block present; no live credentials).

### 4 — Managed identity scaffolded per service

Each of the three container apps has a user-assigned managed identity resource block:
- `managed_identity_bff`
- `managed_identity_agent_execution`
- `managed_identity_mcp_protected_api`

Managed identity principal IDs are wired as outputs. OBO token exchange will use these identities when deployed (M6 does not implement the OBO call path in Terraform — it only ensures identities exist and are assigned).

### 5 — Application Insights / Azure Monitor module scaffolded

`infra/terraform/modules/app-insights/` exists with `main.tf` (placeholder `azurerm_application_insights` resource body), `variables.tf`, and `outputs.tf`. The `instrumentation_key` and `connection_string` outputs are present (sensitive = true in variables, redacted from state display).

### 6 — Azure Monitor tracing is a config-only swap

`OTEL_EXPORTER_OTLP_ENDPOINT` documented in each service's `.env.example` file with the Azure Monitor OTLP ingestion URL placeholder:
```
OTEL_EXPORTER_OTLP_ENDPOINT=https://eastus.otel.monitor.azure.com/v1/traces
```
No Python code change required from M5. The M5 OTEL instrumentation (`identity_lab_auth/telemetry.py`) works with any OTLP-compatible exporter.

### 7 — `AUTH_MODE=strict` enforcement is verified in Python apps

All three Python FastAPI services confirm that in `AUTH_MODE=strict`:
- The `X-Identity-Lab-Fixture` header is ignored / rejected.
- No mock token path is reachable.
- Real JWKS validation is enforced (requires `AUTH_ISSUER` and `AUTH_JWKS_URL`).

Python tests verify each strict-mode constraint. `python -m pytest` passes (229+ tests).

### 8 — `docker/docker-compose.strict-aca.yml` overlay is valid

A `docker-compose.strict-aca.yml` overlay exists that:
- Sets `AUTH_MODE=strict` for all three services.
- Sets `AUTH_ISSUER` and `AUTH_JWKS_URL` to `{tenant-id}` placeholder values.
- Adds `OTEL_EXPORTER_OTLP_ENDPOINT` placeholder pointing at Azure Monitor.
- Passes `docker compose … config --quiet` with the base file.

### 9 — CI validation gates pass without live credentials

A CI-safe validation script or documented command sequence runs:
1. `terraform fmt -check -recursive`
2. `terraform init -backend=false` for `single-tenant-aca`
3. `terraform validate` for `single-tenant-aca`
4. All Compose `config --quiet` checks (base, overlays, strict-aca)
5. No-secret scan: no real GUIDs, tenant IDs, subscription IDs, or tokens in committed files.

All pass with exit code 0. No `terraform apply` is run.

### 10 — No secrets committed

Every file committed as part of M6 uses only:
- Brace-token placeholders: `{tenant-id}`, `{subscription-id}`, `{resource-group}`, `{tenant_id}`
- All-zero GUIDs: `00000000-0000-0000-0000-000000000000`
- Descriptive strings: `placeholder`, `PLACEHOLDER`

No real tenant IDs, subscription IDs, client IDs, client secrets, kubeconfigs, tokens, or certificates appear in any committed file.

---

## Non-Goals

- Deploying any resources to live Azure (no `terraform apply`).
- Implementing runtime code for the OBO path using managed identity (that is a future milestone).
- AKS deployment (optional advanced track from M5; not gated on M6).
- Cross-tenant or vendor-shaped ACA environments.
- M7 client variant implementations.
- Azure OpenAI / Foundry managed identity integration.
- Smoke tests against a live deployed endpoint (manual post-deployment step; no live credentials in repo).

---

## Dependencies

| Dependency | Type | Notes |
|-----------|------|-------|
| M5 (Spec 002) complete | Hard | M5 OTEL instrumentation is the foundation for Azure Monitor swap |
| M4 (Spec 005) complete | Hard | Compose base/overlay strategy and AUTH_MODE patterns are M6 inputs |
| Ashley approval of Agent Execution Service naming | Hard | T00 rename cannot proceed without approval |
| Morpheus architecture review (T11) | Gate | Blocks T01–T08 implementation |
| Trinity security review (T12) | Gate | Blocks T06, T09, T10 implementation |
