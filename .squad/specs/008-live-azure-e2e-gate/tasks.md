# Spec 008 — Tasks

**Spec:** 008-live-azure-e2e-gate  
**Milestone:** M8  
**Updated:** 2026-05-10  
**Primary implementation owner:** Tank  
**Reviewers:** Morpheus, Trinity

---

## Dependency Order

```text
T10 (Tank deployment review) ──────┐
T11 (Morpheus architecture review) ├── (all clear) ──→ implementation stream
T12 (Trinity security review) ─────┘

After T10 + T11 + T12 complete:
  Required path:
    T00 → T01 → T02 → T03 → T04 → T05 → T07 → T08 → T09 → T13 → T14 → T15

  Optional branch (non-blocking):
    T01 → T06
    (if implemented, fold destroy/recreate guidance into T09 docs)
```

---

## T10 — Tank deployment review

**Owner:** Tank  
**Depends on:** Spec 008 artifacts complete  
**Blocks:** All implementation tasks

**Focus areas:**
1. PR validation workflow scope
2. manual deploy workflow contract and approval boundary
3. start/resume and nightly shutdown workflow split
4. smoke/trace workflow orchestration
5. resource-type cost-control matrix and destroy/recreate fallback

**Acceptance:** deployment workflow set, cost-control assumptions, and operator-facing constraints are confirmed in `.progress.md`.

---

## T11 — Morpheus architecture review

**Owner:** Morpheus  
**Depends on:** Spec 008 artifacts complete  
**Blocks:** All implementation tasks

**Focus areas:**
1. opt-in boundary and public CI separation
2. pipeline-first workflow topology
3. cost-control lifecycle model and resource matrix
4. canonical browser smoke driver choice
5. Agent Execution Service naming clarity vs AKS Agent Gateway references

**Acceptance:** sign-off or binding conditions recorded in `.progress.md`.

---

## T12 — Trinity security review

**Owner:** Trinity  
**Depends on:** Spec 008 artifacts complete  
**Blocks:** All implementation tasks

**Focus areas:**
1. least-privilege OIDC and protected-environment assumptions
2. no-token / no-PII / no-unsafe-tracestate telemetry rules
3. APIM/BFF/Agent Execution Service/MCP auth boundaries
4. workflow artifact hygiene and secret exposure boundaries
5. required negative tests, static scans, and KQL leakage checks

**Acceptance:** sign-off or binding conditions recorded in `.progress.md`.

---

## T00 — Implementation kickoff package

**Owner:** Tank  
**Depends on:** T10 + T11 + T12

Finalize workflow names, job boundaries, inputs/outputs, and the resource lifecycle matrix based on accepted review conditions.

**Acceptance:** implementation-ready workflow contract captured in implementation plan/docs.

---

## T01 — Protected environment + OIDC workflow contract

**Owner:** Tank  
**Depends on:** T00

Define and implement the protected GitHub Environment contract and least-privilege OIDC setup for live Azure workflows.

**Acceptance:** live workflows use protected environments, OIDC auth, and binding purpose-scoped identities (deploy, smoke, shutdown/start-resume separated or equivalently constrained) without routine long-lived Azure secrets. Shutdown identity scope is stop/start/scale-focused and cannot perform broad deploy/apply/destroy operations.

---

## T02 — PR validation workflow

**Owner:** Tank / Neo  
**Depends on:** T00

Implement the public-safe PR validation workflow for tests, Terraform validation, workflow policy checks, and secret/identifier scanning.

**Acceptance:** PR validation remains non-live and fails on forbidden live defaults, unsafe identifiers, or any public-CI workflow behavior that attempts live Azure auth, protected-environment bypass, or deploy/apply/destroy actions.

---

## T03 — Manual deploy-live workflow

**Owner:** Tank  
**Depends on:** T01, T02

Implement the manual live deployment workflow that performs IaC, config, image, and app rollout for the private lab environment.

**Acceptance:** workflow remains manual/protected only, uses Azure OIDC, and gates smoke execution behind `LIVE_AZURE_TESTS=true`.

