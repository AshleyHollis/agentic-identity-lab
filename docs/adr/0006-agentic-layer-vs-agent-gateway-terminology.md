# ADR 0006: Agentic Layer vs. AKS Agent Gateway — Canonical Terminology

## Status
Accepted

## Context
The lab's local application-level orchestration service (`apps/agent-gateway/`) and the standalone
[agentgateway.dev](https://agentgateway.dev) infrastructure proxy deployed to AKS both accumulated
the label "agent gateway" in documentation, causing confusion about which layer was meant.

## Decision
Adopt two canonical terms for all architecture and roadmap documentation (no runtime changes):

| Concept | Canonical Term |
|---------|----------------|
| Lab's app-level agent orchestration service (`apps/agent-gateway/`) | **Agentic Layer** |
| Standalone agentgateway.dev binary running as an AKS pod sidecar | **AKS Agent Gateway** |

The directory path `apps/agent-gateway/` is **not renamed** (backward compatibility preserved).
Unqualified "agent gateway" is retired as a standalone architectural term in new documentation.

## Consequences
- Spec 002 sidecar contract documents are unambiguous: the sidecar is the AKS Agent Gateway; the
  orchestration logic is the Agentic Layer.
- Existing docs containing "agent gateway" are updated to one of the two canonical terms.
- Docker Compose service name `agent-gateway` is unchanged (filesystem alias; documented).

## Full decision record
`.squad/architecture/decisions/001-agentic-layer-vs-agent-gateway-terminology.md`
