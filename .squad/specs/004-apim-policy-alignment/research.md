# Research: APIM Policy Alignment

**Status:** Complete  
**Milestone:** M3  
**Spec Phase:** research  
**Created:** 2026-05-10  
**Updated:** 2026-05-10  
**Impact:** Medium

## Codebase findings
- APIM docs live under `docs/apim/`.
- Policy XML examples live under `infra/terraform/policies/apim/`.
- Current ingress and egress examples already include `validate-jwt`, placeholder issuer/audience values, `scp`, and `tid` claims.
- Existing APIM integration tests in `tests/integration/python/test_apim_*.py` inspect fixtures rather than policy files.

## Patterns to follow
- Keep examples as static XML under `infra/terraform/policies/apim`.
- Use placeholder tenant and GUID values only.
- Validate policy shape with Python standard-library XML parsing where possible.
- Preserve docs as companion explanations for the XML examples.

## Quality commands
| Type | Command |
|------|---------|
| Python tests | `python -m pytest` |
| Terraform format | `terraform -chdir=infra\terraform fmt -check -recursive` |
| Terraform validate | `terraform -chdir=infra\terraform\environments\single-tenant validate` |

## Risks
- APIM XML examples can drift from docs because Terraform validation does not parse policy semantics.
- Policy examples may accidentally imply managed identity replacement is safe for delegated paths.
- Static tests must avoid overfitting formatting while still catching important policy regressions.

