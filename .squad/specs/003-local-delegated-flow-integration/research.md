# Research: Local Delegated Flow Integration

**Status:** Complete  
**Milestone:** M2  
**Spec Phase:** research  
**Created:** 2026-05-10  
**Updated:** 2026-05-10  
**Impact:** High

## Codebase findings
- Spec 001 already provides shared auth helpers in `apps/shared/python/identity_lab_auth`.
- BFF, Agent Gateway, and MCP expose FastAPI apps with dependency-based auth paths.
- Existing security tests validate individual service auth behavior.
- Existing integration tests under `tests/integration/python` included several fixture-only assertions that did not prove service integration behavior.

## Patterns to follow
- Use `fastapi.testclient.TestClient` for in-process endpoint checks.
- Use synthetic package names (`bff_app`, `gateway_app`, `mcp_app`) to avoid module collisions between apps named `app`.
- Use `X-Identity-Lab-Fixture` for mock fixture selection.
- Override MCP `get_auth_context` only when simulating an OBO output that is already minted by Agent Gateway.

## Quality commands
| Type | Command | Source |
|------|---------|--------|
| Python tests | `python -m pytest` | `tests/README.md` |

## Risks
- Import collisions between multiple FastAPI apps named `app`.
- Accidentally testing raw fixture mutation rather than real service auth paths.
- Leaking unsafe claims in test assertions or service responses.

## Decisions
- Use in-process FastAPI tests for this milestone rather than container networking.
- Keep mocked OBO exchange explicit and local; do not introduce HTTP clients yet.
- Treat networked Docker Compose flow as Milestone 4 runtime ergonomics, not Milestone 2.

