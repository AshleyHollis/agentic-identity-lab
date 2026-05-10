# Cross-Tenant Identity Guidance

## Trusted vs. Untrusted Tenants
Only tokens from explicitly **trusted tenant IDs** should be accepted.

## Validation Rules
- Validate `iss` and `tid` against an **allowlist**.
- Require the token to be issued by the expected Entra ID tenant.
- Apply **Conditional Access** and **issuer restrictions** where possible.

## Example Allowlist (Placeholders)
```
Allowed tenants:
- 00000000-0000-0000-0000-000000000001
- 00000000-0000-0000-0000-000000000002
```

## Safety Notes
- Do not accept tokens from “common” or “organizations” issuers without checks.
- Never bypass tenant checks for convenience.
