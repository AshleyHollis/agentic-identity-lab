# Agent Execution Service (FastAPI)

Agent Execution Service that enforces delegated-token auth, performs OBO claim exchange for MCP audience, and can execute a live MCP authorization check hop.

## Endpoints
- GET `/healthz`
- GET `/readyz`
- GET `/whoami`
- GET `/debug/claims`
- POST `/agent/invoke`
- POST `/agent/invoke-modern`
- POST `/agent/invoke-low-change`

Invoke endpoints validate the inbound service audience and mint downstream OBO claims for the MCP audience. They must not forward the inbound `Authorization` value to MCP.

When `MCP_CHAIN_ENABLED=true`, invoke endpoints call MCP `POST /tools/authorization-check` using the exchanged OBO authorization header to exercise the delegated chain.

### Downstream chain settings

- `MCP_CHAIN_ENABLED` (default: `false`)
- `MCP_PROTECTED_API_BASE_URL` (required when chain is enabled)
- `MCP_AUTHORIZATION_CHECK_PATH` (default: `/tools/authorization-check`)
- `DOWNSTREAM_TIMEOUT_SECONDS` (default: `10`)
- Strict mode with `MCP_CHAIN_ENABLED=true` also requires protected Entra OBO settings:
  `OBO_TOKEN_URL`, `OBO_CLIENT_ID`, `OBO_CLIENT_SECRET`, and `OBO_REQUIRED_SCOPES`.
  Agent Execution exchanges the inbound Agent-audience token and sends only the MCP-audience
  token to MCP.

## Run locally (Windows)
1. Copy `config/env/agent-execution.env.example` to `config/env/agent-execution.env` and update as needed.
2. From `apps/agent-execution/python-fastapi-agent-framework`:
   - `set PYTHONPATH=..\..\shared\python`
   - `python -m pip install fastapi uvicorn[standard]`
   - `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`
