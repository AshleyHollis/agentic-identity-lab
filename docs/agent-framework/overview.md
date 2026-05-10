# Agent Framework — Agent Execution Service Overview

The lab's **Agent Execution Service** (formerly "Agentic Layer" — see ADR 0008) is the application-level
agent execution component. It is hosted under `apps/agent-gateway/` (legacy path; not renamed — see
ADR 0008). It hosts AI agents that perform agentic work on behalf of users, enforces Entra Agent
ID / OBO boundaries on every tool call, and is the code-first successor to PromptFlow-style Azure
Machine Learning flows.

> **Terminology note (ADR 0008):**
> - **Agent Execution Service** = the lab's app-level agent execution service (`apps/agent-gateway/` legacy path).
>   Display name: **Identity Lab Agent Execution Service** when org/lab qualification is useful.
> - **AKS Agent Gateway** = the standalone [agentgateway.dev](https://agentgateway.dev) infrastructure
>   proxy running as a sidecar in AKS. It handles Entra Agent ID token acquisition and is **not** the
>   Agent Execution Service.
> - **Azure AI Agent Service** / **Foundry Agent Service** = the Microsoft-managed hosted agent product
>   in Azure AI Foundry. This is a separate external product, not the lab's service. Do not use
>   unqualified "Agent Service" to mean the lab's service.
> - **Historical note:** "Agentic Layer" was the M5-era term (ADR 0006). ADR 0008 supersedes ADR 0006.

The Agent Execution Service exposes health and identity endpoints, plus service-specific invoke
routes, while deferring real JWT validation to a shared auth library (`identity_lab_auth`). All
`/whoami` and debug routes return only safe, sanitized claim metadata. Raw tokens are never
returned or logged.

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

From M5 onward, the Agent Execution Service is instrumented with OpenTelemetry. Traces flow to a
Jaeger instance (local Compose) or Azure Monitor (cloud). See ADR 0007 and
`.squad/architecture/decisions/002-end-to-end-tracing-strategy.md`.

## Roadmap note — AKS + Entra Agent ID (M5)

The AKS optional track (Spec 002) deploys the Agent Execution Service to AKS with an **AKS Agent
Gateway** sidecar for Entra Agent ID token acquisition. The sidecar exposes `/Validate`,
`/AuthorizationHeader/{apiName}`, and `/DownstreamApi/{apiName}` on localhost only. The Agent
Execution Service calls these endpoints; the sidecar is **not** the Agent Execution Service itself.

