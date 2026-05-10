# Vendor-Shaped Single-Tenant Environment

This environment models a vendor-shaped single-tenant deployment on Azure Container Apps. It is validation-only and uses placeholder IDs.

## Usage (validation)
```bash
terraform init -backend=false
terraform validate
```

## Notes
- Add vendor-specific identity and API gateway wiring when approved.
- No CI deployment is configured; use GitHub OIDC before adding any deploy steps.
