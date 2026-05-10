# Classic Loader Script (Placeholder)

`chat-loader.js` is a lightweight script intended for classic SharePoint pages. It creates a container and shows a status message while you wire up token acquisition and the BFF session call.

## Usage

1. Host `chat-loader.js` in SharePoint (Site Assets or CDN).
2. Reference it from a classic page with data attributes:

```html
<div id="identity-chat-root"></div>
<script
  src="/SiteAssets/identity-chat/chat-loader.js"
  data-bff-base-url="https://YOUR_BFF_DOMAIN"
  data-chat-path="/chat/session"
  data-user-id="USER_DISPLAY_HINT"
  data-theme="light"
  data-container-id="identity-chat-root"
></script>
```

## Token provider hook

The loader looks for an optional global provider:

```js
window.IdentityChatLoader = {
  getAccessToken: async () => {
    // TODO: Acquire an access token (do not embed secrets or tokens in the page).
    return null;
  },
};
```

If no token provider is configured, the loader renders a safe placeholder message.

## Identity reminder

`userId` is treated as a **display hint only**. The BFF must determine identity from validated access tokens, not from the request body.
