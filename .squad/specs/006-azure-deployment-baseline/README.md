# Spec 006: Azure Deployment Baseline

**Status:** Spec-ready (awaiting review gate)
**Milestone:** M6
**Spec Phase:** spec-prep
**Created:** 2026-06-01
**Updated:** 2026-06-01
**Owners:** Tank (Lead/Infra), Neo (Backend/Rename)
**Reviewers:** Morpheus (Architecture), Trinity (Security)
**Impact:** High

## Summary

Establish the Azure deployment baseline for the Identity Lab: wire Terraform skeletons for Azure Container Apps (ACA) + APIM + managed identity for BFF, Agent Execution Service, and MCP Protected API. Migrate tracing from local Jaeger (M5) to Azure Monitor via OTLP endpoint config swap. Enforce `AUTH_MODE=strict` in the deployment overlay. All infrastructure is placeholder-only; no `terraform apply` runs in public CI.

M6 begins with **Task 0 (T00)**: the filesystem and Compose rename of `agent-gateway` → `agent-execution`, adopting the approved **Agent Execution Service** canonical name.

## Scope (In)

- **M6 Task 0 rename:** `apps/agent-gateway/` → `apps/agent-execution/`; Compose service `agent-gateway` → `agent-execution`; all Python imports, CI commands, and doc references updated.
- **Terraform ACA environment:** `infra/terraform/environments/single-tenant-aca/` with `main.tf`, `variables.tf`, `outputs.tf`, `providers.tf`, `terraform.tfvars.example`.
- **ACA container app modules:** Skeleton resource bodies for BFF, Agent Execution Service, and MCP Protected API container apps in `infra/terraform/modules/container-app/`.
- **APIM wiring:** APIM module connected to ACA backend URLs; JWT validation policy references preserved.
- **Managed identity:** Per-container-app managed identity assignment; APIM system-assigned managed identity skeleton.
- **Azure Monitor / Application Insights:** `infra/terraform/modules/app-insights/` skeleton; `OTEL_EXPORTER_OTLP_ENDPOINT` env var documented in `.env.example` files as the Azure Monitor OTLP ingestion URL placeholder.
- **`AUTH_MODE=strict` deployment overlay:** `docker/docker-compose.strict-aca.yml` for local pre-deploy simulation of strict mode.
- **CI validation gates:** `terraform fmt -check`, `terraform validate`, `docker compose … config --quiet`, no-secret scan — all pass without live Azure credentials.
- **`AUTH_MODE=strict` verification:** Python apps tested to confirm strict mode refuses fixture headers and enforces real JWKS auth.
- **Security review:** Strict auth mode, managed identity boundaries, OBO path, no mock mode in deployed environments.
- **Documentation:** Deployment docs updated; `docs/deployment/aca/` with illustrative ACA deployment notes.

## Scope (Out)

- **`terraform apply` in any CI workflow.** CI validates only; no live resources created from public pipelines.
- **Real tenant IDs, subscription IDs, client IDs, secrets, or tokens** anywhere in committed files.
- **AKS deployment** (optional advanced path from M5; separate tracks).
- **Cross-tenant or vendor-shaped ACA environments** (follow-on work, not M6 gate).
- **M7 client variants** (deferred; depend on M6 ACA endpoint being available).
- **Azure OpenAI / Foundry managed identity path** (separate concern not in M6 scope).
- **Live smoke tests against a deployed endpoint** (documented as post-deployment manual step; no live secrets in repo).

## Naming — Agent Execution Service

| Term | Value |
|------|-------|
| Canonical name | **Agent Execution Service** |
| Folder slug | `agent-execution` |
| Folder path (post-rename) | `apps/agent-execution/` |
| Docker Compose service | `agent-execution` |
| Display name | Identity Lab Agent Execution Service |
| Sub-path (primary) | `apps/agent-execution/python-fastapi/` |

This naming is approved by Ashley Hollis. T00 implements the rename as the first commit of M6.

## Artifacts

| Artifact | Description |
|----------|-------------|
| `goals.md` | M6 goals and success criteria |
| `research.md` | Current state of infra modules, gaps, M5 tracing baseline |
| `requirements.md` | Functional and non-functional requirements |
| `design.md` | Architecture diagram, ACA topology, ADRs, Terraform file structure, OTLP swap design |
| `tasks.md` | Decomposed tasks with owners, dependencies, and validation commands |
| `state.json` | Machine-readable spec state |
| `.progress.md` | Artifact and task progress tracking |

## Related Specs

- Spec 001: Token validation + OBO (complete — shared auth library, strict JWKS)
- Spec 002: AKS + Entra Agent ID (complete — AKS TF skeletons, M5 OTEL instrumentation)
- Spec 003: Local delegated flow (complete — mock OBO integration tests)
- Spec 004: APIM policy alignment (complete — policy XML, ingress/egress)
- Spec 005: Local runtime ergonomics (complete — Compose base/overlay, health checks, `/chat/session`)

## Validation Targets

```
python -m pytest
terraform -chdir=infra\terraform fmt -check -recursive
terraform -chdir=infra\terraform\environments\single-tenant-aca init -backend=false
terraform -chdir=infra\terraform\environments\single-tenant-aca validate
docker compose -f docker\docker-compose.yml -f docker\docker-compose.strict-aca.yml config --quiet
```

> **Public-safe constraint:** No `terraform apply` in CI. Validation only.

> **Scope boundary — M6 vs live E2E (M8):**  
> M6 "Complete" means the Azure deployment *configuration* is validated — Terraform HCL is structurally correct, `AUTH_MODE=strict` is verified in Python, and all CI gates pass without live credentials. M6 does **not** mean the system has been deployed and tested in Azure. Live deployment and end-to-end smoke testing (browser → APIM → BFF → Agent Execution Service → MCP Protected API with real Entra tokens) are the **M8** gate, which is intentionally deferred and opt-in. See `roadmap.md` Status Dashboard for the full picture.

## Coordinator Checkpoint

> **APPROVAL REQUIRED before implementation begins.**
>
> This spec is complete. Coordinator must confirm:
> 1. T00 (rename) is approved to proceed — Neo is unblocked.
> 2. T11 (Morpheus) and T12 (Trinity) reviews are scheduled.
> 3. No implementation tasks (T01–T10) begin until T11 + T12 sign-offs are recorded in `.progress.md`.
