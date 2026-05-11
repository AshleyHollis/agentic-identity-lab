from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass

DEFAULT_REQUIRED_ENVIRONMENTS = (
    "lab-live-azure-deploy",
    "lab-live-azure-smoke",
    "lab-live-azure-ops",
)


@dataclass(frozen=True)
class ContractProfile:
    required_environments: tuple[str, ...]
    required_secrets: dict[str, tuple[str, ...]]
    required_variables: dict[str, tuple[str, ...]]
    optional_variables: dict[str, tuple[str, ...]]


_ZERO_MUTATION_REQUIRED_SECRETS = {
    "lab-live-azure-deploy": (
        "AZURE_CLIENT_ID_DEPLOY",
        "AZURE_TENANT_ID",
        "AZURE_SUBSCRIPTION_ID",
    ),
    "lab-live-azure-smoke": (
        "AZURE_CLIENT_ID_SMOKE",
        "AZURE_TENANT_ID",
        "AZURE_SUBSCRIPTION_ID",
    ),
    "lab-live-azure-ops": (
        "AZURE_CLIENT_ID_SHUTDOWN",
        "AZURE_TENANT_ID",
        "AZURE_SUBSCRIPTION_ID",
    ),
}

_CONTRACT_PROFILES: dict[str, ContractProfile] = {
    "shells": ContractProfile(
        required_environments=DEFAULT_REQUIRED_ENVIRONMENTS,
        required_secrets={},
        required_variables={},
        optional_variables={},
    ),
    "zero-mutation": ContractProfile(
        required_environments=DEFAULT_REQUIRED_ENVIRONMENTS,
        required_secrets=_ZERO_MUTATION_REQUIRED_SECRETS,
        required_variables={},
        optional_variables={
            "lab-live-azure-ops": (
                "AZURE_RESOURCE_GROUP",
                "ACA_APP_NAMES",
                "APIM_SERVICE_NAME",
                "APIM_STOP_SUPPORTED",
                "M8_READINESS_URL",
            ),
            "lab-live-azure-smoke": (
                "AZURE_RESOURCE_GROUP",
                "M9_BROWSER_TRANSPORT",
                "M9_BROWSER_EVIDENCE_JSON",
                "M9_AGENT_BROWSER_TIMEOUT_SECONDS",
                "M9_PLAYWRIGHT_EXPECTED_STATUS",
                "M9_PLAYWRIGHT_TIMEOUT_SECONDS",
                "M9_PLAYWRIGHT_DISPLAY_NAME",
            ),
        },
    ),
    "lifecycle-runtime": ContractProfile(
        required_environments=("lab-live-azure-ops",),
        required_secrets={
            "lab-live-azure-ops": _ZERO_MUTATION_REQUIRED_SECRETS["lab-live-azure-ops"],
        },
        required_variables={
            "lab-live-azure-ops": ("AZURE_RESOURCE_GROUP", "ACA_APP_NAMES"),
        },
        optional_variables={
            "lab-live-azure-ops": (
                "APIM_RESOURCE_GROUP",
                "APIM_SERVICE_NAME",
                "APIM_STOP_SUPPORTED",
                "M8_READINESS_URL",
            ),
        },
    ),
    "smoke-runtime": ContractProfile(
        required_environments=("lab-live-azure-smoke",),
        required_secrets={
            "lab-live-azure-smoke": _ZERO_MUTATION_REQUIRED_SECRETS["lab-live-azure-smoke"],
        },
        required_variables={
            "lab-live-azure-smoke": (
                "AZURE_RESOURCE_GROUP",
                "M9_BROWSER_TRANSPORT",
                "LIVE_SMOKE_SCOPES",
            ),
        },
        optional_variables={
            "lab-live-azure-smoke": (
                "M9_BROWSER_EVIDENCE_JSON",
                "M9_AGENT_BROWSER_TIMEOUT_SECONDS",
                "M9_PLAYWRIGHT_EXPECTED_STATUS",
                "M9_PLAYWRIGHT_TIMEOUT_SECONDS",
                "M9_PLAYWRIGHT_DISPLAY_NAME",
                "LIVE_APIM_BASE_URL",
                "LIVE_READINESS_URL",
                "LIVE_SMOKE_CLIENT_ID",
                "LIVE_AUTHORITY_HOST",
                "LIVE_SMOKE_SCOPES",
                "LIVE_BFF_AUDIENCE",
                "LIVE_AGENT_EXECUTION_AUDIENCE",
                "LIVE_MCP_AUDIENCE",
            ),
        },
    ),
}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only check for protected GitHub Environment contracts "
            "(names only; no secret or variable values)."
        )
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="Repository in OWNER/REPO format.",
    )
    parser.add_argument(
        "--required",
        nargs="+",
        default=None,
        help="Additional required environment names (optional).",
    )
    parser.add_argument(
        "--mode",
        choices=tuple(_CONTRACT_PROFILES.keys()),
        default="shells",
        help=(
            "Validation profile: shells (env shells only), zero-mutation "
            "(m8-live-oidc-contract + m8-deploy-live with all mutation toggles false), "
            "lifecycle-runtime (start/resume + nightly shutdown), "
            "smoke-runtime (protected live smoke placeholders)."
        ),
    )
    return parser


