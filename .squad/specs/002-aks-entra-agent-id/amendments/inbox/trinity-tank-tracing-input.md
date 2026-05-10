# Trinity + Tank Tracing Input — Spec 002 / Roadmap

**Reviewers:** Trinity (security/identity), Tank (infra/runtime observability)  
**Requested by:** Ashley Hollis  
**Phase:** M5 observability/tracing amendment — pre-implementation design input  
**Relates to:** Amendment 001 (`001-agentic-layer-gateway-tracing-roadmap.md`)  
**Status:** Input — pending Morpheus/squad acceptance before implementation  
**Date:** 2026-05-27

---

## Scope and intent

This document feeds the tracing/observability requirements into Spec 002 and the project roadmap.
It covers the full request path — browser/client → BFF → agentic layer (local Python gateway) →
standalone Agent Gateway (AKS) → APIM → Agent ID sidecar → OBO exchange → MCP protected API —
for both mock/local flows and future Azure/AKS deployments.

It does **not** prescribe implementation code. All pseudocode and schema here is design-input only.

---

## Context observations from the codebase

| Observation | Implication |
|---|---|
| All three apps (`bff`, `agent-gateway`, `mcp-protected-api`) already call `identity_lab_diagnostics.get_correlation_id()` and surface `correlation_id` in every response. | Correlation ID scaffolding exists; it needs to be promoted to OTel trace context. |
| `CORRELATION_HEADER=x-correlation-id` is set per-service in `docker-compose.yml`. | The header name is configurable and consistent across the compose stack today. |
| No `traceparent` / `tracestate` (W3C Trace Context) propagation exists yet. | OTel propagation middleware is absent in all three FastAPI apps. |
| No OTel collector, Jaeger, or Azure Monitor exporter service in `docker-compose.yml`. | The compose stack needs an optional trace sink for local visualization. |
| Agent Gateway standalone uses OTel → Jaeger via static or dynamic frontend-policy tracing (agentgateway.dev docs). | When AKS-deployed, the standalone gateway emits spans natively; the lab services must propagate context into it. |
| `sanitize_claims()` already drops `oid`/`sub`; `xms_act_fct` handling is a tracked design gap (design.md §Security). | Safe-claim dimension rules extend naturally to span attribute filtering. |

---

## TR-01 — Span/Trace Model

### TR-01.1 — Canonical trace boundary map

Every inbound user request to the BFF MUST produce a single distributed trace that spans all processing layers.
The following spans are required (names are logical; implementation uses OTel conventions):

```
[Trace root]
 └── bff.request                          # BFF receives inbound call
      ├── bff.auth.validate               # Token validation / fixture resolution
      ├── bff.session.create  (if POST)   # Session ID generation (no PII)
      └── agentic-layer.invoke            # BFF → agentic layer (local agent-gateway)
           ├── agentic-layer.auth.validate
           ├── agentic-layer.obo.exchange  # MCP user OBO or Agent OBO
           │    └── [sidecar boundary — see TR-01.3]
           └── mcp-protected-api.call
                ├── mcp.auth.validate
                └── mcp.tool.execute      # /tools/echo, /tools/authorization-check, etc.
```

For flows involving the standalone Agent Gateway (AKS/M6+):

```
[Trace root — propagated from BFF]
 └── apim.policy.inbound                 # APIM ingress policy span (future)
      └── standalone-agent-gateway.route  # agentgateway OTel span (native)
           ├── agent-id-sidecar.validate  # Sidecar /Validate call
           ├── agent-id-sidecar.obo       # Sidecar /DownstreamApi/{apiName}
           └── mcp-protected-api.call
```

### TR-01.2 — Mandatory span attributes (safe dimensions only)

The following attributes are permitted on any span. No other identity-derived attributes may be added
without a corresponding allowlist amendment reviewed by Trinity.

