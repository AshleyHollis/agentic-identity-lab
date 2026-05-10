# Neo History

## Project Seed

- Project: agentic-identity-lab
- Primary user: Ashley Hollis
- Application focus: FastAPI BFF, agent gateway, MCP-style protected API, shared Python identity and diagnostics helpers.
- Public repo constraints: no secrets, tenant-specific IDs, subscription IDs, generated certificates, or tokens.

## Learnings
- Established FastAPI skeletons with safe claim sanitization and correlation ID helpers.
- Spec 001 requires AUTH_MODE (disabled/mock/strict), fixture-driven claims, and explicit OBO token replacement with audience/scope enforcement.
- Added mock auth settings/fixture loader with header precedence and auth mode test coverage in shared identity_lab_auth.
- Strict auth config defaults use public-safe placeholders (issuer/JWKS/tenant) and strict mode now raises when placeholders or missing values are detected in service settings.
- Implemented shared guard helpers (audience/scope/delegated-only) and AuthContext that sanitizes claims using the safe-claims allowlist from config.
- Added a mock OBO exchange helper that mints downstream claims from delegated AuthContext with audience/scope overrides while preserving safe-claims sanitization (plus security tests for delegated-only OBO).
- MCP protected API now enforces delegated-only access with audience and per-endpoint scope checks (mcp.access vs mcp.write), keeps debug claims gated, and has fixture-driven tests for success and rejection cases.
- Wired BFF auth to shared identity_lab_auth guards and AuthContext with delegated-only audience/scope enforcement, plus fixture-driven BFF auth tests for delegated success and rejection cases.
- Added Milestone 2 integration coverage proving BFF delegated auth through FastAPI and Agent Gateway mock OBO claims accepted by MCP authorization.
