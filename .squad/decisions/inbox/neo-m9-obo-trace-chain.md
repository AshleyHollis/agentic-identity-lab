# Neo M9 OBO Trace Chain — Redacted Implementation Evidence

## Status
- **Pass (code + tests):** Implemented delegated chain wiring for `POST /chat/session` to exercise **BFF -> Agent Execution -> MCP** when enabled.
- **Blocker (live proof still required):** Protected live smoke/trace run must be executed to collect fresh Azure Monitor evidence from delegated browser traffic.

## Implemented backend path
- BFF `POST /chat/session` now invokes Agent Execution `POST /agent/invoke` when `CHAT_SESSION_CHAIN_ENABLED=true`.
- Agent Execution invoke endpoints now call MCP `POST /tools/authorization-check` with OBO authorization when `MCP_CHAIN_ENABLED=true`.
- Authorization forwarding remains strict boundary-safe:
  - BFF forwards inbound delegated bearer to Agent only.
  - Agent performs OBO exchange and forwards OBO authorization to MCP.
  - No raw token/PII values are logged or returned by new logic.

## Config wiring added
- BFF:
  - `CHAT_SESSION_CHAIN_ENABLED`
  - `AGENT_EXECUTION_BASE_URL`
  - `AGENT_EXECUTION_INVOKE_PATH`
  - `DOWNSTREAM_TIMEOUT_SECONDS`
- Agent Execution:
  - `MCP_CHAIN_ENABLED`
  - `MCP_PROTECTED_API_BASE_URL`
  - `MCP_AUTHORIZATION_CHECK_PATH`
  - `DOWNSTREAM_TIMEOUT_SECONDS`
- Terraform live env now sets chain-enabled vars and downstream service URLs for BFF/Agent container apps.

## Telemetry/trace contract updates
- Added dependency-hop execution spans around BFF->Agent and Agent->MCP calls.
- Continued propagation of `traceparent` and correlation header across hops.
- Updated smoke trace evaluator (`tools\ci\m8_smoke_trace_contract.py`) to support `--required-operation`.
- Protected smoke workflow now enforces operation evidence for:
  - `/chat/session`
  - `/agent/invoke`
  - `/tools/authorization-check`

## Validation executed (local, redacted)
- `python -m pytest -q tests\security\test_m9_chain_flow.py tests\security\test_m8_smoke_trace_contract.py tests\security\test_bff_chat_session.py tests\security\test_agent_gateway_auth.py tests\integration\python\test_agent_gateway_obo_success_to_mcp.py`
  - Result: **pass**
- `python -m pytest -q`
  - Result: **pass** (`285 passed`)

## Next live run required (protected)
1. Dispatch `.github\workflows\m8-smoke-trace.yml` with:
   - `live_azure_tests=true`
   - `run_live_azure_checks=true`
2. Confirm browser smoke target points to BFF `/chat/session` protected URL and delegated token source is configured.
3. Verify `tools\ci\m8_smoke_trace_contract.py evaluate` passes with required roles **and required operations**.
4. Capture only redacted outputs: pass/fail, role coverage, operation coverage, row counts.
