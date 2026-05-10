# Goals

## Primary Goals
- Deliver a working offline delegated-token validation story across BFF/agent-gateway/MCP.
- Enforce per-service audience boundaries and required scopes.
- Make the OBO boundary explicit (no token forwarding).
- Keep all outputs public-safe and non-PII.

## Secondary Goals
- Preserve current placeholder endpoints and add minimal auth context signals for tests.
- Align env templates with required audiences/scopes.

## Non-Goals
- Live Azure/Entra ID configuration.
- Production-grade auth middleware or caching.
- App-only token support for delegated endpoints (future consideration).
