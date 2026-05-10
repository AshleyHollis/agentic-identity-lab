# ADR-005 / ADR-M6-01: Azure Container Apps as Default Deployment Path

> **Status:** Accepted
> **Milestone:** M6 — Azure deployment baseline
> **Date:** 2026-06-01
> **Decided by:** Morpheus (Lead/Architect) — M6 T11 Architecture Review
> **Context ADR:** Spec 006 design.md §ADR-M6-01
> **Impact:** High — sets the M6 default compute target and gates all Tank implementation tasks (T01–T08)

---

## Context

M5 (Spec 002) established an optional AKS track with Terraform skeletons under
`infra/terraform/environments/aks/` and `infra/terraform/modules/aks/`. The roadmap states the
M6 goal as "APIM + Container Apps with managed identity." Tank's charter states "Keep Azure
Container Apps as the default deployment target."

M6 must choose a primary deployment path for the ACA Terraform environment (`single-tenant-aca`)
and for all implementation tasks in the Tank stream (T01–T08). The AKS optional path from M5 must
not be disrupted.

---

## Options Evaluated

**Option A — ACA default, AKS optional (RECOMMENDED)**

- New `infra/terraform/environments/single-tenant-aca/` environment for M6.
- AKS skeletons from M5 preserved, unmodified, and continuing to pass `terraform validate`.
- All M6 Tank tasks (T01–T08) assume the ACA path.
- AKS optional advanced path documented in roadmap; available for contributors with AKS access.

**Option B — AKS default, ACA deferred**

- Would require significant redesign of M5 AKS skeletons as the primary path.
- Contradicts explicit roadmap phrasing ("Container Apps with managed identity").
- Contradicts Tank charter.
- Not evaluated further.

---

## Decision

**Option A is accepted.** Azure Container Apps is the M6 default deployment path.

### Rationale

1. **Roadmap alignment:** M6 goal explicitly names "Container Apps." AKS is documented as the
   optional advanced track from M5, not the M6 gate.
2. **Charter alignment:** Tank charter states ACA as the default deployment target.
3. **Operational fit:** ACA eliminates cluster management overhead for a lab/reference context,
   supports native managed identity via the `identity` block on `azurerm_container_app`, and
   supports Dapr and KEDA for future lab extensions.
4. **Continuity:** The M5 AKS skeletons are valuable as an advanced track and must not be
   disrupted. NFR-06 (AKS environment `terraform validate` continues to pass) is preserved.
5. **Managed identity path:** ACA's native user-assigned managed identity support maps directly
   to the OBO boundary design established in M1 (Spec 001) and M2 (Spec 003).

---

## Consequences

### Positive

- Tank implementation tasks T01–T08 have a clear, unambiguous compute target.
- AKS optional path from M5 is preserved and undisturbed.
- ACA managed identity is simpler to scaffold than AKS workload identity federation for the M6
  skeleton scope.
- Contributors with AKS access can continue to exercise the AKS track without M6 changes.

### Negative / costs

- Decisions around AKS path (k8s-bootstrap namespace inconsistency from M5 T14) are deferred;
  AKS contributors must be aware that the namespace issue remains unresolved.
- The ACA container app ingress mode (`external_enabled`) requires documentation in T08: for
  APIM Standard v2 to route to ACA, the BFF container app must have `external_enabled = true`
  OR APIM must be VNet-injected into the ACA environment. The scaffold defaults to
  `external_enabled = false`; Tank (T08) must document the live deployment override.

### Neutral / informational

- `infra/terraform/environments/single-tenant-aca/` is created as the M6 ACA environment.
- All existing environments (`single-tenant`, `cross-tenant/*`, `vendor-shaped-single-tenant`,
  `aks`) remain unchanged.
- The AKS path remains an advanced track for contributors who want to exercise Entra Agent ID /
  AKS Agent Gateway in a deployed cluster context.

---

## Implementation Notes for Tank (T01–T08)

The existing module stubs use generic output names (`id`, `name`). The `single-tenant-aca/main.tf`
(design.md conceptual structure) references specific output attribute names that Tank must implement
with exact matching names in the respective modules:

| Module | Required output name | Currently in outputs.tf |
|--------|---------------------|------------------------|
| `log-analytics` | `workspace_id` | `id` (null TODO) — **must rename/add** |
| `container-apps-env` | `environment_id` | `id` (null TODO) — **must rename/add** |
| `managed-identity` | `identity_id`, `principal_id` | `id` (null TODO) — **must add both** |
| `container-app` | `fqdn`, `identity_id` | `id` (null TODO) — **must add both** |
| `apim` | (backend_url as input var) | missing from variables.tf — **must add** |

These gaps are tracked in T02 (app-insights module), T03 (container-app resource body), T04
(APIM backend_url), and T05 (managed identity wiring). Tank must ensure exact output name
consistency between design.md and the implemented module files before running `terraform validate`.

---

## Open Questions Resolved

| Q# | Question | Resolution |
|----|----------|-----------|
| Q1 | ACA default vs AKS | **Resolved: ACA default, AKS optional.** (This ADR) |
| Q4 | k8s-bootstrap namespace inconsistency (M5 T14) | **Resolved: Defer to post-M6.** AKS path is orthogonal to M6 ACA baseline. No design change needed. |
| Q6 | Container app ingress: external vs internal | **Resolved: Scaffold uses `external_enabled = var.external_enabled` with default `false`.** T08 deployment doc must document that live deployment requires `external_enabled = true` on BFF (or APIM VNet injection). |

---

## References

- Spec 006 design.md §ADR-M6-01
- Spec 006 research.md §2.1 (ACA vs AKS for M6 Default Path)
- Spec 006 tasks.md §T01, T02, T03, T04, T05, T07, T08
- Spec 006 requirements.md §FR-02, §FR-03, §NFR-06
- Roadmap M6 milestone entry
- Tank charter (ACA default)
- ADR-M5-01 (AKS optional track) — recorded in Spec 002 design.md
- `.squad/architecture/decisions/004-agent-execution-service-naming.md`
