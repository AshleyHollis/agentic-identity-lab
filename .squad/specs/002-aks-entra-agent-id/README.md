# Spec 002: AKS + Entra Agent ID Auth (Agent/MCP)

**Status:** Tasks-Ready (implementation blocked — pending Morpheus + Trinity review gate)  
**Milestone:** M5  
**Spec Phase:** tasks-ready  
**Created:** 2026-05-10 (draft)  
**Promoted:** 2026-05-14  
**Owners:** Morpheus (Lead/Architect), Tank (Infra), Trinity (Security), Neo (Backend)  
**Reviewers:** Morpheus (architecture), Trinity (security)  
**Impact:** High

## Terminology

> **Amendment 002 (2026-05-10 — pre-M6 naming):** "Agentic Layer" superseded by **Agent Execution Service** per ADR 0008. See amendment table below.

| Term | Definition |
|------|-----------|
| **Agent Execution Service** | The lab's app-level agent execution service at `apps/agent-gateway/` (legacy filesystem path; not renamed). The application identity boundary for agent tool calls, OBO exchanges, and multi-step agent flows. Display name: **Identity Lab Agent Execution Service** when org/lab qualification is useful. Referred to as Docker Compose service `agent-gateway` (legacy) but canonically called the **Agent Execution Service** in all documentation (per ADR 0008). |
| **AKS Agent Gateway** | The standalone [agentgateway.dev](https://agentgateway.dev) infrastructure proxy — deployed as a sidecar or ingress component in AKS. An infrastructure-layer MCP protocol proxy; **not** the lab's Agent Execution Service. |
| **Entra Agent ID sidecar** | The Microsoft Entra Agent ID SDK running as a sidecar container alongside the agent workload in AKS. Distinct from all of the above. |

**Rule:** The lab's orchestration service is the **Agent Execution Service** (`apps/agent-gateway/`). When referencing the standalone agentgateway.dev proxy, always use **AKS Agent Gateway**. Unqualified "agent gateway" is retired in spec prose. Do not use unqualified "Agent Service" (collision with Azure AI Agent Service).

**Historical note:** During M5 implementation, "Agentic Layer" was the canonical term (ADR 0006). This was superseded by "Agent Execution Service" via ADR 0008, adopted pre-M6.

---

## Summary

Promote Spec 002 from draft/research into a full implementation-ready spec for AKS + Microsoft Entra Agent ID authentication in agent/MCP workloads. Builds directly on Spec 001 local mock validation and OBO boundary rules, Spec 003 delegated flow integration, and Spec 005 runtime ergonomics.

This spec defines the Agent ID sidecar contract, offline fixture strategy, safe-claims allowlist extension, Agent OBO sidecar mock boundary, AKS Terraform skeletons, strict JWKS validation, end-to-end tracing design, and the ADR decisions required before implementation begins.

## Scope (In)

- Agent ID sidecar HTTP contract (`/Validate`, `/AuthorizationHeader/{apiName}`, `/DownstreamApi/{apiName}`).
- Offline fixture set for Agent ID / Agent OBO claim scenarios (blueprint user token, agent OBO MCP token, and five negative cases).
- Safe-claims allowlist extension for non-PII actor metadata (`xms_act_fct`) while continuing to suppress `oid`, `sub`, `email`, `upn`, `name`, `preferred_username`.
- Agent OBO sidecar mock boundary module: validates blueprint audience before exchange, enforces localhost-only sidecar URL, no network calls in offline tests, sanitized output claims, separate from MCP user OBO and Azure OpenAI/Foundry managed identity.
- AKS Terraform module skeletons (`aks`, `workload-identity`, `k8s-bootstrap`) and environment overlay (`environments/aks/`).
- Illustrative AKS manifests/docs: namespace, service account with workload identity annotation, Agent Execution Service deployment with Entra Agent ID sidecar, network policy preventing cross-pod sidecar access.
- Strict JWT/JWKS validation design and tests: reject `alg:none`, reject `HS*`, enforce `kid`, preserve claim checks, ignore fixture header in strict mode, safe JWKS caching.
- End-to-end distributed tracing design for mock and AKS flows using OpenTelemetry + Jaeger, covering visualization goals, span/correlation expectations, and mock-flow instrumentation.
- Three ADR decisions: AKS optional track, Agent ID sidecar mock boundary, JWKS client/caching strategy.
- Validation: offline pytest, Terraform fmt/validate for AKS overlay, no-secret scan.

## Scope (Out)

- Production-grade AKS cluster deployment or full operational manifests.
- Tenant-specific setup steps, secrets, kubeconfigs, or live configuration.
- Live Entra ID SDK wiring or real token acquisition against a live tenant.
- Azure OpenAI/Foundry managed identity wiring (separate integration path).
- M6 Azure deployment baseline (tracked in Spec 006).
- Any implementation until Morpheus architecture review and Trinity security review are complete.

## Artifacts

| Artifact | Status |
|----------|--------|
| `README.md` | Amended (001) |
| `goals.md` | Amended (001) |
| `research.md` | Amended (001) |
| `requirements.md` | Amended (001) |
| `design.md` | Amended (001) |
| `tasks.md` | Amended (001) |
| `state.json` | Amended (001) |
| `.progress.md` | Amended (001) |
| `identity-notes.md` | preserved from draft |
| `infra-notes.md` | preserved from draft |

## Validation Targets

```
python -m pytest
terraform -chdir=infra\terraform fmt -check -recursive
terraform -chdir=infra\terraform\environments\aks validate
```

No-secret scan: no real tenant IDs, subscription IDs, tokens, kubeconfigs, or client secrets anywhere in committed files.

## Related Specs

- Spec 001: shared auth library + OBO boundaries (complete)
- Spec 003: delegated flow integration tests (complete)
- Spec 005: runtime ergonomics + Docker Compose (complete)
- Spec 006 (forthcoming): Azure deployment baseline (ACA default + AKS optional)

## References

- Christian Posta Entra Agent ID on Kubernetes series: https://blog.christianposta.com/entra-agent-id-agw/
- Microsoft Entra Agent ID (public product page; no tenant-specific content referenced)
- AKS Agent Gateway tracing reference (agentgateway.dev): https://agentgateway.dev/docs/standalone/main/reference/observability/traces/

---

## Amendments

| # | Date | Changed By | Summary | Status |
|---|------|-----------|---------|--------|
| 001 | 2026-05-15 | spec-feature (Ashley Hollis) | Terminology clarification (Agentic Layer vs AKS Agent Gateway); E2E tracing requirements (mock + AKS, OTEL/Jaeger); roadmap milestone outcome clarity; tasks T17–T20 added. Implementation remains blocked pending T03. | Approved |
| 001-correction | 2026-05-15 | spec-feature (Ashley Hollis) | Terminology corrected per ADR 0006: "local app gateway" → **Agentic Layer**; "standalone Agent Gateway" → **AKS Agent Gateway**. Earlier draft used "local app gateway" for the `apps/agent-gateway/` service — superseded by ADR 0006 accepted by Morpheus. | Applied |
| 002 | 2026-05-10 | Morpheus (Ashley Hollis approval) | Naming amendment: "Agentic Layer" superseded by **Agent Execution Service** per ADR 0008. Terminology table and body text updated. Historical M5 use of "Agentic Layer" acknowledged. | Applied — pre-M6 |
