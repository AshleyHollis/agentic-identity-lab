# Target State

## Outcome
Provide a set of repeatable identity reference flows (variants A–F) with clear documentation, diagrams, and ADRs.

## Capabilities
- Correct user-delegated token handling across APIM and BFF layers.
- OBO flows for downstream API calls.
- Separate app-only service identity paths.
- Agent framework integration without identity shortcuts.
- Optional AKS track validating Microsoft Entra Agent ID auth for agent/MCP workloads.

## Deliverables
- Minimal runnable samples per variant (future).
- Terraform layout for consistent Azure deployments.
- Shared testing guidance for token/audience validation.

## Success criteria
- Each variant clearly shows token audiences and OBO boundaries.
- No secrets or tenant-specific data in the repo.
- Docs guide new contributors without tribal knowledge.
