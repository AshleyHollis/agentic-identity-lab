# Spec 006 — Research

**Spec:** 006-azure-deployment-baseline
**Milestone:** M6 — Azure deployment baseline
**Updated:** 2026-06-01
**Author:** Tank

---

## 1. Current Infra State Audit

### 1.1 Terraform Modules (existing as of end of M5)

| Module | Path | Status | M6 relevance |
|--------|------|--------|--------------|
| `resource-group` | `infra/terraform/modules/resource-group/` | ✅ Scaffold complete | Used in all environments |
| `log-analytics` | `infra/terraform/modules/log-analytics/` | ✅ Scaffold complete | M6 needs App Insights linked here |
| `container-apps-env` | `infra/terraform/modules/container-apps-env/` | ✅ Scaffold complete | ACA environment |
| `container-app` | `infra/terraform/modules/container-app/` | ⚠️ Placeholder only (`# TODO`) | **M6: add resource body** |
| `apim` | `infra/terraform/modules/apim/` | ✅ Scaffold complete | M6: wire ACA backend |
| `apim-api` | `infra/terraform/modules/apim-api/` | ✅ Scaffold complete | M6: wire backend URL |
| `managed-identity` | `infra/terraform/modules/managed-identity/` | ✅ Scaffold complete | M6: assign per container app |
| `key-vault` | `infra/terraform/modules/key-vault/` | ✅ Scaffold complete | Reference only in M6 |
| `app-service` | `infra/terraform/modules/app-service/` | ✅ Scaffold complete | Not used in ACA path |
| `entra-app-registration` | `infra/terraform/modules/entra-app-registration/` | ✅ Scaffold complete | Reference only |
| `aks` | `infra/terraform/modules/aks/` | ✅ M5 skeleton | AKS optional path; not M6 default |
| `workload-identity` | `infra/terraform/modules/workload-identity/` | ✅ M5 skeleton | AKS path only |
| `k8s-bootstrap` | `infra/terraform/modules/k8s-bootstrap/` | ✅ M5 skeleton | AKS path only |
| `app-insights` | `infra/terraform/modules/app-insights/` | ❌ **Does not exist** | **M6: create** |

**Gap:** The `container-app` module has a placeholder `main.tf` (`# TODO`) with no resource body. This must be implemented in M6 for ACA deployment to be representable in Terraform.

**Gap:** No `app-insights` module exists. Azure Monitor requires an Application Insights resource linked to a Log Analytics workspace. This must be created.

### 1.2 Terraform Environments (existing as of end of M5)

| Environment | Path | Status | Notes |
|------------|------|--------|-------|
| `single-tenant` | `infra/terraform/environments/single-tenant/` | ✅ Exists | Uses App Service module (not ACA) |
| `cross-tenant/shared` | `infra/terraform/environments/cross-tenant/shared/` | ✅ Exists | Placeholder |
| `cross-tenant/tenant-a` | `infra/terraform/environments/cross-tenant/tenant-a/` | ✅ Exists | Placeholder |
| `cross-tenant/tenant-b` | `infra/terraform/environments/cross-tenant/tenant-b/` | ✅ Exists | Placeholder |
| `vendor-shaped-single-tenant` | `infra/terraform/environments/vendor-shaped-single-tenant/` | ✅ Exists | Placeholder |
| `aks` | `infra/terraform/environments/aks/` | ✅ M5 skeleton | AKS optional path |
| `single-tenant-aca` | `infra/terraform/environments/single-tenant-aca/` | ❌ **Does not exist** | **M6: create** |

**Key finding:** The existing `single-tenant` environment uses `modules/app-service`, not `modules/container-app`. The M6 baseline introduces a new `single-tenant-aca` environment that uses the ACA module path. The existing `single-tenant` environment is preserved unchanged.

### 1.3 APIM Policies (existing as of M3)

APIM ingress/egress policy XML exists under `infra/terraform/policies/apim/`:
- `ingress-validate-user-token.xml` — validates user JWT at APIM ingress (`aud` = BFF API, `scp` = `mcp.access`)
- `egress-validate-obo-token.xml` — validates OBO-exchanged token at egress
- `fragments/correlation-id.xml`, `fragments/rate-limit.xml`, `fragments/safe-logging.xml`

These policies are referenced by the APIM module. M6 wires the APIM module's backend URL to point at the ACA BFF endpoint. Policy XML is unchanged.

### 1.4 Docker Compose State (end of M5)

| File | Status | Notes |
|------|--------|-------|
| `docker/docker-compose.yml` | ✅ Complete | Base with `AUTH_MODE=mock`, health checks; service: `agent-gateway` |
| `docker/docker-compose.single-tenant.yml` | ✅ Complete | Overlay |
| `docker/docker-compose.vendor-shaped.yml` | ✅ Complete | Overlay |
| `docker/docker-compose.cross-tenant.local.yml` | ✅ Complete | Overlay |
| `docker/docker-compose.tracing.yml` | ✅ M5 Complete | OTEL collector + Jaeger overlay |
| `docker/docker-compose.strict-aca.yml` | ❌ **Does not exist** | **M6: create** |

The base compose service is named `agent-gateway`. After T00, it becomes `agent-execution`.

### 1.5 OTEL Instrumentation State (end of M5)

