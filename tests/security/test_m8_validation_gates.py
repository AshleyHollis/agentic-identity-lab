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
