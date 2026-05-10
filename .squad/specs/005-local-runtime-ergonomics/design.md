# Spec 005 — Design

**Spec:** 005-local-runtime-ergonomics  
**Milestone:** M4 — Local runtime ergonomics  
**Updated:** 2026-05-14  
**Note:** This is a planning artifact based on the approved session plan and existing roadmap. It is not a design for a deployed system change.

---

## ADR-M4-01: Canonical Local Compose Strategy

**Status: Accepted** — Morpheus architecture review T09 completed 2026-05-14.

### Context

The project currently has one base Compose file (`docker/docker-compose.yml`) and three overlay files. The base file does not set any auth environment variables. Overlays are used to activate variant behavior (single-tenant, vendor-shaped, cross-tenant). A new contributor running `docker compose up` without an overlay gets services with no identity config.

Two strategies are possible:

**Option A — Base-plus-overlay (recommended)**  
The base file sets all safe, non-secret, offline defaults (including `AUTH_MODE=mock`, `AUTH_FIXTURE`, audiences, scopes, trusted tenants). Overlay files apply only the keys that are **different** per variant. This keeps the base runnable standalone and makes overlays minimal and readable.

**Option B — Overlays carry all identity vars**  
The base file contains only build/port/network config. Every overlay must redeclare all identity vars. This prevents the base from being run standalone.

### Decision

**Option A — Base-plus-overlay is adopted.**

Rationale:
- A new contributor can run `docker compose up` from the base file alone and get a working mock-auth local stack.
- Overlay files become diff-readable: they express only what changes per variant.
- This is consistent with Docker Compose's documented merge-and-override semantics.
- It avoids variable duplication across overlay files.

### Consequences

- The base file is the authoritative source of defaults for auth env vars.
- Overlay files MUST NOT duplicate base defaults unless they intentionally override them.
- If a variable is needed by all variants (e.g., `CORRELATION_HEADER`), it belongs in the base.
- When `AUTH_MODE=strict` is introduced (M6), it will be applied in a deployment overlay — not in the base.

---

## ADR-M4-02: Health Check Strategy

**Status: Accepted** — Morpheus architecture review T09 completed 2026-05-14.

### Context

Docker Compose health checks require a command that exits 0 on success. `curl` is commonly used but may not be installed in minimal Python base images.

### Decision

Health checks will use Python stdlib only:

```yaml
healthcheck:
  test: ["CMD", "python", "-c",
    "import urllib.request, sys; urllib.request.urlopen('http://localhost:8080/healthz') or sys.exit(1)"]
  interval: 15s
  timeout: 5s
  retries: 3
  start_period: 10s
```

This works with any Python base image without installing additional tools.

---

## Compose Schema — Base File with Auth Defaults

### `docker/docker-compose.yml` (target state)

