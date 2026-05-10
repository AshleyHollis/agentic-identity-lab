# ADR 0003: Container Apps Default

## Status
Accepted

## Context
The lab needs a deployment default for BFF/API workloads that supports identity integration and scaling.

## Decision
Use Azure Container Apps as the default hosting target for BFF and API services unless a variant requires a different hosting model.

## Consequences
- Consistent baseline for infrastructure and networking.
- Variants can override when required (e.g., SharePoint-hosted constraints).
