# ADR-005: M6 Managed Identity Assignment Strategy — User-Assigned per Container App

> **Status:** Accepted
> **Spec:** 006-azure-deployment-baseline (ADR-M6-03)
> **Date:** 2026-06-01
> **Approved by:** Trinity (Security Reviewer) — M6 T12 security review
> **Deciders:** Trinity (Security), Tank (Infra)
> **Phase:** M6 Azure deployment baseline
> **Impact:** High — determines OBO boundary enforcement at the managed identity scope in Azure Container Apps

---

## Context

Spec 006 introduces three Azure Container Apps (BFF, Agent Execution Service, MCP Protected API) each requiring
a managed identity for:

1. Service-to-service calls within the ACA environment.
2. Agent Execution Service OBO token exchange via Entra ID (future live implementation, not in M6 scope).
3. Downstream role assignments (e.g., Key Vault Secrets User) defined in Terraform.

Azure Container Apps supports two managed identity models:

- **System-assigned** — created with and tied to the container app lifecycle; cannot be pre-assigned roles
  before the container app exists.
- **User-assigned** — created independently; roles can be assigned in Terraform before the container app
  exists; identity survives container app re-creation.

The M1/M3/M5 OBO boundary design requires that **only** the Agent Execution Service has Entra API
permissions to perform OBO token exchange. BFF and MCP Protected API must have no such permissions.
This boundary must be expressible and auditable at the managed identity level in Azure IAM.

The existing `infra/terraform/modules/managed-identity/` module already scaffolds
`azurerm_user_assigned_identity`.

---

## Options

### Option A — User-assigned managed identity per service (RECOMMENDED)

Create three separate `azurerm_user_assigned_identity` resources (one per service):
- `managed_identity_bff`
- `managed_identity_agent_execution`
- `managed_identity_mcp_protected_api`

Role assignments (Key Vault, Entra API permissions) target the specific identity by `principal_id`.
Only `managed_identity_agent_execution` is ever granted Entra OBO API permissions (post-M6 live work).

**Pros:**
- OBO permission boundary is enforceable and auditable per-identity in Azure IAM.
- Role assignments expressible in Terraform before container app exists.
- Identities survive container app re-creation / blue-green deployments.
- Consistent pattern across all three services; reuses existing module.
- Passes `terraform validate` without live credentials.

**Cons:**
- Three managed identity resources instead of one.
- Slightly more Terraform surface.

### Option B — System-assigned managed identity

One identity per container app created implicitly when the container app resource is created.

**Cons:**
- Cannot pre-assign roles; identity does not exist until `terraform apply` completes the container app.
- OBO boundary is harder to audit — no dedicated principal to inspect in Azure Portal pre-deploy.
- Less suitable for declarative IaC workflows where role assignments are defined separately.
- Does not allow pre-creation of Entra API permission grants.

---

## Decision

**Option A — User-assigned managed identity per service.**

Three separate `azurerm_user_assigned_identity` resources MUST be created in the
`single-tenant-aca` environment. Each container app MUST be configured with its
own identity via the `identity` block (`type = "UserAssigned"`).

### OBO Boundary Rules (binding — enforced by managed identity assignment)

| Identity | OBO permissions | Notes |
|----------|----------------|-------|
| `managed_identity_bff` | None | BFF validates inbound user tokens only; no downstream OBO |
| `managed_identity_agent_execution` | Entra OBO API permissions (post-M6) | Only identity permitted to exchange OBO tokens |
| `managed_identity_mcp_protected_api` | None | Validates OBO-exchanged tokens only; no re-exchange |

This maps exactly to the OBO boundary established in M1 (Spec 001) and M2 (Spec 003).

### APIM Managed Identity Scope

APIM uses a **system-assigned** managed identity for its own calling identity (APIM → ACA transport).
APIM MUST NOT be granted Entra OBO API permissions. APIM validates the inbound user JWT (audience,
scope, signature) and routes the original delegated token to BFF. APIM does **not** substitute the
user token with its own MI token on the BFF call. This constraint MUST be documented as a comment
in the Terraform APIM module resource block and in the APIM policy XML.

