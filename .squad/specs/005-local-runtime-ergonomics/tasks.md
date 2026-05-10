# Spec 005 — Tasks

**Spec:** 005-local-runtime-ergonomics  
**Milestone:** M4 — Local runtime ergonomics  
**Updated:** 2026-05-14  
**Primary owners:** Tank, Neo  
**Reviewers:** Morpheus (architecture), Trinity (security)

---

## Dependency Order

```
T09 (Morpheus review) ─┐
T10 (Trinity review)  ─┤─→ T01 → T02 → T03 → T04   [Tank stream]
                        └─→ T05 → T06 → T07 → T08   [Neo stream]
```

T09 and T10 are blocking-review tasks that should run in parallel with each other once this spec is approved. T01–T04 (Tank) and T05–T08 (Neo) can be executed in parallel streams after reviews complete, with the ordering within each stream as listed.

---

## T09 — Architecture review of Compose strategy

**Owner:** Morpheus  
**Depends on:** Spec 005 spec artifacts complete  
**Blocks:** T01–T08 (implementation)  

**Description:**  
Review `design.md` ADR-M4-01 (base-plus-overlay strategy) and ADR-M4-02 (health check strategy). Confirm or amend the Compose schema before implementation begins. Record any amendments to this tasks file.

**Acceptance:**
- Morpheus leaves a written decision note in `.progress.md` under "Log".
- ADR-M4-01 status updated to "Accepted" or "Amended" in `design.md`.

**Validation:** n/a (review task)

---

## T10 — Security review of env examples and `/chat/session` contract

**Owner:** Trinity  
**Depends on:** Spec 005 spec artifacts complete  
**Blocks:** T06, T07, T08 (BFF identity changes)  

**Description:**  
Review `requirements.md` FR-05 through FR-07 and `design.md` BFF browser-runtime contract. Confirm that:
- `/chat/session` response design does not expose tokens or PII.
- CORS config does not introduce wildcard-with-credentials vulnerability.
- `userId` display-only rule is correctly specified and testable.
- Env example placeholders are all-zero GUIDs / template tokens only.

**Acceptance:**
- Trinity leaves a written decision note in `.progress.md` under "Log".
- Any security-required changes to requirements or design are documented before T06–T08 begin.

**Validation:** n/a (review task)

---

## T01 — Wire auth env vars into base Compose

**Owner:** Tank  
**Depends on:** T09 (Morpheus review)  
**Blocks:** T02  

**Description:**  
Update `docker/docker-compose.yml` to add auth environment variables to each service per the design schema in `design.md`. Use the all-zero GUID placeholders and `AUTH_MODE=mock` as base defaults. Do not add `AUTH_ISSUER` or `AUTH_JWKS_URL` to base — these belong in overlays only.

**Files to change:**
- `docker/docker-compose.yml`

**Example — bff service environment block (add):**
```yaml
- AUTH_MODE=mock
- AUTH_FIXTURE=delegated-user
- ALLOWED_AUDIENCES=api://00000000-0000-0000-0000-000000000101
- REQUIRED_SCOPES=mcp.access
- TRUSTED_TENANTS=00000000-0000-0000-0000-000000000000
- CORRELATION_HEADER=x-correlation-id
- ENABLE_DEBUG_CLAIMS=false
```

Repeat with service-appropriate values for `agent-gateway` (audience `...0102`, OBO vars) and `mcp-protected-api` (audience `...0103`).

**Validation:**
```
docker compose -f docker\docker-compose.yml config --quiet
```

---

## T02 — Add health checks to all services in base Compose

**Owner:** Tank  
**Depends on:** T01  
**Blocks:** T03  

**Description:**  
Add `healthcheck` blocks to each service in `docker/docker-compose.yml` using Python stdlib (no curl). Update `depends_on` on `bff` to use `condition: service_healthy` for `agent-gateway` and `mcp-protected-api`.

**Health check command (for each service, adjust port if needed):**
```yaml
healthcheck:
  test: ["CMD", "python", "-c",
    "import urllib.request, sys; urllib.request.urlopen('http://localhost:8080/healthz') or sys.exit(1)"]
  interval: 15s
  timeout: 5s
  retries: 3
  start_period: 10s
```

**Note:** All three services expose `/healthz` on container port 8080.

