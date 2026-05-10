# Variant F — Cross-Tenant

## Summary
Cross-tenant flows (B2B, multi-tenant apps) while preserving correct token audiences and OBO paths.

## Identity flow
- User authenticates in home tenant.
- Resource tenant validates tokens and enforces audience boundaries.
- OBO used for downstream resource calls in the resource tenant.

## When to use
- Shared services across tenants or organizations.

## Risks / limitations
- Tenant consent and admin policies can block flows.
- Multi-tenant registrations require careful audience scoping.

## Implementation notes (TODO)
- Add tenant consent checklist.
- Define allowed issuer and audience validation rules.

## Diagram
See `diagrams/mermaid/variant-f-cross-tenant.mmd`.
