from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.telemetry.validate_m8_kql_contract import run_checks as run_kql_checks  # noqa: E402


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def test_m8_workflow_identity_separation_placeholders() -> None:
    deploy = _read(ROOT / ".github" / "workflows" / "m8-deploy-live.yml")
    start_resume = _read(ROOT / ".github" / "workflows" / "m8-start-resume.yml")
    shutdown = _read(ROOT / ".github" / "workflows" / "m8-nightly-shutdown.yml")

    assert "secrets.AZURE_CLIENT_ID_DEPLOY" in deploy
    assert "secrets.AZURE_CLIENT_ID_SHUTDOWN" in start_resume
    assert "secrets.AZURE_CLIENT_ID_SHUTDOWN" in shutdown

    assert "AZURE_CLIENT_ID_DEPLOY" not in start_resume
    assert "AZURE_CLIENT_ID_SMOKE" not in start_resume
    assert "AZURE_CLIENT_ID_DEPLOY" not in shutdown
    assert "AZURE_CLIENT_ID_SMOKE" not in shutdown


def test_shutdown_workflow_blocks_broad_mutation_commands() -> None:
    shutdown = _read(ROOT / ".github" / "workflows" / "m8-nightly-shutdown.yml")
    forbidden = [
        r"\bterraform\s+(?:-[^\s]+\s+)*(?:apply|destroy)\b",
        r"\baz\s+deployment\s+\w+\s+(?:create|what-if|validate)\b",
        r"\baz\s+group\s+delete\b",
        r"\baz\s+resource\s+delete\b",
        r"\baz\s+containerapp\s+delete\b",
    ]
    for pattern in forbidden:
        assert re.search(pattern, shutdown, re.IGNORECASE) is None


def test_start_resume_workflow_has_dry_run_guardrails() -> None:
    start_resume = _read(ROOT / ".github" / "workflows" / "m8-start-resume.yml")

    assert "dry_run:" in start_resume
    assert "default: true" in start_resume
    assert 'if [[ "${{ inputs.dry_run }}" == "true" ]]' in start_resume
    assert "would_start" in start_resume
    assert "inputs.run_readiness_probe && !inputs.dry_run" in start_resume


def test_lifecycle_workflows_checkout_before_repo_scripts() -> None:
    for workflow_name in ("m8-start-resume.yml", "m8-nightly-shutdown.yml"):
        workflow = _read(ROOT / ".github" / "workflows" / workflow_name)
        checkout_index = workflow.index("uses: actions/checkout@v4")
        preflight_index = workflow.index("python tools/ci/m9_live_preflight.py")
        assert checkout_index < preflight_index


def test_m8_kql_contract_files_have_required_coverage() -> None:
    offenders = run_kql_checks()
    assert offenders == [], "KQL contract offenders found:\n" + "\n".join(offenders)


def test_m8_negative_kql_contract_blocks_extended_pii_claim_keys() -> None:
    negative = _read(ROOT / "tools" / "telemetry" / "kql" / "m8-negative-leakage.kql")
    for forbidden_claim_key in ('"name"', '"given_name"', '"family_name"'):
        assert forbidden_claim_key in negative


def test_deploy_smoke_stage_runs_local_contract_validation() -> None:
    deploy = _read(ROOT / ".github" / "workflows" / "m8-deploy-live.yml")
    assert (
        "validate_m8_kql_contract.py" in deploy
        or "./.github/workflows/m8-smoke-trace.yml" in deploy
    )


def test_deploy_workflow_bootstrap_handoff_exports_and_validates_runtime_vars() -> None:
    deploy = _read(ROOT / ".github" / "workflows" / "m8-deploy-live.yml")
    assert 'source "artifacts/m9-entra-bootstrap.env"' in deploy
    assert "--context deploy-bootstrap-handoff" in deploy
    for required_name in (
        "BFF_AUDIENCE",
        "AGENT_EXECUTION_AUDIENCE",
        "MCP_AUDIENCE",
        "BLUEPRINT_AUDIENCE",
        "BFF_SCOPE_MCP_ACCESS",
        "AGENT_SCOPE_MCP_ACCESS",
        "AGENT_SCOPE_MCP_WRITE",
        "MCP_SCOPE_MCP_ACCESS",
        "MCP_SCOPE_MCP_WRITE",
        "BFF_OBO_CLIENT_ID",
        "AGENT_OBO_CLIENT_ID",
    ):
        assert required_name in deploy


def test_smoke_workflow_requires_playwright_protected_inputs() -> None:
    smoke = _read(ROOT / ".github" / "workflows" / "m8-smoke-trace.yml")
    assert "M9_PLAYWRIGHT_CHAT_URL" in smoke
    assert "M9_PLAYWRIGHT_ACCESS_TOKEN" in smoke
    assert "browser_transport" in smoke
    assert "M9_BROWSER_TRANSPORT" in smoke
    assert "agent-browser" in smoke
    assert "manual-artifact" in smoke
    assert "M9_AGENT_BROWSER_COMMAND" in smoke
    assert "M9_BROWSER_EVIDENCE_JSON" in smoke
    assert "python -m playwright install chromium" in smoke
    assert "python tools/ci/m8_browser_smoke_harness.py --mode live" in smoke


def test_agent_browser_risk_acceptance_controls_are_documented() -> None:
    security = _read(ROOT / "SECURITY.md").lower()
    playwright = _read(ROOT / "docs" / "testing" / "playwright.md").lower()
    required_phrases = (
        "protected, manually invoked workflows",
        "mfa remains manual-only",
        "do not save, upload, or commit browser storage state",
        "no tokens, cookies, storage-state, trace ids, claims, pii, endpoints",
    )
    combined = f"{security}\n{playwright}"
    for phrase in required_phrases:
        assert phrase in combined
