# Spec 008 — Research

**Spec:** 008-live-azure-e2e-gate  
**Milestone:** M8  
**Updated:** 2026-05-10

---

## Current Repository Baseline

### M6 + M7 prerequisites already exist

- Spec 006 established the ACA-first deployment baseline with APIM, BFF, Agent Execution Service, MCP Protected API, managed identities, and Azure Monitor scaffolding.  
  **Cites:** `.squad\specs\006-azure-deployment-baseline\requirements.md`, `.squad\specs\006-azure-deployment-baseline\design.md`
- Spec 007 delivered the browser/client variants and explicitly left live Azure validation for M8 with `LIVE_AZURE_TESTS` as opt-in only.  
  **Cites:** `.squad\specs\007-variant-client-implementations\requirements.md`, `.squad\specs\007-variant-client-implementations\design.md`
- The roadmap already positions M8 as the first live browser → APIM → BFF → Agent Execution Service → MCP gate, and `.squad\identity\now.md` keeps it planning-only.  
  **Cites:** `.squad\project\roadmap.md`, `.squad\identity\now.md`

### Current workflow posture in this repository

- Public CI is validation-only today and includes a guardrail that prevents `LIVE_AZURE_TESTS=true` from becoming a default public path.  
  **Cites:** `.github\workflows\ci.yml`, `.squad\decisions\inbox\tank-m8-pipeline-cost-control.md`
- Existing Azure deployment documentation already prefers GitHub OIDC with `azure/login@v2` over long-lived Azure credentials.  
  **Cites:** `docs\deployment\aca\README.md`, `.squad\decisions\inbox\trinity-m8-security-guardrails.md`
- Ashley's standing directive for M8 is pipeline-first deployment plus low-cost nightly shutdown behavior.  
  **Cites:** `.squad\decisions\inbox\copilot-directive-20260510214240.md`

---

## Tank Consolidation — Pipeline + Cost-Control Findings

### Recommended workflow set

Tank's inbox note converges on a five-workflow operating model:

1. **PR validation pipeline** for lint/test/Terraform validation and policy checks only.
2. **Manual deploy pipeline** for IaC, config, image, and app rollout behind protected environment approval.
3. **Nightly shutdown pipeline** for idempotent scale-down/stop actions with an operator summary.
4. **Optional start/resume pipeline** for bringing the lab back online on demand.
5. **Smoke + trace verification pipeline** for browser → APIM → BFF → Agent Execution Service → MCP validation with Azure Monitor correlation.

**Cites:** `.squad\decisions\inbox\tank-m8-pipeline-cost-control.md`

### Deploy-pipeline shape

Tank's preferred deploy shape is:

- `workflow_dispatch` only
- protected GitHub Environment approval before apply/deploy
- `permissions: id-token: write, contents: read`
- Azure OIDC login via `azure/login@v2`
- build/push images if needed, create a Terraform plan artifact, then apply and deploy configuration/apps
- smoke execution only when explicitly requested and only when `LIVE_AZURE_TESTS=true`

This keeps the live gate auditable, repeatable, and outside default public CI.

**Cites:** `.squad\decisions\inbox\tank-m8-pipeline-cost-control.md`, `.squad\decisions\inbox\copilot-directive-20260510214240.md`

### Cost-control by resource type

Tank's resource guidance for the planning spec is:

| Resource type | Planning recommendation | Why |
|---|---|---|
| ACA-hosted apps | Nightly scale to zero / `minReplicas=0`; keep max scale low | Fastest cost reduction without forcing full redeploy |
| APIM | Leave Consumption running; stop Developer/Premium only if tier supports it | APIM cost profile depends on SKU |
| Log Analytics / App Insights | Reduce retention and cap ingestion; do not treat as stoppable | Spend is telemetry-volume driven |
| ACR (if used) | Keep low-cost tier; add retention cleanup for old images/tags | Usually cheaper than compute, but still billable |
| Optional AKS / Agent Gateway path | Reuse start/stop scheduling patterns only if that future path is activated | Not the default M8 target |
| Full environment teardown | Manual destroy/recreate only | Deepest savings but slowest recovery and highest operator cost |

