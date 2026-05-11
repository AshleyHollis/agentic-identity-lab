# BFF (FastAPI)

BFF service that enforces the local/mock delegated-token boundary and returns safe claim metadata only.

## Endpoints
- GET `/healthz`
- GET `/readyz`
- GET `/whoami`
- GET `/debug/claims`
- POST `/chat/session`

`/whoami`, `/debug/claims`, and `/chat/session` require a delegated token in mock or strict auth mode. Local mock mode uses the `X-Identity-Lab-Fixture` header to select offline-safe claim fixtures.

### POST `/chat/session`

Returns a server-generated session identifier for browser chat clients. In strict mode, this endpoint also invokes Agent Execution (`/agent/invoke`) to exercise the delegated BFF -> Agent -> MCP chain.

Response schema:

```json
{
  "session_id": "<opaque UUID4 — not a token, not derived from user claims>",
  "expires_at": "<ISO-8601 timestamp>"
}
```

No raw bearer token or PII is included in the response.

### Downstream chain settings

- `CHAT_SESSION_CHAIN_ENABLED` (default: `false`)
- `AGENT_EXECUTION_BASE_URL` (required when chain is enabled)
- `AGENT_EXECUTION_INVOKE_PATH` (default: `/agent/invoke`)
- `DOWNSTREAM_TIMEOUT_SECONDS` (default: `10`)
- Strict mode also requires protected Entra OBO settings: `OBO_TOKEN_URL`, `OBO_CLIENT_ID`,
  `OBO_CLIENT_SECRET`, and `OBO_REQUIRED_SCOPES`. The BFF exchanges the inbound BFF-audience
  token and sends only the Agent-audience token downstream.

## `userId` Display-Only Rule

`userId` derived from token claims (`sub`, `oid`, `preferred_username`) is a **display hint only**.

It **MUST NOT** be used as:
- An authorization gate (accept/reject a request)
- A database key for permissions or ownership lookups
- A downstream trust signal forwarded to other services

Authorization decisions are made exclusively by validating `aud`, `scp`, `tid`, and `iss`.
Two tokens that differ only in `sub`/`oid` but share valid `aud`/`scp`/`iss`/`tid` MUST produce
the same authorization outcome. The `/chat/session` endpoint enforces this rule — `session_id` is
a server-generated UUID4 entirely independent of any user identity claim.

## CORS

In `AUTH_MODE=mock` the BFF adds `CORSMiddleware` defaulting to `http://localhost:3000`.
Set `CORS_ALLOWED_ORIGINS` (comma-separated) to override (for example:
`http://localhost:5173,http://localhost:3000,https://localhost:4321`). Wildcard (`*`) is rejected
at startup — it is unconditionally incompatible with `allow_credentials=True`.

For browser clients, `traceparent` is an allowed CORS request header so W3C trace propagation
is not blocked by preflight.

In `AUTH_MODE=strict` (or any non-mock mode), CORS middleware is not registered unless
`CORS_ALLOWED_ORIGINS` is explicitly set.

## Run locally (Windows)
1. Copy `config/env/bff.env.example` to `config/env/bff.env` and update as needed.
2. From `apps/bff/python-fastapi`:
   - `set PYTHONPATH=..\..\shared\python`
   - `python -m pip install fastapi uvicorn[standard]`
   - `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`
