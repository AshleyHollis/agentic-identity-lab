# Agent Gateway (FastAPI)

Agent gateway service that enforces delegated-token auth and performs a local/mock OBO exchange for downstream MCP calls.

## Endpoints
- GET `/healthz`
- GET `/readyz`
- GET `/whoami`
- GET `/debug/claims`
- POST `/agent/invoke`
- POST `/agent/invoke-modern`
- POST `/agent/invoke-low-change`

Invoke endpoints validate the inbound gateway audience and mint mock downstream claims for the MCP audience. They must not forward the inbound `Authorization` value to MCP.

## Run locally (Windows)
1. Copy `config/env/agent-gateway.env.example` to `config/env/agent-gateway.env` and update as needed.
2. From `apps/agent-gateway/python-fastapi-agent-framework`:
   - `set PYTHONPATH=..\..\shared\python`
   - `python -m pip install fastapi uvicorn[standard]`
   - `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`
