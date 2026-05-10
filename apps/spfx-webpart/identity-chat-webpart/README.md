# Identity Chat Web Part (Placeholder)

This is a documentation-first placeholder for an SPFx web part that will host the Identity Lab chat experience.

## Intended behavior

- Render a small container with status text while loading.
- Acquire an access token using SPFx/AAD utilities.
- Call the BFF to create a session using `Authorization: Bearer <token>`.
- Render an iframe or React component for the chat UI.

## Identity reminder

Any `userId` in the request body is **not** identity. The BFF must validate identity from access tokens.
