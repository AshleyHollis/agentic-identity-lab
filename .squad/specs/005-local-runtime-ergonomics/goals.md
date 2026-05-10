# Spec 005 — Goals

**Spec:** 005-local-runtime-ergonomics  
**Milestone:** M4 — Local runtime ergonomics  
**Updated:** 2026-05-14

---

## Primary Goal

Make Docker Compose and env examples fully support the offline mock token flow for BFF, agent-gateway, and MCP protected API, so any contributor can run the full local stack without secrets or a live Azure tenant.

## Success Criteria

1. **Auth wired in base Compose.** `docker/docker-compose.yml` sets `AUTH_MODE=mock`, `AUTH_FIXTURE=delegated-user`, per-service `ALLOWED_AUDIENCES`, `REQUIRED_SCOPES`, `TRUSTED_TENANTS`, and `CORRELATION_HEADER` for every service.

2. **Overlay files are consistent.** `docker-compose.single-tenant.yml`, `docker-compose.vendor-shaped.yml`, and `docker-compose.cross-tenant.local.yml` each apply only the variables that differentiate the variant from the base; they do not duplicate base auth defaults.

3. **Health checks pass.** All three services expose HTTP health endpoints (`/healthz`, `/readyz`) and Compose `healthcheck` blocks verify them at startup. Health checks use Python/HTTP where curl is not available.

4. **All Compose configs validate.** `docker compose … config --quiet` succeeds without warnings for base and all three overlays.

5. **Env examples explain the offline flow.** `config/env/*.env.example` files have inline comments that walk a new contributor through: auth mode, fixture selection, audience/scope placeholders, trusted tenant placeholder, and what changes when moving to `AUTH_MODE=strict`.

6. **BFF browser-runtime prerequisites are ready for M7.**
   - `/chat/session` endpoint exists on BFF and returns a session identifier.
   - BFF CORS configuration allows `http://localhost:3000` (and configurable SPA origins) for local development.
   - Code and documentation make explicit that `userId` extracted from a token or session is a display-only hint; it is never an authorization signal and must never gate resource access.

7. **Python tests remain green.** `python -m pytest` passes with no regressions after all changes.

8. **No secrets committed.** All example files use only placeholder values (e.g., `{tenant-id}`, all-zero GUIDs `00000000-0000-0000-0000-000000000NNN`, `vendor-placeholder`).

## Secondary Goals

- Document the canonical local Compose strategy (base + overlay vs monolithic) so future contributors understand the pattern.
- Record a decision (ADR candidate) on base-vs-overlay relationship to eliminate ambiguity before M6 deployment work.

## Non-Goals

- Running against a real Azure tenant.
- Implementing `AUTH_MODE=strict` enforcement (M6).
- AKS, Terraform, or any cloud infrastructure change (M5/M6).
- Implementing M7 client variants (M7).
