# Single-Tenant Deployment

Single-tenant deployment uses Azure Container Apps with a dedicated resource group and identity boundaries.

## Terraform
- Environment: `infra/terraform/environments/single-tenant`
- Run validation-only steps until deployment is approved.

## Local dev
Use `docker/docker-compose.single-tenant.yml` with the base compose file.
