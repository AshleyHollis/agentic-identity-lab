# ADR 0008: Agent Execution Service — Canonical Naming

## Status
Accepted — supersedes ADR 0006

## Context

ADR 0006 established "Agentic Layer" as the canonical term for the lab's application-level
orchestration service, resolving the original ambiguity with the AKS Agent Gateway
(agentgateway.dev). While that terminology improved clarity during M5, "Agentic Layer" is a
descriptive architectural phrase rather than a proper service name.

Pre-M6 planning confirmed that this component will:
- Host the **Microsoft Agent Framework** and run AI agents performing agentic work on behalf of
  users.
- Replace PromptFlow-style Azure Machine Learning flows with code-first agent execution (see
  also ADR 0004 — No PromptFlow).
- Use **Entra Agent ID / OBO boundaries** to preserve user-delegated identity across every agent
  tool call.
- Run in AKS (or ACA) with many downstream services depending on it.

The component needs a name that functions as a proper service noun — usable in Terraform resource
names, Kubernetes labels, ADR references, and external contributor documentation without
disambiguation footnotes.

## Decision

Adopt **Agent Execution Service** as the canonical service name.

| Context | Name |
|---------|------|
| Short / prose references | **Agent Execution Service** |
| Qualified / lab-context references | **Identity Lab Agent Execution Service** |
| Filesystem slug (legacy) | `apps/agent-gateway/` *(not renamed; preserved for backward compatibility)* |
| Future filesystem slug (after runtime rename) | `agent-execution` |

### Why "Agent Execution Service" over alternatives

| Candidate | Why rejected |
|-----------|-------------|
| Agentic Layer | Phrase, not a service name; "Layer" implies architecture tier, not a deployable service. |
| Agent Gateway | Collides with [agentgateway.dev](https://agentgateway.dev) and the AKS Agent Gateway sidecar. |
| Agent Service (unqualified) | Collides with **Azure AI Agent Service** (Azure AI Foundry managed product). |
| Agent Runtime | Not established naming for this layer; implies a language/process runtime. |
| Agentic Service | Informal adjective; not a recognised service naming pattern. |
| Agentic Orchestration Service | Accurate but verbose; "orchestration" risks confusion with orchestrator patterns. |

### Preserved component distinctions

| Component | Name |
|-----------|------|
| Lab's agent execution application service | **Agent Execution Service** *(this ADR)* |
| agentgateway.dev infrastructure proxy in AKS | **AKS Agent Gateway** *(ADR 0006; unchanged)* |
| Entra Agent ID sidecar container | **Entra Agent ID sidecar** |
| API Management gateway | **APIM** |
| Backend-for-Frontend | **BFF** |
| MCP-protected downstream API | **MCP Protected API** |
| Azure AI Foundry hosted agents | **Azure AI Agent Service** / **Foundry Agent Service** — external Microsoft product; do not use unqualified "Agent Service" to mean the lab's service. |

## Consequences

- All documentation using "Agentic Layer" is updated to "Agent Execution Service".
- The legacy directory `apps/agent-gateway/` and Docker Compose service `agent-gateway` are
  unchanged until a separate runtime rename is completed (Neo/Tank work item).
- ADR 0006 is retained as historical record but marked superseded by this ADR.
- Unqualified "Agent Service" is prohibited in new documentation (collision risk with Azure AI
  Agent Service).

## Full decision record

`.squad/architecture/decisions/004-agent-execution-service-naming.md`
