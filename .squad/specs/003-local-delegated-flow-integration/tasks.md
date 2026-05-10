# Tasks: Local Delegated Flow Integration

**Status:** Complete  
**Milestone:** M2  
**Spec Phase:** execution  
**Created:** 2026-05-10  
**Updated:** 2026-05-10  
**Impact:** High

## Overview
- **Total Tasks:** 5
- **Workflow:** TDD
- **Intent:** MID_SIZED

## Task table
| ID | Task | Owner Agent | Impact | Dependencies | Output Files | Validation | Status |
|----|------|-------------|--------|--------------|--------------|------------|--------|
| T-01 | Replace BFF fixture-only integration test with FastAPI `/whoami` delegated success coverage. | Neo | Medium | Spec 001 | `tests\integration\python\test_delegated_token_success_path.py` | `python -m pytest tests\integration\python\test_delegated_token_success_path.py` | Complete |
| T-02 | Add Agent Gateway → MCP OBO integration success coverage using real gateway auth and MCP tool authorization. | Neo | High | T-01 | `tests\integration\python\test_agent_gateway_obo_success_to_mcp.py` | `python -m pytest tests\integration\python\test_agent_gateway_obo_success_to_mcp.py` | Complete |
| T-03 | Add negative coverage proving MCP rejects a gateway-audience token without OBO. | Trinity | High | T-02 | `tests\integration\python\test_agent_gateway_obo_success_to_mcp.py` | `python -m pytest tests\integration\python\test_agent_gateway_obo_success_to_mcp.py` | Complete |
| T-04 | Update service READMEs to reflect enforced auth and OBO behavior. | Morpheus | Medium | T-01, T-02, T-03 | `apps\bff\python-fastapi\README.md`; `apps\agent-gateway\python-fastapi-agent-framework\README.md`; `apps\mcp-protected-api\python-fastapi\README.md` | File review | Complete |
| T-05 | Run full Python regression suite. | Trinity | High | T-01, T-02, T-03, T-04 | n/a | `python -m pytest` | Complete |

## Completion criteria
- [x] BFF success path exercises FastAPI auth dependency.
- [x] Agent Gateway OBO exchange is used for MCP-audience claims.
- [x] MCP rejects direct replay of gateway-audience claims.
- [x] Service docs match current auth behavior.
- [x] `python -m pytest` passes.

