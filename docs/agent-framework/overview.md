# Agent Framework — Agentic Layer Overview

The lab's **Agentic Layer** is the application-level agent orchestration component. It is hosted under
`apps/agent-gateway/` (legacy path; not renamed — see ADR 0006). It handles agent tool-call routing,
identity context enforcement, and multi-step agent coordination.

> **Terminology note (ADR 0006):**
> - **Agentic Layer** = the lab's app-level orchestration service (`apps/agent-gateway/`).
> - **AKS Agent Gateway** = the standalone [agentgateway.dev](https://agentgateway.dev) infrastructure
>   proxy running as a sidecar in AKS. It handles Entra Agent ID token acquisition and is **not** the
>   Agentic Layer.

The Agentic Layer exposes health and identity endpoints, plus service-specific invoke routes, while
deferring real JWT validation to a shared auth library (`identity_lab_auth`). All `/whoami` and debug
routes return only safe, sanitized claim metadata. Raw tokens are never returned or logged.

## Implementations

| Implementation | Path | Status |
|---------------|------|--------|
| Python (FastAPI) | `apps/agent-gateway/python-fastapi-agent-framework/` | Runnable reference |
| .NET | `apps/agent-gateway/dotnet-agent-framework/` | Scaffold (planned) |

## Separation of auth paths

| Path | Mechanism | Spec |
|------|-----------|------|
| MCP user-delegated OBO | `obo.exchange_on_behalf_of()` — user token → MCP audience | Spec 001/003 |
| Agent OBO (AKS track) | `agent_obo.AgentSidecarClient` — blueprint user token → MCP audience via AKS Agent Gateway sidecar | Spec 002 (M5) |
| Azure OpenAI / Foundry | Separate managed identity path; no shared import with the above | — |

## Observability

From M5 onward, the Agentic Layer is instrumented with OpenTelemetry. Traces flow to a Jaeger
instance (local Compose) or Azure Monitor (cloud). See ADR 0007 and
`.squad/architecture/decisions/002-end-to-end-tracing-strategy.md`.

## Roadmap note — AKS + Entra Agent ID (M5)

The AKS optional track (Spec 002) deploys the Agentic Layer to AKS with an **AKS Agent Gateway**
sidecar for Entra Agent ID token acquisition. The sidecar exposes `/Validate`,
`/AuthorizationHeader/{apiName}`, and `/DownstreamApi/{apiName}` on localhost only. The Agentic Layer
calls these endpoints; the sidecar is **not** the Agentic Layer itself.

