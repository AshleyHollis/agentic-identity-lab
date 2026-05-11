# Tank M9 Cost Shutdown Evidence

**Spec:** 009-live-azure-execution-and-evidence  
**Task:** T13  
**Verdict:** Complete  

## Redacted evidence

- Protected nightly shutdown workflow run `25644655120` succeeded.
- The lifecycle identity passed OIDC login and executed the ACA scale-down path.
- Post-run verification confirmed all three Container Apps are configured with `minReplicas=0`.
- Agent Execution and MCP were verified with internal ingress after the smoke window.
- APIM, Log Analytics, and Application Insights remain running by design; the workflow records them as non-destructive/manual-review cost posture rather than attempting unsupported destructive stop operations.

## Remediation completed during T13

- The lifecycle identity needed Container Apps write permission for the scale-down operation. The lab resource-group scoped Container Apps Contributor role was granted to the lifecycle service principal.

## Public-safety notes

No tenant IDs, subscription IDs, live endpoints, principal object IDs, tokens, or raw resource payloads are included in this artifact.
