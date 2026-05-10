# Amendment 001: Agentic layer, gateway terminology, tracing, and roadmap clarity

**Requested by:** Ashley Hollis  
**Captured by:** Squad Coordinator  
**Processed by:** spec-feature agent  
**Processed date:** 2026-05-15  
**Status:** ✅ Applied — pending Morpheus + Trinity review approval  
**Impact:** High — affects architecture terminology, M5 scope, roadmap deliverables, and observability requirements across mock and future deployed flows.

## Gap

The current roadmap and M5 Spec 002 can create confusion between:

1. The lab's application-level agentic layer / orchestration runtime.
2. The existing local `apps\agent-gateway\python-fastapi-agent-framework` service name.
3. The standalone Agent Gateway project used in AKS, which is not the lab's agentic layer.

The roadmap also does not clearly state what functions/features work at the end of each milestone, making progress hard to evaluate.

The lab needs end-to-end tracing across all mock and future deployed flows so users can visualize request movement through browser/client, BFF, agentic layer, gateway/proxy boundaries, APIM, OBO exchange, and MCP protected APIs.

## Requested changes

- Clarify terminology across roadmap and M5 spec artifacts so "agentic layer" and "standalone Agent Gateway" are separate concepts.
- Make roadmap milestone outcomes more detailed, including explicit functions/features that work at the end of each milestone.
- Add end-to-end tracing as a tracked cross-cutting requirement, including mock flows.
- Review Agent Gateway trace reference: https://agentgateway.dev/docs/standalone/main/reference/observability/traces/

## Expected downstream updates

- Update Spec 002 requirements/design/tasks before M5 review gates proceed.
- Update roadmap dashboard and milestone sections with clearer deliverables.
- Create or identify ADR(s) for naming/terminology and observability/tracing strategy if required.
- Keep implementation blocked until the amended spec/roadmap are reviewed.

## What was applied (2026-05-15)

| Artifact | Change |
|----------|--------|
| `README.md` | Terminology section added; artifact table updated to "amended" |
| `goals.md` | Success Criterion 10 (E2E tracing design) added |
| `research.md` | Section 8 added: terminology disambiguation, standalone Agent Gateway tracing (OTEL/Jaeger reference), E2E trace flow diagrams |
| `requirements.md` | FR-11 (terminology), FR-12 (E2E tracing), NFR-07 (tracing observability) added |
| `design.md` | Terminology Definitions section added at top; AKS manifest layout wording updated; E2E Tracing Design section added (span model, Compose overlay spec, static/dynamic config, visualization goal) |
| `tasks.md` | T17–T20 added (tracing stream); dependency diagram updated; T14/T15 depends-on updated; M5 gate criteria updated |
| `state.json` | T17–T20 added as blocked; amendment record added; validation commands updated |
| `.progress.md` | T17–T20 added to task table; gate checklist updated; log entry added |
| `roadmap.md` | `telemetry.py` added to M5 key files (roadmap already handled by Morpheus; minimal update only) |

## Review gate

Before T17–T20 implementation tasks are unblocked, Morpheus and Trinity must record approval of Amendment 001 in `.progress.md §Log`.
