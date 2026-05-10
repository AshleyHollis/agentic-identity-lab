# Token Acquisition Options (Placeholder)

This repo uses **placeholder** frontend projects to compare token acquisition patterns. None of these examples include production-ready authentication.

## Comparison snapshot

| Surface | Token source | Notes |
| --- | --- | --- |
| Classic loader | External token provider hook | Script waits for a token provider; BFF validates identity. |
| SPFx web part | SPFx/AAD token providers | Recommended for modern SharePoint pages. |
| SPA (public client) | MSAL or similar | Use short-lived access tokens; BFF validates identity. |

## Non-negotiables

- Never embed tenant IDs, client IDs, secrets, or tokens in the repo.
- `userId` in request bodies is a **display hint only**. Identity must come from validated tokens.
- Coordinate auth boundaries with Trinity before implementing real flows.
