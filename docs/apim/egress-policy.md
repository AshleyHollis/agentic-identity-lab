# APIM Egress Policy (Forward OBO Token)

## Goal
Forward a **downstream OBO token** (not the original user token) to backend services.

## Example (Placeholder IDs Only)
```xml
<outbound>
  <base />
  <validate-jwt header-name="x-obo-authorization"
                failed-validation-httpcode="401"
                failed-validation-error-message="Missing or invalid OBO token"
                require-scheme="Bearer">
    <openid-config url="https://login.microsoftonline.com/{tenant-id-placeholder}/v2.0/.well-known/openid-configuration" />
    <audiences>
      <audience>api://00000000-0000-0000-0000-000000000103</audience>
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
    <value>@(context.Request.Headers.GetValueOrDefault("x-obo-authorization", ""))</value>
  </set-header>
  <include-fragment fragment-id="safe-logging" />
</outbound>
```

## Notes
- The OBO token must be created **after** validating the inbound user token.
- APIM expects `x-obo-authorization: Bearer {token}` and forwards it as `Authorization`.
- Validate MCP audience + scopes before forwarding.
- Avoid logging `Authorization` headers.

## Repository example and validation
- Policy XML: `infra/terraform/policies/apim/egress-validate-obo-token.xml`
- Static test: `tests/integration/python/test_apim_egress_validates_obo_token.py`
