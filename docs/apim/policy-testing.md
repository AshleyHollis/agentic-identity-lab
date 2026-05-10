# APIM Policy Testing

## Goals
- Validate **token checks** without live credentials.
- Ensure policies reject wrong audiences, missing scopes, and app-only tokens.

## Recommended Approach
- Use **fixture claims** with placeholder GUIDs.
- Keep tests offline by default; use environment flags for live runs.

## Safety Rules
- Never paste real tokens into tests or logs.
- Keep example values in `tests/fixtures/sample-claims/`.
