# Design: Token Validation and OBO Boundaries (Spec 001)

**Status:** Draft (pending approval)  
**Owners:** Morpheus (Lead/Architect), Neo (Backend), Trinity (Security), Tank (Infra/APIM)  
**Impact:** High  
**Updated:** 2026-05-10

## Design Goals
- Deliver an offline-safe delegated-token validation story across BFF, agent-gateway, and MCP protected API.
- Enforce per-service audience boundaries and required scopes.
- Make the OBO boundary explicit (no inbound token forwarding).
- Keep outputs public-safe (no secrets, tenant IDs, or live tokens).

## Non-Goals
- Live Entra ID integration or JWKS fetching.
- Production-grade auth middleware or caching.
- App-only token support for delegated endpoints (future).

## Architecture Overview
**Local flow (mock-first):**
1. Client → BFF/agent-gateway with delegated token (mock fixture).
2. Service validates `iss/tid/exp/nbf`, `aud`, `scp` (delegated-only).
3. Service exchanges token via mock OBO (audience changes to MCP).
4. MCP protected API validates its own audience + scopes.

**Key rule:** Original user token is never forwarded downstream.

## Service Responsibilities
| Service | Responsibilities | Required `aud` | Required scopes |
| --- | --- | --- | --- |
| BFF (APIM ingress) | Validate delegated token, enforce audience + scope, sanitize claims, initiate OBO for MCP calls | `api://00000000-0000-0000-0000-000000000101` | `mcp.access` |
| Agent gateway | Validate delegated token, enforce audience + scope, perform mock OBO, replace Authorization for MCP calls | `api://00000000-0000-0000-0000-000000000102` | `mcp.access` (read), `mcp.write` (write) |
| MCP protected API | Validate delegated token for MCP audience, enforce per-endpoint scopes, reject app-only | `api://00000000-0000-0000-0000-000000000103` | `mcp.access` (read), `mcp.write` (tool writes) |

## Auth Module Shape (Mock Now, Entra Later)
**Shared module:** `apps/shared/python/identity_lab_auth`
- `AuthMode`: `disabled | mock | strict` with `load_auth_mode()`.
- `load_fixture_claims(name)` in mock mode; **header wins** over env:
  - Header: `X-Identity-Lab-Fixture`
  - Env: `AUTH_FIXTURE`
- `validate_claims(claims, settings)`:
  - Enforce `iss`, `tid`, `exp`, `nbf` (+ optional `iat` sanity)
  - `require_audience()` and `require_scope()` (any-of)
  - Delegated-only guard (`scp` required; `roles`-only rejected)
- `AuthContext`:
  - `authenticated`, `authorized`, `failure_reasons[]`
  - `claims` (sanitized allowlist only), `token_type`, `scopes`, `audiences`, `correlation_id`
- **Strict mode (future):** validate signature via Entra JWKS then reuse the same claim validation path.

## OBO Boundary and Token Flow
- Validate inbound token **before** any exchange.
- Mock OBO exchange returns a **downstream token/claims** with MCP audience.
- Replace outbound `Authorization` with the OBO token; never forward inbound tokens.
- Preserve user context across OBO via the new token, not via headers.
- Azure OpenAI / Foundry auth remains **service-to-service** (Managed Identity), separate from MCP delegated flows.

## APIM Ingress/Egress Implications
**Ingress (BFF + agent-gateway):**
- `validate-jwt` with placeholder issuer/tenant config.
- Enforce `aud` and `scp` per service.
- Require `scp` presence to reject app-only tokens.
- Apply trusted-tenant allowlist; reject `common/organizations` without allowlist.
- Preserve inbound `Authorization`; do **not** replace with managed identity.

**Egress (MCP downstream):**
- Expect OBO token in `x-obo-authorization`.
- Set outbound `Authorization` from `x-obo-authorization`.
- Validate OBO token audience `api://00000000-0000-0000-0000-000000000103`.
- Keep safe logging and correlation IDs; never emit tokens.

**Anti-pattern:** Avoid managed-identity token replacement on delegated flows.

## Config, Env, and Terraform Placeholders (No Secrets)
**Env examples (config/env/*.env.example):**
- `AUTH_MODE=mock` (default remains `disabled`)
- `AUTH_FIXTURE=delegated-user|app-only|wrong-audience`
- `ALLOWED_AUDIENCES=api://00000000-0000-0000-0000-000000000101,...`
- `REQUIRED_SCOPES=mcp.access,mcp.write`
- `TRUSTED_TENANTS=00000000-0000-0000-0000-000000000001`
- `ENABLE_DEBUG_CLAIMS=false`

**Terraform placeholders (infra/terraform):**
- `tenant_id_placeholder`, `openid_config_url_placeholder`
- `apim_ingress_allowed_audiences`, `apim_ingress_required_scopes`
- `apim_obo_downstream_audience`, `apim_obo_required_scopes`
- `trusted_tenant_allowlist`
- `policy_fragment_ids` / `policy_xml_path`

## Safe Claims and Diagnostics Rules
**Safe claims allowlist:** `aud`, `iss`, `tid`, `azp`, `appid`, `scp`, `roles`, `exp`, `nbf`, `iat`, `ver`  
**Never log/return:** `oid`, `sub`, `upn`, `email`, `name`, `preferred_username`, any custom userId headers.  
Debug claims must be sanitized and gated by `ENABLE_DEBUG_CLAIMS`.

## Offline/Mock-First Test Strategy
- Use fixtures in `tests/fixtures/sample-claims/*`.
- Fixture selection: **header overrides env**; unknown fixture → unauthenticated.
- Tests:
  - Delegated success (correct audience + scope)
  - Wrong audience → 401
  - Missing scope → 403
  - App-only token → 403
  - Untrusted tenant → 401
  - OBO boundary: outbound token differs from inbound
- Live Entra tests are gated by explicit env flag and excluded from CI.

## Security Review Gates
- Ingress validates signature (strict), issuer, tenant, audience, expiry/nbf, and required scopes.
- Delegated-only endpoints reject app-only tokens.
- OBO tokens used for downstream; original user tokens never forwarded.
- Safe-claims allowlist only; PII and raw tokens never logged or returned.
- Trusted-tenant allowlist enforced; no `common/organizations` bypass.
- Azure OpenAI / Foundry auth remains on Managed Identity path.

## Open Questions
- Strict mode JWKS caching strategy and rotation cadence.
- Whether any MCP endpoints should support app-only tokens (future scope).

## Implementation Sequencing Recommendation
1. Update shared `identity_lab_auth` (auth mode, fixture loader, guards, AuthContext, mock OBO exchange).
2. Wire BFF, agent-gateway, and MCP protected API to shared validators and OBO exchange.
3. Add pytest coverage for fixture auth, scope/audience checks, delegated-only, and OBO boundary.
4. Update APIM policy examples (ingress/egress) and document anti-patterns.
5. Add env examples + Terraform placeholders (no secrets).
6. Run `python -m pytest` for validation.
