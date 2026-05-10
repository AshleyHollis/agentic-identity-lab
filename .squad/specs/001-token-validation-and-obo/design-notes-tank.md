# Design Notes — Tank (Infra/APIM/DevOps)

## Context
Feature 001 focuses on offline-safe delegated token validation and explicit OBO boundaries across BFF/agent-gateway → MCP protected API. No live tenant IDs or secrets.

## APIM ingress/egress policy updates
- **Ingress (BFF + agent-gateway):**
  - Keep `validate-jwt` with placeholder tenant/openid config.
  - Update required `aud`/`scp` to match spec placeholders:
    - BFF/APIM ingress: `aud=api://00000000-0000-0000-0000-000000000101`, `scp=mcp.access`.
    - Agent gateway: `aud=api://00000000-0000-0000-0000-000000000102`, `scp=mcp.access` or `mcp.write`.
  - Enforce delegated tokens by requiring `scp` (reject app-only tokens lacking `scp`).
  - Add tenant allowlist check (placeholder list) before routing; reject `common/organizations` without allowlist.
  - Preserve `Authorization` header (do **not** replace with managed identity).
  - Continue safe-logging + correlation-id fragments; no tokens/PII.
- **Egress (MCP downstream):**
  - Validate **OBO token** on outbound with `aud=api://00000000-0000-0000-0000-000000000103`.
  - Expect OBO token in a dedicated header (e.g., `x-obo-authorization`) and set outbound `Authorization` from it, never from the inbound user token.
  - Keep safe-logging fragment and avoid any token emission.
- **Anti-pattern callout:** keep `broken-managed-identity-replacement.xml` as a documented “do not use”.

## Terraform placeholders (no secrets)
Add non-secret variables in APIM/APIM-API modules and env tfvars examples:
- `tenant_id_placeholder`, `openid_config_url_placeholder`
- `apim_ingress_allowed_audiences` (list), `apim_ingress_required_scopes` (list)
- `apim_obo_downstream_audience`, `apim_obo_required_scopes`
- `trusted_tenant_allowlist` (list of placeholder GUIDs)
- `policy_fragment_ids` / `policy_xml_path` for ingress/egress attachment
Keep values in `terraform.tfvars.example` with placeholder GUIDs only.

## Docker/local dev env var shape (offline/mock)
Align env examples and compose overrides to support mock validation:
- `AUTH_MODE=mock` (default remains `disabled`)
- `AUTH_FIXTURE=delegated-user|app-only|wrong-audience` (or via `X-Identity-Lab-Fixture`)
- `ALLOWED_AUDIENCES` + `REQUIRED_SCOPES` updated to placeholder GUIDs/scopes above
- `TRUSTED_TENANTS` (comma-separated placeholder GUIDs)
- `ENABLE_DEBUG_CLAIMS=false` (safe by default)
Recommend docker-compose overrides reference `config/env/*.env.example` via `env_file`.

## CI validation updates (still validation-only)
- Add `python -m pytest` to CI for auth tests (offline-safe).
- Add APIM policy linting: XML well-formed check for `infra/terraform/policies/apim/*.xml` and fragments (e.g., `xmllint --noout`).
- Keep existing Terraform fmt/validate and compose validation; no deploy steps.

## Managed identity separation (Azure OpenAI / Foundry vs MCP)
- Use **distinct** managed identity configuration for Azure OpenAI/Foundry (service-to-service).
- Keep delegated MCP user tokens **separate** from AI service auth; no token reuse.
- Avoid APIM policies that swap user tokens for MI tokens on MCP paths.

## Implementation tasks for Tank
1. Update APIM policy examples to match placeholder audiences/scopes and add OBO header handling.
2. Add Terraform module variables + env tfvars examples for tenant/audience/scope placeholders and policy attachment.
3. Update docker compose overrides + env examples for `AUTH_MODE`, `AUTH_FIXTURE`, `TRUSTED_TENANTS`.
4. Extend CI with pytest and APIM XML linting (validation-only).
5. Document MI separation guidance in infra/terraform README or APIM policy docs.
