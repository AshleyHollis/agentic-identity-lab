# Current Focus

**Milestones 1–4 are complete and validated.**

- M1 (Spec 001 — token validation + OBO): Complete
- M2 (Spec 003 — local delegated flow integration): Complete
- M3 (Spec 004 — APIM policy alignment): Complete
- M4 (Spec 005 — local runtime ergonomics): Complete

**Now: Milestone 5 — AKS + Entra Agent ID + Observability**  
Goal: Spec 002 promoted to tasks-ready. Amendment 001 (terminology + tracing) applied and
architecture-reviewed by Morpheus. Implementation is blocked pending Trinity security review (T03).

**Terminology (resolved — ADR 0006):**
- **Agentic Layer** = lab's app-level orchestration service (`apps/agent-gateway/`)
- **AKS Agent Gateway** = agentgateway.dev infrastructure proxy sidecar in AKS

Owner agents: Morpheus, Tank, Trinity, Neo  
Spec: `.squad\specs\002-aks-entra-agent-id\` — all spec artifacts complete + Amendment 001 applied.

**Next actions (in priority order):**

1. **T03 — Trinity:** Security review + ADR-M5-03 (JWKS caching strategy) — **now unblocked**.
2. **T17 — Morpheus:** *(waiting on T03)* Tracing design review.
3. **T04–T13** — Tank, Trinity, Neo implementation streams unblock after T02 ✅ + T03.
4. **T18–T20** — Tracing implementation stream unblocks after T17.

**Architecture decisions recorded (this session):**
- `.squad\architecture\decisions\001-agentic-layer-vs-agent-gateway-terminology.md` — Accepted
- `.squad\architecture\decisions\002-end-to-end-tracing-strategy.md` — Accepted
- `docs\adr\0006-agentic-layer-vs-agent-gateway-terminology.md` — Accepted
- `docs\adr\0007-end-to-end-tracing-strategy.md` — Accepted

See `.squad\specs\002-aks-entra-agent-id\tasks.md` for the full task list and dependency graph.  
See `.squad\project\roadmap.md` for the full milestone status dashboard with per-milestone outcomes.
