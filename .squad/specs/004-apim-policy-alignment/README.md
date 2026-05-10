# Spec 004: APIM Policy Alignment

**Status:** Complete  
**Milestone:** M3  
**Spec Phase:** close  
**Created:** 2026-05-10  
**Updated:** 2026-05-10  
**Impact:** Medium

## Summary
Align APIM ingress/egress policy examples and documentation with the validated audience, scope, tenant, and OBO-boundary rules from Specs 001 and 003. Replace fixture-only APIM integration tests with static checks that parse the actual policy XML examples.

## Scope (In)
- APIM ingress policy example for delegated user-token validation.
- APIM egress policy example for OBO-token validation and forwarding.
- Managed identity token replacement anti-pattern documentation/example.
- Safe logging and correlation guidance.
- Static integration tests that inspect APIM policy XML files.

## Scope (Out)
- Live APIM deployment.
- Policy execution against an Azure tenant.
- Real token acquisition or tenant-specific values.
- Terraform resource changes beyond policy/example alignment.

## Validation
- `python -m pytest`
- `terraform -chdir=infra\terraform fmt -check -recursive`
- `terraform -chdir=infra\terraform\environments\single-tenant validate`

## Outcome
Complete. APIM integration tests now inspect policy XML/docs directly, APIM docs link to their backing policy examples/tests, and all validation targets pass.

