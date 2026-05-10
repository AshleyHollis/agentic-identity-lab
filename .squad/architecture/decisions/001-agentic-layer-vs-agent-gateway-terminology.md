# ADR-001: Agentic Layer vs. AKS Agent Gateway — Canonical Terminology

> **Status:** Superseded by ADR-004 (`.squad/architecture/decisions/004-agent-execution-service-naming.md`) — 2026-05-10  
> The "Agentic Layer" term established here has been replaced by **Agent Execution Service** (approved by Ashley Hollis 2026-05-10T19:30:22.457+10:00). This document is retained as a historical record. The AKS Agent Gateway distinction and all filesystem/runtime backward-compatibility notes from this ADR remain valid and are carried forward into ADR-004.  
> **Date:** 2026-05-14  
> **Deciders:** Morpheus (Lead/Architect), Ashley Hollis (Product Owner)  
> **Phase:** architecture  
> **Impact:** High — terminology propagates across all roadmap milestones, spec artifacts, and developer documentation.

## Context

The lab's monorepo contains a local application-level orchestration service housed under `apps/agent-gateway/`. This directory was created before the standalone [agentgateway.dev](https://agentgateway.dev) project became a tracked infrastructure component in Milestone 5.

As M5 scope matured, both concepts accumulated the label "agent gateway" in written artifacts:

1. **Lab's local service** (`apps/agent-gateway/`) — application-level Python FastAPI and .NET services that route agent tool calls, apply identity context, coordinate multi-step agent flows, and enforce OBO boundaries.
2. **Standalone agentgateway.dev binary/container** — an infrastructure-layer MCP protocol proxy used in AKS as a sidecar to the lab's agent workload. It handles Entra Agent ID token acquisition via `/Validate`, `/AuthorizationHeader/{apiName}`, and `/DownstreamApi/{apiName}` HTTP endpoints on `localhost`. It is **not** the lab's orchestration logic.

This ambiguity creates confusion when reading roadmap milestones, architecture diagrams, and Spec 002 sidecar contract documentation. A developer reading "agent gateway" cannot tell whether the text refers to the Python service they are coding, or the infrastructure proxy the platform team is deploying to AKS.

**Not in scope:** Renaming directories or Python packages in the runtime codebase (no code changes; documentation-only remediation).

## Ranked priorities

1. **Unambiguous comprehension** — any contributor reading a doc or diagram must immediately know which layer is meant.
2. **Backward compatibility** — do not break existing import paths, Docker Compose service names, or CI commands.
3. **Minimal churn** — confine changes to documentation and roadmap artifacts; existing runtime code is unchanged.
4. **Extensibility** — the terminology must scale to future variants (M6 Azure, M7 clients) without further confusion.

## Options considered

### Option 1: Rename both to domain-specific terms
Rename the local service to "Agentic Layer" in all docs; rename the AKS component to "AKS Agent Gateway" (or "Infrastructure Agent Gateway") in all docs. No runtime renaming.

**Pros:**
- Zero ambiguity: "Agentic Layer" = app logic; "AKS Agent Gateway" = infra proxy.
- No code or config changes required.
- Compound label "AKS Agent Gateway" signals hosting context.

**Cons:**
- Minor friction: contributors must learn two names for what previously shared one label.
- Directory path `apps/agent-gateway/` diverges from the new "Agentic Layer" term (documented as legacy alias).

**Score against ranked priorities:**
- Priority 1 (unambiguous): ✅ Both terms are distinct and self-describing.
- Priority 2 (backward compat): ✅ No runtime rename.
- Priority 3 (minimal churn): ✅ Doc-only changes.
- Priority 4 (extensibility): ✅ Scales to M6/M7 without further disambiguation.

### Option 2: Rename only the infrastructure component
Keep "agent gateway" for the local service; introduce "AKS Agent Gateway" only for the AKS proxy.

**Pros:**
- Smallest change surface.

**Cons:**
- Still ambiguous in docs/specs that discuss both layers in the same sentence.
- Readers must infer "agent gateway" means the local service when no AKS qualifier appears.

**Score against ranked priorities:**
- Priority 1 (unambiguous): ❌ Partial — solo "agent gateway" still maps to the local service ambiguously.

### Option 3: Rename apps/agent-gateway/ directory in the monorepo
Rename the directory to `apps/agentic-layer/` to match the new term fully.

