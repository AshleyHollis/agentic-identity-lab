# Warning: Managed Identity Token Replacement

Using `authentication-managed-identity` on inbound requests **replaces** the caller’s token.

## Why This Is Dangerous
- You lose **user context** and delegated access checks.
- Downstream services see **only APIM identity**, not the user.
- It breaks the OBO boundary by bypassing delegated scopes.

## Safe Alternative
- Validate the **user token** at ingress.
- Perform **OBO** to get a downstream token that preserves user identity.
- Forward the OBO token using `x-obo-authorization` (then set `Authorization` downstream).

## Rule of Thumb
Managed identity is for **service-to-service** calls, not user-delegated flows.

## Reference Anti-Pattern
See `infra/terraform/policies/apim/broken-managed-identity-replacement.xml` for an intentionally broken example.

## Repository validation
Static coverage in `tests/integration/python/test_apim_managed_identity_replacement_breaks_delegation.py` keeps this warning tied to the anti-pattern XML.
