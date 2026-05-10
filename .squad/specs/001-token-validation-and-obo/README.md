# Spec 001: Token Validation and OBO Boundaries

**Status:** Draft  
**Owners:** Morpheus (Lead/Architect), Neo (Backend), Trinity (Security Review)  
**Impact:** High

## Summary
Implement offline-safe JWT validation scaffolding and explicit OBO boundaries from BFF/agent-gateway to the MCP protected API. This spec focuses on mock validation and fixture-driven tests so local development can prove audience and scope rules before any Azure deployment.

## Scope (In)
- Shared auth validation hooks in `apps/shared/python/identity_lab_auth` with real audience/scope checks.
- Service auth context updates in BFF, agent-gateway, and MCP protected API.
- Mock validation mode using fixture claims (`tests/fixtures/sample-claims`).
- Explicit OBO exchange boundary (mocked locally); no forwarding of inbound tokens.
- Tests covering delegated/app-only/wrong-audience scenarios.

## Scope (Out)
- Live Entra ID integration, JWKS fetching, or managed identity wiring.
- Real APIM deployment or tenant-specific configuration.
- Full authorization model or data-level RBAC.
- AKS + Microsoft Entra Agent ID auth (tracked as a downstream spec).

## Local Flow (Target)
1. Client → BFF/agent-gateway with delegated token (mocked).
2. Service validates `aud`/`scp` using allowlists.
3. Service exchanges the token via mock OBO and calls MCP protected API.
4. MCP validates its own audience + scopes.

## Downstream follow-on
- Spec 002 will cover AKS + Microsoft Entra Agent ID auth for agent/MCP workloads, building on this local/mock foundation.

## References
- docs/identity/obo-flow.md
- docs/identity/token-audience.md
- docs/identity/token-claims.md
- apps/shared/python/identity_lab_auth/*