| Attribute key | Value source | Notes |
|---|---|---|
| `identity_lab.auth_mode` | `AUTH_MODE` env var | `mock`, `strict` |
| `identity_lab.token_type` | `AuthContext.token_type` | `delegated`, `app-only`, `none` |
| `identity_lab.aud` | sanitized claim `aud` | Audience string; safe — no user identity |
| `identity_lab.tid` | sanitized claim `tid` | Tenant ID; acceptable for tracing dimensions |
| `identity_lab.scp` | sanitized claim `scp` | Scope string; safe |
| `identity_lab.appid` | sanitized claim `appid` | App/service ID; safe |
| `identity_lab.authorized` | `AuthContext.authorized` | Boolean |
| `identity_lab.fixture_name` | fixture header value | Only in `AUTH_MODE=mock`; must be blank in strict |
| `service.name` | OTel resource attribute | Per-service: `bff`, `agent-gateway`, `mcp-protected-api`, `agent-gateway-standalone` |
| `service.version` | App version | e.g. `0.1.0` |
| `correlation_id` | `x-correlation-id` header | Preserved for backward compat with existing responses |

### TR-01.3 — Agent ID sidecar span boundary

Sidecar calls (mock or real) MUST be instrumented as child spans under the agentic-layer invoke span.
In offline/mock mode the sidecar span is a local no-op span (no network call occurs);
its presence in the trace is still required to make the mock flow visualizable in the same
trace view as future live flows.

Sidecar child span names:
- `sidecar.validate` — maps to `GET /Validate`
- `sidecar.authorization-header` — maps to `GET /AuthorizationHeader/{apiName}`
- `sidecar.downstream-api` — maps to `POST /DownstreamApi/{apiName}`

Attributes on sidecar spans:
- `sidecar.api_name` — the named API parameter
- `sidecar.mode` — `mock` or `live`
- `sidecar.result` — `valid`, `invalid`, `error` (no token value)
- `sidecar.reject_reason` — `token_expired`, `wrong_audience`, `untrusted_tenant`, etc. (only on rejection)

### TR-01.4 — APIM policy span (future, M6)

APIM policy spans are out of scope for M5 mock flows but MUST be designed for forward compatibility.
The APIM inbound policy MUST forward the W3C `traceparent` header downstream unchanged.
APIM itself does not natively emit OTel spans; a custom policy header passthrough is sufficient for M6.

---

## TR-02 — Correlation ID and W3C Trace Context Propagation

### TR-02.1 — Header priority and coexistence

The existing `x-correlation-id` header MUST continue to work unchanged.
OTel W3C Trace Context (`traceparent`, `tracestate`) is layered on top, not a replacement.

Priority rules:
1. If an inbound request carries a `traceparent`, extract it as the parent span context.
2. The `x-correlation-id` is extracted from the inbound request (existing behaviour).
3. If no `x-correlation-id` is present, a new UUID is generated (existing behaviour).
4. The `x-correlation-id` is added as a span attribute (`correlation_id`) on the root span.
5. Outbound requests to downstream services MUST carry both `traceparent` and `x-correlation-id`.

### TR-02.2 — Mock/local flow propagation requirement

In the mock Docker Compose stack, all three services MUST propagate `traceparent` on inter-service
calls. This is required even when no collector is configured — the header is generated and forwarded
silently (OTel SDK no-op exporter). When a collector IS configured, traces become visible with no
code change.

### TR-02.3 — Fixture-flow traceability

Mock flows using `X-Identity-Lab-Fixture` MUST be distinguishable in traces via the
`identity_lab.fixture_name` span attribute (see TR-01.2). This enables filtering all mock/fixture
traces in a dashboard without changing trace structure.

---

## TR-03 — OpenTelemetry Compatibility and Public-Safe Defaults

### TR-03.1 — SDK and exporter selection

| Layer | OTel SDK | Exporter (default) | Exporter (Azure, M6+) |
|---|---|---|---|
| BFF, agentic layer, MCP API | `opentelemetry-sdk` (Python) | `OTLPSpanExporter` (gRPC, localhost:4317) or no-op if unconfigured | `azure-monitor-opentelemetry-exporter` |
| Standalone Agent Gateway (AKS) | Native (agentgateway built-in) | OTel collector → Jaeger (per agentgateway.dev docs) | OTel collector → Azure Monitor |

The OTLP exporter endpoint MUST be configurable via `OTEL_EXPORTER_OTLP_ENDPOINT` environment variable.
When this variable is unset, the SDK MUST default to a no-op exporter — **no network calls, no errors,
no required local collector** — so offline tests remain unaffected.

