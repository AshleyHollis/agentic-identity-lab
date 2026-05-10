# SPFx Web Part (Placeholder)

The SPFx placeholder documents the intended web part integration without shipping a full scaffolded project yet.

## Intended flow

1. Use SPFx token providers (AAD/MSGraph) to acquire an access token.
2. Call the BFF with `Authorization: Bearer <token>`.
3. Render chat UI inside the web part.

## Identity rules

- `userId` in the request body is **not** identity.
- Identity must be derived from validated access tokens.

## Files

- `apps/spfx-webpart/README.md`
- `apps/spfx-webpart/identity-chat-webpart/README.md`

Coordinate auth boundaries and token acquisition details with Trinity.
