# Token Claims Guidance

## Validation Modes (Implemented Path)
- **disabled**: no validation (local dev only).
- **mock**: offline fixture claims + claim validation (no JWKS). Fixtures are selected by `X-Identity-Lab-Fixture` (header wins) or `AUTH_FIXTURE` (env).
- **strict (future)**: Entra ID JWKS signature validation + the same claim checks as mock mode.

## Core Claims (Common)
- `aud`: Audience (who the token is for)
- `iss`: Issuer
- `tid`: Tenant ID
- `exp`, `nbf`, `iat`: Time bounds
- `azp` / `appid`: Authorized party / client app

## Delegated Token Indicators
- `scp`: Scopes granted to the user
- `oid`: User object ID (still PII; do not log)
- `sub`: Subject (unique per app + tenant)

## App-Only Token Indicators
- `roles`: App roles granted to the client

## Safe Claims Allowlist
Only allowlisted claims are retained in `AuthContext` and safe logs. The allowlist lives in
`config/claims/safe-claims-allowlist.json` and currently includes:
`aud`, `iss`, `tid`, `azp`, `appid`, `scp`, `roles`, `exp`, `nbf`, `iat`, `ver`.

**Never log or return** PII: `oid`, `sub`, `upn`, `email`, `name`, `preferred_username`, or custom user IDs.
Debug claim output is gated by `ENABLE_DEBUG_CLAIMS`.

## Safe Logging Rules
- **Never log raw tokens**.
- Log only **non-PII, non-unique** metadata (from the allowlist).
- Sanitization truncates long values and drops unknown keys.

## Validation Checklist
- Signature is valid (strict mode) and issuer is trusted.
- Audience matches the **current service**.
- Token is **not expired** and within `nbf`.
- Required scopes are present (`scp`), or reject app-only tokens (`roles` only).
