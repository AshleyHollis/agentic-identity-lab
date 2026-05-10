# Neo Design Notes — Spec 001 (Token Validation + OBO)

## Auth module shape (mock now, Entra later)
- Extend `identity_lab_auth` with:
  - `AuthMode` (`disabled|mock|strict`) + loader (`load_auth_mode()`).
  - Fixture claim loader `load_fixture_claims(name)` keyed by `X-Identity-Lab-Fixture` header or `AUTH_FIXTURE` env.
  - `validate_claims(claims, settings)` that enforces `iss/tid/exp/nbf`, `require_audience`, `require_scope`, and delegated-only.
  - `build_auth_context(request, settings)` returning `AuthContext` with `authenticated`, `authorized`, `failure_reasons[]`, `claims` (sanitized), `token_type`, `scopes`, `audiences`, `correlation_id`.
- Mock mode:
  - Do **not** decode tokens. Use fixture claims only.
  - Unknown fixture → unauthenticated/unauthorized.
- Strict mode (future):
  - Validate JWT signature with Entra JWKS, then reuse the same claim validation path.

## BFF inbound validation responsibilities
- Validate inbound delegated token before any routing.
- Enforce BFF audience `api://00000000-0000-0000-0000-000000000101` + required scopes `mcp.access` (any-of).
- Reject app-only tokens (roles-only) for user flows.
- `/whoami` + `/debug/claims` return **sanitized** claims only; debug claims gated by `ENABLE_DEBUG_CLAIMS`.
- Never forward the inbound token downstream; use OBO exchange for MCP calls.

## Agent gateway OBO boundary responsibilities
- Validate inbound token with gateway audience `api://00000000-0000-0000-0000-000000000102`.
- Require `mcp.access` (read) or `mcp.write` (write) before OBO.
- Perform mock OBO exchange to downstream audience `api://00000000-0000-0000-0000-000000000103`.
- Ensure outbound token/claims differ from inbound (no forwarding).

## MCP protected API audience/scope enforcement
- Validate audience `api://00000000-0000-0000-0000-000000000103`.
- Enforce per-endpoint scopes:
  - `mcp.access` for read-only endpoints.
  - `mcp.write` for write/tool endpoints.
- Reject app-only tokens for delegated endpoints.

## Safe claim handling + logging constraints
- Always use `sanitize_claims` allowlist; never log or return raw tokens.
- Never surface PII claims (`oid`, `sub`, `upn`, `email`, `name`, `preferred_username`).
- Log only correlation ID + sanitized claim metadata.

## Proposed test seams + fixtures
- Unit tests for `require_audience`, `require_scope`, and delegated-only checks.
- Fixture-driven auth tests using:
  - `delegated-user` → success when aud/scope match.
  - `wrong-audience` → 401.
  - `app-only` → 403.
- OBO boundary test: inbound fixture ≠ outbound mock OBO fixture (audience changes).
- Fixture selection precedence: header wins over env; unknown fixture → unauthenticated.

## Implementation task recommendations (Neo)
1. Add `AuthMode`, fixture loader, and validation helpers to `identity_lab_auth`.
2. Extend `AuthContext` to include `authorized` + `failure_reasons`.
3. Implement `require_audience`, `require_scope`, and delegated-only guard logic.
4. Add mock OBO exchange interface + mock implementation in shared auth module.
5. Wire BFF/agent-gateway/MCP auth middleware to use shared validators.
6. Add pytest coverage for mock auth + OBO boundary behavior.
