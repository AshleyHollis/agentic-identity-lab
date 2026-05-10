# Goals — Spec 009

## Primary goal

Prove the lab works live in Azure by executing protected workflows and collecting redacted evidence for browser -> APIM -> BFF -> Agent Execution Service -> MCP Protected API with Azure Monitor / Application Insights traces.

## Done criteria

- Protected deploy succeeds for ACA + APIM.
- Browser smoke succeeds with real delegated Entra sign-in from an approved client path.
- Identity boundaries are proven live: APIM validates, BFF validates but does not OBO, Agent Execution Service performs MCP OBO, MCP rejects the original user token.
- Positive KQL proves the correlated chain across required roles.
- Negative KQL returns zero leakage rows.
- Redacted evidence is reviewed and safe for public summary.
- Shutdown/scale-down is verified and residual-cost resources are documented.

## Non-goals

- No live Azure work in public CI.
- No committed or printed real IDs, endpoints, tokens, secrets, certificates, generated configs, screenshots with sensitive values, or `.env` contents.
- No ACA-to-AKS migration.
- No new identity architecture without Trinity review.
- No live success claim before reviewer gates.
