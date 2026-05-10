# Single-Tenant Environment

This environment is the default single-tenant Azure Container Apps layout. It is validation-only and uses placeholder IDs.

## Usage (validation)
```bash
terraform init -backend=false
terraform validate
```

## Notes
- Replace placeholder IDs in `terraform.tfvars.example` before any real deployment.
- Add APIM, Key Vault, and identity modules as the architecture evolves.
