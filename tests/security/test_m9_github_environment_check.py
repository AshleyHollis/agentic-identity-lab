from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.ci.m9_github_environment_check import (  # noqa: E402
    _CONTRACT_PROFILES,
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


def test_smoke_runtime_profile_flags_missing_live_smoke_variables() -> None:
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
        variables_by_environment={"lab-live-azure-smoke": {"LIVE_APIM_BASE_URL"}},
    )

    missing_vars = result["missing_required_variables"]["lab-live-azure-smoke"]
    assert "LIVE_SMOKE_SCOPES" in missing_vars
    assert "LIVE_BFF_AUDIENCE" in missing_vars
    assert "LIVE_APIM_BASE_URL" not in missing_vars
