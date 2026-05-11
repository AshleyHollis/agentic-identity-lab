# Tank M9 Live Smoke/Trace Evidence

**Spec:** 009-live-azure-execution-and-evidence  
**Tasks:** T08-T11  
**Verdict:** Complete; T12 evidence packaging in progress  

## Redacted evidence

- Protected smoke workflow run `25644428588` succeeded from commit `8622eff`.
- The run passed protected environment approval, OIDC login with the smoke identity, static browser-smoke wiring checks, static KQL contract checks, live readiness telemetry generation, Azure Monitor positive trace verification, and negative leakage verification.
- Positive trace verification observed the expected deployed service roles: BFF, Agent Execution Service, and MCP Protected API.
- Negative leakage verification returned zero forbidden token/PII hits for the checked live telemetry/log surfaces.
- Agent Execution and MCP were restored to internal ingress and scale-to-zero after the protected smoke window.

## Remediations completed during T08-T11

- Enabled live smoke KQL to query Azure Monitor `AppRequests`/`AppDependencies`/`AppTraces` schemas used by the deployed Application Insights resource.
- Added deployed-role overrides to the trace evaluator while preserving static-contract defaults.
- Granted the protected smoke identity the Container Apps Contributor role at the lab resource-group scope so it can temporarily scale/probe internal apps during the protected smoke window.
- Replaced `az containerapp exec` probes because hosted GitHub runners do not provide the TTY required by the Azure CLI exec path.
- Hardened smoke cleanup so internal apps are restored even when the main live smoke step fails.

## Public-safety notes

No tenant IDs, subscription IDs, live endpoints, connection strings, access tokens, or raw KQL result payloads are included in this artifact.
