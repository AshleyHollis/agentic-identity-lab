# Delegated vs. App-Only Tokens

## Delegated (User) Tokens
- Represent a **user + client app**.
- Authorization is driven by **scopes** (`scp` claim).
- Appropriate for interactive requests and MCP user-delegated access.
- Use when you need **user context** or user-specific data access.

## App-Only (Client Credentials) Tokens
- Represent a **service principal** only.
- Authorization is driven by **roles** (`roles` claim).
- Appropriate for background jobs and service-to-service calls with no user.
- **Not** a substitute for user-delegated flows.

## Summary Table
| Property | Delegated | App-Only |
| --- | --- | --- |
| Represents | User + App | App only |
| Claim to enforce | `scp` | `roles` |
| Typical flow | Auth code / OBO | Client credentials |
| Use for MCP user access | ✅ | ❌ |

## Safety Notes
- Never trust a `userId` header alone; require **validated tokens**.
- Never log raw tokens; log only safe, non-PII claim metadata.
