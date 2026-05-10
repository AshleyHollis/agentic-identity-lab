# AKS (Optional)

AKS is an optional target for advanced scenarios. It is not the default deployment model.

## Purpose
- Validate Microsoft Entra Agent ID auth for agent/MCP workloads on AKS (AgentGateway/sidecar pattern).
- Keep public-safe: no tenant IDs, subscription IDs, or live tokens in repo documentation.

## Notes
- Add AKS infrastructure separately when requirements demand Kubernetes control.
- Keep automation validation-only until OIDC and managed identity are ready.
- Reference series: https://blog.christianposta.com/entra-agent-id-agw/ (high-level context only).

## Microsoft Entra Agent ID (optional track)
This repo intends to test Microsoft Entra Agent ID on AKS as a future, optional path. The public-safe reference material is the multi-part series by Christian Posta covering:
- Entra Agent ID fundamentals and blueprints.
- Agent OBO token exchange flows.
- Running the Entra SDK sidecar on Kubernetes.
- Workload identity federation to avoid client secrets.
- AgentGateway + MCP/LLM scenarios on Kubernetes.

Planned AKS notes (no Terraform resources yet):
- Expect a Kubernetes sidecar pattern for the Entra Agent ID SDK.
- Prefer workload identity federation (OIDC issuer + federated identity credential) over client secrets.
- Keep ACA as the default deployment target; AKS is strictly an optional track.
