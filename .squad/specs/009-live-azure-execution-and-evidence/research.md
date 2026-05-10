# Research — Spec 009

## M8 baseline

M8 closed with protected scaffolds and offline validation gates:

- `.github\workflows\m8-live-oidc-contract.yml`
- `.github\workflows\m8-deploy-live.yml`
- `.github\workflows\m8-start-resume.yml`
- `.github\workflows\m8-nightly-shutdown.yml`
- `.github\workflows\m8-smoke-trace.yml`
- `tools\ci\public_safe_validation.py`
- `tools\ci\m8_browser_smoke_harness.py`
- `tools\ci\m8_smoke_trace_contract.py`
- `tools\telemetry\validate_m8_kql_contract.py`
- `tools\telemetry\kql\m8-positive-chain.kql`
- `tools\telemetry\kql\m8-negative-leakage.kql`
- `docs\deployment\aca\m8-operator-guide.md`

M8 did not execute live Azure deployment or smoke tests.

## Imported readiness findings

### Trinity security gates

- Protected environments are mandatory for deploy, smoke, and ops.
- Public CI must not request OIDC tokens, call `azure/login`, fetch access tokens, call live endpoints, run browser sign-in, or run `terraform apply/destroy`.
- Deploy, smoke, and lifecycle identities must be separate or equivalently constrained.
- All live services must use `AUTH_MODE=strict`.
- Telemetry, logs, screenshots, HAR files, KQL exports, and artifacts must not expose tokens, cookies, endpoint/account metadata, PII claim keys/values, or raw `tracestate`.

### Tank deployment readiness

- Add/use protected-live preflight checks before mutation.
- First safe action is a zero-mutation deploy rehearsal.
- Live mutation must happen one scope at a time after approval.
- Smoke with live checks must hard-fail on leakage.

### Mouse client readiness

- Browser smoke must cover approved client boundary wiring for SPA, SharePoint classic, and SPFx readiness.
- Protected-only browser automation must prove delegated sign-in + BFF `/chat/session` without token/PII logging.
- Artifact hygiene must cover screenshots, HAR, console, and trace outputs.

## Open implementation questions

- Actual region, SKUs, app registration values, endpoint values, and smoke user setup are protected-environment concerns outside the repo.
- APIM stoppability depends on selected tier; do not overclaim cost savings.
- Optional destroy/recreate remains a manual operator decision.