def _fetch_environment_names(repo: str) -> set[str]:
    cmd = [
        "gh",
        "api",
        f"repos/{repo}/environments",
        "--paginate",
        "--jq",
        ".environments[].name",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        stderr = proc.stderr.strip() or "gh api call failed"
        raise RuntimeError(f"Unable to query GitHub environments for {repo}: {stderr}")
    names = {line.strip() for line in proc.stdout.splitlines() if line.strip()}
    return names


def _fetch_environment_metadata_names(repo: str, environment: str, metadata: str) -> set[str]:
    if metadata not in {"secrets", "variables"}:
        raise ValueError(f"Unsupported metadata kind: {metadata}")
    cmd = [
        "gh",
        "api",
        f"repos/{repo}/environments/{environment}/{metadata}",
        "--paginate",
        "--jq",
        f".{metadata}[].name",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        stderr = proc.stderr.strip() or "gh api call failed"
        raise RuntimeError(
            f"Unable to query GitHub environment {metadata} for {repo}/{environment}: {stderr}"
        )
    return {line.strip() for line in proc.stdout.splitlines() if line.strip()}


def evaluate_contract(
    profile: ContractProfile,
    existing_environments: set[str],
    secrets_by_environment: dict[str, set[str]],
    variables_by_environment: dict[str, set[str]],
) -> dict[str, object]:
    missing_environments = sorted(set(profile.required_environments) - existing_environments)
    missing_required_secrets: dict[str, list[str]] = {}
    missing_required_variables: dict[str, list[str]] = {}
    missing_optional_variables: dict[str, list[str]] = {}

    for environment, required_names in profile.required_secrets.items():
        available = secrets_by_environment.get(environment, set())
        missing = sorted(set(required_names) - available)
        if missing:
            missing_required_secrets[environment] = missing

    for environment, required_names in profile.required_variables.items():
        available = variables_by_environment.get(environment, set())
        missing = sorted(set(required_names) - available)
        if missing:
            missing_required_variables[environment] = missing

    for environment, optional_names in profile.optional_variables.items():
        available = variables_by_environment.get(environment, set())
        missing = sorted(set(optional_names) - available)
        if missing:
            missing_optional_variables[environment] = missing

    return {
        "required_environments": list(profile.required_environments),
        "missing_environments": missing_environments,
        "missing_required_secrets": missing_required_secrets,
        "missing_required_variables": missing_required_variables,
        "missing_optional_variables": missing_optional_variables,
    }


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    mode = args.mode
    profile = _CONTRACT_PROFILES[mode]
    requested_environments = args.required or []
    required_environments = tuple(
        dict.fromkeys((*profile.required_environments, *requested_environments))
    )
    profile = ContractProfile(
        required_environments=required_environments,
        required_secrets=profile.required_secrets,
        required_variables=profile.required_variables,
        optional_variables=profile.optional_variables,
    )

    try:
        existing = _fetch_environment_names(args.repo)
    except RuntimeError as exc:
        print(str(exc))
        return 2

    secrets_by_environment: dict[str, set[str]] = {}
    variables_by_environment: dict[str, set[str]] = {}
    for environment in profile.required_environments:
        if environment not in existing:
            continue
        try:
            secrets_by_environment[environment] = _fetch_environment_metadata_names(
                args.repo, environment, "secrets"
            )
            variables_by_environment[environment] = _fetch_environment_metadata_names(
                args.repo, environment, "variables"
            )
        except RuntimeError as exc:
            print(str(exc))
            return 2

    result = evaluate_contract(
        profile=profile,
        existing_environments=existing,
        secrets_by_environment=secrets_by_environment,
        variables_by_environment=variables_by_environment,
    )
    payload = {
        "repo": args.repo,
        "mode": mode,
        "required_count": len(profile.required_environments),
        "existing_required_count": len(profile.required_environments)
        - len(result["missing_environments"]),
        **result,
    }
    print(json.dumps(payload, indent=2))
    if (
        result["missing_environments"]
        or result["missing_required_secrets"]
        or result["missing_required_variables"]
    ):
        print("Protected environment contract check failed.")
        return 1
    print("Protected environment contract check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
