# Variant D — SPA Comparison

## Summary
Side-by-side comparison of SPA-only versus BFF-assisted patterns for delegated identity.

## Identity considerations
- **SPA-only**: tokens in browser, higher risk of leakage.
- **BFF-assisted**: tokens stay server-side, clearer OBO control.

## When to use
- Evaluate security posture and operational tradeoffs.

## Risks / limitations
- SPA-only flows often skip OBO correctness or misuse app-only tokens.

## Implementation notes (TODO)
- Provide parallel SPA/BFF samples.
- Add explicit token storage guidance.

## Diagram
See `diagrams/mermaid/variant-d-spa-comparison.mmd`.
