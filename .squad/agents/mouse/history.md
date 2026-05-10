# Mouse History

## Project Seed

- Project: agentic-identity-lab
- Primary user: Ashley Hollis
- Frontend focus: SharePoint classic page loader, SPFx modern path, React/Vite or Next.js SPA comparison, TypeScript placeholders.
- Public repo constraints: no secrets, tenant-specific IDs, subscription IDs, generated certificates, or tokens.

## Learnings
- Documented SharePoint classic loader and SPFx/SPA placeholders with explicit "userId is not identity" guidance.
- Added SharePoint docs and env example placeholders for BFF and SPA configuration.

## M7 Implementation (Batch 1)

- **T02 — SPA Public Client (2026-06-02):** React/Vite SPA with PKCE token acquisition. Implemented MSAL sessionStorage config (no localStorage token caching), BFF integration with bearer token delegation, display_name UI collection (context-only). Validation: npm ci, npm run build, npm run lint, npm run test all passed (3 tests). Variant priority #1.
- **T03 — SharePoint Classic Loader (2026-06-02):** Classic page loader with pluggable token provider callback (testable, non-hardcoded SPUser context). Implemented SPUser context integration for display_name without identity usage. Token flow: OneDrive SPUser → pluggable provider → bearer token to BFF. Validation: npm ci, npm run lint, npm run test passed (4 tests). Variant priority #2.
- **T04 — SPFx Web Part (2026-06-02):** Modern web part with AadHttpClient token acquisition. BFF integration with display_name from SPFx context. Token flow: AadHttpClient → bearer token to BFF. Validation: npm ci, npm run build passed. Variant priority #3.

## M7 Follow-Up (Batch 2)

- **T05 — Tracing Instrumentation Validation (2026-06-15):** OpenTelemetry span validation across BFF + client variants; verified PII/token exclusion, traceparent compliance, span attribute hygiene. Added Jaeger walkthrough and telemetry/PII bans to variant READMEs. Validation: SPA npm ci/build/lint/test, classic npm lint/test, SPFx npm ci/build/test, state parse check all passed.
- **T06 — Architecture Diagrams & Documentation (2026-06-15):** Mermaid diagrams for PKCE (SPA), pluggable provider callback (classic), AadHttpClient (SPFx); BFF-only boundary clarification, traceparent guidance, display-only invariant documentation. Updated variant READMEs and M7/M8 roadmap; Agent Execution Service terminology aligned; M8 E2E with live Azure deferral documented.

## M7 Final Closeout

- **T13 — Final Closeout (2026-06-23):** Reconciled M7 completion after A-01 remediation lifecycle closure and T09/T10 dual review gate acceptance (Morpheus architecture + Trinity security). Updated Spec 007 `.progress.md` (phase: closed, all tasks T00–T13 complete/accepted), `state.json` (status: complete, phase: closed), and `.squad/project/roadmap.md` (M7 marked complete/closed, current focus advanced to M8 planning). Validation: state.json parse PASS; focused status checks confirmed M7 complete, M8 next, no live Azure execution in M7. Morpheus roadmap review initiated for M8 opt-in planning. Spec 007 closed.

## M9 Readiness Follow-Up

- **Client readiness gap closure (2026-07-08):** Expanded `tools/ci/m8_browser_smoke_harness.py` from SPA-only checks to SPA + SharePoint classic + SPFx boundary checks (BFF wiring markers, no `userId` fallback, no token persistence/logging, placeholder scope contract). Added explicit `M9 protected live smoke setup` guidance to each client README and created `.squad/decisions/inbox/mouse-m9-client-readiness.md` with remaining blockers/tasks until Spec 009 exists. Validation: harness static run PASS; focused security tests PASS; SPA/classic/SPFx local build/test/lint commands PASS.
