# Spec 007 — Goals

**Spec:** 007-variant-client-implementations
**Milestone:** M7
**Updated:** 2026-06-01

---

## Primary Goal

Deliver three browser-facing client variants — SPA/public client, SharePoint classic loader, and SPFx web part — that each acquire a delegated Entra token and call the BFF `/chat/session` endpoint correctly. All variants must reinforce the lab's core identity invariant: **identity is established by the validated bearer token at the BFF, never by `userId` or any body field**.

---

## Success Criteria

| # | Criterion | Measurable outcome |
|---|-----------|-------------------|
| G1 | SPA/public client implemented | `apps/spa-public-client/react-vite/` builds, acquires a token via MSAL PKCE flow (placeholder config), calls BFF; `npm run build` passes |
| G2 | SharePoint classic loader implemented | `apps/sharepoint-classic/chat-loader-js/` lints clean; loader script calls BFF with bearer token from token provider |
| G3 | SPFx web part implemented | `apps/spfx-webpart/identity-chat-webpart/` builds; web part calls BFF with `AadHttpClient`-acquired token |
| G4 | Identity invariant enforced | Every variant README and every BFF call site includes the `userId` is display-only comment; negative tests pass |
| G5 | No-token-persistence validated | Per-variant test/assertion confirms tokens are not persisted to localStorage/sessionStorage in ways that survive unexpected page navigation |
| G6 | No-userId-auth-fallback tested | BFF rejects requests with `userId` body field but no/invalid bearer token; test asserts 401 |
| G7 | Local mock mode works | All three variants run against the local Docker Compose BFF (`AUTH_MODE=mock`) without live Azure credentials |
| G8 | Diagrams delivered | Mermaid token-acquisition and BFF-handoff diagrams for each variant in `diagrams/mermaid/` |
| G9 | Tracing propagated | W3C TraceContext `traceparent` forwarded from each client into BFF; spans visible in local Jaeger |
| G10 | Backend unbroken | `python -m pytest` still passes (235+ tests) after all M7 changes |
| G11 | Public-safe | No real tenant IDs, client IDs, secrets, or tokens committed anywhere |

---

## Non-Goals (M7)

- Live Azure end-to-end verification with real Entra tokens (post-M7 gate)
- .NET or Node Agent Execution Service runtime variants (future scope)
- Next.js SPA variant (placeholder only in M7)
- Production SharePoint tenant deployment
- New Agent Execution Service or MCP Protected API features
- Multi-tenant Entra app registration patterns

---

## Relationship to Prior Milestones

M7 builds on:
- **M1/M2**: BFF JWKS validation + mock OBO tested offline — client variants rely on this.
- **M4**: `/chat/session` endpoint and Docker Compose ergonomics — clients call this endpoint.
- **M5**: W3C TraceContext propagation — clients must forward `traceparent`.
- **M6**: ACA deployment baseline — future Azure E2E verification will use ACA endpoints.

---

## Owner Assignments

| Variant | Primary owner | Secondary |
|---------|--------------|-----------|
| SPA/public client | Mouse | Neo (BFF CORS) |
| SharePoint classic loader | Mouse | — |
| SPFx web part | Mouse | — |
| BFF CORS + endpoint extensions | Neo | Mouse (consumer) |
| Architecture review (T11) | Morpheus | — |
| Security review (T12) | Trinity | — |
