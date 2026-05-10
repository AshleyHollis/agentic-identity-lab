# Azure Container Apps (Default)

Azure Container Apps is the default deployment target for this project. The Terraform environments under `infra/terraform/environments/` are validation-only and use placeholder IDs.

## Recommended flow
1. Populate `terraform.tfvars.example` with real values.
2. Run `terraform init -backend=false` and `terraform validate` to confirm wiring.
3. When approved, add an apply workflow using GitHub OIDC and managed identity (no secrets in repo).

## Notes
- No deployment workflows are enabled by default.
- Use managed identity for runtime access (Key Vault, ACR, APIM).
