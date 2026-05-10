# APIM Ingress Policy (Validate User Token)

## Goal
Validate **user-delegated tokens** at the API boundary without logging raw tokens.

## Example (Placeholder IDs Only)
```xml
<inbound>
  <base />
  <include-fragment fragment-id="correlation-id" />
  <include-fragment fragment-id="rate-limit" />
  <validate-jwt header-name="Authorization"
                failed-validation-httpcode="401"
                failed-validation-error-message="Unauthorized"
                require-scheme="Bearer">
    <openid-config url="https://login.microsoftonline.com/{tenant-id-placeholder}/v2.0/.well-known/openid-configuration" />
    <audiences>
      <audience>api://00000000-0000-0000-0000-000000000101</audience>
    </audiences>
    <issuers>
      <issuer>https://sts.windows.net/{tenant-id-placeholder}/</issuer>
      <issuer>https://login.microsoftonline.com/{tenant-id-placeholder}/v2.0</issuer>
    </issuers>
    <required-claims>
      <claim name="scp" match="any">
        <value>mcp.access</value>
        <value>mcp.write</value>
      </claim>
      <claim name="tid" match="any">
        <value>00000000-0000-0000-0000-000000000001</value>
        <value>00000000-0000-0000-0000-000000000002</value>
      </claim>
    </required-claims>
  </validate-jwt>
  <set-header name="Authorization" exists-action="override">
    <value>@(context.Request.Headers.GetValueOrDefault("Authorization", ""))</value>
  </set-header>
</inbound>
```

## Service-Specific Audience/Scope
- **BFF**: `aud=api://00000000-0000-0000-0000-000000000101`, `scp=mcp.access`
- **Agentic Layer**: `aud=api://00000000-0000-0000-0000-000000000102`, `scp=mcp.access|mcp.write`

## Notes
- Validate `aud`, `iss`, `exp`, and required `scp` (delegated-only guard).
- Enforce **trusted-tenant allowlist** (`tid`).
- Preserve inbound `Authorization` for delegated flow; OBO happens later.
- Do **not** log `Authorization` headers or raw tokens; use safe logging fragments.

## Repository example and validation
- Policy XML: `infra/terraform/policies/apim/ingress-validate-user-token.xml`
- Static test: `tests/integration/python/test_apim_ingress_validates_token.py`
