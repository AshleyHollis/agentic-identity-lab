# Research: Token Validation and OBO Boundaries

## Executive Summary
Existing identity documentation defines audience boundaries and OBO safety rules. The shared Python auth module already provides safe-claim sanitization and placeholder guard hooks, and the tests include offline fixture claims. This feature can build on those assets without introducing live secrets.

## External Research
None. This spec relies on internal docs to stay public-safe.

## Codebase Analysis

### Existing Patterns
- Safe claim filtering in `apps/shared/python/identity_lab_auth/claims.py`
- Placeholder audience/scope guards in `apps/shared/python/identity_lab_auth/guards.py`
- Auth context in `apps/*/python-fastapi*/app/auth.py`
- Fixture claims in `tests/fixtures/sample-claims/*.json`
- Identity guidance in `docs/identity/*.md` and APIM guidance in `docs/apim/*.md`

### Dependencies
- FastAPI apps (`apps/*/python-fastapi*/app`)
- `identity_lab_auth` and `identity_lab_diagnostics` shared modules

### Constraints
- No real tenant IDs, secrets, or live tokens.
- Offline-safe tests only (`tests/README.md`).

## Quality Commands

| Type | Command | Source |
|------|---------|--------|
| Test | `python -m pytest` | tests/README.md |

**Local CI**: `python -m pytest`

## Verification Tooling

| Tool | Command/Value | Detected From |
|------|--------------|---------------|
| Dev Server | `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000` | apps/*/README.md |
| Port | `8000` | config/env/*.env.example |
| Health Endpoint | `/healthz` | apps/*/app/main.py |

**Project Type**: API services  
**Verification Strategy**: Run pytest (contract/integration) with fixture claims; optional curl checks against local FastAPI if needed.

## Related Specs
None yet.

## Feasibility Assessment

| Aspect | Assessment | Notes |
|--------|-----------|-------|
| Technical Viability | High | Shared auth helpers and fixtures already exist. |
| Effort Estimate | M | Requires auth middleware updates + tests. |
| Risk Level | Medium | Must avoid token forwarding and avoid secret leakage. |

## Recommendations for Requirements
1. Add a mock auth mode that loads fixture claims by name.
2. Implement audience + scope checks in shared guards and reuse everywhere.
3. Enforce OBO boundary with a mock exchange interface.

## Open Questions
- How should fixture selection be signaled (header vs env)?
- Should required scopes be any-of or all-of?
- Should app-only tokens ever be accepted by MCP endpoints?
