# Goals: Local Delegated Flow Integration

**Status:** Complete  
**Milestone:** M2  
**Spec Phase:** discovery  
**Created:** 2026-05-10  
**Updated:** 2026-05-10  
**Impact:** High

## Problem
Spec 001 established local/mock token validation and an OBO boundary, but Milestone 2 needs a traceable integration proof that the services use those boundaries together. The previous integration tests were mostly fixture assertions, which made progress hard to track and did not prove FastAPI auth dependencies or MCP authorization behavior.

## Primary goals
- Prove BFF accepts valid delegated mock claims through its FastAPI `/whoami` path.
- Prove Agent Gateway can exchange validated delegated claims for MCP-audience OBO claims.
- Prove MCP accepts the downstream OBO claims for tool authorization.
- Prove MCP rejects the original gateway-audience token if it is forwarded directly.
- Keep all tests offline-safe and public-safe.

## Constraints
- No real tenant IDs, subscription IDs, secrets, raw tokens, or live Entra calls.
- Keep Spec 001 semantics unchanged.
- Reuse existing fixture claims and shared auth helpers.
- Keep Windows-friendly commands and paths.

## Non-goals
- Production-grade token forwarding, HTTP clients, retries, or service discovery.
- Live APIM or AKS validation.
- UI client implementation.

## Success criteria
- Integration tests exercise FastAPI app/auth modules rather than only inspecting JSON fixtures.
- OBO output has MCP audience and expected scopes.
- Sanitized claims remain safe; `sub` and `oid` are not returned.
- `python -m pytest` passes.

