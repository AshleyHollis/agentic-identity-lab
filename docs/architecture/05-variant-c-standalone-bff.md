# Variant C — Standalone BFF

## Summary
A standalone web app with a BFF mediates all API calls, ensuring that user-delegated tokens are never exposed to the browser.

## Identity flow
- User authenticates via Entra ID.
- Web app sends session to BFF.
- BFF exchanges for delegated tokens and calls API A.
- API A performs OBO when calling API B.

## When to use
- Greenfield apps prioritizing security and clean token boundaries.

## Risks / limitations
- BFF adds operational overhead.
- Requires careful session handling.

## Implementation notes (TODO)
- Define BFF routes and token cache strategy.
- Add API A and API B skeletons.

## Diagram
See `diagrams/mermaid/variant-c-standalone-bff.mmd`.
