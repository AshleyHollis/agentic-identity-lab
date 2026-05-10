# Variant D — SPA Comparison

## Summary
M7 implements the React/Vite public client as a BFF-assisted SPA using MSAL Auth Code + PKCE and explicit trace propagation.

## M7 implementation notes

### Token acquisition + BFF handoff
- SPA acquires delegated token with MSAL Browser PKCE (`acquireTokenSilent` then interactive fallback).
- MSAL cache is `sessionStorage` (not `localStorage`), with `storeAuthStateInCookie: false`.
- SPA calls `POST /chat/session` with bearer token + `traceparent`; optional `display_name` is supported as display metadata.

### BFF-only boundary and comparison outcome
- M7 uses the BFF-assisted model as the implemented path.
- Browser client never calls Agent Execution Service or MCP directly.
- `userId`/`display_name` are never auth signals; identity comes only from bearer-token validation at BFF.
- Backend chain remains BFF → **Agent Execution Service** → MCP Protected API (not AKS Agent Gateway).

### Tracing
- SPA forwards W3C `traceparent` on each BFF request.
- BFF forwards trace context through Agent Execution Service into MCP.
- Telemetry must exclude raw tokens and PII claims.

### Scope and deferral
- M7 covers local/mock flows and placeholder configuration only.
- Live Azure tenant E2E for this variant is deferred to M8 with explicit opt-in.

## When to use
- Browser-first UI needing delegated identity while keeping trust decisions in the BFF.

## Risks / limitations
- Browser environment still requires careful XSS and token-handling hygiene.
- Redirect URIs and CORS origins must remain explicit; wildcards are prohibited.

## Diagram
See `diagrams/mermaid/variant-d-spa-comparison.mmd`.
