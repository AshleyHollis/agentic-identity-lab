# Spec 007: Variant Client Implementations

**Status:** Spec-ready (pending coordinator approval before implementation)
**Milestone:** M7
**Spec Phase:** spec.feature — spec-first gate
**Created:** 2026-06-01
**Updated:** 2026-06-01
**Requested by:** Ashley Hollis
**Owners:** Mouse (Frontend/SharePoint/TypeScript), Neo (Backend integration)
**Reviewers:** Morpheus (Architecture), Trinity (Security)
**Impact:** High

---

## Summary

M7 delivers the first browser-facing client variants that acquire delegated tokens and call the BFF. Three client surfaces are in scope: a SPA/public client (highest priority), a SharePoint classic loader, and an SPFx web part. All variants call the BFF only — the Python/backend stack (BFF + Agent Execution Service + MCP Protected API) is the stable backend and is not modified in M7 except for minor BFF CORS/endpoint additions.

M7 is a **spec-first gate**: no implementation code ships until this spec is reviewed and approved. The checkpoint at the bottom of this README must be satisfied before any `apps/` changes begin.

---

## Scope (In)

- **SPA/public client** (`apps/spa-public-client/react-vite/`): PKCE delegated-token acquisition via MSAL browser, calls BFF `/chat/session`. Placeholder Entra app config only (no real tenant/client IDs).
- **SharePoint classic loader** (`apps/sharepoint-classic/chat-loader-js/`): JavaScript loader for classic SharePoint pages. Acquires token from SharePoint page context or a supplied token provider. Calls BFF with delegated bearer token.
- **SPFx web part** (`apps/spfx-webpart/identity-chat-webpart/`): SPFx web part acquires delegated token via `@microsoft/sp-http` AadHttpClient or `@microsoft/sp-core-library` AadTokenProvider. Calls BFF.
- **Identity rule enforcement**: All three variants must enforce that `userId` or any body field is display/context only; identity is established solely by the validated bearer token at the BFF.
- **No-token-persistence tests**: Each variant must include a test/check asserting tokens are not persisted to localStorage/sessionStorage in ways that survive page navigation unexpectedly.
- **No-userId-auth fallback tests**: Each variant must include a test asserting that the BFF rejects requests with no/invalid bearer token even when `userId` is present in the body.
- **Local/mock mode**: All variants work against the local Docker Compose BFF stack in `AUTH_MODE=mock` for local dev. Azure E2E is out of scope for M7 (see Scope Out).
- **Diagrams**: Token acquisition and BFF handoff diagrams (Mermaid) for each variant.
- **Tracing**: Client-originated requests create W3C TraceContext spans propagated through BFF → Agent Execution Service → MCP Protected API. Local visualization in Jaeger; Azure Monitor in deployed mode.
- **Docs**: Architecture doc updates for variants A (classic), B (SPFx), D (SPA); inline security comments.

---

## Scope (Out)

- **`terraform apply` / live Azure deployment**: No live Azure resources created from public CI. Azure E2E verification is deferred to a dedicated post-M7 gate (M7-AzureVerify or M8).
- **Real tenant IDs, client IDs, subscription IDs, secrets, or live tokens** in any committed file.
- **Net-new backend services**: BFF, Agent Execution Service, and MCP Protected API are not modified for new endpoints in M7 except minor CORS additions and a `/chat/session` POST body extension for `display_name` (display only).
- **Runtime language variants** (.NET or Node Agent Execution Service implementations): These are future scope, not M7.
- **Next.js variant** (`apps/spa-public-client/nextjs/`): Placeholder only in M7; not implemented.
- **Agent Execution Service client SDK**: Not in scope; clients call BFF only.
- **Production deployment of SPFx packages**: No SharePoint tenant deployment in CI.
- **Multi-tenant Entra app registration**: Placeholder single-tenant config patterns only.

---

## Identity Invariant (non-negotiable)

> **`userId` in any request body is display/context only. It is NEVER used as an authorization gate, database key, or downstream trust signal. Identity is established solely by the validated bearer token at the BFF.**

