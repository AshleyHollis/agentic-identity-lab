# On-Behalf-Of (OBO) Flow

OBO lets an API exchange a **validated user token** for a downstream token while preserving user identity.

## High-Level Steps
1. Client gets a delegated access token for **API A**.
2. API A **validates** the token (issuer, audience, expiry, scopes).
3. API A exchanges the token for a **downstream token** to **API B**.
4. API A calls API B with the **OBO token** (not the original token).

## Implemented Validation Path (Mock → Strict)
**Mock/offline (current):**
- Claims come from fixtures (`X-Identity-Lab-Fixture` header wins over `AUTH_FIXTURE` env).
- Claim checks still enforce `aud`, `iss`, `tid`, `exp/nbf`, and `scp`.
- OBO exchange is mocked and mints a downstream token with the MCP audience.

**Strict (future):**
- Validate signature via Entra ID JWKS, then reuse the same claim checks.

## OBO Boundary Rules
- **Never forward** the inbound `Authorization` header to MCP.
- The gateway must **replace** outbound auth with an OBO/downstream token.
- APIM egress expects the OBO token in `x-obo-authorization` and sets `Authorization` from it.

## Why This Matters
- Preserves **user context** while respecting **audience boundaries**.
- Avoids token replay across services.

## Safety Requirements
- Validate `aud`, `iss`, `tid`, `exp`, and `scp` **before** exchange.
- Delegated-only endpoints must reject app-only tokens.
- Use a confidential client with a **Managed Identity** or Key Vault secret (future strict path).

## Placeholder Example (Identifiers Only)
```
Tenant ID: 00000000-0000-0000-0000-000000000001
API A App ID: 00000000-0000-0000-0000-000000000010
API B App ID: 00000000-0000-0000-0000-000000000020
```
