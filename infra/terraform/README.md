# Terraform

This folder contains Terraform modules, environments, and APIM policy examples for the agentic-identity-lab infrastructure. Azure Container Apps is the default deployment target.

## Structure
- `modules/`: Reusable Terraform modules (skeletons with TODOs).
- `environments/`: Environment configurations for single-tenant, vendor-shaped single-tenant, and cross-tenant layouts.
- `policies/`: APIM policy fragments and examples used by the API gateway.

## Validation-only posture
These templates avoid live tenant/subscription IDs and do not deploy by default. CI is validation-only. Add GitHub OIDC and managed identity wiring before any deployment automation.

## Quick start (validation)
```bash
terraform -chdir=infra/terraform/environments/single-tenant init -backend=false
terraform -chdir=infra/terraform/environments/single-tenant validate
```

## Notes
- Replace placeholder IDs in `terraform.tfvars.example` when you are ready to deploy.
- Add resource implementations inside module `main.tf` files as the design stabilizes.
