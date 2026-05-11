from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.ci.m8_browser_smoke_harness import validate_browser_smoke_wiring  # noqa: E402
from tools.ci.m8_smoke_trace_contract import (  # noqa: E402
    evaluate_trace_results,
    validate_smoke_trace_scaffold,
)
from tools.ci.m8_browser_smoke_harness import validate_live_inputs  # noqa: E402


def test_m8_browser_smoke_harness_wiring_is_clean() -> None:
    offenders = validate_browser_smoke_wiring(ROOT)
    assert offenders == [], "M8 browser smoke harness wiring offenders found:\n" + "\n".join(offenders)


def test_m8_browser_smoke_harness_live_input_contract_requires_protected_inputs() -> None:
    offenders = validate_live_inputs(env={})
    assert any("M9_PLAYWRIGHT_CHAT_URL" in offender for offender in offenders)
    assert any("M9_PLAYWRIGHT_ACCESS_TOKEN" in offender for offender in offenders)


def test_m8_browser_smoke_harness_live_input_contract_accepts_protected_values() -> None:
    offenders = validate_live_inputs(
        env={
            "M9_PLAYWRIGHT_CHAT_URL": "https://contoso.example.com/chat/session",
            "M9_PLAYWRIGHT_ACCESS_TOKEN": "redacted-protected-token",
            "M9_PLAYWRIGHT_EXPECTED_STATUS": "200",
            "M9_PLAYWRIGHT_TIMEOUT_SECONDS": "30",
        }
    )
    assert offenders == []


def test_m8_browser_smoke_harness_live_input_contract_rejects_placeholder_values() -> None:
    offenders = validate_live_inputs(
        env={
            "M9_PLAYWRIGHT_CHAT_URL": "https://{placeholder}/chat/session",
            "M9_PLAYWRIGHT_ACCESS_TOKEN": "<token-placeholder>",
            "M9_PLAYWRIGHT_EXPECTED_STATUS": "ok",
            "M9_PLAYWRIGHT_TIMEOUT_SECONDS": "0",
        }
    )
    assert any("M9_PLAYWRIGHT_CHAT_URL" in offender for offender in offenders)
    assert any("M9_PLAYWRIGHT_ACCESS_TOKEN" in offender for offender in offenders)
    assert any("M9_PLAYWRIGHT_EXPECTED_STATUS" in offender for offender in offenders)
    assert any("M9_PLAYWRIGHT_TIMEOUT_SECONDS" in offender for offender in offenders)


def test_m8_trace_contract_static_scaffold_is_clean() -> None:
    workflow_text = (ROOT / ".github" / "workflows" / "m8-smoke-trace.yml").read_text(
        encoding="utf-8"
    )
    positive_kql = (ROOT / "tools" / "telemetry" / "kql" / "m8-positive-chain.kql").read_text(
        encoding="utf-8"
    )
    negative_kql = (ROOT / "tools" / "telemetry" / "kql" / "m8-negative-leakage.kql").read_text(
        encoding="utf-8"
    )
    offenders = validate_smoke_trace_scaffold(workflow_text, positive_kql, negative_kql)
    assert offenders == [], "M8 smoke+trace scaffold offenders found:\n" + "\n".join(offenders)


def test_m8_trace_contract_evaluation_flags_missing_roles_and_leakage() -> None:
    offenders = evaluate_trace_results(
        positive_rows=[{"cloud_RoleName": "apim"}],
        negative_rows=[{"signal": "logs"}],
    )
    assert offenders
    assert any("missing required roles" in offender for offender in offenders)
    assert any("negative leakage query returned 1 rows" == offender for offender in offenders)


def test_m8_trace_contract_evaluation_passes_with_full_chain_and_no_leakage() -> None:
    offenders = evaluate_trace_results(
        positive_rows=[
            {"cloud_RoleName": "apim"},
            {"cloud_RoleName": "bff"},
            {"cloud_RoleName": "agent-execution"},
            {"cloud_RoleName": "mcp-protected-api"},
        ],
        negative_rows=[],
    )
    assert offenders == []


def test_m8_trace_contract_evaluation_flags_missing_required_operations() -> None:
    offenders = evaluate_trace_results(
        positive_rows=[
            {"cloud_RoleName": "apim", "name": "GET /readyz"},
            {"cloud_RoleName": "bff", "name": "POST /chat/session"},
            {"cloud_RoleName": "agent-execution", "name": "POST /agent/invoke"},
            {"cloud_RoleName": "mcp-protected-api", "name": "GET /whoami"},
        ],
        negative_rows=[],
        required_operations=(
            "/chat/session",
            "/agent/invoke",
            "/tools/authorization-check",
        ),
    )
    assert any("missing required operations" in offender for offender in offenders)
