# Foundry / OpenAI Auth Notes

Auth integration with Foundry or OpenAI is intentionally deferred. The current services only return safe, sanitized claim metadata and never emit raw tokens.

When adding JWT validation, use the shared guard hooks and keep token processing isolated from response payloads and logs.