```yaml
name: agentic-identity-lab
services:
  bff:
    build:
      context: ../apps/bff/python-fastapi
      dockerfile: Dockerfile
    ports:
      - "8080:8080"
    environment:
      - SERVICE_NAME=bff
      - LOG_LEVEL=info
      - PYTHONUNBUFFERED=1
      - AUTH_MODE=mock
      - AUTH_FIXTURE=delegated-user
      - ALLOWED_AUDIENCES=api://00000000-0000-0000-0000-000000000101
      - REQUIRED_SCOPES=mcp.access
      - TRUSTED_TENANTS=00000000-0000-0000-0000-000000000000
      - CORRELATION_HEADER=x-correlation-id
      - ENABLE_DEBUG_CLAIMS=false
      # AUTH_ISSUER and AUTH_JWKS_URL are not set — only needed for AUTH_MODE=strict
    healthcheck:
      test: ["CMD", "python", "-c",
        "import urllib.request, sys; urllib.request.urlopen('http://localhost:8080/healthz') or sys.exit(1)"]
      interval: 15s
      timeout: 5s
      retries: 3
      start_period: 10s
    depends_on:
      agent-gateway:
        condition: service_healthy
      mcp-protected-api:
        condition: service_healthy

  agent-gateway:
    build:
      context: ../apps/agent-gateway/python-fastapi-agent-framework
      dockerfile: Dockerfile
    ports:
      - "8081:8080"
    environment:
      - SERVICE_NAME=agent-gateway
      - LOG_LEVEL=info
      - PYTHONUNBUFFERED=1
      - AUTH_MODE=mock
      - AUTH_FIXTURE=delegated-user
      - ALLOWED_AUDIENCES=api://00000000-0000-0000-0000-000000000102
      - REQUIRED_SCOPES=mcp.access,mcp.write
      - OBO_DOWNSTREAM_AUDIENCE=api://00000000-0000-0000-0000-000000000103
      - OBO_REQUIRED_SCOPES=mcp.access,mcp.write
      - TRUSTED_TENANTS=00000000-0000-0000-0000-000000000000
      - CORRELATION_HEADER=x-correlation-id
      - ENABLE_DEBUG_CLAIMS=false
    healthcheck:
      test: ["CMD", "python", "-c",
        "import urllib.request, sys; urllib.request.urlopen('http://localhost:8080/healthz') or sys.exit(1)"]
      interval: 15s
      timeout: 5s
      retries: 3
      start_period: 10s

  mcp-protected-api:
    build:
      context: ../apps/mcp-protected-api/python-fastapi
      dockerfile: Dockerfile
    ports:
      - "8082:8080"
    environment:
      - SERVICE_NAME=mcp-protected-api
      - LOG_LEVEL=info
      - PYTHONUNBUFFERED=1
      - AUTH_MODE=mock
      - AUTH_FIXTURE=delegated-user
      - ALLOWED_AUDIENCES=api://00000000-0000-0000-0000-000000000103
      - REQUIRED_SCOPES=mcp.access,mcp.write
      - TRUSTED_TENANTS=00000000-0000-0000-0000-000000000000
      - CORRELATION_HEADER=x-correlation-id
      - ENABLE_DEBUG_CLAIMS=false
    healthcheck:
      test: ["CMD", "python", "-c",
        "import urllib.request, sys; urllib.request.urlopen('http://localhost:8080/healthz') or sys.exit(1)"]
      interval: 15s
      timeout: 5s
      retries: 3
      start_period: 10s

networks:
  default:
    name: agentic-identity-lab
```

> **Note:** All GUIDs above are all-zero placeholders safe for public repository. No real tenant IDs, client IDs, or secrets are included.

---

## Compose Schema — Overlay Files (target state)

### `docker-compose.single-tenant.yml`

```yaml
services:
  bff:
    environment:
      - TENANT_MODE=single-tenant
      - AUTH_ISSUER=https://login.microsoftonline.com/{tenant-id}/v2.0
      - AUTH_JWKS_URL=https://login.microsoftonline.com/{tenant-id}/discovery/v2.0/keys
  agent-gateway:
    environment:
      - TENANT_MODE=single-tenant
      - AUTH_ISSUER=https://login.microsoftonline.com/{tenant-id}/v2.0
      - AUTH_JWKS_URL=https://login.microsoftonline.com/{tenant-id}/discovery/v2.0/keys
  mcp-protected-api:
    environment:
      - TENANT_MODE=single-tenant
      - AUTH_ISSUER=https://login.microsoftonline.com/{tenant-id}/v2.0
      - AUTH_JWKS_URL=https://login.microsoftonline.com/{tenant-id}/discovery/v2.0/keys
```

> Auth mode remains `mock` from the base. `ISSUER_URL` is not changed to `AUTH_ISSUER` without confirming config.py reads this variable.

### `docker-compose.vendor-shaped.yml`

```yaml
services:
  bff:
    environment:
      - TENANT_MODE=vendor-shaped
      - VENDOR_ID=vendor-placeholder
  agent-gateway:
    environment:
      - TENANT_MODE=vendor-shaped
      - VENDOR_ID=vendor-placeholder
  mcp-protected-api:
    environment:
      - TENANT_MODE=vendor-shaped
      - VENDOR_ID=vendor-placeholder
```

### `docker-compose.cross-tenant.local.yml`

```yaml
services:
  bff:
    environment:
      - TENANT_MODE=cross-tenant
      - TENANT_A_ISSUER=https://login.microsoftonline.com/{tenant-a-id}/v2.0
      - TENANT_B_ISSUER=https://login.microsoftonline.com/{tenant-b-id}/v2.0
  agent-gateway:
    environment:
      - TENANT_MODE=cross-tenant
      - TENANT_A_ISSUER=https://login.microsoftonline.com/{tenant-a-id}/v2.0
      - TENANT_B_ISSUER=https://login.microsoftonline.com/{tenant-b-id}/v2.0
  mcp-protected-api:
    environment:
      - TENANT_MODE=cross-tenant
      - TENANT_A_ISSUER=https://login.microsoftonline.com/{tenant-a-id}/v2.0
      - TENANT_B_ISSUER=https://login.microsoftonline.com/{tenant-b-id}/v2.0
```

