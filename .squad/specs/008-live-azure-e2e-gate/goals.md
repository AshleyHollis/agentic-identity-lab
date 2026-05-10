# Spec 008 — Goals

**Spec:** 008-live-azure-e2e-gate  
**Milestone:** M8  
**Updated:** 2026-05-10

---

## Primary Goal

Define a **low-cost, pipeline-first, public-safe** plan for the lab's first live Azure end-to-end gate so the full delegated path can later be deployed and verified without making live Azure execution part of default public CI.

---

## Success Criteria

| # | Criterion | Measurable outcome |
|---|-----------|-------------------|
| G1 | Opt-in live posture defined | M8 requires protected `workflow_dispatch` and/or protected schedule; no default `push` / `pull_request` live execution |
| G2 | Pipeline-first deployment defined | Spec covers IaC, configuration, image/app deployment, and smoke tests via GitHub Actions |
| G3 | Full path validated in scope | Browser client → APIM → BFF → Agent Execution Service → MCP Protected API is explicitly the required live smoke path |
| G4 | Trace verification defined | Azure Monitor / Application Insights verification approach and KQL/workbook expectations are documented |
| G5 | Telemetry guardrails defined | Raw tokens, PII claims, and unsafe trace/log fields are explicitly prohibited |
| G6 | Low-cost model defined | Manual start, nightly stop, cost-safe defaults, and resource lifecycle matrix are documented |
| G7 | Review gates defined | Tank implementation is blocked on Tank deployment review, Morpheus architecture review, and Trinity security review |
| G8 | ADRs captured | Major deployment/cost-control choices are represented as ADRs in `design.md` and `state.json` |
| G9 | Public-safe placeholders only | No real subscription, tenant, app, or secret values appear in any M8 spec artifact |
| G10 | Planning coherence maintained | `roadmap.md` and `.squad\identity\now.md` both point to Spec 008 as planning-only / not started live |

---

## Non-Goals (this spec change)

- Deploying Azure resources
- Implementing GitHub Actions workflows
- Running live smoke tests
- Selecting real subscription, environment, or tenant names
- Introducing any non-placeholder secrets or identities
