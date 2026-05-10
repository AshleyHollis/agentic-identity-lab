# Goals: APIM Policy Alignment

**Status:** Complete  
**Milestone:** M3  
**Spec Phase:** discovery  
**Created:** 2026-05-10  
**Updated:** 2026-05-10  
**Impact:** Medium

## Problem
APIM policy examples must stay aligned with the implemented local identity rules: validate delegated user tokens at ingress, validate OBO tokens for MCP at egress, preserve user delegation, and avoid raw token logging. Existing APIM integration tests only inspected JSON fixtures and did not verify policy XML examples.

## Goals
- Ensure ingress policy examples validate `Authorization` bearer tokens, audience, issuer, delegated `scp`, and trusted tenant claims.
- Ensure egress policy examples validate `x-obo-authorization` for the MCP audience before setting downstream `Authorization`.
- Ensure managed identity replacement remains documented as an anti-pattern for delegated flows.
- Add policy-file checks so drift is caught by `python -m pytest`.
- Keep all examples public-safe with placeholder-only GUIDs and tenant placeholders.

## Non-goals
- Deploy APIM.
- Execute APIM policies against Azure.
- Add tenant-specific IDs, secrets, or raw tokens.

