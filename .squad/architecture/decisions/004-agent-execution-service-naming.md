# ADR-004: Agent Execution Service — Canonical Naming

> **Status:** Accepted  
> **Supersedes:** ADR-001 (`.squad/architecture/decisions/001-agentic-layer-vs-agent-gateway-terminology.md`)  
> **Date:** 2026-05-10  
> **Approved by:** Ashley Hollis (Product Owner) — 2026-05-10T19:30:22.457+10:00  
> **Deciders:** Morpheus (Lead/Architect), Ashley Hollis (Product Owner)  
> **Phase:** pre-M6 naming amendment  
> **Impact:** High — central component name affects roadmap, specs, ADRs, docs, M6 implementation, and all future references.

---

## Context

ADR-001 established "Agentic Layer" as the canonical term for the lab's application-level orchestration service after resolving ambiguity with the AKS Agent Gateway (agentgateway.dev). That naming improved clarity at M5 but remained an internal descriptive phrase rather than a proper service name.

During pre-M6 planning, Ashley Hollis raised three successive concerns (captured in `.squad/decisions/inbox/copilot-directive-20260510190927.md` through `…190929.md`):

1. The component will contain the **Microsoft Agent Framework** and run AI agents that perform agentic work on behalf of users — replacing PromptFlow-style Azure Machine Learning flows with code-first agent execution.
2. It will be hosted in AKS, host many AI agents, use **Entra Agent ID / OBO boundaries**, and many services will depend on it.
3. The name must clearly describe _what the component does_, not merely distinguish it from another component.

External research (Morpheus naming proposal v2, `.squad/decisions/inbox/morpheus-naming-proposal-pre-m6-v2.md`) evaluated six candidate names against three constraints: **low collision** (no clash with established Azure/Microsoft product names), **descriptive** (clearly conveys function), and **scalable** (works as a proper service name across M6/M7 and future contributors).

---

## Rejected Candidates

