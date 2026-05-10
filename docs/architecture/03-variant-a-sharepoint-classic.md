# Variant A — SharePoint Classic

## Summary
M7 implements a minimal classic SharePoint loader (`chat-loader.js`) that acquires a delegated token, calls the BFF, and relies on backend OBO flow to reach protected APIs.

## M7 implementation notes

### Token acquisition + BFF handoff
- Token acquisition is pluggable; default provider uses `_spPageContextInfo.aadTokenProviderFactory`.
- Local/mock mode uses a stub provider for non-tenant testing.
- Loader sends `POST /chat/session` with:
  - `Authorization: Bearer {delegated-token}`
  - `traceparent: 00-{trace-id}-{span-id}-01`
  - optional `display_name` (display-only metadata)

### Auth boundary and identity invariant
- Browser code calls the **BFF only**.
- `userId` and `display_name` in request body are display/context only, never identity.
- Identity is established only by validated bearer token at the BFF.
- Backend continues through **Agent Execution Service** (not AKS Agent Gateway) and then MCP Protected API.

### Tracing
- Classic loader manually creates `traceparent` and forwards it on every BFF call.
- BFF forwards trace context downstream to Agent Execution Service and MCP.
- Client spans/logs must not include raw tokens or PII claims.

### Scope and deferral
- M7 is local/mock focused and keeps classic integration minimal.
- Live Azure E2E is deferred to M8 and requires explicit opt-in.

## When to use
- Existing classic SharePoint estates that need delegated identity without direct browser-to-backend trust.

## Risks / limitations
- Classic pages have fewer isolation guarantees than modern SPFx surfaces.
- Token references must remain short-lived in memory and never persisted by loader code.

## Diagram
See `diagrams/mermaid/variant-a-sharepoint-classic.mmd`.
