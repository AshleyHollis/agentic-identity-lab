# Spec 007 — Tasks

**Spec:** 007-variant-client-implementations
**Milestone:** M7
**Updated:** 2026-06-01
**Primary owners:** Mouse (Frontend), Neo (BFF extensions)
**Reviewers:** Morpheus (Architecture), Trinity (Security)

---

## Dependency Order

```
T11 (Morpheus architecture review) ──┐
T12 (Trinity security review)      ──┤── (all clear) ──→ IMPLEMENT
                                      │
After T11 + T12 complete:            │
  Neo stream:   T00 → T01            │
  Mouse stream: T02 → T03 → T04 ◄───┘
                      ↓
                     T05 (tracing) — parallel across variants
                      ↓
                     T06 (diagrams + docs)
                      ↓
                     T07 (negative tests)
                      ↓
                     T08 (CI validation gates)
                      ↓
                     T09 (Morpheus post-impl review)
                      ↓
                     T10 (Trinity post-impl security review)
                      ↓
                     T13 (final closeout)

T11 and T12 run in parallel with each other.
T00/T01 (Neo) can begin after T12 sign-off.
T02–T04 (Mouse) can begin after T11 + T12 sign-offs.
T05–T08 depend on T00–T04 being complete for the respective variant.
```

---

## T11 — Architecture Review

**Owner:** Morpheus
**Depends on:** Spec 007 spec artifacts complete
**Blocks:** All implementation tasks

**Description:**
Review Spec 007 goals, requirements, design, and tasks for architectural coherence before any implementation begins.

**Focus areas:**
1. Token acquisition flow correctness for each variant (SPA, classic, SPFx).
2. BFF CORS extension design — confirm explicit origins, wildcard prohibition.
3. `/chat/session` body extension (Decision R3): approve or reject `display_name` field.
4. Tracing design — confirm `traceparent` propagation from each client type.
5. Azure E2E gate strategy — confirm M7 stays local/mock only; M7-AzureVerify milestone.
6. Scope split — confirm runtime language variants (.NET/Node) are out of M7 scope.
7. Variant priority order — SPA first, then classic, then SPFx.

**Acceptance:**
- Morpheus sign-off recorded in `.progress.md`.
- Any binding conditions or required design changes recorded.
- ADR-M7-01, ADR-M7-02, ADR-M7-03 confirmed or amended.

---

## T12 — Security Review

**Owner:** Trinity
**Depends on:** Spec 007 spec artifacts complete
**Blocks:** All token acquisition implementation tasks (T02–T04)

**Description:**
Review Spec 007 from an identity and auth security perspective before any client token acquisition code ships.

**Focus areas:**
1. MSAL `sessionStorage` vs `localStorage` — confirm ADR-M7-01.
2. Classic loader token persistence — confirm token not stored to storage APIs.
3. SPFx `AadHttpClient` vs `AadTokenProvider` — confirm ADR-M7-02 token provider choice.
4. `userId` invariant — confirm negative test coverage is sufficient.
5. CORS configuration — confirm wildcard prohibition and explicit origin documentation.
6. `traceparent` span attributes — confirm PII rules apply to client-originated spans.
7. Public-safe constraint — confirm no real tenant/client IDs/secrets in M7 committed files.
8. Azure E2E opt-in — confirm `LIVE_AZURE_TESTS` flag requirement and CI default.

**Acceptance:**
- Trinity sign-off recorded in `.progress.md`.
- Binding conditions recorded (if any).
- All conditions must be satisfied before Token acquisition code ships.

---

## T00 — BFF CORS + env example update

**Owner:** Neo
**Depends on:** T12 sign-off
**Blocks:** T02 (SPA integration), T03 (classic integration)

**Description:**
Update BFF CORS configuration and env examples to support browser client origins for local dev.

**Scope:**
1. Add `CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000` to `config/env/bff.env.example`.
2. Verify `main.py` CORS guard (wildcard prohibition) is still in place.
3. Add documentation note in `apps/bff/python-fastapi/README.md` (or create it) explaining CORS for client variants.
4. If T11 approves `display_name` field (Decision R3): add `ChatSessionRequest` Pydantic model to `main.py` with identity invariant comment.
5. Verify `python -m pytest` still passes (235+ tests).

**Acceptance:**
- `bff.env.example` includes CORS origin for Vite/Next.js local dev ports.
- Wildcard CORS prohibition comment present in `main.py`.
- `display_name` field (if approved) has identity invariant comment.
- `python -m pytest` passes.

---

## T01 — BFF `/chat/session` body model (if T11 approves)

**Owner:** Neo
**Depends on:** T11 sign-off (Decision R3), T00
**Blocks:** T02–T04 (client integration tests that send body)

**Description:**
If T11 approves the optional `display_name` body field, add the `ChatSessionRequest` Pydantic model and update the `/chat/session` endpoint signature.

**Scope:**
1. Add `ChatSessionRequest` model with `display_name: str | None = None`.
2. Add identity invariant comment in docstring and inline comment.
3. Add a test asserting `display_name` is returned in response metadata (display only) or silently ignored.
4. Add a negative test: `display_name` present, no bearer token → 401.

