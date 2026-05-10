# Spec 008: Live Azure E2E Gate

**Status:** Spec-ready (planning artifacts complete; implementation blocked pending review)  
**Milestone:** M8  
**Spec Phase:** spec.feature — planning / opt-in live gate  
**Created:** 2026-05-10  
**Updated:** 2026-05-10  
**Requested by:** Ashley Hollis  
**Owners:** Tank (Infra/Deploy), Neo (Backend/Smoke), Mouse (Browser smoke driver)  
**Reviewers:** Morpheus (Architecture), Trinity (Security)  
**Impact:** High

---

## Summary

M8 defines the first **opt-in live Azure end-to-end gate** for the lab. Its implementation target is a private, secrets-holding GitHub Actions environment that deploys the full Azure path — **browser client → APIM → BFF → Agent Execution Service → MCP Protected API** — and verifies end-to-end tracing in Azure Monitor / Application Insights.

This spec is **planning only**. It does **not** deploy Azure resources, create live pipelines, or introduce real tenant/subscription identifiers. It defines the workflow topology, low-cost operating model, review gates, and public-safe constraints required before Tank begins implementation.

---

## Scope (In)

- Define the **workflow topology** for live Azure deployment via GitHub Actions only: build/publish, IaC apply, app/config rollout, smoke tests, manual start, scheduled stop, and optional full teardown.
- Define the **opt-in boundary**: M8 is not part of default public CI and must require explicit manual dispatch and/or protected scheduled workflows.
- Define the **canonical browser smoke path** using an M7 client through APIM → BFF → Agent Execution Service → MCP Protected API.
- Define **Azure Monitor / Application Insights trace verification** for the live chain, including telemetry safety rules.
- Define the **low-cost lab operating model**: cost-safe defaults, nightly shutdown of all stoppable resources, manual/dispatch start, and documentation for resources that cannot truly stop.
- Define the **resource lifecycle matrix** for Container Apps, APIM, ACR, Log Analytics, App Insights, managed identities, and resource group teardown options.
- Record **ADRs** for major deployment and cost-control choices before implementation.
- Keep all examples **public-safe** with placeholders only.

## Scope (Out)

- Any live Azure deployment from this spec artifact.
- Any new GitHub Actions implementation in this spec change.
- Real tenant IDs, subscription IDs, app IDs, secrets, client secrets, tokens, certificates, or environment names tied to a real subscription.
- Making live Azure tests part of `push` / `pull_request` public CI defaults.
- Replacing the M6 ACA default path with AKS.
- Treating `agentgateway.dev` or the AKS Agent Gateway as the same component as the **Agent Execution Service**.

---

## Artifacts

| Artifact | Description |
|----------|-------------|
| `goals.md` | M8 goals and success criteria |
| `research.md` | Existing repo baseline plus consolidated Tank cost-control and Trinity security findings |
| `requirements.md` | Functional and non-functional requirements for opt-in live Azure E2E |
| `design.md` | Workflow topology, resource lifecycle model, telemetry rules, and ADRs |
| `tasks.md` | Implementation/review/closeout task plan |
| `state.json` | Machine-readable spec state |
| `.progress.md` | Artifact and task progress tracking |

---

## Related Specs

- Spec 006: Azure deployment baseline (ACA + APIM + managed identity validation only)
- Spec 007: Variant client implementations (browser-side token acquisition; M8 prerequisite)

---

## Planned Validation Targets

```
terraform -chdir=infra\terraform\environments\single-tenant-aca init -backend=false
terraform -chdir=infra\terraform\environments\single-tenant-aca validate
python -m pytest
docker compose -f docker\docker-compose.yml config --quiet
LIVE_AZURE_TESTS=true python -m pytest tests\e2e
```

> **Important:** Only the spec artifact validation runs as part of this change. The live Azure commands above are future implementation targets and remain opt-in.

---

## Naming Boundary

**Agent Execution Service** is the AKS/ACA-hosted service that executes agents for the lab. It is **not** the AKS Agent Gateway / `agentgateway.dev` proxy. If AKS or `agentgateway.dev` appears anywhere in M8 implementation planning, it must be called out as an optional infrastructure sidecar/proxy concern, not the core execution service.

---

## Coordinator Checkpoint

> **Approval required before implementation begins.**
>
> 1. Spec 008 artifacts are reviewed and accepted.
> 2. M8 remains **opt-in** and is **not** enabled in default public CI.
> 3. ADR-M8-01 through ADR-M8-04 are accepted or amended.
> 4. T10 (Tank deployment review), T11 (Morpheus architecture review), and T12 (Trinity security review) are recorded in `.progress.md`.
> 5. Tank implementation tasks do not start until T10 + T11 + T12 sign-offs are complete.
