from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.ci.m9_github_environment_check import (  # noqa: E402
    _CONTRACT_PROFILES,
    _fetch_environment_metadata_names,
    _fetch_environment_names,
    evaluate_contract,
)


def test_zero_mutation_profile_requires_identity_secrets_but_not_runtime_variables() -> None:
    profile = _CONTRACT_PROFILES["zero-mutation"]
    existing = {
        "lab-live-azure-deploy",
        "lab-live-azure-smoke",
        "lab-live-azure-ops",
    }
    secrets = {
        "lab-live-azure-deploy": {
            "AZURE_CLIENT_ID_DEPLOY",
            "AZURE_TENANT_ID",
            "AZURE_SUBSCRIPTION_ID",
        },
        "lab-live-azure-smoke": {
            "AZURE_CLIENT_ID_SMOKE",
            "AZURE_TENANT_ID",
            "AZURE_SUBSCRIPTION_ID",
        },
        "lab-live-azure-ops": {
            "AZURE_CLIENT_ID_SHUTDOWN",
            "AZURE_TENANT_ID",
            "AZURE_SUBSCRIPTION_ID",
        },
    }
    variables = {
        "lab-live-azure-deploy": set(),
        "lab-live-azure-smoke": set(),
        "lab-live-azure-ops": set(),
    }

    result = evaluate_contract(
        profile=profile,
        existing_environments=existing,
        secrets_by_environment=secrets,
        variables_by_environment=variables,
    )

    assert result["missing_required_secrets"] == {}
    assert result["missing_required_variables"] == {}
    assert "lab-live-azure-smoke" in result["missing_optional_variables"]


def test_smoke_runtime_profile_requires_transport_and_resource_group_variables() -> None:
    profile = _CONTRACT_PROFILES["smoke-runtime"]
    existing = {"lab-live-azure-smoke"}
    secrets = {
        "lab-live-azure-smoke": {
            "AZURE_CLIENT_ID_SMOKE",
            "AZURE_TENANT_ID",
            "AZURE_SUBSCRIPTION_ID",
        }
    }

    result = evaluate_contract(
        profile=profile,
        existing_environments=existing,
        secrets_by_environment=secrets,
        variables_by_environment={"lab-live-azure-smoke": {"AZURE_RESOURCE_GROUP"}},
    )

    missing_vars = result["missing_required_variables"]["lab-live-azure-smoke"]
    assert "M9_BROWSER_TRANSPORT" in missing_vars
    assert "AZURE_RESOURCE_GROUP" not in missing_vars


def test_fetch_environment_names_uses_paginate() -> None:
    with patch("tools.ci.m9_github_environment_check.subprocess.run") as run:
        run.return_value.returncode = 0
        run.return_value.stdout = "lab-live-azure-smoke\n"
        run.return_value.stderr = ""
        result = _fetch_environment_names("AshleyHollis/agentic-identity-lab")

    assert result == {"lab-live-azure-smoke"}
    command = run.call_args.args[0]
    assert "--paginate" in command


def test_fetch_environment_metadata_names_uses_paginate() -> None:
    with patch("tools.ci.m9_github_environment_check.subprocess.run") as run:
        run.return_value.returncode = 0
        run.return_value.stdout = "LIVE_APIM_BASE_URL\n"
        run.return_value.stderr = ""
        result = _fetch_environment_metadata_names(
            "AshleyHollis/agentic-identity-lab", "lab-live-azure-smoke", "variables"
        )

    assert result == {"LIVE_APIM_BASE_URL"}
    command = run.call_args.args[0]
    assert "--paginate" in command
