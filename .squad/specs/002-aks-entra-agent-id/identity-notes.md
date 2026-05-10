# Identity & Security Notes — Spec 002: AKS + Entra Agent ID

## Purpose
Add a dedicated AKS track that validates Microsoft Entra Agent ID authentication and its interaction with MCP access in a public-safe way.

## Identity questions this track should test
- Can an agent obtain tokens via Entra Agent ID without long-lived secrets (workload identity federation)?
- Does Agent OBO produce a token where the **user is the subject** and the **agent is the actor**?
- Can we enforce `aud`/`iss`/`tid`/`scp`/`appid` checks at each boundary (agent, gateway, MCP)?
- Are agent identities scoped correctly to the intended Kubernetes workload (no cross-pod token reuse)?
- Do we avoid mixing Agent ID tokens with Azure OpenAI/Foundry auth or MCP delegated user tokens?

## How Agent ID relates to existing identity paths
- **User-delegated OBO (existing):** User token → service validates → OBO token for downstream MCP.
- **Agent ID (new):** Agent identity is a **workload identity** tied to a blueprint; Agent OBO exchanges a **user token scoped to the blueprint** into a downstream token where the agent is the actor.
- **Service/workload identity:** The Entra Agent ID sidecar uses workload identity federation (Kubernetes service account OIDC) to authenticate the **blueprint**, not a client secret.
- **Azure OpenAI/Foundry auth:** Remains **service-to-service** (managed identity or API key) and must not reuse Agent ID tokens or MCP user-delegated tokens.

## AKS-specific trust boundaries & assumptions (from the blog series)
- The Entra Agent ID SDK runs as a **sidecar** and exposes a localhost HTTP API (`/Validate`, `/AuthorizationHeader/{apiName}`, `/DownstreamApi/{apiName}`).
- Sidecar handles token exchange and can mint Agent OBO tokens; the agent app should not handle raw token exchanges directly.
- **Workload identity federation** is preferred: the blueprint trusts the Kubernetes service account OIDC issuer/JWKS and avoids client secrets.
- **Blueprint ↔ Kubernetes mapping:** A blueprint aligns to a **Kubernetes service account** (class of agent). An agent identity maps to a **deployment** (replicas share identity).
- Sidecar is **localhost-only**; enforce network policies to prevent cross-pod access to the sidecar.

## Token audience/scope concerns
- **User token for Agent OBO** must target the blueprint audience (example: `api://00000000-0000-0000-0000-000000000201/access_as_user`).
- **Agent OBO token** must target the MCP audience (example: `api://00000000-0000-0000-0000-000000000103`) and include agent identity claims (`appid`).
- Validate `iss`, `tid`, `aud`, `exp/nbf`, required `scp`, and reject app-only tokens for user-delegated endpoints.
- Agent OBO tokens can be validated using actor/agent claims (e.g., `xms_act_fct` in the blog examples); do not log raw claims or tokens.

## APIM / AgentGateway integration assumptions
- Gateway validates JWTs for **audience** and **issuer** before proxying.
- Downstream MCP calls should only accept **Agent OBO tokens** with the correct audience and expected agent identity.
- Azure OpenAI/Foundry routes should validate against the **cognitiveservices** audience and remain separate from MCP and Agent ID paths.

## Public-safe constraints
- Use **placeholder GUIDs** only.
- Never log, store, or paste raw tokens.
- No tenant IDs, subscription IDs, secrets, or certificates in repo.

## Test strategy (public-safe)
- **Offline fixtures** for agent identity and Agent OBO claims (allowlist-only).
- **Negative cases**: wrong audience, missing `scp`, app-only token, untrusted tenant, missing actor claims.
- **Live tests** (optional, gated) should only log safe-claim allowlist and never capture raw tokens.

## Explicit non-goals
- No live tenant IDs, secrets, or tokens in the repo.
- No production-grade AKS deployment in this spec.
- No credential onboarding or agent provisioning scripts in this public repo.
