# Contributing

Thanks for helping improve the Agentic Identity Lab. This repo is intentionally a **public-safe skeleton**. Keep it minimal, clear, and secure.

## Ground rules
- **No secrets**: do not add tenant IDs, subscription IDs, certs, or tokens.
- Use placeholders and `.env.example`/`terraform.tfvars.example` only.
- Prefer reusable skeletons + TODOs over overbuilt implementations.

## Architecture changes
- Record architectural decisions in ADRs under `docs/adr/`.
- Update relevant variant docs and diagrams when you change flows.
- Keep language clear for future contributors.

## Pull request checklist
- [ ] No secrets or tenant-specific data.
- [ ] Docs updated (README + variant docs).
- [ ] Mermaid diagrams updated (if flows changed).
- [ ] ADR added or updated for architecture changes.
- [ ] Public-safety review completed before final handoff.

## Development notes
- Keep code comments minimal and explanatory only.
- Avoid tooling sprawl; use existing linters/tests once added.

## Getting help
Open a GitHub issue describing the change and the variant it impacts.
