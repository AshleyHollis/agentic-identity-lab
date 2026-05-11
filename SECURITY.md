# Security Policy

## Purpose
This repository is **educational** and focuses on safe identity guidance. It is **not production-ready** security advice.

## Reporting a Vulnerability
Please use GitHub Security Advisories for responsible disclosure.

## Public Repo Safety Requirements
- **Never commit secrets** (client secrets, certificates, private keys, tokens, or credentials).
- **Never log or expose raw tokens**. Use redaction and safe claim allowlists.
- Use **placeholder GUIDs** for examples (e.g., `00000000-0000-0000-0000-000000000001`).
- Only include example values in `.env.example` or `terraform.tfvars.example`.

## Key Management and Identity
- Store secrets in **Azure Key Vault** (or equivalent) and access via **Managed Identity** where possible.
- Prefer **Managed Identity** for service-to-service authentication.
- Use **GitHub OIDC** for CI/CD deployments instead of long-lived secrets.

## Token Safety
- Do **not** persist or replay access tokens.
- Avoid logging PII claims (name, email, UPN); use a **safe-claims allowlist**.
- Separate **Azure OpenAI / Foundry service auth** from **MCP user-delegated access**.

## Accepted-risk Browser Automation
- Agent-browser or agent-browser-like testing is allowed only under explicit risk acceptance and must not be used from public push or pull-request CI.
- Local runs may use a human-completed MFA session, but MFA remains manual-only; do not automate bypass, recovery, or step-up prompts.
- CI live browser checks must run only from protected, manually invoked workflows with environment approval and short-lived protected inputs.
- Do not save, upload, or commit browser storage state, cookies, HAR files, traces, screenshots, videos, raw claims, endpoints, or token-bearing logs.
- Delete any local browser profile, storage-state, or cookie files immediately after the run; prefer ephemeral contexts that never call `storageState()`.
