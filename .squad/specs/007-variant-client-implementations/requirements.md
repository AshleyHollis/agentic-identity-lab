# Spec 007 — Requirements

**Spec:** 007-variant-client-implementations
**Milestone:** M7
**Updated:** 2026-06-01

---

## Functional Requirements

### FR-01 — SPA PKCE token acquisition
The React/Vite SPA must acquire a delegated access token using MSAL browser PKCE flow with placeholder Entra app settings. The token acquisition configuration must use `{tenant-id}` and `{client-id}` brace-token placeholders; no real values may be committed.

### FR-02 — SPA BFF call
The SPA must call the BFF `POST /chat/session` with the delegated access token in the `Authorization: Bearer {token}` header. The BFF must validate the token and return a session.

### FR-03 — Classic loader token acquisition
The SharePoint classic loader must acquire a delegated access token from a pluggable token provider. The default provider implementation must use `_spPageContextInfo.aadTokenProviderFactory` when available (SharePoint Online with modern infrastructure). A stub provider must be included for local/mock dev.

### FR-04 — Classic loader BFF call
The classic loader must call the BFF `POST /chat/session` with the delegated token in the `Authorization: Bearer {token}` header. The loader must not add `userId` as an authorization value.

### FR-05 — SPFx token acquisition
The SPFx web part must acquire a delegated access token using `AadHttpClient` via `this.context.aadHttpClientFactory.getClient(bffResourceUri)`. The client must be configured with placeholder `bffResourceUri` from web part properties.

### FR-06 — SPFx BFF call
The SPFx web part must call the BFF `POST /chat/session` via the `AadHttpClient`. The `AadHttpClient` must attach the bearer token automatically.

### FR-07 — `userId` display-only enforcement
All three client variants must:
a. Not use `userId` or any body field as an authorization gate.
b. Include a code comment at any BFF call site stating `userId` is display/context only.
c. Pass a negative test: request with `userId` body field but no/invalid bearer token must receive a 401.

### FR-08 — No-token-persistence
Each client variant must include a test or assertion validating that:
- SPA: MSAL token cache storage is set to `sessionStorage` (not `localStorage`).
- Classic loader: token is not stored in `localStorage` or `sessionStorage`; it is used in-memory only.
- SPFx: `AadHttpClient` manages token caching internally; no localStorage write by web part code.

### FR-09 — Local mock mode
All three client variants must work against the local Docker Compose BFF stack with `AUTH_MODE=mock`. Each variant README must include a "local dev" section explaining how to run against the local BFF.

### FR-10 — `traceparent` propagation
Each client variant must generate and forward a W3C `traceparent` header on every BFF request:
- SPA: Use `@opentelemetry/api` instrumentation or manual `traceparent` construction.
- Classic loader: Manual `traceparent` construction (minimal dependency).
- SPFx: Manual `traceparent` construction injected via `AadHttpClient` request options.

### FR-11 — Env/config placeholders
Each variant must provide a `.env.example` or equivalent config placeholder file with:
- `VITE_ENTRA_CLIENT_ID={client-id}` (SPA)
- `VITE_ENTRA_TENANT_ID={tenant-id}` (SPA)
- `VITE_BFF_BASE_URL=http://localhost:8000` (SPA, local dev default)
- `VITE_BFF_API_SCOPE={bff-api-scope}` (SPA)
- Classic and SPFx: equivalent `config.example.json` or env snippets

### FR-12 — Diagrams
Mermaid sequence diagrams must be created or updated for each variant:
- `diagrams/mermaid/variant-a-sharepoint-classic.mmd` — updated for M7
- `diagrams/mermaid/variant-b-spfx.mmd` — updated for M7
- `diagrams/mermaid/variant-d-spa-comparison.mmd` — updated for M7

### FR-13 — Architecture docs
Architecture docs for each variant must be updated with token acquisition detail and BFF handoff description:
- `docs/architecture/03-variant-a-sharepoint-classic.md`
- `docs/architecture/04-variant-b-spfx.md`
- `docs/architecture/06-variant-d-spa-comparison.md`

---

## Non-Functional Requirements

### NFR-01 — Public-safe
No real tenant IDs, client IDs, subscription IDs, secrets, or generated tokens in any committed file. All placeholder values use `{tenant-id}`, `{client-id}`, `{bff-api-scope}` brace tokens or all-zero GUIDs (`00000000-0000-0000-0000-000000000000`).

### NFR-02 — No CORS wildcard with credentials
The BFF `CORS_ALLOWED_ORIGINS` must never include `*` when `allow_credentials=True`. Client variant README files must document the explicit origin(s) for local dev (e.g., `http://localhost:5173`).

### NFR-03 — Python backend regression
`python -m pytest` must pass with no regressions (235+ tests) after all M7 changes.

### NFR-04 — Spec-first gate
No implementation code ships before T11 (Morpheus) and T12 (Trinity) sign-offs are recorded in `.progress.md`.

### NFR-05 — Minimal placeholder projects
Client variant projects are minimal and clearly marked as placeholders. Do not scaffold full production SPFx packages or full React apps with unnecessary complexity.

### NFR-06 — No live Azure tests in public CI
CI must not execute live Entra token acquisition or call real BFF endpoints. All CI validation runs against local mock stack or builds/lints only.

### NFR-07 — Span PII rules
Tracing spans from client variants must not include raw tokens, `oid`, `sub`, `email`, `upn`, or other PII. Only safe, sanitized attributes following `sanitize_claims()` rules.

### NFR-08 — Token-persistence rule in docs
Each variant's README must include a "Token security" section stating the token storage policy and why `localStorage` long-term storage is prohibited.

### NFR-09 — Canonical naming
All variant code and docs use "Agent Execution Service" (not "Agentic Layer", not unqualified "Agent Gateway"). Client variants call the BFF only; "Agent Execution Service" is mentioned as the backend tier clients never call directly.

### NFR-10 — Azure E2E opt-in
Live Azure E2E tests (client → APIM → BFF → Agent Execution Service → MCP with real Entra tokens) must be documented as a post-M7 step. A `LIVE_AZURE_TESTS=true` env flag or similar opt-in must be required before any live test runs. This flag must never be set in public CI defaults.
