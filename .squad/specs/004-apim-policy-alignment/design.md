# Design: APIM Policy Alignment

**Status:** Complete  
**Milestone:** M3  
**Spec Phase:** design  
**Created:** 2026-05-10  
**Updated:** 2026-05-10  
**Impact:** Medium

## Approach
Use static file validation for APIM policy examples because this public lab does not execute policies against live Azure. The tests should parse XML examples and assert the identity-critical pieces that must not drift:

- `validate-jwt` target header.
- Bearer scheme requirement.
- Expected placeholder audiences.
- Required delegated `scp` claim.
- Trusted tenant `tid` allowlist claim.
- OBO header mapping from `x-obo-authorization` to `Authorization`.
- Anti-pattern warning text.

## Policy boundaries
| Boundary | Header validated | Audience | Required claims | Header forwarded |
|----------|------------------|----------|-----------------|------------------|
| Ingress | `Authorization` | BFF or agent-gateway | `scp`, `tid` | Preserve inbound `Authorization` |
| Egress | `x-obo-authorization` | MCP | `scp`, `tid` | Set downstream `Authorization` from OBO header |

## Testing strategy
- Use `xml.etree.ElementTree` to parse APIM XML files.
- Use targeted string checks for APIM expressions and documentation prose.
- Avoid real APIM calls or Azure dependencies.

## Files
- `docs/apim/ingress-policy.md`
- `docs/apim/egress-policy.md`
- `docs/apim/managed-identity-token-replacement-warning.md`
- `infra/terraform/policies/apim/ingress-validate-user-token.xml`
- `infra/terraform/policies/apim/egress-validate-obo-token.xml`
- `infra/terraform/policies/apim/broken-managed-identity-replacement.xml`
- `tests/integration/python/test_apim_ingress_validates_token.py`
- `tests/integration/python/test_apim_egress_validates_obo_token.py`
- `tests/integration/python/test_apim_managed_identity_replacement_breaks_delegation.py`

