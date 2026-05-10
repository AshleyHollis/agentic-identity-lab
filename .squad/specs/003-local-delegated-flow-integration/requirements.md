# Requirements: Local Delegated Flow Integration

**Status:** Complete  
**Milestone:** M2  
**Spec Phase:** requirements  
**Created:** 2026-05-10  
**Updated:** 2026-05-10  
**Impact:** High

## User stories

### US-1: Trackable local delegated success path
**As a** lab maintainer  
**I want to** run an integration test that exercises BFF delegated auth through FastAPI  
**So that** Milestone 2 has a concrete proof beyond fixture inspection.

**Acceptance Criteria:**
- [x] AC-1.1: `/whoami` returns authenticated delegated context for `delegated-user`.
- [x] AC-1.2: Returned claims are sanitized and omit unsafe user identifiers.

### US-2: OBO boundary reaches MCP authorization
**As a** security reviewer  
**I want to** prove Agent Gateway OBO claims are accepted by MCP authorization  
**So that** downstream MCP calls use the MCP audience instead of replaying the inbound token.

**Acceptance Criteria:**
- [x] AC-2.1: Agent Gateway produces OBO claims with the MCP audience.
- [x] AC-2.2: MCP `/tools/authorization-check` accepts the OBO context.
- [x] AC-2.3: The OBO authorization value is not the inbound token.

### US-3: Direct token replay is rejected
**As a** security reviewer  
**I want to** prove MCP rejects a gateway-audience token without OBO  
**So that** audience boundaries are enforced across services.

**Acceptance Criteria:**
- [x] AC-3.1: MCP rejects `delegated-gateway` claims with HTTP 401.
- [x] AC-3.2: The rejection reason is `invalid_audience`.

## Functional requirements
| ID | Requirement | Priority | Verify |
|----|-------------|----------|--------|
| FR-1 | Integration tests must load real FastAPI app/auth modules for BFF and MCP. | Must | `python -m pytest tests\integration\python` |
| FR-2 | Agent Gateway integration coverage must call `resolve_auth_context()` and `exchange_for_mcp()`. | Must | `python -m pytest tests\integration\python\test_agent_gateway_obo_success_to_mcp.py` |
| FR-3 | MCP authorization must be checked through `/tools/authorization-check`. | Must | `python -m pytest tests\integration\python\test_agent_gateway_obo_success_to_mcp.py` |
| FR-4 | README files must no longer claim auth is not enforced for services where Spec 001 enforces auth. | Should | File review |

## Non-functional requirements
| ID | Requirement | Metric | Target |
|----|-------------|--------|--------|
| NFR-1 | Offline-safe validation | Network calls | 0 |
| NFR-2 | Public-safe outputs | Raw tokens/secrets | 0 committed |
| NFR-3 | Regression safety | Test command | `python -m pytest` passes |

## Out of scope
- Real HTTP calls between running containers.
- Real OBO tokens.
- Client UI flow from SharePoint/SPFx.
- APIM policy execution.

## Dependencies
- Spec 001 shared auth and mock OBO helpers.
- Fixture claims in `tests/fixtures/sample-claims`.

## Success criteria
- `python -m pytest` passes.
- Milestone 2 has a traceable spec directory and task state.
- Integration tests demonstrate both success and replay rejection.

