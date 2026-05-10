# Current State Context

## Snapshot
This repository is an initial, public-safe skeleton. It contains docs, diagrams, and ADRs only.

## Constraints
- Public repo: no secrets, tenant IDs, subscription IDs, or certificates.
- Use placeholders and example files only.
- Architecture must remain understandable for future contributors.

## Stakeholders
- **Identity**: ensures correct token audience and OBO behavior.
- **Infrastructure**: defines repeatable deployment layout.
- **Application**: builds BFF/API and client samples.
- **Frontend**: validates UX and authentication flows.

## Gaps
- No implementation code yet.
- No automation pipelines for deployments.
- No tenant-specific configuration.

## Next step
Populate the variant-specific skeletons and keep token flow correctness as the primary gate.
