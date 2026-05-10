# Cross-Tenant Environment: Shared

Shared infrastructure environment for cross-tenant scenarios. This configuration is validation-only with placeholder IDs.

## Usage (validation)
```bash
terraform init -backend=false
terraform validate
```

## Notes
- Shared resources should avoid tenant-specific secrets.
- Add APIM and shared observability modules when ready.