**Validation:**
```
docker compose -f docker\docker-compose.yml config --quiet
```

---

## T03 — Validate and tidy all Compose overlays

**Owner:** Tank  
**Depends on:** T02  
**Blocks:** T04  

**Description:**  
Review and update each overlay file against ADR-M4-01 (minimal, non-duplicating overlays). Per the design decision, overlay files should only carry variables that differ from the base. The existing single-tenant overlay sets `ISSUER_URL` — this should be confirmed against config.py (the variable name is `AUTH_ISSUER` in app config); correct the overlay if the variable name is wrong.

Run `config --quiet` on all four combinations and confirm zero errors.

**Files to check:**
- `docker/docker-compose.single-tenant.yml`
- `docker/docker-compose.vendor-shaped.yml`
- `docker/docker-compose.cross-tenant.local.yml`

**Validation:**
```
docker compose -f docker\docker-compose.yml config --quiet
docker compose -f docker\docker-compose.yml -f docker\docker-compose.single-tenant.yml config --quiet
docker compose -f docker\docker-compose.yml -f docker\docker-compose.vendor-shaped.yml config --quiet
docker compose -f docker\docker-compose.yml -f docker\docker-compose.cross-tenant.local.yml config --quiet
```

---

## T04 — Update Docker/local development documentation

**Owner:** Tank  
**Depends on:** T03  
**Blocks:** none (terminal in Tank stream)  

**Description:**  
Rewrite `docker/README.md` to include:
1. Overview of the base-plus-overlay strategy.
2. Explanation of `AUTH_MODE=mock` and how offline fixture-driven auth works.
3. Step-by-step startup for base and each variant.
4. How to verify services are healthy (`/healthz`, `docker compose ps`).
5. Note on env file usage vs inline env vars in Compose.
6. Note on how to switch to `AUTH_MODE=strict` (M6 concern; refer to future spec).

**Files to change:**
- `docker/README.md`

**Validation:** Doc review — no automated test. Spot-check that commands in README are syntactically correct.

---

## T05 — Wire auth env vars into overlay files

**Owner:** Neo  
**Depends on:** T09 (Morpheus review)  
**Blocks:** none (parallel with T01 stream after review)  

**Description:**  
Cross-check overlay files against the design. Confirm that `TENANT_MODE`, `VENDOR_ID`, and issuer variables are correctly named and not duplicating base auth defaults. This may require coordination with T03 (Tank) — if Tank has already made changes, Neo verifies consistency and does not re-duplicate effort.

**Note:** Neo should verify whether `config.py` in any service reads `TENANT_MODE`, `TENANT_A_ISSUER`, `TENANT_B_ISSUER`, or `VENDOR_ID` and flag any missing config keys to Morpheus for a follow-on decision.

**Files to check:**
- `docker/docker-compose.single-tenant.yml`
- `docker/docker-compose.vendor-shaped.yml`
- `docker/docker-compose.cross-tenant.local.yml`
- `apps/bff/python-fastapi/app/config.py`
- `apps/agent-gateway/python-fastapi-agent-framework/app/config.py`
- `apps/mcp-protected-api/python-fastapi/app/config.py`

**Validation:**
```
python -m pytest
```

---

## T06 — Add `/chat/session` BFF endpoint

**Owner:** Neo  
**Depends on:** T10 (Trinity review), T05  
**Blocks:** T07  

**Description:**  
Add `POST /chat/session` to `apps/bff/python-fastapi/app/main.py`. The endpoint:
- Requires auth context (delegated mock token in `AUTH_MODE=mock`).
- Generates and returns a `session_id` (UUID4, not a token).
- Includes the mandatory `userId` display-only comment (see `design.md`).
- Does NOT embed tokens or PII in the response.

Add a `CORS_ALLOWED_ORIGINS` field to `Settings` in `apps/bff/python-fastapi/app/config.py`.

Add `CORS_ALLOWED_ORIGINS=http://localhost:3000` to `config/env/bff.env.example` with an explanatory comment.

Add tests:
- `test_chat_session_returns_session_id` — POST succeeds with mock auth, response contains `session_id`.
- `test_chat_session_requires_auth` — POST without auth returns 401/403.
- `test_chat_session_userid_is_not_authz` — session_id is not derived from `sub`/`oid` claim value.

