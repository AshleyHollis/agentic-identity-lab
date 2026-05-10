# React + Vite SPA Public Client (M7 Placeholder)

Minimal browser client showing delegated token acquisition with MSAL Auth Code + PKCE and BFF-only calls.

> M7 scope: local/mock validation only. No live Azure E2E in this milestone.

## Local dev

1. Copy `.env.example` to `.env` and keep placeholder values unless doing private local setup.
2. Install dependencies:
   ```bash
   npm ci
   ```
3. Start the app:
   ```bash
   npm run dev
   ```
4. Build/lint/test:
   ```bash
   npm run build
   npm run lint
   npm test
   ```

## Env placeholders

- `VITE_ENTRA_CLIENT_ID={client-id}`
- `VITE_ENTRA_TENANT_ID={tenant-id}`
- `VITE_BFF_BASE_URL=http://localhost:8000`
- `VITE_BFF_API_SCOPE={bff-api-scope}`

No secrets, tenant IDs, client IDs, or tokens may be committed.

## M9 protected live smoke setup

- Keep all repo values placeholder-only; set real values only in protected operator environment variables.
- Required browser/client variables for smoke execution:
  - `VITE_ENTRA_CLIENT_ID`
  - `VITE_ENTRA_TENANT_ID`
  - `VITE_BFF_BASE_URL`
  - `VITE_BFF_API_SCOPE`
- The smoke runner must call BFF via `VITE_BFF_BASE_URL` and never hardcode endpoint URLs.
- `display_name` is optional context only; never add `userId` fallback logic as an identity signal.

## Auth and BFF contract

- Uses MSAL Browser **Auth Code + PKCE** flow (not implicit flow).
- Uses `cacheLocation: 'sessionStorage'` and `storeAuthStateInCookie: false`.
- Calls **BFF only** (`POST /chat/session`) with:
  - `Authorization: Bearer {token}`
  - `traceparent: 00-{trace-id}-{span-id}-01`
- `display_name`/`userId` in request body is display-only context and never identity.

## Token security

- This app never writes raw tokens to `localStorage`, `sessionStorage`, IndexedDB, logs, or spans.
- Token validation at the BFF is the trust anchor for identity.
- `sessionStorage` is selected to reduce persistence compared to `localStorage` while allowing tab refresh UX.

## Local tracing walkthrough (Docker Compose + Jaeger)

1. Start the local stack:
   ```bash
   docker compose -f docker/docker-compose.yml up -d
   ```
2. Run this SPA (`npm run dev`) with `VITE_BFF_BASE_URL=http://localhost:8000`.
3. Trigger `POST /chat/session` from the UI.
4. Open Jaeger at `http://localhost:16686`, search recent traces, and verify the flow spans BFF + Agent Execution Service.

## Telemetry safety rules (BC-07)

- Never place raw tokens, `oid`, `sub`, `email`, `upn`, or `preferred_username` in span attributes, structured logs, or `tracestate`.
- Only emit sanitized, non-PII metadata in client telemetry.

## Redirect origins (explicit only)

- Register exact redirect origins (for example `http://localhost:5173`) in Entra app registration.
- Do not use wildcard redirect URIs.
- BFF CORS must use explicit origins only (`*` is prohibited).