**Acceptance:**
- `python -m pytest` passes (235+ tests + new T01 tests).
- `display_name` never used for authorization.

---

## T02 — SPA / Public Client implementation

**Owner:** Mouse
**Depends on:** T11 + T12 sign-offs, T00 (BFF CORS)

**Description:**
Implement the minimal React/Vite SPA public client in `apps/spa-public-client/react-vite/`.

**Scope:**
1. Create `package.json` with `react`, `@azure/msal-browser`, `@azure/msal-react`, `@opentelemetry/api`, `@opentelemetry/instrumentation-fetch` (and Vite dev deps).
2. Create `src/authConfig.ts` with placeholder MSAL config (`cacheLocation: 'sessionStorage'`).
3. Create `src/App.tsx`: MSAL provider, login button, acquire token, call BFF `/chat/session`.
4. Create `src/bffClient.ts`: fetch wrapper with `Authorization: Bearer {token}` + `traceparent` header.
5. Create `.env.example` with `VITE_ENTRA_CLIENT_ID`, `VITE_ENTRA_TENANT_ID`, `VITE_BFF_BASE_URL`, `VITE_BFF_API_SCOPE` (all placeholder values).
6. Create `README.md` with: local dev instructions, token security section, `userId` display-only note.
7. Configure `eslint` + `tsconfig.json`; ensure `npm run build` and `npm run lint` pass.
8. Clearly mark all Entra config as placeholders.

**Acceptance:**
- `npm ci && npm run build` passes.
- `npm run lint` passes.
- `.env.example` uses only `{tenant-id}`, `{client-id}`, `{bff-api-scope}` brace tokens.
- No real tenant/client IDs committed.
- `cacheLocation: 'sessionStorage'` in MSAL config (not `localStorage`).
- Identity invariant comment at BFF call site.

---

## T03 — SharePoint Classic Loader implementation

**Owner:** Mouse
**Depends on:** T11 + T12 sign-offs, T00

**Description:**
Implement the minimal SharePoint classic loader in `apps/sharepoint-classic/chat-loader-js/`.

**Scope:**
1. Create `package.json` with lint tooling (ESLint or similar); no runtime framework dependencies.
2. Create `chat-loader.js`: pluggable token provider interface + default `_spPageContextInfo.aadTokenProviderFactory` implementation + stub mock provider.
3. Token acquisition: acquire once, pass to BFF immediately, do NOT store in localStorage/sessionStorage.
4. Manual `traceparent` generation via `crypto.randomUUID()` or `Math.random().toString(16)`.
5. BFF call: `fetch(bffBaseUrl + '/chat/session', { method: 'POST', headers: { Authorization, traceparent, 'Content-Type': 'application/json' }, body: JSON.stringify({ display_name }) })`.
6. Create `config.example.json` with `bffBaseUrl`, `bffResourceUri` as placeholder values.
7. Create `README.md` with: token security section, `userId` display-only note, how to use with classic pages.
8. Update `sample-aspx-snippets/classic-page-snippet.html` to reference the implementation.
9. Ensure `npm run lint` passes.

**Acceptance:**
- `npm ci && npm run lint` passes.
- No `localStorage.setItem` or `sessionStorage.setItem` for token storage in loader code.
- Pluggable token provider interface present with stub and SharePoint default implementations.
- `traceparent` generated and forwarded.
- Identity invariant comment at BFF call site.

---

## T04 — SPFx Web Part implementation

**Owner:** Mouse
**Depends on:** T11 + T12 sign-offs

**Description:**
Implement the minimal SPFx web part in `apps/spfx-webpart/identity-chat-webpart/`.

**Scope:**
1. Scaffold minimal SPFx web part structure: `package.json`, `gulpfile.js`, `tsconfig.json`, `.yo-rc.json` (minimal — not full Yeoman output).
2. Create `src/webparts/identityChat/IdentityChatWebPart.ts`: `AadHttpClient` acquisition, BFF call, render session ID.
3. Web part properties: `bffBaseUrl`, `bffResourceUri` (placeholder values; not real IDs).
4. `package-solution.json`: include `webApiPermissionRequests` with placeholder `resource` and `scope` values.
5. Manual `traceparent` injected via `AadHttpClient` request options (`{ headers: { traceparent } }`).
6. No `localStorage.setItem` or `sessionStorage.setItem` for token storage.
7. Create `README.md` with: token security section, `userId` display-only note, local dev instructions.
8. Ensure `npm ci && gulp build` passes (or `npm run build` if SPFx scripts use that).

**Acceptance:**
- `npm ci && gulp build` (or equivalent) passes.
- `webApiPermissionRequests` uses placeholder `{client-id}` brace tokens, not real IDs.
- `AadHttpClient` used for BFF call (not raw fetch).
- No localStorage write by web part code.
- `traceparent` header forwarded.
- Identity invariant comment at BFF call site.

---

## T05 — Tracing validation across variants

**Owner:** Mouse
**Depends on:** T02, T03, T04

**Description:**
Verify that `traceparent` is propagated from each client variant into BFF and through to Agent Execution Service.

