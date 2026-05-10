# ADR 0002: Terraform Layout

## Status
Accepted

## Context
We need a predictable layout for infrastructure that supports multiple variants and environments.

## Decision
Adopt `infra/` with:
- `infra/modules/` for reusable modules.
- `infra/envs/<env>/` for environment composition.

## Consequences
- Consistent deployments across variants.
- Clear separation between modules and environment wiring.
