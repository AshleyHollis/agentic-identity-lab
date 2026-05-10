# SharePoint Classic Loader (Placeholder)

This folder contains a minimal, public-safe loader for classic SharePoint pages. It is a **placeholder** that shows where to plug in token acquisition and the BFF session call. It does **not** implement real authentication.

## Contents

- `chat-loader-js/` — a standalone loader script that can be hosted in Site Assets.
- `sample-aspx-snippets/` — HTML snippets for classic pages or script editor web parts.

## Important notes

- **Do not treat `userId` in request bodies as identity.** Identity must come from validated access tokens.
- Do not embed tenant IDs, client IDs, secrets, or tokens in pages.
- Coordinate auth boundaries and token acquisition with Trinity.

## Quick start

1. Copy `chat-loader-js/chat-loader.js` to a SharePoint location (e.g., `SiteAssets/identity-chat/`).
2. Use the snippet in `sample-aspx-snippets/classic-page-snippet.html`.
3. Provide a token provider (see `chat-loader-js/README.md`).

For configuration placeholders, see `config/env/sharepoint-loader.env.example`.
