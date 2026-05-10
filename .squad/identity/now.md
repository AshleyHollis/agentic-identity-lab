# Current Focus

**Milestones 1–6 are complete and validated.**

- M1 (Spec 001 — token validation + OBO): Complete
- M2 (Spec 003 — local delegated flow integration): Complete
- M3 (Spec 004 — APIM policy alignment): Complete
- M4 (Spec 005 — local runtime ergonomics): Complete
- M5 (Spec 002 — AKS + Entra Agent ID + Observability): Complete
- M6 (Spec 006 — Azure deployment baseline): ✅ Complete and closed (2026-06-01)

**Now: Milestone 7 — Variant client implementations (spec creation phase)**  
Goal: Create `.squad/specs/007-variant-client-implementations/` spec artifacts (goals, requirements, design, tasks) before any implementation begins. Owner agents: Mouse, Neo.

**M6 final closeout summary:**
- T00–T13 all complete. Morpheus post-implementation review ACCEPTED. Trinity post-implementation security review ACCEPTED (commit 7ada3e0).
- Final validation (Tank, 2026-06-01): 235/235 pytest pass; `terraform fmt -check -recursive` PASS; `terraform init/validate` single-tenant-aca PASS; docker compose strict-aca + tracing configs PASS; no-secret scan PASS.
- Spec 006 state.json → phase: closed, status: complete. roadmap.md M6 → ✅ Complete. Current position → M7 spec creation.

**Terminology (resolved — ADR 0008):**
- **Agent Execution Service** = lab's app-level agent execution service (`apps/agent-execution/`) — code-first successor to PromptFlow-style Azure ML flows.
- **AKS Agent Gateway** = agentgateway.dev infrastructure proxy sidecar in AKS
- **Historical note:** "Agentic Layer" was the M5-era term (ADR 0006); superseded by ADR 0008 pre-M6. `apps/agent-gateway/` renamed to `apps/agent-execution/` in M6 T00.

Owner agents (M7): Mouse (UI/clients), Neo (backend integration)  
Spec: `.squad\specs\007-variant-client-implementations\` — not yet created.

**Next actions (in priority order):**

1. **Spec 007 creation** — Mouse or Neo: Create spec directory and all required artifacts (README, goals, requirements, design, tasks, state.json, .progress.md) for M7 variant client implementations before any code work begins.
2. **M7 T11 (Morpheus architecture review)** — after spec artifacts are complete.
3. **M7 T12 (Trinity security review)** — after T11.
4. **M7 implementation** — after all review gates satisfied.

**Architecture decisions recorded (M6):**
- `.squad\architecture\decisions\005-aca-default-deployment-path.md` — ACCEPTED (ACA as M6 default)
- `.squad\architecture\decisions\005-m6-managed-identity-assignment-strategy.md` — ACCEPTED (user-assigned MI per service)
- `.squad\architecture\decisions\006-azure-monitor-otlp-endpoint.md` — ACCEPTED (OTLP endpoint swap)

See `.squad\specs\006-azure-deployment-baseline\tasks.md` for the full M6 task list.  
See `.squad\project\roadmap.md` for the full milestone status dashboard with per-milestone outcomes.
