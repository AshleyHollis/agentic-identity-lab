# SharePoint Classic Chat Loader (M7 placeholder)

This folder contains a minimal, public-safe SharePoint classic loader for Spec 007 T03.

## What this implementation does

- Provides a **pluggable token provider** interface.
- Default provider uses `_spPageContextInfo.aadTokenProviderFactory` (no ADAL).
- Includes a **mock token provider** for local/mock BFF testing.
- Acquires token once and immediately calls `POST /chat/session`.
- Sends `Authorization: Bearer`, `traceparent`, and `Content-Type: application/json`.
- Request body may include only `display_name`.

## Config placeholders

See `config.example.json`.

- `bffBaseUrl`: `http://localhost:8000`
- `bffResourceUri`: `api://{client-id}`

No live tenant/client IDs or secrets are committed.

## Script usage on classic page

```html
<script
  src="/SiteAssets/identity-chat/chat-loader.js"
  data-bff-base-url="http://localhost:8000"
  data-bff-resource-uri="api://{client-id}"
  data-session-path="/chat/session"
  data-display-name="Classic User"
  data-token-provider="mock"
></script>
```

The loader auto-starts when both `data-bff-base-url` and `data-bff-resource-uri` are set.

## M9 protected live smoke setup

- Keep script attributes and `config.example.json` placeholders in-repo; operators inject real values only in protected environments.
- Live smoke must wire:
  - `data-bff-base-url` (or `bffBaseUrl`) for BFF endpoint selection
  - `data-bff-resource-uri` (or `bffResourceUri`) for delegated token audience
  - optional `data-display-name` as display context only
- Never add `userId` request fields or fallback identity behavior in the loader.
- Tokens are in-memory only; do not persist or log them during browser automation.

## Token providers

Use default SharePoint provider:

```js
const provider = window.IdentityChatClassicLoader.createSharePointTokenProvider();
window.IdentityChatClassicLoader.loadChat({
  bffBaseUrl: 'http://localhost:8000',
  bffResourceUri: 'api://{client-id}',
  tokenProvider: provider,
});
```

Use mock provider for local dev:

```js
window.IdentityChatClassicLoader.loadChat({
  bffBaseUrl: 'http://localhost:8000',
  bffResourceUri: 'api://{client-id}',
  useMockTokenProvider: true,
  mockAccessToken: 'mock-access-token',
});
```

## Identity + security notes

- `userId` is **not** sent as an auth signal; identity comes only from bearer token validation at BFF.
- `display_name` is display/context only.
- Raw tokens are used in-memory and **not** written to `localStorage` or `sessionStorage`.
- Do not log raw tokens.

## Local development (M7)

- M7 is local/mock only. No live Azure token flow in this phase.
- Use Docker Compose BFF mock mode and the mock token provider above.

## Local tracing walkthrough (Docker Compose + Jaeger)

1. Start the local stack:
   ```bash
   docker compose -f docker/docker-compose.yml up -d
   ```
2. Load a classic page using this loader with `data-bff-base-url="http://localhost:8000"`.
3. Trigger a session call and confirm the outbound request includes `traceparent`.
4. Open Jaeger at `http://localhost:16686` and verify traces include BFF + Agent Execution Service spans.

## Telemetry safety rules (BC-07)

- Never emit raw tokens, `oid`, `sub`, `email`, `upn`, or `preferred_username` in span attributes, structured logs, or `tracestate`.
- Keep telemetry attributes sanitized and non-PII.

## Validation

```bash
npm ci
npm run lint
npm test
```
