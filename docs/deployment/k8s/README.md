# AKS Manifest Reference — Illustrative Only

> **⚠ ILLUSTRATIVE REFERENCE ONLY — not applied by CI or production automation.**
>
> All names, image references, GUIDs, and IDs in this directory are placeholder values.
> No manifest in this directory is applied by any CI pipeline or automated deployment workflow.
> These files exist solely as architectural reference for the AKS deployment shape described in
> Spec 002 (M5 — AKS + Entra Agent ID auth exploration).

---

## Terminology

| Term | Meaning |
|------|---------|
| **Agent Execution Service** | The lab's app-level agent execution service at `apps/agent-gateway/` (Docker Compose service: `agent-gateway` — legacy). Handles agent tool calls, identity context, and OBO boundaries. Display name: **Identity Lab Agent Execution Service** when org/lab context is useful. |
| **AKS Agent Gateway** | The [agentgateway.dev](https://agentgateway.dev) open-source MCP protocol proxy deployed as infrastructure in AKS. Not the Agent Execution Service. |
| **Entra Agent ID sidecar** | The Entra Agent ID SDK container running in the same pod as the Agent Execution Service in AKS. Exposes `/Validate`, `/AuthorizationHeader/{apiName}`, and `/DownstreamApi/{apiName}` on `localhost` only. |

See ADR `docs/adr/0008-agent-execution-service-naming.md` for the full canonical term map.
*(Historical note: ADR `docs/adr/0006-agentic-layer-vs-agent-gateway-terminology.md` used "Agentic Layer" for this service during M5; superseded by ADR 0008.)*

---

## Files in this directory

| File | Purpose |
|------|---------|
| `namespace.yaml` | Kubernetes namespace for Agent Execution Service workloads |
| `service-account.yaml` | Service account with Azure Workload Identity annotations |
| `agent-gateway-deployment.yaml` | Agent Execution Service pod spec with Entra Agent ID sidecar container |
| `network-policy.yaml` | NetworkPolicy preventing cross-pod access to the sidecar port |

---

## Deployment topology (AKS flow)

```
┌─ AKS Cluster ────────────────────────────────────────────────────────────────┐
│  Namespace: agent-workloads                                                   │
│                                                                               │
│  ┌─ Pod: agent-gateway ─────────────────────────────────────────────────┐    │
│  │  Container: agent-execution-svc    (port 8000 — external-accessible) │    │
│  │  Container: entra-agent-id-sidecar (port 9090 — localhost only)      │    │
│  │                                                                       │    │
│  │  Pod annotation: azure.workload.identity/use: "true"                 │    │
│  └───────────────────────────────────────────────────────────────────────┘   │
│         ↑                                                                     │
│  ┌─ AKS Agent Gateway pod ──────┐                                            │
│  │  (agentgateway.dev proxy)    │ ←── inbound MCP/HTTP traffic               │
│  │  Routes to Agent Exec Svc    │                                            │
│  └──────────────────────────────┘                                            │
└───────────────────────────────────────────────────────────────────────────────┘
```

The **AKS Agent Gateway** (agentgateway.dev) is a separate pod that proxies inbound
MCP protocol traffic to the Agent Execution Service. It is infrastructure only — it does not
contain the application logic in `apps/agent-gateway/`.

The **Entra Agent ID sidecar** runs in the same pod as the Agent Execution Service. The
Agent Execution Service calls the sidecar on `http://localhost:9090` for token validation
and Agent OBO exchange. The sidecar port is never reachable from outside the pod.

---

## Application order

When applied to a cluster (illustrative — not automated), manifests should be applied
in this order:

1. `namespace.yaml`
2. `service-account.yaml`
3. `network-policy.yaml`
4. `agent-gateway-deployment.yaml`

---

## Placeholder values used

| Placeholder | Meaning |
|-------------|---------|
| `00000000-0000-0000-0000-000000000000` | Generic placeholder GUID |
| `00000000-0000-0000-0000-000000000001` | Trusted tenant ID (placeholder) |
| `00000000-0000-0000-0000-000000000201` | Blueprint app / client ID (placeholder) |
| `your-registry.azurecr.io` | Container registry hostname (placeholder) |
| `your-aks-oidc-issuer-url` | AKS OIDC issuer URL (placeholder) |

No real tenant IDs, subscription IDs, client secrets, tokens, or kubeconfigs appear
anywhere in this directory.