---

## BFF Browser-Runtime Contract — `/chat/session`

### Purpose

The `/chat/session` endpoint provides M7 browser clients (React, Next.js, SharePoint) with a session identifier they can use to correlate subsequent chat requests. It does NOT expose raw tokens or user identity signals.

### Endpoint Specification

```
POST /chat/session
Authorization: Bearer <mock-token>
Content-Type: application/json
```

**Request body:** Empty or `{}`.

**Response (200 OK):**
```json
{
  "session_id": "<opaque-string>",
  "expires_at": "<ISO-8601-timestamp>"
}
```

**`session_id`:** A server-generated opaque identifier (e.g., UUID4). It is not a token, not a claim value, and not derived from `userId`.

**`userId` rule (mandatory comment in implementation):**
```python
# userId from token claims (sub, oid, preferred_username) is a display hint ONLY.
# It MUST NOT be used as an authorization gate, database key, or downstream trust signal.
# Session authorization is based solely on aud, scp, tid, and iss validation.
```

### CORS Configuration

BFF must add FastAPI `CORSMiddleware` conditionally. The middleware is only registered when the application is in `AUTH_MODE=mock` OR when `CORS_ALLOWED_ORIGINS` is explicitly set via the environment variable.

**Settings field** (to add to `config.py`):
```python
cors_allowed_origins: list[str]  # empty list disables CORS middleware
```

When loading settings:
- If `AUTH_MODE=mock` and `CORS_ALLOWED_ORIGINS` is not set → default to `["http://localhost:3000"]`.
- If `AUTH_MODE != mock` and `CORS_ALLOWED_ORIGINS` is not set → default to `[]` (CORS middleware not added).
- If `CORS_ALLOWED_ORIGINS` is explicitly set → parse comma-separated list (any mode).

**Startup guard (wildcard rejection):**
```python
_cors_origins = settings.cors_allowed_origins
if _cors_origins:
    # Security guard: wildcard MUST NOT be combined with allow_credentials=True
    if "*" in _cors_origins:
        raise RuntimeError(
            "CORS_ALLOWED_ORIGINS must not contain '*' when credentials are enabled. "
            "Set explicit origins (e.g. http://localhost:3000) instead."
        )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type", "x-correlation-id"],
    )
# If _cors_origins is empty, CORS middleware is not registered.
```

`cors_allowed_origins` is read from `CORS_ALLOWED_ORIGINS` env var (comma-separated). Wildcard `*` MUST NOT be used when `allow_credentials=True` — rejected at startup.

New env example variable to add to `bff.env.example`:
```
# CORS allowed origins for local browser clients (comma-separated; no wildcard with credentials)
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

---

## Environment Variable Reference Table

| Variable | BFF | Agent-GW | MCP | Notes |
|----------|-----|----------|-----|-------|
| `AUTH_MODE` | `mock` | `mock` | `mock` | Base default |
| `AUTH_FIXTURE` | `delegated-user` | `delegated-user` | `delegated-user` | Base default |
| `ALLOWED_AUDIENCES` | `...0101` | `...0102` | `...0103` | Per-service, all-zero GUIDs |
| `REQUIRED_SCOPES` | `mcp.access` | `mcp.access,mcp.write` | `mcp.access,mcp.write` | Per-service |
| `OBO_DOWNSTREAM_AUDIENCE` | — | `...0103` | — | Agent-GW only |
| `OBO_REQUIRED_SCOPES` | — | `mcp.access,mcp.write` | — | Agent-GW only |
| `TRUSTED_TENANTS` | `00..0000` | `00..0000` | `00..0000` | All-zero placeholder |
| `CORRELATION_HEADER` | `x-correlation-id` | `x-correlation-id` | `x-correlation-id` | Same across all |
| `ENABLE_DEBUG_CLAIMS` | `false` | `false` | `false` | Base default |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:3000` | — | — | BFF only; M4 addition |
| `AUTH_ISSUER` | placeholder | placeholder | placeholder | Overlay only; strict mode |
| `AUTH_JWKS_URL` | placeholder | placeholder | placeholder | Overlay only; strict mode |
| `TENANT_MODE` | — | — | — | Overlay only |
