# Requirements: Token Validation and OBO Boundaries

## Public-Safety Constraints
- No secrets, tenant IDs, subscription IDs, or real tokens.
- Never log raw Authorization headers or token contents.
- Only log sanitized claim metadata (aud, iss, tid, scp/roles, exp, azp/appid).

## Functional Requirements
- **FR-1 Auth Mode:** Each service supports `AUTH_MODE` in `{disabled, mock, strict}`. Default remains `disabled`; `mock` is required for this feature.
- **FR-2 Fixture Claims:** In mock mode, load claims from `tests/fixtures/sample-claims` via header `X-Identity-Lab-Fixture` or env `AUTH_FIXTURE`. Supported values: `delegated-user`, `app-only`, `wrong-audience`. Unknown values → unauthenticated.
- **FR-3 Audience Enforcement:** Implement `identity_lab_auth.guards.require_audience()` to validate `aud` against `Settings.allowed_audiences` (any-of). Fail with **401**.
- **FR-4 Scope Enforcement:** Implement `identity_lab_auth.guards.require_scope()` to validate `scp` against `Settings.required_scopes` (any-of). Missing scopes → **403**.
- **FR-5 Delegated Only:** For BFF/agent-gateway/MCP endpoints in this feature, reject app-only tokens (roles-only) unless explicitly configured later.
- **FR-6 Auth Context:** `AuthContext` exposes authenticated + authorized flags and reason(s) for failure, while continuing to return sanitized claims.
- **FR-7 OBO Boundary:** Introduce a mock OBO exchange interface (shared module) that returns a downstream token/claims with MCP audience; never forward inbound tokens.
- **FR-8 MCP Enforcement:** MCP protected API validates its own audience + scopes using the same guard functions.
- **FR-9 Tests:** Add tests for delegated success, wrong audience, missing scope, app-only rejection, and OBO boundary token replacement.

## Non-Functional Requirements
- Offline-safe by default (no network calls to Entra).
- Windows-friendly paths and commands.
- Minimal changes to existing endpoint surfaces.

## Acceptance Criteria
- `python -m pytest` passes with new auth tests.
- BFF/agent-gateway `/whoami` indicates authorized when fixture is `delegated-user` and scopes/audiences match.
- Requests with `wrong-audience` fixture fail with **401**; missing scopes fail with **403**.
- MCP protected API never receives the original inbound token in mock OBO flow.
- Debug claims remain sanitized and gated by `ENABLE_DEBUG_CLAIMS`.

## Open Design Questions
- Does fixture selection prefer header or env when both are set?
- Should scope enforcement be any-of or all-of for `REQUIRED_SCOPES`?
