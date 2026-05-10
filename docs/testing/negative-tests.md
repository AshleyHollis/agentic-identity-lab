# Negative Test Cases

## Must Reject
- App-only token presented where delegated is required.
- Token with wrong `aud`.
- Token missing required `scp`.
- Token from untrusted tenant.

## Expected Outcomes
- 401 for missing/invalid token
- 403 for valid token lacking required scope/role
