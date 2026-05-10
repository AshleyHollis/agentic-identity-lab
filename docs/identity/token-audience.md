# Token Audience (aud) Boundaries

## Why Audience Matters
The `aud` claim prevents token replay across services. A token for **BFF** is not valid for the
**Agent Execution Service** or **MCP Protected API**, and vice versa.

> **Terminology (ADR 0008):** "Agent Execution Service" = the lab's app-level agent execution service
> (`apps/agent-gateway/` legacy path). "AKS Agent Gateway" = the agentgateway.dev infrastructure
> proxy sidecar in AKS. "Azure AI Agent Service" = the external Microsoft-managed product in Azure AI
> Foundry. These are separate components — do not use unqualified "Agent Service" to mean the lab's service.
> **Historical note:** "Agentic Layer" was the M5-era term (ADR 0006); superseded by ADR 0008.

## Validated Audiences & Scopes (Placeholder IDs)
These values match the current service defaults and are enforced via `ALLOWED_AUDIENCES` + `REQUIRED_SCOPES`.

| Service boundary | Required `aud` | Required scopes |
| --- | --- | --- |
| BFF (APIM ingress) | `api://00000000-0000-0000-0000-000000000101` | `mcp.access` |
| Agent Execution Service | `api://00000000-0000-0000-0000-000000000102` | `mcp.access`, `mcp.write` |
| MCP protected API | `api://00000000-0000-0000-0000-000000000103` | `mcp.access` (read), `mcp.write` (write/tools) |

## OBO Boundary
- The **Agent Execution Service must exchange** the inbound token for a downstream token with MCP audience.
- Downstream calls **must not forward** the original inbound `Authorization` header.

## Anti-Patterns
- Accepting **multiple audiences** without tight allowlists.
- Using a **single shared audience** for every service.
- Treating the inbound token as valid for MCP without an OBO exchange.