**Scope:**
1. Manual integration test (or README walkthrough): start local Docker Compose + Jaeger; run each client variant against local BFF; verify Jaeger shows spans from BFF + Agent Execution Service + MCP.
2. Unit test (SPA): mock `fetch`, assert `traceparent` header is present in the BFF call.
3. Unit test (classic loader): mock `fetch`, assert `traceparent` header is present.
4. Document span attribute rules in each variant README (no raw tokens, no PII).

**Acceptance:**
- `traceparent` header present in BFF calls from all three variants (verified by unit test or log inspection).
- No raw token, `oid`, `sub`, `email`, or `upn` in span attributes.

---

## T06 — Diagrams and architecture doc updates

**Owner:** Mouse
**Depends on:** T02, T03, T04 (for accurate flow details)

**Description:**
Create/update Mermaid diagrams and architecture docs for each variant.

**Scope:**
1. Update `diagrams/mermaid/variant-a-sharepoint-classic.mmd` with M7 token acquisition flow.
2. Update `diagrams/mermaid/variant-b-spfx.mmd` with M7 token acquisition flow.
3. Update `diagrams/mermaid/variant-d-spa-comparison.mmd` with M7 PKCE flow.
4. Update `docs/architecture/03-variant-a-sharepoint-classic.md` with M7 implementation notes.
5. Update `docs/architecture/04-variant-b-spfx.md` with M7 implementation notes.
6. Update `docs/architecture/06-variant-d-spa-comparison.md` with M7 implementation notes.

**Acceptance:**
- All three Mermaid diagrams updated and render correctly.
- Architecture docs updated with token acquisition and BFF handoff description.

---

## T07 — Negative tests (no-token-persistence, no-userId-auth-fallback)

**Owner:** Mouse
**Depends on:** T02, T03, T04

**Description:**
Add negative test coverage for each variant's identity invariant and token persistence rules.

**Scope:**
1. **SPA**: Unit test — MSAL config `cacheLocation` is `sessionStorage` (not `localStorage`). Integration test — request to BFF with `userId` in body but no bearer token → expect 401.
2. **Classic loader**: Unit test — token is not written to `localStorage` or `sessionStorage` during BFF call. Integration test — request with `userId` in body but no bearer token → expect 401.
3. **SPFx**: Unit test — web part code does not call `localStorage.setItem` or `sessionStorage.setItem`. Integration test — mock BFF that asserts 401 when no token provided.
4. **Python BFF regression**: `python -m pytest` must still pass (235+ tests).

**Acceptance:**
- Per-variant test assertions for token persistence and `userId`-no-auth rejection.
- `python -m pytest` passes.

---

## T08 — CI validation gates

**Owner:** Mouse / Neo
**Depends on:** T02–T07

**Description:**
Wire CI-safe validation commands for each client variant. No live Azure calls in CI.

**Scope:**
1. Add `npm ci && npm run build` for SPA to CI or Makefile (offline; no Entra calls).
2. Add `npm ci && npm run lint` for classic loader.
3. Add `npm ci && gulp build` for SPFx web part.
4. Add `python -m pytest` regression check.
5. Confirm `docker compose config --quiet` still passes with any new compose changes.
6. No-secret scan: verify no real tenant/client IDs committed.

**Acceptance:**
- All validation commands run in CI without live Azure credentials.
- No secrets scan passes.
- `python -m pytest` passes.

---

## T09 — Morpheus post-implementation architecture review

**Owner:** Morpheus
**Depends on:** T02–T08

**Description:**
Post-implementation review of all M7 client variant code and docs for architectural coherence.

**Focus areas:**
1. Token acquisition code matches the design in this spec.
2. `traceparent` propagation is correct.
3. `userId` invariant is enforced in code and docs.
4. BFF CORS and endpoint changes are minimal and correct.
5. No backend services modified beyond approved scope.
6. Azure E2E gate is documented correctly in roadmap.

---

## T10 — Trinity post-implementation security review

**Owner:** Trinity
**Depends on:** T02–T08

**Description:**
Post-implementation security review of all M7 token acquisition code.

**Focus areas:**
1. MSAL `cacheLocation: 'sessionStorage'` — confirmed in code.
2. Classic loader — no localStorage token storage.
3. SPFx — no localStorage token storage by web part code.
4. `userId` negative tests pass.
5. CORS wildcard prohibition still in place.
6. No real tenant/client IDs/secrets committed.
7. Span attributes contain no PII.
8. `LIVE_AZURE_TESTS` opt-in is documented and not defaulted in CI.

---

## T13 — Final closeout

**Owner:** Mouse (coordinator)
**Depends on:** T09 + T10

**Description:**
Validate all M7 tasks complete; update spec state and roadmap.

**Scope:**
1. Run all validation commands; record results in `.progress.md`.
2. Update `state.json`: `phase → closed`, `status → complete`.
3. Update `roadmap.md`: M7 → ✅ Complete; add M7-AzureVerify gate entry.
4. Update `.squad/identity/now.md`: current position → M7-AzureVerify or M8.
