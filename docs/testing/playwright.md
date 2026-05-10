# Playwright Guidance

## Scope
Use Playwright only for **UI flows** that do not expose tokens.

## Safety Rules
- Disable console/network logging of Authorization headers.
- Use **mocked** identity where possible.
- Never record or persist access tokens.
