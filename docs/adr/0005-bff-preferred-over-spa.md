# ADR 0005: BFF Preferred Over SPA

## Status
Accepted

## Context
SPA-only patterns often expose delegated tokens to the browser and blur OBO boundaries.

## Decision
Prefer a BFF pattern for user-delegated flows. SPA-only is documented for comparison but not the default.

## Consequences
- Better control of token handling and OBO exchange.
- Added operational component (BFF) to maintain.
