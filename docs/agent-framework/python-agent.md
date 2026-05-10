# Agentic Layer — Python (FastAPI)

> **Path:** `apps/agent-gateway/python-fastapi-agent-framework/`  
> **Terminology:** This service is the lab's **Agentic Layer** — the application-level agent
> orchestration component. The directory is named `agent-gateway` for historical reasons (see ADR 0006).

The Python Agentic Layer is a FastAPI service that exposes `/agent/invoke` variants for placeholder
routing. The service uses shared Python helpers for correlation IDs and safe claim sanitization,
keeping responses token-free.

JWT validation is not enabled yet, but the auth context and guard hooks are structured to accept
verification logic next.
