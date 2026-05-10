# Tank History

## Project Seed

- Project: agentic-identity-lab
- Primary user: Ashley Hollis
- Infrastructure focus: Terraform modules/environments, Azure Container Apps, APIM ingress/egress policies, Docker Compose, GitHub Actions validation.
- Public repo constraints: no secrets, tenant-specific IDs, subscription IDs, generated certificates, or tokens.

## Learnings

- Spec 004 APIM policy alignment passed Terraform validation using `terraform -chdir=infra\terraform fmt -check -recursive` and `terraform -chdir=infra\terraform\environments\single-tenant validate`.
- Created Terraform module and environment skeletons with validation-only placeholders and ACA as default target.
- Added APIM policy examples plus Docker Compose variants for bff, agent-gateway, and mcp-protected-api.
- Added validation-only GitHub Actions workflows for terraform, docker compose, docs, and security scans.
- Drafted APIM/OBO policy guidance and placeholder-driven Terraform/env requirements for token validation without secrets.
- Updated APIM ingress/egress policy placeholders to enforce delegated scp, trusted tenant allowlists, and OBO header forwarding with downstream audience validation.
- Aligned env example auth settings with service config fields, using mock-first defaults and strict-mode placeholders for future Entra wiring.
- Added AKS optional planning notes for Microsoft Entra Agent ID, covering infra gaps and validation-only guidance.
