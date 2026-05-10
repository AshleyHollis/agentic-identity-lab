# Variant B — SPFx

## Summary
M7 implements a minimal SPFx web part using `AadHttpClient` for delegated-token calls to the BFF, preserving a strict browser-to-BFF boundary.

## M7 implementation notes

### Token acquisition + BFF handoff
- Web part gets an `AadHttpClient` from `context.aadHttpClientFactory.getClient(bffResourceUri)`.
- `AadHttpClient` attaches `Authorization: Bearer {token}` automatically.
- Web part sends `POST /chat/session` with manual `traceparent` plus optional `display_name`.

### Auth boundary and identity invariant
- SPFx code calls **BFF only** for session bootstrap.
- `userId`/`display_name` are display-only request metadata.
- Identity is established only by BFF bearer-token validation.
- Downstream execution path remains BFF → **Agent Execution Service** → MCP Protected API.
- The Agent Execution Service in this flow is not the AKS Agent Gateway sidecar.

### Tracing
- SPFx generates `traceparent` per BFF request and forwards it via request headers.
- BFF forwards trace context to Agent Execution Service and MCP.
- No raw token or PII claim values should be emitted in client telemetry.

### Scope and deferral
- M7 remains local/mock focused with placeholder-only config.
- Live Azure E2E validation is deferred to M8.

## When to use
- SharePoint Online modern pages where delegated identity must be handled with SPFx-native auth primitives.

## Risks / limitations
- Permission grants (`webApiPermissionRequests`) must stay scoped to placeholder BFF resource/scope only.
- Using `SPHttpClient` or manual token plumbing would violate the approved boundary.

## Diagram
See `diagrams/mermaid/variant-b-spfx.mmd`.
