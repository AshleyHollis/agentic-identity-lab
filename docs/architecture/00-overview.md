# Architecture Overview

## Goal
Establish a public-safe lab that proves correct identity and token flow patterns across SharePoint, web apps, APIs, APIM, and agent frameworks, plus an optional AKS track for Microsoft Entra Agent ID in agent/MCP workloads.

## Non-goals
- Production-ready deployments or tenant-specific guidance.
- Storing secrets, certificates, or real IDs.
- Overbuilt implementations before the identity story is nailed.

## Common building blocks
- **User-facing entry point**: SharePoint or standalone web app.
- **APIM**: validates and forwards user-delegated tokens.
- **BFF/API**: enforces token audiences and scopes.
- **Downstream APIs**: require OBO when called for a user.
- **Agent frameworks**: orchestrate tools but do not replace auth rules.

## Identity boundaries (must hold in all variants)
- Every API requires a token with its own audience.
- OBO is required for user-delegated calls between APIs.
- APIM must not replace delegated tokens with managed identity.
- App-only tokens are service identity and do **not** represent users.
- Azure OpenAI / Foundry auth is separate from MCP user delegation.

## Deliverables
- Variant narratives (A–F).
- ADRs for architectural decisions.
- Diagrams that show token flow and audience boundaries.
