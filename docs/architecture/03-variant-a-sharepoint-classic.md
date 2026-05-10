# Variant A — SharePoint Classic

## Summary
Legacy SharePoint pages call APIs through APIM with user-delegated tokens. This variant validates that classic SharePoint can still participate in correct OBO flows.

## Identity flow
- User authenticates via Entra ID.
- SharePoint page calls APIM with delegated user token.
- APIM validates and forwards the token to the BFF/API.
- BFF uses OBO when calling downstream APIs.

## When to use
- Existing classic SharePoint estates needing validated API access.

## Risks / limitations
- Limited modernization options in classic pages.
- Token handling must be explicit to avoid silent delegation loss.

## Implementation notes (TODO)
- Add client-side token acquisition guidance.
- Add classic page integration sample.

## Diagram
See `diagrams/mermaid/variant-a-sharepoint-classic.mmd`.
