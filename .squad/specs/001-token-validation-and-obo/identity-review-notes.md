# Identity & Security Review Notes — Token Validation + OBO

## Public-safe constraints (must-haves)
- Never log, persist, or return raw access tokens. Use safe-claims allowlist only.
- Use placeholder GUIDs in examples/configs (public repo policy).
- Enforce delegated user tokens for MCP user flows; reject app-only tokens.
- Validate `iss`, `aud`, `exp`, `nbf`, `tid`, and required `scp` before any OBO.
- Enforce trusted tenant allowlist; reject `common/organizations` issuers without checks.
- Never authorize using `userId` headers alone.
- OBO must exchange to downstream audience; never forward original user token.

## Claims handling
**May be used internally (and safe to return when sanitized):**
- `aud`, `iss`, `tid`, `azp`, `appid`, `scp`, `roles`, `exp`, `nbf`, `iat`, `ver`

**Must not be returned to clients or logged (PII/unique):**
- `oid`, `sub`, `upn`, `email`, `name`, `preferred_username`, any custom userId headers

## Audience & scope requirements (placeholder IDs)
| Boundary | Required `aud` | Required scope(s) | Notes |
| --- | --- | --- | --- |
| APIM/BFF ingress | `api://00000000-0000-0000-0000-000000000101` | `mcp.access` | Delegated token only. |
| Agent gateway | `api://00000000-0000-0000-0000-000000000102` | `mcp.access` (read) / `mcp.write` (write) | Validate before OBO. |
| MCP protected API | `api://00000000-0000-0000-0000-000000000103` | `mcp.write` for tool writes; `mcp.access` for read-only | Enforce per-endpoint scopes. |

## OBO boundary rules
- OBO token must be minted **after** inbound validation completes.
- Preserve user context (`sub`/`oid`) across OBO; only `aud` changes.
- Use confidential client (Managed Identity or Key Vault secret).
- APIM egress must forward OBO token, not the original user token.

## Offline/mock test strategy (before live Entra)
- Default to offline tests using `tests/fixtures/sample-claims/*` with placeholder GUIDs.
- Verify negative cases: wrong audience, missing scope, app-only token, untrusted tenant.
- Use an environment flag to enable live Entra tests (disabled by default).
- Validate APIM policy behavior with fixture claims; never paste real tokens.

## Azure OpenAI / Foundry separation
Azure OpenAI / Foundry authentication remains **service-to-service** (Managed Identity) and must stay **separate** from MCP user-delegated token paths.

## Risks to call out
- APIM managed-identity token replacement breaks delegation and strips user context.
- Accepting multi-audience or shared-audience tokens enables replay across services.
- Logging PII claims or tokens violates public repo policy.
- Skipping tenant allowlists enables cross-tenant token injection.

## Security review acceptance criteria
- Ingress validates signature, issuer, audience, tenant, expiry, and required scopes.
- App-only tokens are rejected for user-delegated endpoints.
- OBO tokens are used for downstream calls; original user tokens never forwarded.
- Only safe-claims allowlist is returned/logged; PII claims excluded.
- Trusted-tenant allowlist enforced; untrusted tenant rejected.
- Azure OpenAI/Foundry auth remains on Managed Identity path (no user token reuse).
