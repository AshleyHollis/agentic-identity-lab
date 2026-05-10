# Docker — Local Development Guide

This directory contains Docker Compose files for running the agentic-identity-lab stack locally.
All examples use all-zero GUID placeholders and offline mock auth — no real tenant IDs, tokens, or secrets are included.

---

## Compose Strategy: Base-plus-Overlay

The base file (`docker-compose.yml`) sets safe, offline defaults for all services including `AUTH_MODE=mock`.
Overlay files (`docker-compose.*.yml`) apply only the variables that differ per variant.

```
docker-compose.yml                     ← base: mock auth, health checks, ports
docker-compose.single-tenant.yml       ← overlay: adds AUTH_ISSUER, AUTH_JWKS_URL, TENANT_MODE
docker-compose.vendor-shaped.yml       ← overlay: adds TENANT_MODE, VENDOR_ID
docker-compose.cross-tenant.local.yml  ← overlay: adds TENANT_MODE, TENANT_A_ISSUER, TENANT_B_ISSUER
```

Overlays are **merged** on top of the base. Any variable already set in the base is inherited unless the overlay explicitly overrides it.

---

## AUTH_MODE=mock — Offline Fixture-Driven Auth

When `AUTH_MODE=mock` (the base default), services accept a pre-signed fixture token without contacting any identity provider.
No Azure AD tenant, no JWKS endpoint, and no internet connection are required.

The fixture identity used is controlled by `AUTH_FIXTURE=delegated-user`, which selects a bundled claims fixture from the shared `identity_lab_auth` library.

Auth environment variables set in the base:

| Variable | Value (base default) | Notes |
|---|---|---|
| `AUTH_MODE` | `mock` | Offline fixture-driven auth; no live IdP needed |
| `AUTH_FIXTURE` | `delegated-user` | Fixture identity for local dev |
| `ALLOWED_AUDIENCES` | per-service all-zero GUID | Public-safe placeholder |
| `REQUIRED_SCOPES` | per-service scope list | Validated against fixture token |
| `TRUSTED_TENANTS` | `00000000-0000-0000-0000-000000000000` | All-zero placeholder tenant |
| `CORRELATION_HEADER` | `x-correlation-id` | Forwarded across service calls |
| `ENABLE_DEBUG_CLAIMS` | `false` | Set to `true` to log decoded claims |

`AUTH_ISSUER` and `AUTH_JWKS_URL` are **not** set in the base — they are only required for `AUTH_MODE=strict` and belong in deployment overlays (see M6 note below).

---

## Starting the Stack

### Base stack (mock auth, no overlay)

The simplest way to start — all services run with offline mock auth:

```bash
docker compose -f docker/docker-compose.yml up --build
```

### Single-tenant overlay

Adds `AUTH_ISSUER` and `AUTH_JWKS_URL` for a single Entra ID tenant.
Replace `{tenant-id}` in the overlay file with your tenant ID before running:

```bash
docker compose -f docker/docker-compose.yml -f docker/docker-compose.single-tenant.yml up --build
```

### Vendor-shaped overlay

```bash
docker compose -f docker/docker-compose.yml -f docker/docker-compose.vendor-shaped.yml up --build
```

### Cross-tenant overlay

Adds `TENANT_A_ISSUER` and `TENANT_B_ISSUER`.
Replace `{tenant-a-id}` and `{tenant-b-id}` in the overlay before running:

```bash
docker compose -f docker/docker-compose.yml -f docker/docker-compose.cross-tenant.local.yml up --build
```

### Tracing overlay (opt-in, local only)

Adds an OpenTelemetry Collector and Jaeger for local trace visualization.
No cloud credentials or external endpoints are required.

```bash
docker compose -f docker/docker-compose.yml -f docker/docker-compose.tracing.yml up --build
```

Once the stack is up, open **http://localhost:16686** to view the Jaeger UI.

The overlay:
- Runs `otel/opentelemetry-collector-contrib:0.104.0` on ports `4317` (gRPC) and `4318` (HTTP).
- Runs `jaegertracing/all-in-one:1.58` with UI on port `16686`.
- Sets `OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317` on `bff`, `agent-gateway`, and `mcp-protected-api`.
- All services join the existing `agentic-identity-lab` Docker network so `otel-collector:4317` resolves by DNS.

In offline/test mode (`AUTH_MODE=mock` without the tracing overlay), set `OTEL_SDK_DISABLED=true`
to suppress OTLP export and avoid network calls during `pytest`.

Collector config is in `docker/otel-collector-config.yaml`.

> **Note:** Image versions and port mappings in the tracing overlay are illustrative.
> See `docker/docker-compose.tracing.yml` for pinning guidance.

---

## Verifying Service Health

All three services expose `/healthz` on their container port (8080). The base Compose file configures Python-stdlib health checks — no `curl` required.

After starting the stack, check service status:

```bash
docker compose -f docker/docker-compose.yml ps
```

All services should show `healthy` in the STATUS column. If a service shows `starting`, wait a few seconds and re-check — `start_period` is 10 seconds.

Probe individual endpoints directly:

```bash
# BFF
curl http://localhost:8080/healthz

# Agent Gateway
curl http://localhost:8081/healthz

# MCP Protected API
curl http://localhost:8082/healthz
```

The BFF `depends_on` is configured with `condition: service_healthy` for both `agent-gateway` and `mcp-protected-api`, so it will not start until its dependencies pass health checks.

---

## Env File vs Inline Environment Variables

Variables can be supplied in two ways:

**Inline in the Compose file (current approach):**
```yaml
environment:
  - AUTH_MODE=mock
```
Used for safe, non-secret defaults in the base file. Suitable for public repositories.

**Via an env file:**
```yaml
env_file:
  - ../config/env/bff.env
```
Use this for local overrides containing real tenant IDs or client secrets.
Copy the example files from `config/env/` and populate with your values:

```bash
cp config/env/bff.env.example config/env/bff.env
cp config/env/agent-gateway.env.example config/env/agent-gateway.env
cp config/env/mcp-protected-api.env.example config/env/mcp-protected-api.env
```

The `*.env` files (without `.example`) are gitignored — never commit real credentials.

---

## Switching to AUTH_MODE=strict (M6 Note)

`AUTH_MODE=strict` enables live JWT validation against a real Entra ID JWKS endpoint.
This mode requires `AUTH_ISSUER` and `AUTH_JWKS_URL` to be set to real values.

**Do not enable `AUTH_MODE=strict` in the base Compose file.**
It will be applied via a deployment overlay as part of M6 (production deployment gate).
Refer to the M6 spec for the strict-mode deployment overlay schema and the service-to-service OBO flow requirements.

---

## Notes

- Update the `apps/` context paths in `docker-compose.yml` if service folders are moved.
- All GUIDs in the base and overlay examples are all-zero placeholders — safe for public repositories.
- Do not commit real tenant IDs, client IDs, secrets, or tokens to any Compose or env file.

