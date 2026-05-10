# ADR 0007: End-to-End Tracing Strategy — OpenTelemetry + Jaeger (Local) → Azure Monitor (Cloud)

## Status
Accepted

## Context
The lab's identity flows span multiple services. Without trace instrumentation it is difficult to
visualize where a request is, which service is responsible for a failure, and whether token exchanges
happen in the correct order. Ashley Hollis's directive requires end-to-end tracing across **all**
flows, including mock/local flows, so the environment is easy to visualize.

The standalone AKS Agent Gateway (agentgateway.dev) has a built-in OpenTelemetry → Jaeger pipeline
(OTLP collector on `localhost:4317`, Jaeger UI on `localhost:16686`). The lab's strategy aligns with
this native integration.

## Decision
Use **OpenTelemetry** (OTLP) as the standard instrumentation framework across all lab services.

| Phase | Tracing backend |
|-------|----------------|
| Local / mock (M5+) | Jaeger all-in-one in Docker Compose (`localhost:16686`) |
| AKS flows (M5+) | AKS Agent Gateway's built-in Jaeger integration |
| Azure / cloud (M6+) | Azure Monitor OTLP endpoint (env-var swap; no code change) |

**Propagation:** W3C TraceContext (`traceparent`/`tracestate`) on all outbound HTTP calls.

**PII safety:** Span attributes follow `sanitize_claims()` rules — `oid`, `sub`, `email`, `upn`,
`name`, raw bearer tokens are **never** included in span attributes.

**Test mode:** `OTEL_SDK_DISABLED=true` (or no-op exporter) in unit-test runs so tests do not
require a running Jaeger instance.

## Consequences
- Contributors can run `docker compose up` and open `localhost:16686` to see the BFF → Agentic
  Layer → MCP Protected API request chain as visual traces.
- The AKS Agent Gateway's built-in Jaeger spans appear in the same UI when AKS flows are exercised.
- Python services (`bff`, `agent-gateway/python-fastapi-*`, `mcp-protected-api`) gain OpenTelemetry
  SDK dependencies.
- Docker Compose gains a Jaeger all-in-one container.

## Full decision record
`.squad/architecture/decisions/002-end-to-end-tracing-strategy.md`
