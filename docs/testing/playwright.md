# Playwright Guidance

## Scope
Use Playwright only for **UI flows** that do not expose tokens. Ashley has accepted the residual risk of agent-browser style E2E checks for Spec 009, but that acceptance does not remove the controls below.

## Safety Rules
- Disable console/network logging of Authorization headers.
- Use **mocked** identity where possible.
- Never record or persist access tokens.
- Agent-browser/manual-state flows are **local by default**. CI use is limited to protected, manually invoked workflows with environment approval; never run them on public push or pull-request triggers.
- MFA may remain human/manual-only. Do not script MFA bypasses or publish MFA state.
- Use ephemeral browser contexts. Do not save storage state, cookies, localStorage, sessionStorage, IndexedDB, HAR, Playwright traces, screenshots, videos, raw claims, endpoints, usernames, or token-bearing logs.
- If a manual browser profile or state file is unavoidable for local diagnosis, store it outside git, keep it machine-local, delete it after the run, and never attach it to issues, PRs, or workflow artifacts.
- Uploaded evidence must be boolean/count/status-only and redacted; no tokens, cookies, storage-state, trace IDs, claims, PII, endpoints, or tenant-specific identifiers.

## Review Checklist
- Public CI cannot execute live identity browser automation.
- Protected live workflows require explicit opt-in, GitHub environment approval, and short artifact retention.
- Harnesses never call `storageState()` or upload browser profiles.
- Logs and artifacts contain only sanitized pass/fail evidence.
- Azure OpenAI / Foundry service authentication remains separate from MCP delegated user access.

## Manual artifact transport (redacted)
Use this when MFA/manual browser interaction is required and direct Playwright token automation is not available.

1. Run the manual browser/session check outside CI.
2. Capture only boolean/status evidence into `docs/testing/m9-browser-manual-evidence-template.json` shape.
3. Ensure values contain no token, cookie, endpoint, tenant, claim, username, or raw trace data.
4. Point `M9_BROWSER_EVIDENCE_JSON` to the redacted JSON and use `M9_BROWSER_TRANSPORT=manual-artifact`.