**Cites:** `.squad\decisions\inbox\tank-m8-pipeline-cost-control.md`

### Planning implications

- M8 should default to **scale-down/start-up**, not nightly destroy/recreate.
- APIM stoppability is SKU-sensitive, so the spec must preserve a fallback of `left_running` plus explicit cost reporting.
- IaC, configuration, and app deployment need to stay in the same protected pipeline family to avoid undocumented portal drift.

**Cites:** `.squad\decisions\inbox\tank-m8-pipeline-cost-control.md`

---

## Trinity Consolidation — Security + Telemetry Guardrails

### Identity and environment boundary

Trinity's inbox note makes the following conditions binding for M8:

- Use GitHub OIDC federated identity with `azure/login@v2` wherever supported.
- Keep Azure RBAC least-privilege and scoped to the dedicated lab resource group or narrower.
- Split identities/principals by purpose where practical: deploy/apply, smoke, and nightly shutdown.
- Require protected GitHub Environments for live deploy and live smoke.
- Keep public `pull_request` / `push` CI validation-only.

**Cites:** `.squad\decisions\inbox\trinity-m8-security-guardrails.md`

### Delegated identity boundaries

Trinity explicitly requires:

- real delegated browser-auth flow for smoke validation
- APIM preserves the inbound `Authorization` header to the BFF
- BFF validates the inbound bearer token but does **not** perform the MCP OBO exchange
- Agent Execution Service is the **only** OBO boundary for MCP downstream access
- MCP Protected API rejects the original user token if presented directly

These constraints align with M6/M7 boundaries and must remain visible in M8 implementation planning.

**Cites:** `.squad\decisions\inbox\trinity-m8-security-guardrails.md`

### Telemetry and artifact hygiene

Trinity's required no-leakage rules prohibit:

- raw bearer/JWT/token strings
- PII claim values such as `oid`, `sub`, `email`, `upn`, `preferred_username`, `name`
- `Authorization`, `Cookie`, `Set-Cookie`, and token-bearing query strings in logs or traces
- unsafe `tracestate` content carrying user, token, tenant, or session identifiers
- secrets or tokens in screenshots, HAR files, Playwright traces, uploaded artifacts, or debug logs

**Cites:** `.squad\decisions\inbox\trinity-m8-security-guardrails.md`

### Required negative checks

Trinity calls for explicit negative/static validation gates in M8 planning:

1. workflow policy scan for public-CI/live-step regressions
2. secret and identifier scanning
3. client token-handling scan
4. delegated-auth negative tests (`401` on missing/invalid/wrong-audience token paths)
5. OBO-boundary tests
6. telemetry leakage checks, including KQL negative checks for forbidden fields/token-like content
7. artifact hygiene checks

**Cites:** `.squad\decisions\inbox\trinity-m8-security-guardrails.md`

---

## Consolidated Spec Direction

Tank and Trinity together sharpen Spec 008 into the following planning position:

- **Public CI remains validation-only** and adds M8-specific policy/scan checks, but never live deploy/apply/smoke.
- **Manual protected deploy** is the only approved live rollout path, using Azure OIDC and an explicit `LIVE_AZURE_TESTS=true` guard for any smoke step.
- **Nightly shutdown** is the default cost-control motion; **start/resume** is optional but recommended for operator convenience.
- **Smoke + trace verification** must prove the full browser → APIM → BFF → Agent Execution Service → MCP chain and prove the absence of token/PII leakage.
- **Destroy/recreate** remains a documented manual fallback for expensive non-stoppable resources, not the default nightly action.

This consolidation is sufficient to move Spec 008 from draft placeholders to review-ready planning.

---

## Public-Safe Naming

No subscription-specific or tenant-specific values are committed in this spec. Example placeholders remain:

- GitHub environment: `lab-live-azure`
- workflow input environment slug: `agentidlab-live`
- resource prefix example: `agentidlab-live-{region}`

These are descriptive placeholders only.
