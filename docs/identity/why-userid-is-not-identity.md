# Why `userId` Is Not Identity

## The Problem
Headers like `userId` or `x-user-id` are **client-controlled**. They provide **no cryptographic proof**.

## The Fix
Use **validated access tokens** to prove identity:
- Verify signature, issuer, audience, and expiry.
- Enforce required scopes or roles.

## Guidance
- Treat `userId` as **display-only metadata** at best.
- **Never authorize** access based solely on a userId header.
