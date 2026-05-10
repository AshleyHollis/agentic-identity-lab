# React + Vite SPA (Placeholder)

This folder is a **comparison placeholder** for a public-client SPA flow. It is not a production-ready auth implementation.

## Intended flow

1. Use a public-client auth library (e.g., MSAL) to acquire an access token.
2. Call the BFF with `Authorization: Bearer <token>`.
3. Treat any `userId` in the request body as a display hint only.

## Configuration

See `config/env/spa.env.example` for placeholder environment variables. Do not store secrets or tenant-specific IDs in this repo.
