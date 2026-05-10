# Cross-Tenant Environment: Tenant B

Tenant B environment for cross-tenant scenarios. This configuration is validation-only with placeholder IDs.

## Usage (validation)
```bash
terraform init -backend=false
terraform validate
```

## Notes
- Use this alongside the `shared` and `tenant-a` environments.
- Add Entra cross-tenant configuration modules when ready.