| Candidate | Rejection reason |
|-----------|-----------------|
| **Agentic Layer** *(ADR-001 term)* | Descriptive phrase, not a service name. "Layer" implies architecture tier, not a deployable service. Not scalable as a proper noun for external contributors. |
| **Agent Gateway** | Collides directly with [agentgateway.dev](https://agentgateway.dev) and the AKS Agent Gateway sidecar already established in ADR-001. High collision risk. |
| **Agent Service** (unqualified) | Collides with **Azure AI Agent Service** (Azure AI Foundry hosted agent service, GA 2025). Using this unqualified would cause immediate confusion with the Azure managed product. |
| **Agent Runtime** | Not established Microsoft/industry terminology for this layer. "Runtime" implies a host process or language runtime (e.g., Dapr runtime, WASM runtime) rather than a service owning business logic. |
| **Agentic Service** | Adjectival "agentic" is informal; not a recognised service naming pattern in Azure or Microsoft Agent Framework docs. Marginally better than "Agentic Layer" but still not a proper service name. |
| **Agentic Orchestration Service** | Accurate but verbose. "Orchestration" may be confused with orchestrator patterns (Dapr, Temporal) unrelated to the lab's scope. |

---

## Decision

Adopt **Agent Execution Service** as the canonical service name, with the following naming conventions:

| Context | Name |
|---------|------|
| Short / prose references | **Agent Execution Service** |
| Qualified / org-context references | **Identity Lab Agent Execution Service** |
| Directory slug (filesystem, Docker Compose service name) | `agent-gateway` *(legacy; not renamed — Neo owns runtime renames)* |
| New filesystem slug when runtime rename occurs | `agent-execution` |
| Roadmap / spec references | Agent Execution Service |
| AKS deployment object names (when renamed) | `agent-execution` |

### Rationale

**"Agent Execution Service"** satisfies all three constraints:

1. **Low collision:** The term "execution" is not used by Azure AI Foundry's hosted "Agent Service" product, Microsoft AutoGen, Semantic Kernel, or agentgateway.dev. A full phrase search of Azure documentation and GitHub shows no registered product with this exact name.
2. **Descriptive:** The name conveys that this service _executes agents_ — it is the runtime host for AI agents performing agentic tasks on behalf of users. "Execution" aligns with Microsoft Agent Framework concepts where an agent executor runs the agent loop.
3. **Scalable:** Works as a proper service noun across roadmap milestones, ADRs, Terraform resource names, Kubernetes labels, and external contributor documentation without footnotes.

**Relation to PromptFlow replacement:** The Agent Execution Service is the code-first successor to PromptFlow-style Azure Machine Learning flows (see also `docs/adr/0004-no-promptflow.md`). Where PromptFlow provided a visual DAG-based orchestration layer for LLM pipelines in Azure ML, the Agent Execution Service provides a Python-first agent execution host that:
- Runs inside the lab's infrastructure (AKS / ACA), not inside Azure ML.
- Implements the **Microsoft Agent Framework** agent loop (plan → tool call → observe → iterate).
- Enforces **Entra Agent ID / OBO boundaries** on every tool call, preserving user-delegated identity throughout the agent loop.
- Is instrumentable with OpenTelemetry without Azure ML SDK dependencies.

### Preserved distinctions

This ADR does not change the names or scopes of adjacent components. The following table is authoritative:

| Component | Canonical Name | Notes |
|-----------|----------------|-------|
| Lab's agent execution application service | **Agent Execution Service** | This ADR. Formerly "Agentic Layer". |
| agentgateway.dev infrastructure proxy in AKS | **AKS Agent Gateway** | ADR-001; unchanged. |
| Entra Agent ID sidecar container | **Entra Agent ID sidecar** | Unchanged. |
| API Management gateway | **APIM** | Unchanged. |
| Backend-for-Frontend | **BFF** | Unchanged. |
| MCP-protected downstream API | **MCP Protected API** | Unchanged. |
| Azure AI Foundry hosted agents | **Azure AI Agent Service** / **Foundry Agent Service** | External Microsoft product; never use unqualified "Agent Service" to mean the lab's service. |

---

## Consequences

### Positive
- Spec 002 and future specs can reference "Agent Execution Service" as a proper noun without disambiguation footnotes.
- Terraform resource names, Kubernetes labels, and Docker image tags can use the `agent-execution` slug when Tank/Neo perform runtime renames.
- Roadmap M6 and beyond use a stable, unambiguous name.
- New contributors immediately understand the component's role from its name.

### Negative / costs
- All existing documentation that uses "Agentic Layer" must be updated to "Agent Execution Service". (This ADR acceptance initiates that update.)
- ADR-001's term map is superseded; ADR-001 is retained as historical record only.
- The filesystem path `apps/agent-gateway/` and Docker Compose service name `agent-gateway` remain unchanged until Neo performs the runtime rename (separate work item).

### Neutral / informational
- The legacy path `apps/agent-gateway/` and Docker Compose service `agent-gateway` are documented as legacy aliases until the runtime rename is complete.
- `AUTH_MODE`, `ALLOWED_AUDIENCES`, `REQUIRED_SCOPES` env vars are unaffected by this naming change.
- All placeholder GUIDs (`00000000-0000-0000-0000-00000000NNNN`) remain unchanged.

---

## Implementation scope (this ADR)

**Docs/spec artifacts only** — no runtime filesystem renames (Neo owns those).

Files updated as part of accepting this ADR:
- `.squad/project/roadmap.md` — terminology table, milestone outcome references.
- `.squad/specs/002-aks-entra-agent-id/requirements.md`, `design.md`, `tasks.md`, `.progress.md`.
- `docs/agent-framework/overview.md`, `python-agent.md`, `dotnet-agent.md`.
- `docs/identity/token-audience.md`.
- `docs/apim/ingress-policy.md`.
- `docs/architecture/07-variant-e-agent-framework.md`.
- `docs/adr/0006-agentic-layer-vs-agent-gateway-terminology.md` — marked superseded.
- `.squad/architecture/decisions/001-agentic-layer-vs-agent-gateway-terminology.md` — marked superseded.

Files **not** changed (runtime boundary):
- `apps/agent-gateway/**` — no runtime code, import, or Docker Compose config change.
- Docker Compose service names.
- Python package names, module imports, or environment variable names.
- Terraform resource names (future Neo/Tank work item).

---

## Review checkpoints

- [x] Ashley Hollis approval received — 2026-05-10T19:30:22.457+10:00.
- [x] Naming research completed (morpheus-naming-proposal-pre-m6-v2.md).
- [ ] Runtime rename by Neo — `apps/agent-gateway/` → `apps/agent-execution/` (separate work item, not part of this ADR).
- [ ] Terraform / Kubernetes resource rename by Tank (separate work item, triggered after Neo's runtime rename).
- [ ] Re-review trigger: if Microsoft releases a product called "Agent Execution Service", revisit naming.

---

## References

- Approval directive: `.squad/decisions/inbox/copilot-directive-20260510190927.md` through `…190929.md`
- Naming proposals: `.squad/decisions/inbox/morpheus-naming-proposal-pre-m6.md`, `…-v2.md`
- Superseded ADR (squad): `.squad/architecture/decisions/001-agentic-layer-vs-agent-gateway-terminology.md`
- Superseded ADR (public): `docs/adr/0006-agentic-layer-vs-agent-gateway-terminology.md`
- Public counterpart: `docs/adr/0008-agent-execution-service-naming.md`
- No-PromptFlow ADR: `docs/adr/0004-no-promptflow.md`
- Microsoft Agent Framework: https://learn.microsoft.com/en-us/azure/ai-services/agents/overview
- Azure AI Agent Service (external product — not the lab's service): https://azure.microsoft.com/en-us/products/ai-services/ai-agent-service
- agentgateway.dev: https://agentgateway.dev
