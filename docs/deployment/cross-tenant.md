# Cross-Tenant Deployment

Cross-tenant deployments split infrastructure across tenant A, tenant B, and shared resources.

## Terraform
- Tenant A: `infra/terraform/environments/cross-tenant/tenant-a`
- Tenant B: `infra/terraform/environments/cross-tenant/tenant-b`
- Shared: `infra/terraform/environments/cross-tenant/shared`

## Local dev
Use `docker/docker-compose.cross-tenant.local.yml` with the base compose file.
