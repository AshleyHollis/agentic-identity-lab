# Design Notes — Trinity (Identity & Security)
Feature 001: Token Validation and OBO Boundaries

## Required token validation checks + failure behavior
- Validate bearer token presence (strict/mock), and in strict mode validate signature via trusted issuer/JWKS.
- Enforce `iss` + `tid` against a trusted-tenant allowlist; reject `common`/`organizations` issuers.
- Enforce `aud` against per-service allowlists.
- Enforce time bounds (`exp`, `nbf`, optionally `iat` sanity).
- Enforce delegated token shape: `scp` required for user flows; reject app-only (`roles`-only) tokens.
- Failure behavior: **401** for missing/invalid token, invalid issuer/tenant/audience, or expired/not-yet-valid. **403** for missing scopes or app-only tokens on delegated endpoints. Log only sanitized claims + reason codes; never log raw tokens.

## Delegated vs app-only rejection rules
- For BFF, agent-gateway, and MCP protected API in this feature, accept **delegated tokens only** (`scp` present).
- Reject tokens with only `roles`. If both `scp` and `roles` exist, treat as delegated and ignore `roles`.

## Audience/scope matrix (placeholder IDs)
| Boundary | Required `aud` | Required scopes (any-of) | Notes |
| --- | --- | --- | --- |
| BFF/APIM ingress | `api://00000000-0000-0000-0000-000000000101` | `mcp.access` | Delegated only. |
| Agent gateway | `api://00000000-0000-0000-0000-000000000102` | `mcp.access` (read), `mcp.write` (write) | Validate before OBO. |
| MCP protected API | `api://00000000-0000-0000-0000-000000000103` | `mcp.access` (read), `mcp.write` (tool writes) | Enforce per-endpoint scope. |

## OBO exchange boundaries (never forward)
- Validate inbound token **before** any OBO exchange.
- Mint a downstream token **only** for the MCP audience; replace `Authorization` for downstream calls.
- Never forward the original user token, `Authorization` header, or `userId`/PII headers.
- Preserve user context across OBO (user identity is carried by the OBO token, not headers).
- APIM must not use managed-identity inbound token replacement for delegated flows.
- Keep Azure OpenAI/Foundry auth **service-to-service** (Managed Identity) and separate from delegated MCP flows.

## Safe claims & PII rules
- Safe allowlist only: `aud`, `iss`, `tid`, `azp`, `appid`, `scp`, `roles`, `exp`, `nbf`, `iat`, `ver`.
- Never return/log PII or unique user identifiers: `oid`, `sub`, `upn`, `email`, `name`, `preferred_username`, or custom userId headers.
- Debug claims remain gated by `ENABLE_DEBUG_CLAIMS` and must be sanitized.

## Offline/mock-first security test plan + live Entra gates
**Offline (default):**
- Use fixture claims via `X-Identity-Lab-Fixture` or `AUTH_FIXTURE`.
- Test cases: delegated success, wrong audience → 401, missing scope → 403, app-only → 403, untrusted tenant → 401, OBO boundary (downstream token differs from inbound).
- APIM policy tests use fixtures only; never paste real tokens.

**Live Entra follow-up (gated):**
- Controlled by explicit env flag; disabled by default and excluded from CI.
- Requires validated issuer/JWKS, trusted-tenant allowlist, and confidential client configuration.
- OBO integration tests must confirm downstream audience + delegated identity preservation.

## Security review acceptance criteria
- Ingress validates signature (strict), issuer, tenant, audience, expiry/nbf, and required scopes.
- Delegated-only endpoints reject app-only tokens.
- OBO tokens are used for downstream calls; original user tokens never forwarded.
- Safe-claims allowlist only; PII and raw tokens never logged or returned.
- Trusted-tenant allowlist enforced; no `common/organizations` bypass.
- Azure OpenAI/Foundry auth remains on Managed Identity path (no user token reuse).