---

## Consequences

### Positive

- OBO boundary is auditable in Azure IAM: only `managed_identity_agent_execution` will ever hold
  Entra API permissions for OBO token exchange.
- Separation of managed identities makes it impossible (by configuration) for BFF or MCP Protected
  API to acquire OBO permissions accidentally.
- Aligns with Spec 001 auth boundary design carried through M1–M5.
- Works with `managed-identity` Terraform module already scaffolded.

### Negative / costs

- Three additional Terraform resources.
- Requires explicit `principal_id` outputs wired in `outputs.tf` for post-M6 role assignment work.

### Neutral / informational

- M6 does not implement live Entra API permission grants or role assignments — these are deferred
  to post-M6 work with live Azure credentials outside the public repo.
- Role assignment placeholder blocks (empty resource blocks or comments) MUST be present in the
  `single-tenant-aca/main.tf` to document intent without requiring live scope.

---

## Security conditions required for T01–T10 implementation

These conditions are binding and MUST be satisfied in the corresponding implementation task:

### C1 — Blueprint audience strict-mode validation (required in T09)

**Gap identified:** `validate_strict_config()` in `apps/shared/python/identity_lab_auth/auth_settings.py`
does not validate `blueprint_audience`. In `AUTH_MODE=strict`, the Agent Execution Service starts
successfully even when `BLUEPRINT_AUDIENCE` env var is absent, defaulting to
`BLUEPRINT_AUDIENCE_PLACEHOLDER = "api://00000000-0000-0000-0000-000000000201/access_as_user"`
(an all-zero GUID URL). Real Entra tokens will never match this audience, causing silent
misconfiguration that is hard to diagnose in a live environment.

**Required fix (T09):** In `apps/agent-execution/python-fastapi-agent-framework/app/config.py`,
add a check after `validate_strict_config()` that when `auth_mode == AuthMode.STRICT`,
`blueprint_audience` must not be the placeholder value. The check MUST use the same
`_looks_like_placeholder` logic (or an equivalent) and raise `ValueError` with a clear message.
A test verifying this must be added and pass in `python -m pytest`.

Example addition in `load_settings()`:

```python
if settings.auth_mode == AuthMode.STRICT:
    validate_strict_config(...)
    # Blueprint audience must also be configured in strict mode
    from identity_lab_auth.auth_settings import _looks_like_placeholder
    if _looks_like_placeholder(settings.blueprint_audience) or \
       "00000000-0000-0000-0000-000000000" in settings.blueprint_audience:
        raise ValueError(
            "Strict auth mode requires a real BLUEPRINT_AUDIENCE; "
            f"got placeholder {settings.blueprint_audience!r}."
        )
```

### C2 — APIM must not substitute delegated token (required in T04)

**Required constraint (T04):** The Terraform APIM module and APIM policy XML used in the
`single-tenant-aca` environment MUST include an explicit comment stating that APIM's
system-assigned managed identity is used for APIM's own resource access only and MUST NOT
be injected as an Authorization header on calls to BFF. The existing Spec 004 ingress policy
(`ingress-validate-user-token.xml`) validates and routes the original user JWT — this
behavior MUST be preserved and not overridden by MI token injection in any APIM policy fragment.

---

## Implementation notes

Tasks implementing this decision:
- **T01** — Create `single-tenant-aca` environment; wire three managed identity modules.
- **T04** — Wire APIM module; add C2 comment constraint.
- **T05** — Wire managed identity per container app; confirm `identity_ids` in each container app module.
- **T09** — Implement C1 blueprint audience strict-mode validation; add test.

---

## References

- Spec 006 design.md — ADR-M6-03 pending question
- Spec 006 research.md — Q3 (user-assigned vs system-assigned), Q5 (APIM MI role scope)
- M1 OBO boundary: `.squad/specs/001-token-validation-obo/design.md`
- M2 agent OBO: `.squad/specs/002-aks-entra-agent-id/design.md`
- Existing managed-identity module: `infra/terraform/modules/managed-identity/`
- T12 security review: this ADR is the security sign-off for ADR-M6-03
