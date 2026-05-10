# Agent Execution Service — Python (FastAPI)

> **Path:** `apps/agent-gateway/python-fastapi-agent-framework/`  
> **Terminology:** This service is the lab's **Agent Execution Service** — the application-level agent
> execution component. The directory is named `agent-gateway` for historical reasons (see ADR 0008).
> Display name: **Identity Lab Agent Execution Service** when org/lab context is useful.

The Python Agent Execution Service is a FastAPI service that exposes `/agent/invoke` variants for
placeholder routing. The service uses shared Python helpers for correlation IDs and safe claim
sanitization, keeping responses token-free.

JWT validation is not enabled yet, but the auth context and guard hooks are structured to accept
verification logic next.
