# Spec 007 — Research

**Spec:** 007-variant-client-implementations
**Milestone:** M7
**Updated:** 2026-06-01

---

## Current State of Client Placeholders

### SPA / Public Client (`apps/spa-public-client/`)

Two sub-directories exist:
- `apps/spa-public-client/react-vite/` — directory present; no `package.json` yet; placeholder only.
- `apps/spa-public-client/nextjs/` — directory present; placeholder only; out of scope for M7.

**Gaps identified:**
- No `package.json`, no MSAL dependency, no token acquisition code.
- No BFF client call (fetch to `/chat/session`).
- No `.env.example` with BFF URL + Entra app placeholders.
- No `traceparent` forwarding.
- No test scaffold.

### SharePoint Classic Loader (`apps/sharepoint-classic/`)

Structure present:
- `apps/sharepoint-classic/chat-loader-js/` — placeholder loader script directory.
- `apps/sharepoint-classic/sample-aspx-snippets/` — HTML snippet examples.
- `apps/sharepoint-classic/README.md` — has identity invariant note, but no implementation.

**Gaps identified:**
- No `package.json`, no lint config.
- No actual loader script (`chat-loader.js` mentioned in README but content is minimal/placeholder).
- No token provider interface defined.
- No `traceparent` injection.
- No test assertions for token persistence or userId-auth fallback.

### SPFx Web Part (`apps/spfx-webpart/`)

Structure present:
- `apps/spfx-webpart/identity-chat-webpart/` — placeholder directory.
- `apps/spfx-webpart/README.md` — has auth boundary note but no implementation.

**Gaps identified:**
- No SPFx project scaffolded (`package.json`, `gulpfile.js`, `.yo-rc.json` etc.).
- No `AadHttpClient` or `AadTokenProvider` usage.
- No build pipeline.
- No `traceparent` forwarding.

### BFF (`apps/bff/python-fastapi/app/main.py`)

- `/chat/session` POST endpoint exists. Returns `session_id` + `expires_at`.
- CORS middleware exists but requires explicit origins (wildcard prohibited).
- `userId` invariant comment is present in `main.py` at the `/chat/session` endpoint.
- **Gap:** CORS `CORS_ALLOWED_ORIGINS` env var must be set for browser clients to call BFF from `localhost:3000` etc. — this needs to be documented and included in env examples.
- **Gap:** The `/chat/session` body currently accepts no body fields. A `display_name` field (display only) may be useful for client variants — decision deferred to T11.

---

## Prior Art / Reference

### MSAL Browser (SPA PKCE)
- `@azure/msal-browser` is the standard MSAL library for browser SPAs.
- PKCE flow is the recommended Entra public client flow; implicit grant is deprecated.
- `acquireTokenSilent` + `acquireTokenPopup` / `loginPopup` is the standard pattern.
- Access tokens should be stored in MSAL's in-memory token cache by default; `localStorage` caching is opt-in and not recommended for sensitive tokens.
- Reference: https://learn.microsoft.com/en-us/azure/active-directory/develop/tutorial-v2-react

### SPFx AAD Token Acquisition
- `AadHttpClient` (via `this.context.aadHttpClientFactory`) is the recommended SPFx pattern for calling Entra-protected APIs.
- `AadTokenProvider` (via `this.context.aadTokenProviderFactory`) provides raw token strings.
- SPFx manages token caching in-process; no localStorage exposure.
- SPFx requires `webApiPermissionRequests` in `package-solution.json` and admin consent in the tenant.
- Reference: https://learn.microsoft.com/en-us/sharepoint/dev/spfx/use-aadhttpclient

### SharePoint Classic Token Acquisition
- Classic pages can use `_spPageContextInfo.aadTokenProviderFactory` (available since SharePoint 2019 / SPO with modern infrastructure) to acquire tokens for Entra apps.
- Alternatively, `window.fetch` with a manually provided token via a loader parameter.
- The loader must NOT store the token in localStorage beyond the page session.
- Reference: SharePoint Framework cross-domain call guidance.

### W3C TraceContext from Browsers
- Browser clients must generate a `traceparent` header for each BFF request.
- Libraries: `@opentelemetry/api`, `@opentelemetry/context-zone`, or manual construction.
- The `traceparent` format: `00-{trace-id}-{span-id}-{flags}`.
- The BFF already propagates `traceparent` downstream (M5 instrumentation).

### Identity Invariant — Prior Enforcement
- `apps/bff/python-fastapi/app/main.py` line 102–104: `userId` comment is already present at `/chat/session`.
- `apps/sharepoint-classic/README.md`: invariant note present.
- `apps/spfx-webpart/README.md`: invariant note present.
- Need to ensure this is also present in client-side code comments, not just server-side.

---

## Decisions Required (for T11/T12)

| # | Question | Options | Recommend |
|---|----------|---------|-----------|
| R1 | MSAL token cache storage | `sessionStorage` (default MSAL browser) vs `localStorage` vs `memoryStorage` | `sessionStorage` for SPA (survives tab refresh, not cross-tab); document rationale |
| R2 | BFF CORS allowed origins for local dev | Hardcode `http://localhost:5173` (Vite default) in `.env.example` | Document; do not allow wildcard |
| R3 | `/chat/session` body extension | Accept optional `display_name` (string, display only) vs keep body-free | Accept `display_name` with identity invariant comment; T11 decision |
| R4 | SPFx token provider choice | `AadHttpClient` vs `AadTokenProvider` | `AadHttpClient` (handles auth header automatically); document |
| R5 | Classic loader token provider interface | Pluggable callback vs `_spPageContextInfo` direct | Pluggable callback (future-safe); `_spPageContextInfo` as default impl |
| R6 | Tracing library for browser clients | `@opentelemetry/api` full SDK vs minimal manual `traceparent` generation | Minimal manual `traceparent` for SharePoint classic; OTEL SDK for SPA |
| R7 | Azure E2E gate timing | Part of M7 vs separate M7-AzureVerify milestone | Separate gate — M7 stays local/mock only |

---

## Security Research Notes (for T12)

- MSAL browser does not expose the raw access token via DOM API — it is not readable from `document` or `window` by other scripts if using `sessionStorage` cache. However, `sessionStorage` is accessible to any same-origin JS.
- SPFx web parts run in isolated iframes in modern SharePoint — the token is not accessible to other web parts unless explicitly shared.
- SharePoint classic pages do not have iframe isolation. The loader script must minimize token surface area: acquire once, pass to BFF immediately, do not store.
- The BFF must be the trust anchor — clients are untrusted; all authorization decisions happen server-side.
- `userId` in request body: if included, BFF must log that it is ignored for auth. No client should rely on `userId` for any behavior beyond UI display.
