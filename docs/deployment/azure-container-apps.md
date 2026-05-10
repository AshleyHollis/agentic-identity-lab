# Azure Container Apps (Default)

Azure Container Apps is the default deployment target for this project. The Terraform environments under `infra/terraform/environments/` are validation-only and use placeholder IDs.

## Recommended flow
1. Populate `terraform.tfvars.example` with real values.
2. Run `terraform init -backend=false` and `terraform validate` to confirm wiring.
3. When approved, add an apply workflow using GitHub OIDC and managed identity (no secrets in repo).

## Azure Monitor OTLP configuration (ADR-M6-02)

All three Python services (BFF, Agent Execution, MCP Protected API) use a single
`OTEL_EXPORTER_OTLP_ENDPOINT` env var to configure OpenTelemetry tracing.  No code change
from the M5 instrumentation is required — only an endpoint swap.

### Local / offline
```
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317   # Jaeger or OTEL collector
```

### ACA deployment — Azure Monitor
Set the env var in each container app to the Azure Monitor OTLP ingestion endpoint for
your Log Analytics workspace region:
```
OTEL_EXPORTER_OTLP_ENDPOINT=https://{region}.otelgw.azure.com
```
Replace `{region}` with your workspace region (e.g. `eastus`, `westeurope`).  The endpoint
is public; **do not embed instrumentation keys or connection strings in env examples**.
Use a Key Vault reference or managed identity secret binding for any secret values.

### Span attribute security constraints
The following are enforced by `identity_lab_auth/telemetry.py` and must never be bypassed:

- Raw bearer token strings **must not** be set as span attributes.
- PII claim keys (`oid`, `sub`, `email`, `upn`, `name`, `preferred_username`,
  `given_name`, `family_name`) **must not** appear as span attributes.
- `identity_lab.fixture_name` is always set to `""` (empty) in `AUTH_MODE=strict`.

### Test environments
Set `OTEL_SDK_DISABLED=true` to disable all tracing in CI and unit-test runs.
Leave `OTEL_EXPORTER_OTLP_ENDPOINT` unset to activate the no-op tracer in offline/dev runs.

## Notes
- No deployment workflows are enabled by default.
- Use managed identity for runtime access (Key Vault, ACR, APIM).
- `AUTH_MODE` must be set to `strict` in all ACA container apps (not a variable — hardcoded
  per T03 design note).  `AUTH_MODE=mock` is unconditionally blocked in the deployment overlay.
