# Classic Page Loader (Placeholder)

The classic SharePoint loader is a lightweight script that can be hosted in Site Assets and injected into classic pages. It is a **placeholder** for wiring a BFF-backed chat experience.

## Where it lives

- `apps/sharepoint-classic/chat-loader-js/chat-loader.js`
- `apps/sharepoint-classic/sample-aspx-snippets/classic-page-snippet.html`

## Expected flow

1. Page loads the loader script.
2. Loader requests an access token from a provided token hook.
3. Loader calls the BFF to create a chat session.
4. Page renders the chat UI (iframe or web component).

## Identity rules

- `userId` in the request body is **not** identity. It is a display hint only.
- The BFF must validate identity from access tokens.

## Example snippet

```html
<div id="identity-chat-root"></div>
<script
  src="/SiteAssets/identity-chat/chat-loader.js"
  data-bff-base-url="https://YOUR_BFF_DOMAIN"
  data-chat-path="/chat/session"
  data-user-id="USER_DISPLAY_HINT"
></script>
```

## Configuration placeholders

See `config/env/sharepoint-loader.env.example`.
