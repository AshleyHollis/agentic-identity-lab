# Spec 003: Local Delegated Flow Integration

**Status:** Complete  
**Milestone:** M2  
**Spec Phase:** execution  
**Created:** 2026-05-10  
**Updated:** 2026-05-10  
**Impact:** High

## Summary
Prove the local delegated-token request flow from BFF/agent-gateway into the MCP protected API using the mock OBO exchange created in Spec 001. This spec closes the gap between unit/security validation and an integration-level proof that downstream MCP authorization uses OBO claims rather than the inbound gateway token.

## Scope (In)
- In-process FastAPI integration tests for BFF delegated auth.
- Agent Gateway mock OBO exchange integration into MCP authorization checks.
- Negative coverage proving MCP rejects an inbound gateway-audience token without OBO.
- Service README updates so documentation reflects enforced auth behavior.

## Scope (Out)
- Live Entra ID, JWKS, or real token acquisition.
- Networked service-to-service HTTP calls between containers.
- Full BFF-to-AgentGateway orchestration endpoint.
- Azure deployment or APIM runtime validation.

## Related specs
- Spec 001: `.squad/specs/001-token-validation-and-obo/`
- Spec 002: `.squad/specs/002-aks-entra-agent-id/`

## Validation
`python -m pytest`

