# Trinity History

## Project Seed

- Project: agentic-identity-lab
- Primary user: Ashley Hollis
- Identity focus: delegated user tokens, scopes, audiences, app-only role tokens, OBO, APIM validation/forwarding, and cross-tenant trust.
- Public repo constraints: no secrets, tenant-specific IDs, subscription IDs, generated certificates, or tokens.

## Learnings

- Seeded identity/APIM/testing docs and pytest placeholders with fixture-only claims and placeholder GUIDs to keep guidance public-safe.
- Added token-validation/OBO review notes emphasizing audience/scope enforcement, trusted-tenant allowlists, safe-claim handling, and OpenAI/Foundry separation.
- Documented Spec 001 security design notes covering validation checks, delegated-only rules, audience matrix, OBO boundaries, safe-claim handling, and offline/live test gates.
- Expanded fixture-driven security tests to assert safe-claims allowlists across BFF, agent gateway, MCP, and mock OBO exchange outputs.
- Added Spec 002 identity notes for AKS + Entra Agent ID, highlighting sidecar usage, workload identity federation, agent OBO boundaries, and public-safe constraints.
- Added Milestone 2 negative integration coverage proving MCP rejects a gateway-audience token replay without OBO, preserving audience-boundary enforcement.
- Replaced APIM fixture-only tests with policy XML/doc checks for ingress validation, OBO egress forwarding, and managed identity anti-pattern warnings.
