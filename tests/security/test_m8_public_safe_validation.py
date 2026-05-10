from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.ci.public_safe_validation import _scan_workflow_runtime_exposure, run_all_checks  # noqa: E402


def test_public_safe_validation_policy_is_clean() -> None:
    offenders = run_all_checks()
    assert offenders == [], "Public-safe validation offenders found:\n" + "\n".join(offenders)


def test_runtime_exposure_scan_flags_az_account_show_log_output(tmp_path: Path) -> None:
    workflow = tmp_path / "m8-live-oidc-contract.yml"
    workflow.write_text(
        """
name: test
jobs:
  contract:
    steps:
      - run: az account show --output table
""".strip(),
        encoding="utf-8",
    )

    offenders = _scan_workflow_runtime_exposure(workflow, workflow.read_text(encoding="utf-8"))

    assert any("az account show must not emit account metadata to logs" in offender for offender in offenders)


def test_runtime_exposure_scan_allows_non_logging_azure_check(tmp_path: Path) -> None:
    workflow = tmp_path / "m8-live-oidc-contract.yml"
    workflow.write_text(
        """
name: test
jobs:
  contract:
    steps:
      - run: az account show --output none
""".strip(),
        encoding="utf-8",
    )

    offenders = _scan_workflow_runtime_exposure(workflow, workflow.read_text(encoding="utf-8"))

    assert offenders == []


def test_runtime_exposure_scan_flags_endpoint_variable_in_summary(tmp_path: Path) -> None:
    workflow = tmp_path / "m8-start-resume.yml"
    workflow.write_text(
        """
name: test
jobs:
  resume:
    steps:
      - run: echo "Readiness probe passed for ${M8_READINESS_URL}" >> "$GITHUB_STEP_SUMMARY"
""".strip(),
        encoding="utf-8",
    )

    offenders = _scan_workflow_runtime_exposure(workflow, workflow.read_text(encoding="utf-8"))

    assert any("workflow output must not print live endpoint variable 'M8_READINESS_URL'" in offender for offender in offenders)


def test_runtime_exposure_scan_allows_safe_summary_wording(tmp_path: Path) -> None:
    workflow = tmp_path / "m8-start-resume.yml"
    workflow.write_text(
        """
name: test
jobs:
  resume:
    steps:
      - run: echo "Readiness probe passed." >> "$GITHUB_STEP_SUMMARY"
""".strip(),
        encoding="utf-8",
    )

    offenders = _scan_workflow_runtime_exposure(workflow, workflow.read_text(encoding="utf-8"))

    assert offenders == []
