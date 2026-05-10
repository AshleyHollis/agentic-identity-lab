# Agentic Identity Lab

Public lab for proving end-to-end identity flows across SharePoint, web apps, APIs, APIM, and agent frameworks. This repository is intentionally a safe, documented skeleton; implementations land in variant-specific folders later.

## What this lab proves
- End-to-end user-delegated identity across UI → APIM → BFF → downstream APIs.
- On-behalf-of (OBO) exchanges when API A calls API B for a user.
- Token audience boundaries per API and per downstream service.
- Clear separation of user-delegated identity paths from service-to-service paths.
- AKS-based agent workloads using Microsoft Entra Agent ID auth (roadmap).

## What it is not
- Not a production-ready reference implementation.
- Not a tenant-specific deployment guide.
- Not a secrets store or credential sample repo.
- Not a promise of full feature parity across variants.

## Core identity lessons
- A userId in request body is **not** identity.
- Delegated tokens include user claims and `scp`.
- App-only tokens use `roles`/`appid` and **do not** represent a user.
- Each API must receive a token with its own `aud`.
- OBO is required when API A calls API B on behalf of a user.
- APIM validates and forwards user tokens on delegated paths.
- APIM replacing `Authorization` with a managed identity breaks delegation.
- Azure OpenAI / Azure AI Foundry auth is **separate** from MCP user-delegated flows.

## Architecture variants (A–F)
- **A. SharePoint Classic** – legacy pages calling APIs through APIM. [Docs](docs/architecture/03-variant-a-sharepoint-classic.md)
- **B. SPFx** – modern SharePoint client with APIM + BFF. [Docs](docs/architecture/04-variant-b-spfx.md)
- **C. Standalone BFF** – web app + BFF + downstream APIs. [Docs](docs/architecture/05-variant-c-standalone-bff.md)
- **D. SPA Comparison** – BFF vs SPA-only tradeoffs. [Docs](docs/architecture/06-variant-d-spa-comparison.md)
- **E. Agent Framework** – agent orchestration with delegated user calls. [Docs](docs/architecture/07-variant-e-agent-framework.md)
- **F. Cross-Tenant** – B2B and cross-tenant flows. [Docs](docs/architecture/08-variant-f-cross-tenant.md)

## Repository map
- `apps/` – application variants and implementation scaffolds.
- `config/` – shared configuration templates and examples.
- `docs/` – architecture narrative and ADRs.
- `diagrams/` – identity and token flow diagrams.
- `docker/` – container definitions and local environment helpers.
- `infra/` – infrastructure-as-code layouts (Terraform, etc.).
- `tests/` – test fixtures and variant-specific testing assets.

## Quick start (placeholders)
1. Review the [architecture overview](docs/architecture/00-overview.md).
2. Pick a variant (A–F) and read its doc.
3. Follow the variant’s TODOs once implementation folders exist.

## Local development (placeholders)
- Copy `.env.example` → `.env` in the relevant variant once provided.
- Run the BFF/API/Frontend tasks listed in that variant’s README.

## Azure deployment (placeholders)
- Terraform layout is documented in [ADR 0002](docs/adr/0002-terraform-layout.md).
- Environments will live under `infra/` (to be added).

## Testing (placeholders)
- Run variant-specific test commands once implementations are added.

## Security warning
This is a public repo. **Do not** add secrets, tenant IDs, subscription IDs, client secrets, or certificates. Use `.env.example` and `terraform.tfvars.example` only.

## Cleanup (placeholders)
- Use `terraform destroy` for the environment you created.
- Remove any registered apps or managed identities created for the lab.

## Contributing
Read [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