---

## T04 — Start-resume workflow

**Owner:** Tank  
**Depends on:** T01

Implement the manual start/resume workflow that brings the lab back online from a stopped or scaled-down state.

**Acceptance:** idempotent start behavior with ready-state verification and resource-action summary.

---

## T05 — Nightly shutdown workflow

**Owner:** Tank  
**Depends on:** T01

Implement the nightly stop/scale-down workflow and keep destructive actions out of the scheduled path.

**Acceptance:** scheduled workflow reports resource actions and clearly distinguishes stopped, scaled-to-zero, left-running, and destroy-only resources.

---

## T06 — Optional destroy workflow

**Owner:** Tank  
**Depends on:** T01

Implement a separately approved manual destroy/recreate workflow only if the accepted cost model requires it.

**Acceptance:** destructive workflow is manual-only, explicitly approved, and documents data-loss/recovery boundaries.

**Non-blocking note:** T06 is optional and does not gate T09/T13/T14/T15 unless the team explicitly commits to implementing destroy/recreate in this milestone.

---

## T07 — Canonical browser smoke + trace workflow

**Owner:** Neo / Mouse  
**Depends on:** T03, T04

Implement the canonical live browser smoke harness and trace verification flow for APIM → BFF → Agent Execution Service → MCP.

**Acceptance:** smoke harness requires explicit live opt-in, validates the full path, executes the binding telemetry/KQL contract, and hard-fails the workflow on any leakage finding.

---

## T08 — Security and telemetry validation gates

**Owner:** Trinity / Tank / Neo  
**Depends on:** T02, T03, T05, T07

Add required negative tests, static scans, artifact hygiene checks, and KQL leakage verification.

**Acceptance:**
1. validation fails on token/PII leakage, auth-boundary regressions, unsafe workflow/artifact behavior, missing workflow principal separation controls, or missing RBAC scope documentation for deploy/smoke/shutdown identities
2. telemetry contract implementation includes versioned KQL artifacts covering `requests`, `dependencies`, `traces`, and `logs`
3. telemetry contract explicitly bans raw tokens, `Authorization` values, `oid`, `sub`, `email`, `upn`, `preferred_username`, and unsafe `tracestate` content
4. static/local validation tests for the KQL contract are required in CI (no live Azure query execution required for this planning revision)
5. smoke/trace pipeline and any deploy-triggered smoke stage fail on KQL contract failure

---

## T09 — Cost model and operator documentation

**Owner:** Tank  
**Depends on:** T04, T05, T07, T08

Document start/stop behavior, resource-type cost expectations, and operator guidance for the live lab. If T06 is implemented, include an additional destroy/recreate section.

**Acceptance:** required docs explain what scales to zero, what may stay billable, how smoke/trace verification is invoked safely, and the documented RBAC scope boundaries for deploy/smoke/shutdown identities. If T06 is implemented, docs also explain when destroy/recreate is appropriate and its recovery boundaries.

---

## T13 — Morpheus implementation conformance review

**Owner:** Morpheus  
**Depends on (required path):** T03, T04, T05, T07, T08, T09  
**Conditional dependency:** include T06 only if the team explicitly implements T06 in this milestone.

Verify implementation matches approved architecture, ADRs, and naming boundaries.

---

## T14 — Trinity implementation security review

**Owner:** Trinity  
**Depends on (required path):** T03, T04, T05, T07, T08, T09  
**Conditional dependency:** include T06 only if the team explicitly implements T06 in this milestone.

Verify live-token handling, telemetry hygiene, workflow artifact safety, and protected-environment boundaries.

---

## T15 — Final closeout

**Owner:** Tank (with Morpheus/Trinity sign-off)  
**Depends on (required path):** T13 + T14  
**Conditional dependency:** include T06 evidence only if T06 is explicitly implemented; otherwise T06 remains non-blocking.

Run final validation, update state, and mark M8 complete only after the live gate is proven and cost controls are documented.
