# SPFx Web Part (Placeholder)

This folder holds a minimal SPFx placeholder for the Identity Lab. It is **not** a generated SPFx project yet; it documents the intended structure and auth boundaries.

## Contents

- `identity-chat-webpart/` — placeholder web part package.

## Auth boundary

SPFx should obtain access tokens via approved client-side flows (e.g., AAD token provider). The BFF must still validate identity from the access token, **never** from `userId` in a request body.

Coordinate token acquisition details with Trinity before implementing.
