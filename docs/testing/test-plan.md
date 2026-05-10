# Identity Test Plan

## Coverage
- Delegated token acceptance (happy path)
- App-only token rejection
- Wrong audience rejection
- Missing scope rejection
- Cross-tenant allow/deny
- APIM ingress/egress token handling

## Offline First
- Use **fixture claims** in `tests/fixtures/sample-claims/`.
- Live Azure tests are **opt-in** via environment flags.

## Safety
- Never include raw tokens or secrets in tests or logs.
