# Requirements — Spec 009

## Functional

- FR-01: Use the M8 protected workflow family unless an approved ADR changes the topology.
- FR-02: Deploy/update resource group, ACR, ACA environment/apps, APIM, managed identities, App Insights, and Log Analytics.
- FR-03: Run BFF, Agent Execution Service, and MCP Protected API in strict auth mode.
- FR-04: Execute browser or controlled agent-browser smoke with a real delegated Entra token and APIM front-door call; Entra MFA may be completed manually by the human operator.
- FR-05: Preserve the OBO boundary: only Agent Execution Service exchanges for the MCP audience.
- FR-06: Emit a non-secret correlation marker for KQL proof.

## Security

- SR-01: Protected GitHub Environments are mandatory for live deploy, smoke, and lifecycle workflows.
- SR-02: Public CI remains validation-only and never requests live identity or Azure mutation permissions.
- SR-03: Deploy, smoke, and lifecycle OIDC identities are separate or equivalently constrained and documented with placeholders only.
- SR-04: Lifecycle identity cannot deploy, apply, destroy, or delete resources.
- SR-05: APIM validates issuer/audience/scope before forwarding to BFF and must not replace delegated auth with managed identity.
- SR-06: BFF validates inbound user token and must not perform MCP OBO.
- SR-07: MCP Protected API rejects the original user token and accepts only MCP-audience delegated tokens.
- SR-08: Workflow logs, summaries, screenshots, HAR files, traces, KQL exports, and artifacts must not expose secrets, tokens, endpoint/account metadata, forbidden PII claims, or raw `tracestate`.
- SR-09: Trinity acceptance is required before any live success claim.
- SR-10: Agent-browser use is an accepted risk only for protected live E2E verification, with ephemeral browser state and no persisted cookies, tokens, storage state, usernames, raw claims, screenshots, HAR files, endpoints, or raw trace/KQL evidence in public artifacts.

## Observability

- OR-01: Positive KQL returns correlated role/operation evidence for APIM, BFF, Agent Execution Service, and MCP where telemetry is available.
- OR-02: Positive evidence covers requests plus at least one dependency/trace signal.
- OR-03: Negative KQL returns zero rows across requests, dependencies, traces, and logs.
- OR-04: KQL result handling reports only pass/fail counts and role coverage when public.

## Cost controls

- CR-01: Manual start/resume is required before smoke if resources are stopped.
- CR-02: Nightly shutdown/scale-down remains enabled before closeout.
- CR-03: ACA apps scale to zero where compatible.
- CR-04: APIM, App Insights, Log Analytics, and ACR residual costs are documented.
- CR-05: Optional teardown is manual-only and never scheduled by default.
