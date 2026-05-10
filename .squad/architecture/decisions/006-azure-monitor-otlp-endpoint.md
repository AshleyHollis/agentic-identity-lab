# ADR-006 / ADR-M6-02: Azure Monitor via OTLP Endpoint (Config-Only Swap from M5 Jaeger)

> **Status:** Accepted
> **Milestone:** M6 — Azure deployment baseline
> **Date:** 2026-06-01
> **Decided by:** Morpheus (Lead/Architect) — M6 T11 Architecture Review
> **Context ADR:** Spec 006 design.md §ADR-M6-02
> **Impact:** High — determines tracing backend strategy for all deployed ACA environments

---

## Context

M5 (Spec 002) delivered full OpenTelemetry instrumentation across all three Python services (BFF,
Agent Execution Service, MCP Protected API) via `apps/shared/python/identity_lab_auth/telemetry.py`.
The M5 instrumentation uses the OTEL SDK with an OTLP exporter. Locally, traces flow to a
containerised OTEL Collector → Jaeger via `OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317`.

M6 must document and scaffold the Azure Monitor tracing path for deployed ACA environments.
Two ingestion strategies are available:

1. **OTLP endpoint** (`https://{region}.otel.monitor.azure.com/v1/traces`) — SDK-native; env-var-only
   change; requires zero code modification.
2. **App Insights connection string** (`APPLICATIONINSIGHTS_CONNECTION_STRING`) — requires the Azure
   Monitor OpenTelemetry Distro package (`azure-monitor-opentelemetry`); adds a Python dependency;
   requires code change.

---

## Options Evaluated

**Option A — OTLP endpoint swap (RECOMMENDED)**

- Change `OTEL_EXPORTER_OTLP_ENDPOINT` env var from the local Jaeger URL to
  `https://{region}.otel.monitor.azure.com/v1/traces` at deploy time.
- Zero code change from M5. The OTEL SDK consumes `OTEL_EXPORTER_OTLP_ENDPOINT` natively.
- Vendor-neutral: if Azure Monitor is replaced (e.g., with Grafana Cloud or Honeycomb), only
  the env var changes — no code change, no package swap.
- Azure Monitor OTLP ingestion is GA as of 2024. Requires workspace-based Application Insights
  (not classic); this is the default for new resources.
- Local Compose + Jaeger continues to work unchanged for local development.

**Option B — App Insights connection string + Azure Monitor OpenTelemetry Distro**

- Adds `azure-monitor-opentelemetry` as a Python package dependency for all three services.
- Provides richer App Insights features: availability tests, live metrics stream, custom events.
- Requires code change in `identity_lab_auth/telemetry.py` and all three service entrypoints.
- Ties the instrumentation to Azure Monitor at the code level; swapping backends requires a
  code change.

---

## Decision

**Option A is accepted.** Azure Monitor is integrated via the OTLP endpoint env var swap only.
No code change from M5 instrumentation. `APPLICATIONINSIGHTS_CONNECTION_STRING` is deferred to
post-M6 as an optional enhancement.

### Rationale

1. **Zero code change:** M5 instrumentation (`identity_lab_auth/telemetry.py`) is already correct.
   The OTEL SDK reads `OTEL_EXPORTER_OTLP_ENDPOINT` without modification. Changing this env var
   is the minimum necessary to target Azure Monitor.
2. **Vendor neutrality:** The OTEL SDK is vendor-neutral by design. Coupling to the Azure Monitor
   distro at the code level would reduce portability of the lab reference implementation.
3. **M6 scope constraint:** M6 is a baseline — no `terraform apply`, no live Azure credentials.
   The App Insights connection string cannot be tested without live App Insights. The OTLP URL
   is documentable as a placeholder without requiring live validation.
4. **App Insights module:** The `app-insights` module (created in T02) outputs `connection_string`
   (sensitive). This output is available if a future milestone adds the Azure Monitor distro path.
5. **Local-vs-deployed distinction:** Local development continues to use Jaeger via Docker Compose
   tracing overlay (`docker-compose.tracing.yml`). Deployed ACA uses Azure Monitor. The
   `docker-compose.strict-aca.yml` overlay documents the Azure Monitor endpoint as a placeholder,
   making the local/deployed distinction explicit.

---

## Consequences

### Positive

- No code change in `identity_lab_auth/telemetry.py` or any service entrypoint.
- No new Python package dependencies.
- `python -m pytest` continues to pass with `OTEL_SDK_DISABLED=true` in test runs.
- Local Jaeger flow (M5) is completely unchanged for local development.
- Azure Monitor is activated purely by env var at deploy time.
- Future switch to any OTLP-compatible backend (Grafana Cloud, Honeycomb, Datadog OTLP) requires
  only an env var change.

### Negative / costs

- Richer App Insights features (availability tests, live metrics) are not available without the
  Azure Monitor distro. These are deferred to post-M6 as optional enhancements.
- Azure Monitor OTLP ingestion requires the Application Insights resource to be workspace-based
  (not classic). This is enforced by the `app-insights` module design (FR-04).
- `OTEL_EXPORTER_OTLP_ENDPOINT` uses HTTPS (not gRPC). The M5 local setup uses gRPC
  (`http://otel-collector:4317`). The OTEL SDK supports both; the switch is handled automatically
  by the endpoint URL scheme (`https://` → HTTP/1.1 OTLP, `http://` → gRPC OTLP).

### Neutral / informational

- `APPLICATIONINSIGHTS_CONNECTION_STRING` is documented as a post-M6 optional enhancement.
  The `app-insights` Terraform module (T02) outputs this value (sensitive) for use when needed.
- `OTEL_SDK_DISABLED=true` remains the correct setting for pytest runs (unchanged from M5).
- The env var pattern is documented in each service's `config/env/*.env.example` by Neo (T10).

---

## Open Questions Resolved

| Q# | Question | Resolution |
|----|----------|-----------|
| Q2 | Azure Monitor OTLP endpoint vs App Insights connection string | **Resolved: OTLP endpoint (Option A).** No code change. (This ADR) |

---

## Environment Variable Reference

| Context | `OTEL_EXPORTER_OTLP_ENDPOINT` value |
|---------|--------------------------------------|
| Local development (Compose) | `http://otel-collector:4317` (M5 tracing overlay) |
| Local strict-mode simulation | `https://{region}.otel.monitor.azure.com/v1/traces` (placeholder) |
| Deployed ACA | `https://{region}.otel.monitor.azure.com/v1/traces` (real region at deploy time) |
| Unit test runs | unset (OTEL_SDK_DISABLED=true) |

> **Placeholder format:** `{region}` must be replaced with the actual Azure region (e.g., `eastus`,
> `westeurope`) at deploy time. This value must NOT be committed as a real value.

---

## References

- Spec 006 design.md §ADR-M6-02, §Azure Monitor Tracing — OTLP Endpoint Swap Design
- Spec 006 research.md §1.5 (OTEL Instrumentation State)
- Spec 006 requirements.md §FR-07, §FR-04
- Spec 006 tasks.md §T02 (app-insights module), §T10 (env var documentation)
- `.squad/architecture/decisions/002-end-to-end-tracing-strategy.md`
- `apps/shared/python/identity_lab_auth/telemetry.py`
- Azure Monitor OTLP ingestion: https://learn.microsoft.com/en-us/azure/azure-monitor/app/opentelemetry-enable
