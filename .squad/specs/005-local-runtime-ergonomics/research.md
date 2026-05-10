# Spec 005 — Research

**Spec:** 005-local-runtime-ergonomics  
**Milestone:** M4 — Local runtime ergonomics  
**Updated:** 2026-05-14

---

## Current State Audit

### Docker Compose — `docker/docker-compose.yml`

The base Compose file defines three services (`bff`, `agent-gateway`, `mcp-protected-api`) with:
- Correct build contexts pointing to `../apps/{service}/`.
- Ports mapped: bff→8080, agent-gateway→8081, mcp-protected-api→8082.
- Only `SERVICE_NAME`, `LOG_LEVEL`, and `PYTHONUNBUFFERED` set in `environment`.
- **Gap:** No `AUTH_MODE`, `AUTH_FIXTURE`, `ALLOWED_AUDIENCES`, `REQUIRED_SCOPES`, `TRUSTED_TENANTS`, `CORRELATION_HEADER`, or any identity-related environment variable is present.
- **Gap:** No `healthcheck` blocks defined for any service.
- `depends_on` is present on bff (depends on agent-gateway and mcp-protected-api) but does not use condition-based health checks.

### Compose Overlays

| File | Purpose | Current State |
|------|---------|--------------|
| `docker-compose.single-tenant.yml` | Single tenant variant | Sets `TENANT_MODE=single-tenant` and `ISSUER_URL` with `{tenant-id}` placeholder. Missing auth mode/fixture. |
| `docker-compose.vendor-shaped.yml` | Vendor-shaped tenant | Sets `TENANT_MODE=vendor-shaped` and `VENDOR_ID=vendor-placeholder`. Missing auth mode/fixture. |
| `docker-compose.cross-tenant.local.yml` | Cross-tenant local | Sets `TENANT_MODE=cross-tenant` with two placeholder issuer URLs. Missing auth mode/fixture. |

All overlays repeat env vars across all three services instead of service-specific sections where only relevant services differ.

### Env Example Files — `config/env/*.env.example`

All three `.env.example` files (`bff.env.example`, `agent-gateway.env.example`, `mcp-protected-api.env.example`) are well-structured and already contain:
- `AUTH_MODE=mock` with `disabled | mock | strict` inline comment.
- `AUTH_FIXTURE=delegated-user` with fixture override note.
- Placeholder `AUTH_ISSUER` and `AUTH_JWKS_URL` with `{tenant_id}` tokens.
- `ALLOWED_AUDIENCES` with all-zero GUID placeholders.
- `REQUIRED_SCOPES`.
- `TRUSTED_TENANTS` with all-zero GUID placeholder.
- `ENABLE_DEBUG_CLAIMS=false`.
- `CORRELATION_HEADER=x-correlation-id`.

**Assessment:** Env example files are in good shape. They need minor polish (step-by-step offline flow commentary) but no structural changes.

**Gap:** The env example values are *not* reflected in the Compose `environment:` blocks. A developer running `docker compose up` gets services with no auth config unless they manually provide a `.env` file.

### Application Config — `apps/{service}/app/config.py`

All three services use `identity_lab_auth` `load_auth_mode()` and fall back to safe defaults when env vars are absent:
- BFF defaults: `ALLOWED_AUDIENCES=api://00000000-0000-0000-0000-000000000101`, `REQUIRED_SCOPES=mcp.access`.
- Agent-gateway defaults: `ALLOWED_AUDIENCES=api://00000000-0000-0000-0000-000000000102`, OBO downstream `api://00000000-0000-0000-0000-000000000103`.
- MCP defaults: `ALLOWED_AUDIENCES=api://00000000-0000-0000-0000-000000000103`, `REQUIRED_SCOPES=mcp.access,mcp.write`.

All defaults use all-zero GUID patterns — safe for public repo. The `load_auth_mode()` default (when `AUTH_MODE` env var is absent) must be verified to be `mock` or `disabled`, not `strict`.

### BFF Application — `apps/bff/python-fastapi/app/main.py`

Current endpoints:
- `GET /healthz` — health probe.
- `GET /readyz` — readiness probe.
- `GET /whoami` — returns auth context claims.
- `GET /debug/claims` — returns claims when `ENABLE_DEBUG_CLAIMS=true`.

**Gap:** No `/chat/session` endpoint. M7 client variants require this to establish a conversation session identifier without exposing raw tokens.

**Gap:** No CORS middleware configured. M7 React/Next.js SPA clients running on `localhost:3000` will be blocked by browser CORS policy.

**Gap:** No `userId` display-only policy documented or enforced in code comments/tests.

### Docker README — `docker/README.md`

Basic placeholder. Describes three `docker compose` commands. Lacks:
- Explanation of auth modes.
- Step-by-step offline startup guide.
- Notes on env file vs inline env vars.
- Health check verification steps.

## Key Gaps Summary

| # | Gap | Severity | Owner |
|---|-----|----------|-------|
| G1 | Base Compose missing auth env vars | High | Tank |
| G2 | No health checks in any Compose service | High | Tank |
| G3 | Overlays not wired to base auth strategy | Medium | Tank/Neo |
| G4 | BFF missing `/chat/session` endpoint | High | Neo |
| G5 | BFF missing CORS middleware | High | Neo |
| G6 | `userId` display-only rule undocumented | Medium | Neo |
| G7 | Docker docs too thin to guide new devs | Low | Tank |
| G8 | Env examples lack step-by-step commentary | Low | Neo |

## Findings on Auth Mode Defaults

The `identity_lab_auth` `load_auth_mode()` function (from shared library) reads `AUTH_MODE` env var. When absent, the offline default must be confirmed as `mock`. This is safe — if Compose does not set `AUTH_MODE`, the service will fall back to the shared library default. This should be verified by Tank during T01 and covered by a test assertion.

## Compose Strategy Observation

The current overlay files include `services.bff`, `services.agent-gateway`, and `services.mcp-protected-api` blocks even when only one of them changes. Docker Compose merges overlays correctly regardless, but the pattern is verbose. The design decision (ADR candidate) is whether to keep three-service blocks in every overlay (explicit but repetitive) or use minimal overlays (only the services/keys that change). This spec recommends documenting the chosen strategy in `design.md`.