### TR-03.2 — Sampling defaults (public-safe)

Default sampling MUST be `ParentBased(root=AlwaysOn)` in mock/local mode.
In AKS/production mode the default SHOULD be `TraceIdRatioBased(0.1)` (10%) or parent-based.
Sampling rate MUST be configurable via `OTEL_TRACES_SAMPLER` and `OTEL_TRACES_SAMPLER_ARG`
standard env vars — no lab-specific sampling config required.

The standalone Agent Gateway's `randomSampling` and `clientSampling` knobs (per agentgateway.dev
dynamic tracing docs) MUST be set to appropriate values in the AKS deployment manifests.
For local Compose the gateway's static tracing config (if used) should enable `randomSampling: true`.

### TR-03.3 — Service name and resource attributes

Each service MUST set `service.name` as an OTel resource attribute matching its Docker Compose
service name: `bff`, `agent-gateway`, `mcp-protected-api`.
The standalone Agent Gateway in AKS MUST set `service.name=agent-gateway-standalone` to distinguish
it from the local Python agentic layer service. This prevents confusion in Jaeger service dropdowns.

---

## TR-04 — Security Constraints (Trinity)

### TR-04.1 — Absolute prohibitions on span attributes

The following MUST NEVER appear as span attributes, log fields, or structured log dimensions,
regardless of `AUTH_MODE`:

| Prohibited value | Category |
|---|---|
| Raw bearer token string | Credential |
| `oid` claim value | PII (user object ID) |
| `sub` claim value | PII (user subject) |
| `email`, `upn`, `preferred_username` | PII (user identity) |
| `name`, `given_name`, `family_name` | PII (user name) |
| `client_secret`, any secret string | Credential |
| Full JWT (header.payload.signature) | Credential + PII |

These align with the existing `sanitize_claims()` suppression list in `FR-05` / `NFR-01`.

### TR-04.2 — Fixture header in strict mode

When `AUTH_MODE=strict`, the `identity_lab.fixture_name` span attribute MUST be set to an empty
string or omitted. The fixture header value MUST NOT be recorded in any span, log, or structured
output in strict mode (mirrors the strict-mode fixture suppression in `design.md`).

### TR-04.3 — Trace export destination security

The OTLP exporter endpoint (`OTEL_EXPORTER_OTLP_ENDPOINT`) MUST NOT be set to a public internet
address in any committed config, compose file, or `.env.example`. Permitted values are:
- `http://localhost:4317` or `http://127.0.0.1:4317` (local Jaeger/collector)
- `http://otel-collector:4317` (internal Docker network)
- Azure Monitor connection string via `APPLICATIONINSIGHTS_CONNECTION_STRING` (M6+, no bearer token in URL)

### TR-04.4 — Trace data retention and PII

Future Azure Monitor integration MUST use sampling or custom telemetry processors to ensure
PII-bearing span attributes (if any slip through) are scrubbed before export.
A `SafeClaimSpanProcessor` (name is illustrative) SHOULD be designed as a pipeline step that
applies the same `sanitize_claims()` allowlist logic to span attributes before they leave the process.
This processor is a design requirement for M6; it is not required for M5 mock flows.

---

## TR-05 — Standalone Agent Gateway Trace Integration (AKS)

