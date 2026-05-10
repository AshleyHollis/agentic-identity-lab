# Design: Local Delegated Flow Integration

**Status:** Complete  
**Milestone:** M2  
**Spec Phase:** design  
**Created:** 2026-05-10  
**Updated:** 2026-05-10  
**Impact:** High

## Architecture
The milestone stays in local/mock mode and verifies the service boundary with in-process FastAPI tests:

1. BFF receives fixture-selected delegated claims and returns sanitized auth context from `/whoami`.
2. Agent Gateway validates gateway-audience claims with `resolve_auth_context()`.
3. Agent Gateway calls `exchange_for_mcp()` to mint downstream MCP-audience claims.
4. MCP receives the OBO claims through a dependency override that simulates the downstream authenticated context.
5. MCP `/tools/authorization-check` validates scopes and audience using existing Spec 001 guards.

## Why in-process instead of networked containers
Milestone 2 is about delegated-flow correctness, not runtime orchestration. In-process FastAPI tests provide deterministic coverage of the auth boundaries without adding Docker networking, HTTP client behavior, or service discovery concerns. Those belong to Milestone 4.

## Security design
- Keep fixture selection via `X-Identity-Lab-Fixture`.
- Preserve safe-claims sanitization.
- Assert unsafe user identifiers are absent from responses.
- Assert MCP rejects gateway-audience claims without OBO.
- Assert OBO authorization is not the inbound token.

## Files
- `tests/integration/python/test_delegated_token_success_path.py`
- `tests/integration/python/test_agent_gateway_obo_success_to_mcp.py`
- `apps/bff/python-fastapi/README.md`
- `apps/agent-gateway/python-fastapi-agent-framework/README.md`
- `apps/mcp-protected-api/python-fastapi/README.md`

## Validation
Run `python -m pytest`.

