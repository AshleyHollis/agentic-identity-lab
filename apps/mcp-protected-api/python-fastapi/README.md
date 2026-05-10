# MCP Protected API (FastAPI)

MCP-style protected API that enforces local/mock delegated-token auth, audience checks, and per-tool scopes.

## Endpoints
- GET `/healthz`
- GET `/readyz`
- GET `/whoami`
- GET `/debug/claims`
- POST `/tools/echo`
- POST `/tools/authorization-check`

Tool endpoints require delegated claims with the MCP audience. A token minted for BFF or agent-gateway is rejected unless it has passed through the mock OBO boundary.

## Run locally (Windows)
1. Copy `config/env/mcp-protected-api.env.example` to `config/env/mcp-protected-api.env` and update as needed.
2. From `apps/mcp-protected-api/python-fastapi`:
   - `set PYTHONPATH=..\..\shared\python`
   - `python -m pip install fastapi uvicorn[standard]`
   - `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`