This invariant must be:
1. Stated in code comments at every BFF endpoint that receives a body.
2. Stated in the README and docs of every client variant.
3. Covered by at least one negative test per variant (request with `userId` but no/invalid token must be rejected).

---

## Artifacts

| Artifact | Description |
|----------|-------------|
| `README.md` | This file — spec overview, scope, checkpoint |
| `goals.md` | M7 goals and success criteria |
| `research.md` | Current state of client placeholders, gaps, prior art |
| `requirements.md` | Functional and non-functional requirements per variant |
| `design.md` | Architecture diagrams, token flows, ADRs, tracing design |
| `tasks.md` | Decomposed tasks with owners, dependencies, validation |
| `state.json` | Machine-readable spec state |
| `.progress.md` | Artifact and task progress tracking |

---

## Related Specs

- Spec 001: Token validation + OBO (complete — shared auth library, strict JWKS)
- Spec 003: Local delegated flow (complete — mock OBO integration tests)
- Spec 004: APIM policy alignment (complete — ingress JWT validation)
- Spec 005: Local runtime ergonomics (complete — Docker Compose, `/chat/session`)
- Spec 006: Azure deployment baseline (complete — ACA Terraform, Azure Monitor OTLP)

---

## Variant Priority

| Priority | Variant | Slug | App path |
|----------|---------|------|----------|
| 1 | SPA / public client | `spa-public-client` | `apps/spa-public-client/react-vite/` |
| 2 | SharePoint classic loader | `sharepoint-classic` | `apps/sharepoint-classic/chat-loader-js/` |
| 3 | SPFx web part | `spfx-webpart` | `apps/spfx-webpart/identity-chat-webpart/` |

---

## Validation Targets

```
# Python backend regression (must not break)
python -m pytest

# SPA build (placeholder — requires Node)
cd apps/spa-public-client/react-vite && npm ci && npm run build

# SharePoint classic loader lint (placeholder)
cd apps/sharepoint-classic/chat-loader-js && npm ci && npm run lint

# SPFx build (placeholder — requires Node + gulp)
cd apps/spfx-webpart/identity-chat-webpart && npm ci && gulp build

# Docker Compose local stack (BFF + AUTH_MODE=mock for client dev)
docker compose -f docker/docker-compose.yml config --quiet
```

> **Public-safe constraint:** No live Entra tokens, tenant IDs, client IDs, or secrets in any committed file. Placeholder values must use `{tenant-id}`, `{client-id}`, `{bff-api-scope}` brace tokens or all-zero GUIDs only.

---

## Azure End-to-End Verification Gate

Per the directive captured in `.squad/decisions/inbox/copilot-directive-20260510202925.md`, the roadmap must make clear when the lab deploys everything to Azure and verifies the full end-to-end flow.

M7 covers **local/mock mode only**. Azure E2E verification (client → APIM → BFF → Agent Execution Service → MCP Protected API with real Entra tokens) is explicitly tied to a post-M7 milestone gate. This gate is tracked in `roadmap.md` as **M7-AzureVerify** (or M8 if scoped separately). Live Azure tests require an opt-in mechanism and must never run in public CI without explicit credentials configuration.

---

## Coordinator Checkpoint

> **⛔ APPROVAL REQUIRED before any implementation begins.**
>
> This spec is complete. Coordinator (Ashley Hollis) must confirm:
>
> 1. **Spec reviewed**: All eight artifacts (`README.md`, `goals.md`, `research.md`, `requirements.md`, `design.md`, `tasks.md`, `state.json`, `.progress.md`) reviewed and accepted.
> 2. **Variant priority confirmed**: SPA first, then classic, then SPFx.
> 3. **Azure E2E gate confirmed**: M7 implementation stays local/mock only; a separate gate (M7-AzureVerify or M8) is added to the roadmap for live Azure tests.
> 4. **T11 (Morpheus architecture review) scheduled** — must complete before T01–T10 implementation begins.
> 5. **T12 (Trinity security review) scheduled** — must complete before any token acquisition code ships.
> 6. **No implementation tasks begin** until T11 + T12 sign-offs are recorded in `.progress.md`.
