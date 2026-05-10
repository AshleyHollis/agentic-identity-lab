# Current Focus

**Milestones 1–8 are complete and validated.**

- M1 (Spec 001 — token validation + OBO): ✅ Complete
- M2 (Spec 003 — local delegated flow integration): ✅ Complete
- M3 (Spec 004 — APIM policy alignment): ✅ Complete
- M4 (Spec 005 — local runtime ergonomics): ✅ Complete
- M5 (Spec 002 — AKS + Entra Agent ID + Observability): ✅ Complete
- M6 (Spec 006 — Azure deployment baseline): ✅ Complete and closed
- M7 (Spec 007 — variant client implementations): ✅ Complete and closed (T13 closeout)
- M8 (Spec 008 — live Azure E2E gate): ✅ Complete and closed (T15 closeout)

**Now: M9 is spec-ready; live execution remains blocked pending approval.**

- M8 delivered protected, opt-in live workflow scaffolds plus static/public-safe validation gates.
- M8 closeout made no live Azure deployment or smoke execution claims.
- M9 is tracked by Spec 009: `.squad\specs\009-live-azure-execution-and-evidence\`.
- M9 is the first milestone allowed to claim protected live Azure deployment and browser → APIM → BFF → Agent Execution Service → MCP verification after reviewer gates.
- No live Azure deployment, smoke run, workflow dispatch, `.env` read, or secret-value handling has occurred in this planning update.

**Immediate next focus:**
1. Tank confirms protected GitHub Environment readiness and deployment preflight without exposing live values.
2. Keep `LIVE_AZURE_TESTS` opt-in posture and validation-only public CI defaults.
3. Trinity reviews identity/security/evidence handling before any live execution claim.
4. Ashley approves the [CHECKPOINT] before protected live deploy/smoke workflows are dispatched.

See `.squad\project\roadmap.md` for milestone dashboard details and validation summaries.
