# Morpheus M9 Accepted-Risk Agent-Browser Path

**Spec:** 009-live-azure-execution-and-evidence  
**Milestone:** M9  
**Role:** Morpheus / Lead Architect  
**Date:** 2026-05-11  
**Directive source:** Ashley Hollis via Copilot directive note  
**Verdict:** Accepted risk with controls; M9 remains open until real live E2E proof exists.

## Decision

Ashley accepts that Entra MFA does not need to be solved for automation now. MFA may be a manual-only human operator step. Ashley also accepts the risk of using an agent-browser path if it makes full E2E verification easier and better.

M9 acceptance is therefore amended: a protected browser or controlled agent-browser run can satisfy the browser proof if it exercises the real delegated flow through APIM, BFF, Agent Execution Service, and MCP, and if the evidence package is redacted and reviewed.

## Required controls

- Protected GitHub Environment approval for live deploy, smoke, and lifecycle operations.
- Human-operated Entra MFA is allowed; no requirement to bypass or automate MFA.
- Agent-browser state must be ephemeral: no persisted cookies, tokens, storage state, usernames, raw claims, screenshots, HAR files, endpoints, raw traces, or raw KQL rows in public artifacts.
- Public evidence may include only redacted pass/fail status, role coverage/counts, non-secret correlation markers, and suppressed-value statements.
- Positive trace/log proof must cover the full intended path for the same smoke window.
- Negative leakage proof must return zero forbidden token/PII hits for the same smoke window.
- Shutdown or scale-down must be verified after the run.
- Tank, Trinity, and Morpheus review gates remain required before any M9 success claim.

## What does not count as complete

- Readiness-only probes or generated readiness telemetry.
- Static harness validation without a live delegated front-door flow.
- Browser-originated calls that cannot prove the delegated token and APIM-fronted path safely.
- Any evidence package containing IDs, endpoints, tokens, cookies, usernames, raw claims, raw traces, screenshots, HAR files, or raw KQL rows.

## Remaining to close M9

1. Configure protected smoke runtime inputs and an approved test identity without exposing values.
2. Run the browser or controlled agent-browser full flow with manual MFA if needed.
3. Capture a non-secret correlation marker and redacted trace/log proof for APIM, BFF, Agent Execution Service, and MCP where available.
4. Pass negative leakage verification for the same smoke window.
5. Produce the redacted evidence package.
6. Verify shutdown/scale-down after the live run.
7. Obtain Tank deployment readiness, Trinity security/evidence acceptance, and Morpheus architecture closeout.
