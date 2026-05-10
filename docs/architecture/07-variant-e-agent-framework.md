# Variant E — Agent Framework

## Summary
Agent orchestration (e.g., Microsoft Agent Framework) performs tool calls while preserving user-delegated identity.

## Identity flow
- User authenticates with Entra ID in the host app.
- The host app obtains delegated tokens for user-initiated tool calls.
- Agents call APIs through BFF/APIM using OBO for downstream calls.
- Azure OpenAI / Foundry auth is separate and uses its own credentials.

## When to use
- Agentic workflows that still require user-audited actions.

## Risks / limitations
- Avoid mixing LLM service credentials with user-delegated calls.

## Roadmap note — AKS + Entra Agent ID (M5)
- The AKS optional track (Spec 002) deploys the **Agentic Layer** to AKS with an **AKS Agent Gateway**
  sidecar (agentgateway.dev) for Entra Agent ID token acquisition.
- The AKS Agent Gateway sidecar is an **infrastructure proxy** — it is not the Agentic Layer.
  The Agentic Layer contains the orchestration logic; the AKS Agent Gateway sidecar handles Agent ID
  auth on `localhost` via `/Validate`, `/AuthorizationHeader/{apiName}`, and `/DownstreamApi/{apiName}`.
- See ADR 0006 (`docs/adr/0006-agentic-layer-vs-agent-gateway-terminology.md`) for the canonical
  terminology decision.

## Implementation notes (TODO)
- Add agent host skeleton and tool registry.
- Document token broker responsibilities.

## Diagram
See `diagrams/mermaid/variant-e-agent-framework.mmd`.
