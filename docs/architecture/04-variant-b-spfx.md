# Variant B — SPFx

## Summary
Modern SharePoint Framework web parts call APIM through a BFF. This validates delegated token flow in SharePoint Online modern experiences.

## Identity flow
- User authenticates via Entra ID.
- SPFx web part obtains delegated user token.
- APIM validates and forwards the token to the BFF.
- BFF performs OBO to reach downstream APIs.

## When to use
- Modern SharePoint sites needing secure API calls.

## Risks / limitations
- Token storage and caching must remain in-memory.
- Avoid SPA-only patterns that leak tokens to the browser.

## Implementation notes (TODO)
- Add SPFx package layout and build steps.
- Add BFF proxy endpoints.

## Diagram
See `diagrams/mermaid/variant-b-spfx.mmd`.
