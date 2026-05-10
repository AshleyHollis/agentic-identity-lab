# Spec 005: Local Runtime Ergonomics

**Status:** Complete  
**Milestone:** M4  
**Spec Phase:** complete  
**Created:** 2026-05-14  
**Updated:** 2026-05-14  
**Owners:** Tank (Lead), Neo (Backend)  
**Reviewers:** Morpheus (Architecture), Trinity (Security)  
**Impact:** Medium

## Summary

Wire Docker Compose and env examples to support the offline mock token flow across BFF, agent-gateway, and MCP protected API. Establish the base-vs-overlay compose strategy, add health checks, and deliver the BFF browser-runtime prerequisites (`/chat/session`, local CORS, `userId` display-only rule) needed by M7 client implementations.

## Scope (In)

- Auth environment variables (`AUTH_MODE`, `AUTH_FIXTURE`, audiences, scopes, trusted tenants, correlation header) wired into `docker/docker-compose.yml` and all overlay files.
- Service health checks for all three services using Python/HTTP fallback if curl is unavailable.
- Validated Compose configs for base, single-tenant, vendor-shaped, and cross-tenant variants.
- Env example files documented to explain the offline mock token flow.
- Updated Docker/local development documentation.
- BFF `/chat/session` endpoint (local browser contract for M7).
- Local-safe CORS config on BFF for SPA origins.
- Explicit `userId` display-only rule documented and verified.
- Decision recorded: canonical local Compose strategy and base-vs-overlay relationship.

## Scope (Out)

- Live Entra ID deployment, JWKS fetching, or managed identity.
- Real tenant IDs, secrets, or tokens anywhere in config examples.
- AKS, Terraform, or Azure deployment changes (M5/M6).
- M7 client variant implementations.
- `AUTH_MODE=strict` enforcement (reserved for M6 deployment gate).

## Artifacts

| Artifact | Description |
|----------|-------------|
| `goals.md` | M4 goals and success criteria |
| `research.md` | Current state audit of Compose, env, and config |
| `requirements.md` | Functional and non-functional requirements |
| `design.md` | Compose strategy decision, overlay schema, `/chat/session` contract |
| `tasks.md` | Decomposed tasks with owners, deps, and validation commands |
| `state.json` | Machine-readable spec state |
| `.progress.md` | Artifact and task progress tracking |

## Related Specs

- Spec 001: Token validation + OBO (complete — shared auth library)
- Spec 003: Local delegated flow (complete — mock OBO integration tests)
- Spec 004: APIM policy alignment (complete — policy XML + Terraform)
- Spec 007 (forthcoming): M7 client variants depend on M4 BFF `/chat/session` and CORS

## Validation Targets

```
docker compose -f docker\docker-compose.yml config --quiet
docker compose -f docker\docker-compose.yml -f docker\docker-compose.single-tenant.yml config --quiet
docker compose -f docker\docker-compose.yml -f docker\docker-compose.vendor-shaped.yml config --quiet
docker compose -f docker\docker-compose.yml -f docker\docker-compose.cross-tenant.local.yml config --quiet
python -m pytest
```

## Completion

M4 completed with all Spec 005 tasks and gate checklist items satisfied. Final validation passed for the base Compose file, all three overlay combinations, and the Python test suite (`65 passed`).
