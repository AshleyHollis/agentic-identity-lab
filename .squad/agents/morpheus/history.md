# Morpheus History

## Project Seed

- Project: agentic-identity-lab
- Primary user: Ashley Hollis
- Stack: Azure, Microsoft Entra ID, OAuth2/OIDC, APIM, Terraform, Python/FastAPI, Microsoft Agent Framework, SharePoint, React/Vite or Next.js, .NET and Node placeholders.
- Public repo constraints: no secrets, tenant-specific IDs, subscription IDs, generated certificates, or tokens.

## Learnings

- Established initial public-safe repo skeleton with ADRs, architecture docs, and identity-focused diagrams for variants A–F.
- Added a tools/ placeholder README for future helper scripts with public repo safety constraints.

- Drafted project roadmap and Spec 001 for offline-safe token validation and OBO boundaries; prioritized local delegated flow before Azure deployment.
- Synthesized Spec 001 design covering shared auth module shape, OBO boundary rules, APIM implications, and mock-first testing with placeholder configuration.
- Drafted Spec 001 task plan with owner routing, dependency order, and validation steps for mock auth, OBO boundaries, APIM updates, tests, and docs.
- Aligned identity and APIM docs to the implemented mock/strict validation paths, safe-claims allowlist, and OBO boundary/policy placeholders.
- Added an AKS + Microsoft Entra Agent ID roadmap track and Spec 002 stub; updated architecture/deployment docs to position it as downstream of Spec 001.
- Repaired Milestone 2 tracking by adding Spec 003 for local delegated flow integration and linking it from the roadmap after the coordinator skipped the spec-first workflow.
- Created and closed Spec 004 for APIM policy alignment, linking Milestone 3 to tracked requirements/tasks and APIM documentation validation.
- Added Status Dashboard to project roadmap with milestone progress table, validation targets, and current milestone pointer at M4 (local runtime ergonomics); enabled team visibility into roadmap state and next phase clarity.