Based on [agentgateway.dev tracing reference](https://agentgateway.dev/docs/standalone/main/reference/observability/traces/):

### TR-05.1 — Static vs dynamic tracing choice

**Recommendation:** Use **dynamic tracing** (frontend-policy level) for AKS deployments.
Rationale: each listener (BFF-facing, MCP-facing) may have different sampling and attribute needs.
Dynamic tracing allows CEL expression-based span attributes — e.g., `request.path` for route
dimensions — without rebuilding the gateway binary.

### TR-05.2 — Attribute configuration for identity flows

For the agent-gateway standalone frontend policies in AKS, the following dynamic span attributes
SHOULD be configured (CEL expressions are illustrative):

```yaml
# frontendPolicies[].tracing.attributes (agentgateway dynamic tracing)
- key: identity_lab.auth_mode
  value: "'strict'"                     # literal; AKS always strict
- key: identity_lab.route
  value: request.path                   # dynamic; safe — no PII
- key: identity_lab.method
  value: request.method
# NOTE: jwt.sub MUST NOT be used as a CEL expression here — PII prohibition (TR-04.1)
# NOTE: jwt.oid MUST NOT be used — PII prohibition (TR-04.1)
```

### TR-05.3 — Service name in Jaeger/Azure Monitor

The standalone Agent Gateway MUST set the `service.name` resource attribute to
`agent-gateway-standalone` so it appears as a distinct service in Jaeger's service dropdown
and in Azure Monitor's application map.

### TR-05.4 — Collector and Jaeger in AKS (M6)

An OTel collector sidecar or DaemonSet MUST be included in the AKS deployment design (M6 scope).
The collector receives traces from both the standalone Agent Gateway and the Python services via OTLP gRPC.
For M5 (skeleton only), the AKS manifests SHOULD include commented-out collector references
so the pattern is documented before M6 implementation.

### TR-05.5 — Local Compose Jaeger profile (optional, M5 scope)

A Jaeger all-in-one container SHOULD be added to `docker-compose.yml` under an optional
`--profile tracing` profile. This means: not started by default, requires explicit `--profile tracing`
flag. When started, it exposes `localhost:16686` (Jaeger UI) and `localhost:4317` (OTel gRPC).
Services should pick up `OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317` via a
compose profile overlay.

This is the primary visualization mechanism for mock flows without any live Azure dependency.

---

## TR-06 — Azure Monitor / Application Insights Integration Path (M6+)

### TR-06.1 — Connection string pattern

The Azure Monitor OTLP exporter for Python accepts `APPLICATIONINSIGHTS_CONNECTION_STRING`.
This env var MUST only be set in:
- AKS environment overlays (`infra/terraform/environments/aks/*.tfvars.example` — placeholder only)
- Kubernetes secrets (not committed)
- Local `.env` files (gitignored, never committed)

### TR-06.2 — No live Azure required for mock tests

All pytest tests MUST continue to pass with `APPLICATIONINSIGHTS_CONNECTION_STRING` unset.
The OTel SDK no-op exporter fallback (TR-03.1) ensures this.

### TR-06.3 — Application map topology

When connected to Application Insights, the distributed trace MUST produce an application map
showing:
```
[browser] → bff → agent-gateway → [sidecar] → mcp-protected-api
                                 ↑
                          (standalone-agent-gateway in AKS path)
```
This topology is verified visually in M6 acceptance, not by automated test.

### TR-06.4 — KQL query patterns for identity flows

The following KQL patterns SHOULD be documented in `docs/observability/` (new directory, M6 scope)
for querying identity/auth events in Log Analytics:

```kql
// All rejected auth events (non-PII dimensions)
AppDependencies
| where Properties["identity_lab.authorized"] == "false"
| project TimeGenerated, Name, Properties["identity_lab.auth_mode"],
          Properties["identity_lab.token_type"], Properties["sidecar.reject_reason"]
| order by TimeGenerated desc

// Fixture-based mock requests (filter in dev)
AppRequests
| where Properties["identity_lab.fixture_name"] != ""
| summarize count() by Properties["identity_lab.fixture_name"], bin(TimeGenerated, 5m)
```

---

## Acceptance Criteria

The following acceptance criteria SHOULD be added to Spec 002 (and carried into M5/M6 task lists):

### For M5 (mock/local flows)

| AC | Criterion |
|---|---|
| AC-TR-01 | A `correlation_id` attribute appears on spans for all three services in the mock Compose stack when a trace collector is active. |
| AC-TR-02 | `traceparent` is forwarded on all inter-service HTTP calls in the mock Compose stack. |
| AC-TR-03 | No raw token string, `oid`, `sub`, `email`, or `upn` value appears in any span attribute in any `AUTH_MODE`. |
| AC-TR-04 | In `AUTH_MODE=mock`, the `identity_lab.fixture_name` span attribute is present and non-empty; in `AUTH_MODE=strict` it is absent or empty. |
| AC-TR-05 | The OTel SDK defaults to a no-op exporter when `OTEL_EXPORTER_OTLP_ENDPOINT` is unset; `python -m pytest` passes with this variable unset. |
| AC-TR-06 | A Jaeger `--profile tracing` compose profile (or equivalent) allows a developer to run `docker compose --profile tracing up` and see end-to-end spans for a mock `/agent/invoke` call in the Jaeger UI. |
| AC-TR-07 | Sidecar mock spans appear in the trace tree (as local no-op spans) under the agentic-layer invoke span, making the mock OBO flow visualizable. |

### For M6 (AKS / Azure Monitor)

| AC | Criterion |
|---|---|
| AC-TR-08 | The standalone Agent Gateway emits spans with `service.name=agent-gateway-standalone` visible in Jaeger and/or Azure Monitor application map. |
| AC-TR-09 | A `SafeClaimSpanProcessor` (or equivalent telemetry processor) is active in the OTel pipeline, preventing prohibited attributes from reaching the Azure Monitor exporter. |
| AC-TR-10 | The Application Insights application map shows the expected four-node topology (bff → agent-gateway → sidecar → mcp-protected-api). |
| AC-TR-11 | `APPLICATIONINSIGHTS_CONNECTION_STRING` unset → no test failure; set → traces appear in Application Insights within 60 seconds of a request. |

---

## Recommended New Tasks for Spec 002 / Roadmap

These tasks SHOULD be added to `tasks.md` (or a new tracing sub-spec) by Morpheus after review:

| Task ID | Owner | Description | Depends on |
|---|---|---|---|
| T-OBS-01 | Tank | Add optional `--profile tracing` Jaeger service to `docker-compose.yml` | T02, T03 |
| T-OBS-02 | Neo | Add OTel SDK middleware to BFF, agentic-layer, MCP API (no-op default, OTLP when configured) | T-OBS-01 |
| T-OBS-03 | Neo | Propagate `traceparent` + `x-correlation-id` on all outbound inter-service HTTP calls | T-OBS-02 |
| T-OBS-04 | Neo | Instrument sidecar boundary (mock + live) with child spans per TR-01.3 | T10, T-OBS-02 |
| T-OBS-05 | Trinity | Implement and test `SafeClaimSpanProcessor` / span attribute filter (M6 pre-req) | T-OBS-02 |
| T-OBS-06 | Tank | Document standalone Agent Gateway dynamic tracing config for AKS manifests (TR-05) | T05 |
| T-OBS-07 | Tank + Trinity | Write `docs/observability/` with KQL patterns and Application Insights topology diagram | T-OBS-05 |

**Blocking recommendation:** T-OBS-01 through T-OBS-04 SHOULD be added to the M5 task set.
T-OBS-05 through T-OBS-07 belong in M6.

---

## ADR Recommendation

Trinity + Tank jointly recommend a new ADR for Spec 002:

**ADR-M5-04 — Observability/tracing strategy**

_Question:_ Should distributed tracing use (A) OTel SDK with OTLP no-op default + Jaeger local opt-in,
or (B) Azure Monitor SDK direct instrumentation from day one?

_Recommendation:_ **Option A** — OTel SDK with no-op default. Rationale:
- Zero impact on offline tests (no-op exporter when unconfigured).
- Jaeger local profile provides visualization without any Azure dependency.
- Azure Monitor is an additional OTLP exporter added at M6; no code change required in services.
- Aligns with standalone Agent Gateway's native OTel → OTLP pipeline.
- Prevents any accidental PII/token export to a live Azure workspace during M5 development.

_Owner:_ Morpheus (architecture) + Tank (infra), reviewed by Trinity (security).

---

## Terminology Note (Amendment 001 alignment)

Consistent with Amendment 001, this document uses:

| Term | Meaning |
|---|---|
| **Agentic layer** | The lab's local Python agentic/orchestration runtime (`apps/agent-gateway/python-fastapi-agent-framework`) |
| **Standalone Agent Gateway** | The `agentgateway.dev` binary/container deployed in AKS as a protocol gateway/proxy |
| **MCP protected API** | `apps/mcp-protected-api/python-fastapi` |
| **Agent ID sidecar** | Entra Agent ID sidecar process (co-located with the standalone Agent Gateway in AKS) |

These terms are used consistently in all span names, attribute keys, and task descriptions above.