**Files to change:**
- `apps/bff/python-fastapi/app/main.py`
- `apps/bff/python-fastapi/app/config.py`
- `config/env/bff.env.example`
- `tests/` — new test file or extension of existing BFF tests

**Validation:**
```
python -m pytest
```

---

## T07 — Add local CORS config to BFF

**Owner:** Neo  
**Depends on:** T06  
**Blocks:** T08  

**Description:**  
Add FastAPI `CORSMiddleware` to the BFF application. Read `CORS_ALLOWED_ORIGINS` from settings. Default to `["http://localhost:3000"]`. Do not use wildcard `*` when `allow_credentials=True`.

```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "x-correlation-id"],
)
```

Add tests:
- `test_cors_allows_localhost_origin` — preflight OPTIONS returns correct `Access-Control-Allow-Origin`.
- `test_cors_no_wildcard_with_credentials` — assert `allow_origins` does not contain `*` when credentials are enabled.
- `test_cors_wildcard_rejected_at_startup` — assert that constructing Settings (or initialising the app) with `CORS_ALLOWED_ORIGINS=*` raises `RuntimeError` before the app starts serving requests.
- `test_cors_disabled_in_strict_mode_without_explicit_origins` — assert that when `AUTH_MODE=strict` and `CORS_ALLOWED_ORIGINS` is not set, the CORS middleware is not registered (i.e., no `Access-Control-Allow-Origin` header in responses).

**Files to change:**
- `apps/bff/python-fastapi/app/main.py`
- Tests as above

**Validation:**
```
python -m pytest
```

---

## T08 — Document and test `userId` display-only rule

**Owner:** Neo  
**Depends on:** T07  
**Blocks:** none (terminal in Neo stream)  

**Description:**  
Ensure the `userId` display-only rule is:
1. Commented in the `/chat/session` endpoint implementation (done in T06).
2. Documented in `docs/identity/` or `apps/bff/README.md` — a short paragraph stating the rule and its rationale.
3. Covered by a test that asserts that two mock tokens with **different `sub`/`oid` claim values** (but identical, valid `scp`/`aud`/`iss`) produce the same authorization outcome (both succeed). The endpoint MUST NOT evaluate the `sub`/`oid` claim to accept or reject the request — authorization depends only on `aud`, `scp`, `tid`, and `iss`.

This is a security-correctness documentation and test task, not a code-behavior change.

**Files to change:**
- `apps/bff/python-fastapi/README.md` (or equivalent doc file — create if absent)
- Tests (extend T06 test file or add a dedicated `test_userid_rule.py`)

**Validation:**
```
python -m pytest
```

---

## Summary Table

| ID | Title | Owner | Depends On | Validation |
|----|-------|-------|-----------|------------|
| T09 | Architecture review | Morpheus | spec complete | n/a |
| T10 | Security review | Trinity | spec complete | n/a |
| T01 | Wire auth vars into base Compose | Tank | T09 | `docker compose … config --quiet` |
| T02 | Add health checks | Tank | T01 | `docker compose … config --quiet` |
| T03 | Validate and tidy overlays | Tank | T02 | all 4 `config --quiet` |
| T04 | Update Docker docs | Tank | T03 | doc review |
| T05 | Wire auth vars into overlay files | Neo | T09 | `python -m pytest` |
| T06 | Add `/chat/session` BFF endpoint | Neo | T10, T05 | `python -m pytest` |
| T07 | Add local CORS config to BFF | Neo | T06 | `python -m pytest` |
| T08 | Document and test `userId` rule | Neo | T07 | `python -m pytest` |

## M4 Gate Criteria

All of the following must be true before M4 is marked complete:

- [ ] All Compose configs pass `config --quiet` (base + 3 overlays)
- [ ] `python -m pytest` passes with new tests for T06–T08
- [ ] BFF `/chat/session` endpoint exists and returns `session_id`
- [ ] CORS allows `http://localhost:3000` without wildcard
- [ ] `userId` display-only rule is documented and tested
- [ ] Docker README explains offline mock token flow
- [ ] No real GUIDs, tenant IDs, tokens, or secrets committed
- [ ] Morpheus architecture sign-off recorded in `.progress.md`
- [ ] Trinity security sign-off recorded in `.progress.md`
