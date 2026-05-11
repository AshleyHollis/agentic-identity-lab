# Trinity M9 elevated access review

Verdict: **PASS-WITH-CONTROLS** for M9 deploy/smoke after the guardrails in this change are present.

## Findings

- Protected deploy failed at Entra app bootstrap because the deploy identity lacked Microsoft Graph app-registration capability for app discovery/update.
- OBO client secrets are required only for confidential app OBO exchanges: BFF -> Agent Execution Service and Agent Execution Service -> MCP. They must stay in protected environment secrets or Key Vault, never in repo output.
- The Terraform Container App module previously placed `OBO_CLIENT_SECRET` in plain ACA environment variables. This review moves those values to ACA secret-backed env vars.
- Terraform apply/import output can include live identifiers/endpoints. The workflow now suppresses detailed apply/import output and removes temporary live tfvars/log files.
- The dynamically fetched Terraform storage account key is now masked before being written to the GitHub environment.
- Failed protected run logs were inspected with redacted pattern scans. No JWT/Bearer/GitHub-token signatures were detected; client-secret-like Terraform/apply lines were treated as leakage risk and mitigated going forward by secret-backed env vars plus output suppression.

## Minimum acceptable access

1. Prefer normal GitHub OIDC deploy identity.
2. Minimum Graph grant for bootstrap: application registration read/write capability sufficient to list, create/update, and pre-authorize only the lab app registrations. Avoid broad directory roles where possible.
3. Use elevated/breakglass only if normal OIDC cannot complete the authorized Graph bootstrap.
4. If breakglass is used: retrieve credentials only from Key Vault at runtime, mask immediately, do not echo account metadata, rotate/revoke after use, and record run ID/time/operator in the protected decision trail.
5. Do not upload token-bearing logs, tfvars, browser state, HAR, trace, screenshots, raw KQL rows, raw claims, endpoints, tenant IDs, subscription IDs, client IDs, or object IDs.

## Proceed controls

- Run protected workflows only via manual dispatch and protected environments.
- Keep deploy, smoke, and lifecycle identities separate.
- Grant admin consent only for delegated lab scopes required by the strict chain.
- Confirm smoke evidence remains redacted/digested only.
