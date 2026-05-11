# Mouse M9 Browser Smoke Unblock (Redacted)

Date: 2026-05-11  
Owner: Mouse (Frontend / SharePoint / TypeScript)

## Objective status

1. Reconcile prior browser-evidence changes: **Complete** (already committed on `main`, working tree was clean).
2. Manual-artifact template + coverage + protected input wiring: **Complete**.
3. `M9_AGENT_BROWSER_COMMAND` preparation path: **Complete** (no repo automation script exists; documented exact non-secret protected setup command).
4. Deploy/smoke execution state: **Blocked on deploy** (latest protected deploy run is failed; static harness/contract checks rerun and passed).
5. Redacted decision artifact: **Complete** (this file).

## Redacted evidence snapshot

- Latest protected deploy run: `25651314772` (failed).
- Latest protected smoke failures tied to missing protected inputs:
  - `25651456852` (`M9_PLAYWRIGHT_ACCESS_TOKEN` missing)
  - `25651495126` (`M9_AGENT_BROWSER_COMMAND` missing)
- Browser evidence template present: `docs/testing/m9-browser-manual-evidence-template.json`.
- Manual artifact safety/contract tests passed in `tests/security/test_m8_smoke_trace_contract.py`.

## Verification executed in this batch (local/static only)

```powershell
python -m pytest -q tests/security/test_m8_smoke_trace_contract.py tests/security/test_m9_github_environment_check.py
python tools/ci/m8_browser_smoke_harness.py --mode static --output-json artifacts\m8-browser-smoke-harness-local.json
python tools/ci/m8_smoke_trace_contract.py validate --workflow-file .github\workflows\m8-smoke-trace.yml --positive-kql tools\telemetry\kql\m8-positive-chain.kql --negative-kql tools\telemetry\kql\m8-negative-leakage.kql
```

Result: **PASS** for all commands above.

## Smoke-ready operator instructions (redacted)

1. Use `browser_transport=manual-artifact` to avoid durable Playwright access token dependency.
2. Dispatch:
   - `gh workflow run m8-smoke-trace.yml --ref main -f environment_slug=agentidlab-live -f live_azure_tests=true -f run_live_azure_checks=true -f browser_transport=manual-artifact -f browser_evidence_json=docs/testing/m9-browser-manual-evidence-template.json -f kql_lookback=30m`
3. If agent-browser path is required, set `M9_AGENT_BROWSER_COMMAND` in `lab-live-azure-smoke` via stdin from a local non-committed file.

## Public-safety confirmation

No tokens, cookies, storage state, tenant/client IDs, endpoints, usernames, raw claims, screenshots, HAR, raw traces, or raw KQL rows were added.
