# Tasks: Token Validation and OBO Boundaries

## Recommended first implementation batch
- **Batch 1 (parallel-ready):** T-01 (mock/offline auth core), T-08 (APIM policy placeholders)
- **Batch 2 (after T-01):** T-02, T-03, T-04

## Task Table
| ID | Task | Owner Agent | Impact | Dependencies | Output Files | Validation |
| --- | --- | --- | --- | --- | --- | --- |
| T-01 | Implement mock/offline JWT validation core (auth mode + fixture loader with header-over-env precedence). | Neo | High | - | apps\shared\python\identity_lab_auth\__init__.py; apps\shared\python\identity_lab_auth\claims.py | `python -m pytest tests\security -k fixture` |
| T-02 | Add safe-claims allowlist, AuthContext, and guards for audience/scope/delegated-only enforcement. | Neo | High | T-01 | apps\shared\python\identity_lab_auth\guards.py; apps\shared\python\identity_lab_auth\token_type.py; apps\shared\python\identity_lab_auth\claims.py | `python -m pytest tests\security -k guards` |
| T-03 | Create mock OBO boundary abstraction that mints downstream MCP claims (no token forwarding). | Neo | High | T-02 | apps\shared\python\identity_lab_auth\obo.py; apps\shared\python\identity_lab_auth\__init__.py | `python -m pytest tests\security -k obo` |
| T-04 | Wire strict mode config plumbing (AuthMode strict + JWKS placeholders + service config toggles). | Neo | Medium | T-01 | apps\shared\python\identity_lab_auth\__init__.py; apps\bff\python-fastapi\app\config.py; apps\agent-gateway\python-fastapi-agent-framework\app\config.py; apps\mcp-protected-api\python-fastapi\app\config.py | `python -m pytest tests\security -k strict` |
| T-05 | BFF validation: enforce audience/scope, delegated-only, and safe claims with shared auth. | Neo | High | T-02, T-04 | apps\bff\python-fastapi\app\auth.py; apps\bff\python-fastapi\app\config.py | `python -m pytest tests\security -k bff` |
| T-06 | Agent gateway: validate delegated token and enforce OBO boundary (replace outbound Authorization). | Neo | High | T-02, T-03, T-04 | apps\agent-gateway\python-fastapi-agent-framework\app\auth.py; apps\agent-gateway\python-fastapi-agent-framework\app\config.py | `python -m pytest tests\security -k gateway` |
| T-07 | MCP protected API: enforce audience/scope per endpoint and reject app-only tokens. | Neo | High | T-02, T-04 | apps\mcp-protected-api\python-fastapi\app\auth.py; apps\mcp-protected-api\python-fastapi\app\config.py | `python -m pytest tests\security -k mcp` |
| T-08 | Update APIM policy/config placeholders for ingress/egress validation + OBO header mapping (no secrets). | Tank | High | - | infra\terraform\policies\apim\ingress-validate-user-token.xml; infra\terraform\policies\apim\egress-validate-obo-token.xml; infra\terraform\policies\apim\fragments\* | `terraform -chdir=infra\terraform fmt -check -recursive` |
| T-09 | Update env examples for auth mode, audiences, scopes, and fixtures (public-safe). | Tank | Medium | T-04 | config\env\bff.env.example; config\env\agent-gateway.env.example; config\env\mcp-protected-api.env.example | `docker compose -f docker\docker-compose.yml config --quiet` |
| T-10 | Add fixture-driven tests for delegated success, wrong audience, missing scope, app-only rejection, and OBO boundary. | Trinity | High | T-01, T-02, T-03, T-05, T-06, T-07 | tests\security\*; tests\fixtures\sample-claims\* | `python -m pytest tests\security` |
| T-11 | Update identity + APIM docs with validated audiences/scopes, safe-claims rules, and OBO boundary notes. | Morpheus | Medium | T-05, T-06, T-07, T-08 | docs\identity\obo-flow.md; docs\identity\token-audience.md; docs\identity\token-claims.md; docs\apim\ingress-policy.md; docs\apim\egress-policy.md; docs\apim\managed-identity-token-replacement-warning.md | n/a (docs only) |
| T-12 | Final integration review + sequencing gate (ensure tests green, safe-claims only, no token forwarding). | Morpheus | High | T-08, T-09, T-10, T-11 | n/a (review gate) | `python -m pytest && terraform -chdir=infra\terraform fmt -check -recursive` |
