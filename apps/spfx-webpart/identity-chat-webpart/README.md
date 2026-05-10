# Identity Chat SPFx Web Part (M7 T04)

Minimal SPFx placeholder web part for Spec 007 T04. This project demonstrates the **approved auth boundary**: SPFx code uses `AadHttpClient` for BFF calls and never handles raw access tokens directly.

## Security and identity rules

- Uses `context.aadHttpClientFactory.getClient(bffResourceUri)` for `POST /chat/session`.
- Does **not** use `AadTokenProvider` in web part code.
- Does **not** use `SPHttpClient` for BFF calls.
- Web part code does not persist tokens to `localStorage` or `sessionStorage`.
- `traceparent` is generated manually and forwarded in request headers.
- `userId` / `display_name` values in request body are **display context only**; identity is established only by BFF bearer-token validation.

## Placeholder configuration only

This project intentionally keeps public-safe placeholder values only:

- `bffBaseUrl` default: `http://localhost:8000`
- `bffResourceUri` default: `api://{client-id}`
- `config/package-solution.json` permission request:
  - `resource`: `api://{client-id}`
  - `scope`: `access_as_user`

Do not commit real tenant IDs, client IDs, tokens, or secrets.

## M9 protected live smoke setup

- Keep in-repo defaults as placeholders; configure real values only through protected operator workflows/tenant configuration.
- Smoke execution must provide:
  - `bffBaseUrl` web part property wired to the target BFF base URL
  - `bffResourceUri` web part property wired to delegated API audience
- Continue using `AadHttpClient` only; do not introduce raw token plumbing, persistence, or logging.
- `display_name` remains optional display context only; never add `userId` identity fallback.

## Local build / validation

From this folder:

```powershell
npm ci
npm run build
npm test
```

`npm run build` runs `gulp build`, which compiles TypeScript (`src/**/*.ts`) into `lib/`.
`npm test` runs a static/unit guard that verifies `traceparent` is passed in `AadHttpClient` request options.

## Local tracing walkthrough (Docker Compose + Jaeger)

1. Start the local stack:
   ```bash
   docker compose -f docker/docker-compose.yml up -d
   ```
2. Build the web part (`npm run build`) and run it against `http://localhost:8000` BFF settings.
3. Trigger `POST /chat/session` from the web part.
4. Open Jaeger at `http://localhost:16686` and confirm traces flow through BFF + Agent Execution Service.

## Telemetry safety rules (BC-07)

- Never include raw tokens, `oid`, `sub`, `email`, `upn`, or `preferred_username` in span attributes, structured logs, or `tracestate`.
- Emit only sanitized, non-PII telemetry attributes.

## M7 scope note

M7 is local/mock focused and does **not** include live Azure E2E flows. Live tenant validation is deferred to M8 and must be explicit opt-in.