M5 delivered full OTEL instrumentation in `apps/shared/python/identity_lab_auth/telemetry.py`:
- `setup_telemetry()`, `get_tracer()`, `instrument_fastapi()`, `record_auth_attributes()`, `record_obo_attributes()`, `safe_span_attribute_key()`
- All three services instrumented (BFF, Agent Execution Service, MCP Protected API)
- `OTEL_EXPORTER_OTLP_ENDPOINT` env var already consumed by the OTEL SDK
- `OTEL_SDK_DISABLED=true` in unit test runs (no-op exporter)

**M6 Azure Monitor swap:** Azure Monitor supports OTLP ingestion at `https://{region}.otel.monitor.azure.com/v1/traces`. This is a pure env var change — no code change. The OTEL SDK consumes `OTEL_EXPORTER_OTLP_ENDPOINT` natively.

**Connection string vs OTLP:** Azure Monitor also supports direct Application Insights SDK ingestion via `APPLICATIONINSIGHTS_CONNECTION_STRING`. The OTLP endpoint approach is preferred for M6 because it requires zero code change from M5 and preserves OTEL vendor-neutrality (ADR-M6-02 pending Morpheus review).

### 1.6 AUTH_MODE=strict — Current Behaviour Audit

Based on Spec 001 and M5 implementation:

- `AUTH_MODE=strict` causes the shared auth library to ignore `X-Identity-Lab-Fixture` header.
- In strict mode, `AUTH_ISSUER` and `AUTH_JWKS_URL` are required. Missing values → startup error.
- JWKS validation is enforced: `alg:none` rejected, `HS*` rejected, `kid` required (Spec 002 T09).
- Fixture header suppression in strict mode was verified in M5 T18 (OTEL span has `fixture_name` blanked in strict mode).

**Gap to verify:** Confirm that a missing `AUTH_ISSUER` or `AUTH_JWKS_URL` in strict mode causes a clear startup error (not a silent default) across all three services. Task T09 verifies this.

---

## 2. Azure Container Apps — Design Research

### 2.1 ACA vs AKS for M6 Default Path

Per Tank charter: "Keep Azure Container Apps as the default deployment target."
Per roadmap M6: "APIM + Container Apps with managed identity."
Per Spec 002 ADR-M5-01: AKS is an optional track; ACA remains the default.

ACA advantages for this lab context:
- No cluster management overhead.
- Native managed identity support (`azurerm_container_app` → `identity` block).
- Native Dapr support (future option).
- KEDA-based scaling (optional).
- Lower operational cost for a lab/reference implementation.

AKS optional advanced path: Available from M5 Terraform skeletons. Entra Agent ID / AKS Agent Gateway remain available for contributors who want to exercise the advanced path. This is not gated on M6.

### 2.2 Managed Identity Strategy Research

Azure Container Apps supports:
- **System-assigned managed identity:** Tied to the container app lifecycle; simpler but harder to pre-assign roles.
- **User-assigned managed identity:** Created independently; can be assigned roles before the container app exists; recommended for infrastructure-as-code workflows.

For M6, user-assigned managed identity per service is preferred (ADR-M6-03 pending Trinity review):
- Allows role assignments to be defined in Terraform before the container app is created.
- Consistent pattern across all three services.
- The `managed-identity` module already scaffolds `azurerm_user_assigned_identity`.

### 2.3 APIM + ACA Backend Wiring

APIM backend URL for ACA follows the pattern:
```
https://<container-app-name>.<env-unique-id>.<region>.azurecontainerapps.io
```

This URL is an output of the `container-app` Terraform module. The APIM module reads it via `var.backend_url`. M6 wires this output-to-input connection in the `single-tenant-aca/main.tf`.

### 2.4 Workload Identity (ACA)

ACA supports workload identity federation (GitHub OIDC → Azure managed identity) for CI/CD. M6 documents this in `terraform.tfvars.example` as comments. No live federated credential is committed. The pattern is:
1. GitHub Actions OIDC token issued by GitHub.
2. `azure/login` action exchanges OIDC token for Azure access token via federated credential.
3. Terraform uses this access token; no client secret required.

This is documentation only in M6 — no live wiring.

---

## 3. Naming Dependency

The task prompt states: **Approved central component name: Agent Execution Service, slug agent-execution, display name Identity Lab Agent Execution Service.**

The Morpheus v2 naming proposal (`.squad/decisions/inbox/morpheus-naming-proposal-pre-m6-v2.md`) proposed "Agent Runtime." Ashley has approved "Agent Execution Service" as the canonical name. This spec uses "Agent Execution Service" throughout. T00 implements the rename.

All M6 Terraform resource names, Compose service names, and documentation use `agent-execution` as the slug.

---

## 4. Open Questions for Review Gate

| # | Question | Owner | Priority |
|---|----------|-------|----------|
| Q1 | ACA default vs AKS — confirm Morpheus accepts ACA as M6 default | Morpheus (T11) | High |
| Q2 | Azure Monitor OTLP endpoint vs App Insights connection string — confirm approach | Morpheus (T11) | High |
| Q3 | User-assigned vs system-assigned managed identity per service | Trinity (T12) | High |
| Q4 | k8s-bootstrap namespace inconsistency from M5 (flagged in T14) — address in M6 or defer | Morpheus (T11) | Medium |
| Q5 | APIM managed identity role assignment scope (subscription vs resource group) | Tank + Trinity (T12) | Medium |
| Q6 | Container app ingress: external (public) or internal (VNet)? | Morpheus (T11) | Medium |
