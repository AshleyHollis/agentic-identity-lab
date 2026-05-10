# Spec 005 — Requirements

**Spec:** 005-local-runtime-ergonomics  
**Milestone:** M4 — Local runtime ergonomics  
**Updated:** 2026-05-14

---

## Functional Requirements

### FR-01 — Auth env vars in base Compose

The base `docker/docker-compose.yml` MUST set the following environment variables for **each** service (`bff`, `agent-gateway`, `mcp-protected-api`):

| Variable | Value (base default) |
|----------|----------------------|
| `AUTH_MODE` | `mock` |
| `AUTH_FIXTURE` | `delegated-user` |
| `ALLOWED_AUDIENCES` | Service-specific all-zero GUID (see env examples) |
| `REQUIRED_SCOPES` | Service-specific scope list |
| `TRUSTED_TENANTS` | `00000000-0000-0000-0000-000000000000` |
| `CORRELATION_HEADER` | `x-correlation-id` |
| `ENABLE_DEBUG_CLAIMS` | `false` |

Placeholders for strict mode (`AUTH_ISSUER`, `AUTH_JWKS_URL`) MAY be included as commented-out lines.

### FR-02 — Health checks in base Compose

Each service in `docker/docker-compose.yml` MUST have a `healthcheck` block that:
- Issues an HTTP GET to the service's `/healthz` endpoint.
- Uses Python (`python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/healthz')"`) or equivalent when curl is not available in the image.
- Sets `interval`, `timeout`, `retries`, and `start_period` appropriate for local dev startup.

`depends_on` on `bff` MUST use `condition: service_healthy` for `agent-gateway` and `mcp-protected-api`.

### FR-03 — Overlay files are minimal and consistent

Each overlay file (`single-tenant`, `vendor-shaped`, `cross-tenant`) MUST:
- Only set variables that are **different** from or **additive** to the base.
- Not duplicate base auth defaults (`AUTH_MODE`, `AUTH_FIXTURE`, etc.) unless intentionally overriding them.
- Use `{placeholder}` tokens or all-zero GUIDs — never real tenant IDs.

### FR-04 — Compose configs validate without warnings

All four Compose configurations MUST produce zero errors when run with:
```
docker compose -f docker\docker-compose.yml [[-f docker\docker-compose.<variant>.yml]] config --quiet
```

### FR-05 — BFF `/chat/session` endpoint

BFF (`apps/bff/python-fastapi/app/main.py`) MUST expose a `POST /chat/session` endpoint that:
- Requires a valid auth context (delegated mock token in local mode).
- Returns a JSON body containing at minimum a `session_id` field (opaque string, not a token).
- Does NOT return or embed a raw bearer token in the response.
- MUST NOT use `userId` extracted from the token as an authorization decision — it is display-only.

### FR-06 — BFF local CORS configuration

BFF MUST include CORS middleware that:
- Allows `http://localhost:3000` by default when `AUTH_MODE=mock` and `CORS_ALLOWED_ORIGINS` is not set (configurable via `CORS_ALLOWED_ORIGINS` env var, comma-separated).
- Allows `Authorization` header to be passed from browser clients.
- Is only active in `AUTH_MODE=mock` or when `CORS_ALLOWED_ORIGINS` is explicitly set; if neither condition holds, CORS middleware MUST NOT be added.
- Does NOT use wildcard (`*`) origins in configurations that accept `Authorization` headers.
- MUST raise a startup error (`RuntimeError` or equivalent) if `CORS_ALLOWED_ORIGINS` contains `*` (wildcard) — wildcard is unconditionally forbidden when `allow_credentials=True`. This validation MUST occur at app initialisation, before accepting requests.

### FR-07 — `userId` display-only rule

The BFF MUST enforce the following rule in code and documentation:
> `userId` derived from token claims (e.g., `sub`, `oid`, `preferred_username`) is a display hint only. It MUST NOT be used as an authorization gate, as a database key for permissions, or forwarded downstream as a trust signal. Authorization decisions are made by validating `aud`, `scp`, `tid`, and `iss` only.

This rule MUST be:
1. Documented in a code comment on the `/chat/session` endpoint.
2. Covered by at least one test asserting that a request with a mismatched `userId` field (if sent) does not produce a different authorization outcome.

### FR-08 — Env example commentary

Each `config/env/*.env.example` file MUST include a short step-by-step comment block explaining the offline mock token flow:
1. Set `AUTH_MODE=mock` (default — no Azure tenant needed).
2. Select a fixture with `AUTH_FIXTURE` or the `X-Identity-Lab-Fixture` header.
3. Replace `{tenant_id}` placeholders only when switching to `AUTH_MODE=strict`.
4. All GUIDs in this file are all-zero placeholders — replace with real values for strict mode.

### FR-09 — Docker/local dev documentation update

`docker/README.md` MUST be updated to include:
- A description of `AUTH_MODE=mock` and how the offline flow works.
- Step-by-step startup instructions for each Compose variant.
- Note on health checks and how to verify services are healthy.
- Note on env file usage vs inline Compose vars.

---

## Non-Functional Requirements

### NFR-01 — No secrets or real IDs committed

All placeholder values MUST use one of:
- All-zero GUIDs: `00000000-0000-0000-0000-000000000NNN`
- Literal brace tokens: `{tenant-id}`, `{tenant_id}`, `{tenant-a-id}`, `{tenant-b-id}`
- Descriptive strings: `vendor-placeholder`

Real tenant IDs, real client IDs, real secrets, and real tokens MUST NOT appear in any file committed to the repository.

### NFR-02 — Python tests remain green

`python -m pytest` MUST pass with no regressions after all changes. New tests for `/chat/session`, CORS, and `userId` rule MUST be added and green.

### NFR-03 — No runtime code changes beyond BFF endpoints

The shared `identity_lab_auth` library, `agent-gateway` app code, and `mcp-protected-api` app code MUST NOT be modified except for additive changes expressly required by this spec. M4 is a Docker/env/BFF ergonomics milestone, not a shared-library change.

### NFR-04 — Compose base file is the canonical local entry point

The `docker/docker-compose.yml` base file, optionally combined with a variant overlay, MUST be the only supported pattern for local development. Monolithic single-file variants MUST NOT be introduced.

### NFR-05 — Health check does not require curl

Health check commands MUST NOT require `curl` to be installed in the service image. Python stdlib HTTP is sufficient.

---

## Constraints

- This spec does not authorize any live Azure deployment, network call to Entra, or creation of new Python packages.
- The `/chat/session` endpoint MUST be added to the BFF only — not to agent-gateway or mcp-protected-api.
- CORS configuration is local-development-only; production CORS policy is an M6 concern.
- `AUTH_MODE=strict` enforcement on Compose is an M6 gate; M4 does not enable strict mode.
