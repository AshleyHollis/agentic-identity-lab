# Next.js SPA (Placeholder)

This folder is a minimal placeholder for a Next.js-based public-client SPA comparison. It does not include a functional auth implementation.

## Intended flow

- Acquire access tokens via an approved public-client library.
- Call the BFF with `Authorization: Bearer <token>`.
- Use `userId` only as a display hint; identity comes from validated tokens.

See `config/env/spa.env.example` for placeholder configuration values.
