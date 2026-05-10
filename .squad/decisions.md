# Squad Decisions

## Active Decisions

### D001 — Agent Execution Service Naming (2026-05-15)

**Decision:** The AKS-hosted service that hosts and executes AI agents is canonically named **Agent Execution Service** with folder slug `agent-execution`.

**Context:** Service replaces PromptFlow/Azure ML flows with Python-first Agent Framework agents. Executes agents doing agentic work (LLM calls, tool calls, reasoning) on behalf of users with delegated identity (OBO tokens) preserved throughout.

**Rationale:**
- "Execution" describes primary responsibility (host + execute agents)
- Signals AKS deployment context ("Service")
- Maintains PromptFlow replacement narrative without co-opting PromptFlow vocabulary
- Zero collisions with Agent Framework (library), Azure AI Agent Service (managed product), Azure AI Foundry (platform), APIM, agentgateway.dev (proxy), or MCP

**Alternatives considered:** Agent Runtime, Agent Engine, Agent Host, Agent Workbench, Agent Factory, Agent Platform — all evaluated and rejected (see morpheus-naming-proposal-pre-m6-v2.md in decisions/inbox).

**Approval:** Ashley Hollis (2026-05-15)

**Related artifacts:**
- `.squad/orchestration-log/2026-05-15-m6-naming-approval-and-launch.md` — full event log
- `.squad/decisions/inbox/morpheus-naming-proposal-pre-m6-v2.md` — detailed analysis
- Forthcoming ADRs: `ADR-004-agent-execution-service-naming.md` (squad), `docs/adr/0009-agent-execution-service-naming.md` (public)

**Downstream impacts:**
- M6 Task 0: Filesystem rename `apps/agent-gateway/` → `apps/agent-execution/` + Docker Compose service rename
- All documentation terminology amendments (Morpheus T01)
- Spec 006 M6 references post-rename paths

---

## Governance

- All meaningful changes require team consensus
- Document architectural decisions here
- Keep history focused on work, decisions focused on direction