**Pros:**
- Perfect alignment between filesystem and terminology.

**Cons:**
- Breaks Docker Compose service names, import paths, and CI commands.
- High churn; unrelated to identity correctness goals.
- Violates Priority 2 and 3.

**Score against ranked priorities:**
- Priority 2 (backward compat): ❌ Would break existing tooling.
- Priority 3 (minimal churn): ❌ Large blast radius.

## Decision

We chose **Option 1**: rename both concepts in documentation only.

### Canonical term map

| Concept | Canonical Term | Filesystem Path | Notes |
|---------|----------------|-----------------|-------|
| Lab's app-level agent orchestration service | **Agentic Layer** | `apps/agent-gateway/` | Directory path retained as legacy; always called "Agentic Layer" in docs/roadmap |
| Standalone agentgateway.dev proxy in AKS | **AKS Agent Gateway** | Deployed to AKS pod sidecar | Infrastructure component; NOT the agentic layer |
| `apps/agent-gateway/python-fastapi-agent-framework` | Agentic Layer — Python (FastAPI) | — | Full sub-path name unchanged |
| `apps/agent-gateway/dotnet-agent-framework` | Agentic Layer — .NET | — | Full sub-path name unchanged |

### Rationale

Option 1 satisfies Priority 1 (unambiguous) at zero cost to Priority 2 (backward compat) and Priority 3 (minimal churn). The compound qualifier "AKS" in "AKS Agent Gateway" immediately signals the infrastructure context, while "Agentic Layer" signals application orchestration logic. The legacy path `apps/agent-gateway/` is documented as such so contributors are not surprised.

### Consequences

**Positive:**
- Spec 002 sidecar contract documentation is unambiguous — the sidecar is the AKS Agent Gateway, not the Agentic Layer.
- Roadmap milestones can reference each tier precisely.
- Architecture diagrams can label both tiers without footnotes.

**Negative / costs:**
- Existing docs that say "agent gateway" (lowercase, unqualified) must be updated to one of the two canonical terms.
- A contributor reading `apps/agent-gateway/` in the filesystem will need to consult this ADR or the doc alias note to understand why the directory is named differently from the docs.

**Neutral / informational:**
- The `apps/agent-gateway/` Docker Compose service name is **not** changed. Doc aliases will note: "Docker Compose service: `agent-gateway`; referred to in architecture docs as the Agentic Layer."
- "Agent gateway" (unqualified, lowercase) is retired as a standalone architectural term in new documentation.

## Implementation notes

Files updated as part of this ADR acceptance:
- `.squad/project/roadmap.md` — milestone sections updated to use canonical terms.
- `docs/agent-framework/overview.md`, `python-agent.md`, `dotnet-agent.md` — headings and body text updated.
- `docs/identity/token-audience.md` — table row updated.
- `docs/apim/ingress-policy.md` — comment updated.
- `docs/architecture/07-variant-e-agent-framework.md` — terminology updated.

Files **not** changed (runtime code boundary):
- `apps/agent-gateway/**` — no runtime code, import, or config change.
- Docker Compose service names.
- Python package names or module imports.

## Review checkpoints

- [ ] Confirmed at M5 implementation start that Spec 002 sidecar contract docs use "AKS Agent Gateway" consistently.
- [ ] Confirmed at M6 deployment baseline that infrastructure Terraform/manifest docs use "AKS Agent Gateway".
- [ ] Re-review trigger: if the lab adopts the agentgateway.dev binary as the **primary** application layer (replacing the Python FastAPI service), this ADR must be revisited.

## References

- Source directive: `.squad/decisions/inbox/copilot-directive-20260510171147.md`
- Amendment: `.squad/specs/002-aks-entra-agent-id/amendments/inbox/001-agentic-layer-gateway-tracing-roadmap.md`
- Spec 002 sidecar design: `.squad/specs/002-aks-entra-agent-id/design.md`
- agentgateway.dev project: https://agentgateway.dev
- Christian Posta — Entra Agent ID on AKS with Agent Gateway: https://blog.christianposta.com/entra-agent-id-agw/
- Related ADR: `docs/adr/0003-container-apps-default.md` (ACA default hosting)
- Related ADR: `docs/adr/0006-agentic-layer-vs-agent-gateway-terminology.md` (public-docs counterpart)
