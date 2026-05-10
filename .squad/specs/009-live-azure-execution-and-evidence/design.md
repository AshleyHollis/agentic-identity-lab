# Design — Spec 009

## Architecture under test

```text
Browser smoke client
  -> Azure API Management
  -> BFF Container App
  -> Agent Execution Service Container App
  -> MCP Protected API Container App
  -> Application Insights / Log Analytics
```

ACA remains the M9 live target. AKS Agent Gateway / `agentgateway.dev` remains out of scope unless a later ADR adds it as an optional proxy concern.

## Workflow execution order

1. Run offline validation: `python tools\ci\public_safe_validation.py`, `python tools\telemetry\validate_m8_kql_contract.py`, static browser harness, and smoke-trace contract validation.
2. Dispatch `.github\workflows\m8-live-oidc-contract.yml` for zero-mutation OIDC checks.
3. Dispatch `.github\workflows\m8-deploy-live.yml` first with mutation toggles disabled, then with approved mutation scope.
4. Dispatch `.github\workflows\m8-start-resume.yml` if needed.
5. Dispatch `.github\workflows\m8-smoke-trace.yml` with `LIVE_AZURE_TESTS=true` and protected live checks enabled.
6. Run positive and negative KQL contracts.
7. Produce redacted evidence summary.
8. Verify `.github\workflows\m8-nightly-shutdown.yml` or an approved manual ops shutdown.

## Evidence model

Allowed public evidence:

- Workflow names and pass/fail states.
- Redacted run IDs or opaque evidence IDs.
- Non-secret correlation IDs.
- KQL row counts and role-coverage summaries.
- Statements that endpoint/account values were suppressed.

Forbidden public evidence:

- Tenant IDs, subscription IDs, app/client/object IDs.
- Endpoint URLs, hostnames, APIM URLs, callback URLs.
- Tokens, Authorization/Cookie headers, auth codes, certificates, secrets.
- Raw screenshots, HAR files, console logs, or KQL rows with sensitive values.
- PII claim keys/values: `oid`, `sub`, `email`, `upn`, `preferred_username`, `name`, `given_name`, `family_name`.
- Raw or user/token-bearing `tracestate`.

## ADR-M9-01 — Reuse the M8 protected workflow family

**Decision:** M9 executes the M8 protected workflow family instead of creating a second live topology.

**Rationale:** M8 already established protected OIDC, deploy, start/resume, shutdown, smoke, and KQL scaffolds. Reuse reduces drift and focuses review on readiness/evidence.

**Status:** Accepted for M9 planning.

## ADR-M9-02 — Redacted evidence only

**Decision:** Repo-tracked evidence must be redacted summaries only; raw live artifacts remain protected.

**Rationale:** The repository is public and live evidence can contain endpoints, account metadata, tokens, or PII if mishandled.

**Status:** Accepted for M9 planning.

## ADR-M9-03 — Cost controls are closeout gates

**Decision:** M9 cannot close until shutdown/scale-down is verified and residual-cost resources are documented.

**Rationale:** Live Azure proof creates real cost exposure.

**Status:** Accepted for M9 planning.

## ADR-M9-04 — Reviewer gates before live success claims

**Decision:** Tank deployment readiness, Trinity security/evidence acceptance, and Morpheus architecture closeout are required before M9 claims live success.

**Rationale:** Live verification crosses infrastructure, identity, telemetry safety, public workflow safety, and cost controls.

**Status:** Accepted for M9 planning.
