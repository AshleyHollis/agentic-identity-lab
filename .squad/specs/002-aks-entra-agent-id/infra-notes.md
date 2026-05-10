# AKS + Microsoft Entra Agent ID (optional track) — Infra Notes

## Scope
Planning-only placeholder for a future AKS track. No Terraform resources are implemented yet, and nothing here should introduce tenant IDs, subscription IDs, secrets, certs, or tokens.

## Reference (public-safe)
- Christian Posta’s Entra Agent ID on Kubernetes series: https://blog.christianposta.com/entra-agent-id-agw/
  - Covers Entra Agent ID fundamentals, OBO token exchange, Kubernetes sidecar deployment, workload identity federation, and AgentGateway + MCP/LLM scenarios.

## Likely AKS components (future)
- AKS cluster with OIDC issuer enabled.
- Azure AD Workload Identity + federated identity credentials for service accounts.
- Kubernetes namespaces/service accounts for agent-gateway, MCP protected API, and supporting services.
- Entra Agent ID SDK sidecar pattern for agent workloads.
- Ingress layer (NGINX or AGIC) with optional Application Gateway if required by the scenario.
- ACR for images, Log Analytics for observability, and optional Key Vault for runtime configuration (no secrets committed).
- RBAC, network policies, and managed identity role assignments as needed.

## Terraform gaps to add later
- New AKS module (cluster + node pools + networking).
- Workload identity module (OIDC issuer + federated identity credentials).
- Kubernetes bootstrap module (namespaces, service accounts, basic RBAC).
- Optional ingress/app gateway module and wiring for AgentGateway.
- Environment overlay for `aks` (or feature flags) that does not replace the default ACA path.

## How AKS differs from the default ACA path
- ACA remains the default deployment target; AKS is strictly optional.
- ACA uses Container Apps environment primitives; AKS requires Kubernetes manifests/Helm and cluster operations.
- Identity on AKS relies on workload identity federation + service account bindings; ACA uses managed identity at the app level.
- Ingress becomes cluster-managed (Ingress Controller/App Gateway) vs ACA-managed ingress.

## Validation-only CI / deployment safety
- Keep CI validation-only (terraform fmt/validate). No public workflow auto-deploys.
- Avoid apply/plan against live tenants until explicit approval and OIDC/MI wiring are complete.
- Keep all variables and outputs placeholder-only; no kubeconfigs or credentials in repo.

## Roadmap note
Coordinate roadmap updates with Morpheus before adding a new AKS milestone.
