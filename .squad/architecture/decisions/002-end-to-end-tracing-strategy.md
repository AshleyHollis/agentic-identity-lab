# ADR-002: End-to-End Tracing Strategy — OpenTelemetry + Jaeger (Local) → Azure Monitor (Cloud)

> **Status:** Accepted  
> **Date:** 2026-05-14  
> **Deciders:** Morpheus (Lead/Architect), Ashley Hollis (Product Owner)  
> **Phase:** architecture  
> **Impact:** High — cross-cutting observability requirement; applies from M5 onward to all request flows including mock/local flows.

## Context

The lab's identity flows span multiple services (Browser/Client → BFF → Agent Execution Service → [AKS Agent Gateway sidecar] → APIM → MCP Protected API). Without trace instrumentation, it is difficult to visualize where a request is, which service is responsible for a failure, and whether token exchanges happen in the correct order.

The directive from Ashley Hollis requires:
- End-to-end tracing across all flows, **including mock/local flows**, so the environment is easy to visualize.
- The AKS Agent Gateway (agentgateway.dev) has a built-in OpenTelemetry → Jaeger pipeline (referenced: https://agentgateway.dev/docs/standalone/main/reference/observability/traces/).

**Key facts from agentgateway.dev tracing docs:**
- The AKS Agent Gateway emits OTLP traces to an OpenTelemetry collector on `localhost:4317`.
- Jaeger receives collected traces; Jaeger UI is on `localhost:16686`.
- Supports static (global) and dynamic (per-listener) tracing configuration.
- Dynamic tracing allows CEL expressions on span attributes (e.g., `request.path`, `jwt.sub`).
- Trace spans include `list_tools` and `call_tool` for MCP tool invocations.

**The lab's mock/local flows** (M1–M4 complete; M5 in progress) run entirely in Docker Compose with fixture-based tokens and no live Azure endpoints. Tracing must work in this mode without any cloud dependency.

**Not in scope:**
- Implementing production-grade distributed tracing infrastructure.
- Log aggregation or metrics pipelines (a separate concern).
- Real `jwt.sub` values in span attributes (PII constraint — suppressed per `sanitize_claims()`).

## Ranked priorities

1. **Visibility in mock flows first** — contributors must be able to run `docker compose up` and see request traces without Azure credentials.
2. **Alignment with AKS Agent Gateway's native integration** — avoid a parallel tracing stack that diverges from agentgateway.dev's built-in pipeline.
3. **No PII in traces** — span attributes must not include `oid`, `sub`, `email`, `upn`, or raw bearer tokens; safe-claims rules apply to trace attributes.
4. **Incremental path to cloud** — the local Jaeger setup must be replaceable with Azure Monitor (OTLP endpoint) in M6+ without re-instrumenting services.

## Options considered

### Option 1: OpenTelemetry → Jaeger (local) → Azure Monitor (cloud)
Instrument all lab services with the OpenTelemetry SDK (Python: `opentelemetry-sdk`, `opentelemetry-exporter-otlp`). Run a Jaeger all-in-one container in Docker Compose for local visualization. In M6+, swap the OTLP exporter endpoint to Azure Monitor's OTLP ingestion URL.

**Pros:**
- Vendor-neutral instrumentation (OTLP standard).
- Consistent with the AKS Agent Gateway's native pipeline (both use OTLP → Jaeger).
- Jaeger runs in Docker with a single container; zero cloud dependency for local flows.
- Azure Monitor supports OTLP natively; migration is a config-only change (env var swap).
- W3C TraceContext propagation (`traceparent`/`tracestate`) is the OpenTelemetry default.

**Cons:**
- Adds `opentelemetry-sdk` and related packages as dependencies to BFF, Agent Execution Service, and MCP Protected API services.
- Mock/test flows will generate trace data; test isolation may require disabling or directing traces to a no-op exporter in unit test mode.

**Score against ranked priorities:**
- Priority 1 (mock flows first): ✅ Jaeger in Compose; zero cloud deps.
- Priority 2 (AKS alignment): ✅ Same OTLP pipeline as agentgateway.dev.
- Priority 3 (no PII): ✅ Span attributes use `sanitize_claims()` output keys only.
- Priority 4 (incremental to cloud): ✅ Env-var swap of OTLP endpoint.

### Option 2: Azure Application Insights SDK only
Use the Application Insights Python SDK for all services; skip local Jaeger.

**Pros:**
- Direct integration with Azure Monitor without an extra pipeline.

**Cons:**
- Requires Azure credentials and a live Application Insights resource for any trace visualization.
- Breaks Priority 1 (mock flows first).
- Diverges from the AKS Agent Gateway's Jaeger pipeline.

**Score against ranked priorities:**
- Priority 1 (mock flows first): ❌ No offline trace UI.
- Priority 2 (AKS alignment): ❌ Divergent pipeline.

### Option 3: Structured log correlation only (no distributed trace)
Use correlation IDs in log fields (already partially in place) and skip OTLP spans.

**Pros:**
- Zero new dependencies.

**Cons:**
- No graphical request-flow visualization.
- Correlation across services requires log querying, not a trace UI.
- Does not meet the Ashley Hollis directive ("visualize what is going on in the environment").

**Score against ranked priorities:**
- Priority 1 (mock flows first): ❌ No visual trace; logs only.

## Decision

We chose **Option 1**: OpenTelemetry SDK instrumentation for all lab services, Jaeger (Docker Compose) for local visualization, Azure Monitor (OTLP) for cloud visualization in M6+.

### Canonical tracing architecture

```
[Browser/Client]
      │  traceparent header
      ▼
[BFF]  ──── OTLP span ──────────────────────────────────────┐
      │  traceparent forwarded                               │
      ▼                                                      │
[Agent Execution Service]  ─── OTLP span ───────────────────────────────┤
      │  (AKS: AKS Agent Gateway sidecar emits its own spans) │
      ▼                                                      │
[APIM]  ─── (future: Azure Monitor span) ─────────────────────┤
      │                                                      │
      ▼                                                      ▼
[MCP Protected API]  ─── OTLP span ────────────────── OTLP Collector (localhost:4317)
                                                             │
                                                       Jaeger (localhost:16686)
                                                       [or Azure Monitor in M6+]
```

### Span attribute rules (PII safety)

Span attributes MUST follow safe-claims rules:
- ✅ Allowed: `service.name`, `http.method`, `http.route`, `http.status_code`, `trace.correlation_id`, `token.audience` (aud value only), `token.scope` (scp value only), `token.version` (ver).
- ❌ Prohibited: `oid`, `sub`, `email`, `upn`, `name`, `preferred_username`, raw bearer token strings.
- `jwt.sub` dynamic attribute (from agentgateway.dev CEL examples) MUST NOT be used in the lab; use `token.audience` instead.

### Propagation standard

W3C TraceContext headers (`traceparent`, `tracestate`) — the OpenTelemetry SDK default. All lab services MUST forward these headers on outbound HTTP calls.

### Local Compose service

Add a `jaeger` service to `docker/docker-compose.yml` (or an overlay) using `jaegertracing/all-in-one` image:
- OTLP gRPC collector: `localhost:4317`
- Jaeger UI: `localhost:16686`

### Mock/test mode

In `AUTH_MODE=mock` (offline pytest), tracing is directed to a **no-op OTLP exporter** (or suppressed via env var `OTEL_SDK_DISABLED=true`) so unit tests do not depend on a running Jaeger instance. Integration tests that validate trace emission use `pytest-httpserver` or an in-process OTLP receiver.

### Cloud migration (M6+)

Set `OTEL_EXPORTER_OTLP_ENDPOINT` to the Azure Monitor OTLP ingestion URL. No code changes required. All existing span definitions remain valid.

### Rationale

Option 1 satisfies all four priorities. It aligns with the agentgateway.dev pipeline (Priority 2), works offline in Docker Compose (Priority 1), propagates only safe attributes (Priority 3), and migrates to Azure Monitor by env-var swap (Priority 4).

### Consequences

**Positive:**
- Contributors can run `docker compose up` and open `localhost:16686` to see the full request chain as traces.
- The AKS Agent Gateway's built-in Jaeger spans are automatically visible in the same Jaeger UI when AKS flows are exercised.
- PII protection is enforced at the span attribute level, consistent with `sanitize_claims()`.

**Negative / costs:**
- Python services (`bff`, `agent-gateway/python-fastapi-*`, `mcp-protected-api`) gain OpenTelemetry SDK dependencies.
- Docker Compose gains a Jaeger container (resource overhead minimal for local dev).
- Test suites must explicitly disable or stub the OTLP exporter to avoid test-time network calls.

**Neutral / informational:**
- The existing correlation ID logging (already in place via `apps/shared/python`) complements rather than duplicates distributed traces — logs get `trace_id`/`span_id` injected; traces get `correlation_id` as a span attribute.

## Implementation notes

**M5 scope (this spec):**
- Design the trace instrumentation plan (this ADR).
- Add tracing outcome to M5 gate checklist.
- Add Jaeger to Docker Compose overlay (design only in M5; implementation in M5 implementation stream).
- Document span attribute rules in `docs/architecture/` or `docs/testing/`.

**M5 implementation tasks (add to Spec 002 or new Spec 006-tracing):**
- Add `opentelemetry-sdk`, `opentelemetry-exporter-otlp-proto-grpc` to service requirements.
- Instrument BFF, Agent Execution Service, and MCP Protected API with `tracer.start_as_current_span()`.
- Forward `traceparent`/`tracestate` on outbound HTTP calls.
- Add Jaeger all-in-one to Docker Compose.
- Add OTEL env vars to `.env.example` files.

**M6 scope:**
- Swap OTLP endpoint to Azure Monitor in Terraform/deployment config.
- Validate end-to-end traces visible in Azure Monitor.

## Review checkpoints

- [ ] M5 implementation start: Jaeger container added to Docker Compose; BFF span confirmed visible in Jaeger UI.
- [ ] M5 gate: Trace visualization confirmed for BFF → Agent Execution Service → MCP Protected API mock flow.
- [ ] M6 gate: Azure Monitor OTLP endpoint tested; traces visible in Azure portal.
- [ ] Re-review trigger: if `sanitize_claims()` rules change, re-verify span attribute allowlist.

## References

- Source directive: `.squad/decisions/inbox/copilot-directive-20260510171147.md`
- Amendment: `.squad/specs/002-aks-entra-agent-id/amendments/inbox/001-agentic-layer-gateway-tracing-roadmap.md`
- AKS Agent Gateway tracing docs: https://agentgateway.dev/docs/standalone/main/reference/observability/traces/
- Jaeger: https://www.jaegertracing.io
- OpenTelemetry Python SDK: https://opentelemetry.io/docs/languages/python/
- Azure Monitor OTLP: https://learn.microsoft.com/en-us/azure/azure-monitor/app/opentelemetry-enable
- Related ADR: `docs/adr/0007-end-to-end-tracing-strategy.md` (public-docs counterpart)
- Spec served: `.squad/specs/002-aks-entra-agent-id/` (M5 — adds tracing outcome)
