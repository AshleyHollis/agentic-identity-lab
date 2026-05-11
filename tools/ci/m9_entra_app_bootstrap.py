from __future__ import annotations

import argparse
import json
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any


AZURE_CLI_APP_ID = "04b07795-8ddb-461a-bbee-02f9e1bf7b46"


@dataclass(frozen=True)
class AppSpec:
    key: str
    display_name: str
    scopes: tuple[str, ...]
    public_client: bool = False


def _run_az_json(args: list[str]) -> Any:
    command = ["az", *args, "--output", "json", "--only-show-errors"]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError("Azure CLI call failed while bootstrapping Entra app registrations.")
    try:
        return json.loads(completed.stdout or "null")
    except json.JSONDecodeError as exc:
        raise RuntimeError("Azure CLI returned invalid JSON payload.") from exc


def _run_az(args: list[str]) -> None:
    command = ["az", *args, "--only-show-errors"]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError("Azure CLI call failed while applying Entra app configuration.")


def _stable_scope_id(display_name: str, scope_value: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"agentic-identity-lab:{display_name}:{scope_value}"))


def _new_scope(display_name: str, scope_value: str, scope_id: str) -> dict[str, Any]:
    title = scope_value.replace(".", " ").title()
    return {
        "id": scope_id,
        "value": scope_value,
        "type": "User",
        "isEnabled": True,
        "adminConsentDisplayName": f"{display_name} {title}",
        "adminConsentDescription": f"Allow delegated access to {display_name} ({scope_value}).",
        "userConsentDisplayName": f"Access {display_name}",
        "userConsentDescription": f"Allow the app to access {display_name} on your behalf.",
    }


def _merge_scopes(display_name: str, existing: list[dict[str, Any]], required: tuple[str, ...]) -> list[dict[str, Any]]:
    by_value = {
        str(item.get("value", "")).strip(): dict(item)
        for item in existing
        if isinstance(item, dict) and str(item.get("value", "")).strip()
    }
    merged: list[dict[str, Any]] = []
    for scope_value in required:
        scope = by_value.get(scope_value)
        if scope is None:
            scope_id = _stable_scope_id(display_name, scope_value)
            scope = _new_scope(display_name, scope_value, scope_id)
        else:
            scope["isEnabled"] = True
            scope.setdefault("id", _stable_scope_id(display_name, scope_value))
            scope.setdefault("type", "User")
            scope.setdefault("adminConsentDisplayName", f"{display_name} {scope_value}")
            scope.setdefault("adminConsentDescription", f"Allow delegated access to {display_name}.")
            scope.setdefault("userConsentDisplayName", f"Access {display_name}")
            scope.setdefault("userConsentDescription", f"Allow delegated access to {display_name}.")
        merged.append(scope)
    return merged


def _merge_required_resource_access(
    existing: list[dict[str, Any]],
    resource_app_id: str,
    scope_ids: list[str],
) -> list[dict[str, Any]]:
    entries = [dict(item) for item in existing if isinstance(item, dict)]
    resource_scope_set = set(scope_ids)
    updated = False
    for entry in entries:
        if str(entry.get("resourceAppId", "")).strip() != resource_app_id:
            continue
        existing_access = [
            dict(item)
            for item in entry.get("resourceAccess", [])
            if isinstance(item, dict) and str(item.get("id", "")).strip()
        ]
        by_id = {str(item["id"]): item for item in existing_access}
        for scope_id in resource_scope_set:
            if scope_id not in by_id:
                by_id[scope_id] = {"id": scope_id, "type": "Scope"}
        entry["resourceAccess"] = sorted(by_id.values(), key=lambda item: str(item["id"]))
        updated = True
        break
    if not updated and resource_scope_set:
        entries.append(
            {
                "resourceAppId": resource_app_id,
                "resourceAccess": [{"id": scope_id, "type": "Scope"} for scope_id in sorted(resource_scope_set)],
            }
        )
    return entries


def _merge_preauthorized(
    existing: list[dict[str, Any]],
    client_app_id: str,
    delegated_permission_ids: list[str],
) -> list[dict[str, Any]]:
    entries = [dict(item) for item in existing if isinstance(item, dict)]
    required_set = set(delegated_permission_ids)
    updated = False
    for entry in entries:
        if str(entry.get("appId", "")).strip() != client_app_id:
            continue
        existing_ids = {
            str(item).strip()
            for item in entry.get("delegatedPermissionIds", [])
            if str(item).strip()
        }
        entry["delegatedPermissionIds"] = sorted(existing_ids | required_set)
        updated = True
        break
    if not updated and required_set:
        entries.append(
            {
                "appId": client_app_id,
                "delegatedPermissionIds": sorted(required_set),
            }
        )
    return entries


def _find_application(display_name: str) -> dict[str, Any] | None:
    payload = _run_az_json(["ad", "app", "list", "--display-name", display_name])
    if not isinstance(payload, list):
        return None
    matches = [item for item in payload if isinstance(item, dict) and item.get("displayName") == display_name]
    if not matches:
        return None
    if len(matches) > 1:
        raise RuntimeError(f"Multiple app registrations found for display name '{display_name}'.")
    return matches[0]


def _ensure_application(spec: AppSpec) -> dict[str, Any]:
    existing = _find_application(spec.display_name)
    if existing is None:
        app = _run_az_json(
            [
                "ad",
                "app",
                "create",
                "--display-name",
                spec.display_name,
                "--sign-in-audience",
                "AzureADMyOrg",
            ]
        )
        if not isinstance(app, dict):
            raise RuntimeError(f"Unable to create app registration for '{spec.display_name}'.")
    else:
        app = existing

    app_id = str(app.get("appId", "")).strip()
    if not app_id:
        raise RuntimeError(f"App registration '{spec.display_name}' does not contain an appId.")
    details = _run_az_json(["ad", "app", "show", "--id", app_id])
    if not isinstance(details, dict):
        raise RuntimeError(f"Unable to query details for app '{spec.display_name}'.")
    return details


def _ensure_service_principal(app_id: str) -> None:
    check = subprocess.run(
        ["az", "ad", "sp", "show", "--id", app_id, "--output", "none", "--only-show-errors"],
        capture_output=True,
        text=True,
        check=False,
    )
    if check.returncode == 0:
        return
    _run_az(["ad", "sp", "create", "--id", app_id])


def _patch_application(app_object_id: str, payload: dict[str, Any]) -> None:
    _run_az(
        [
            "rest",
            "--method",
            "PATCH",
            "--url",
            f"https://graph.microsoft.com/v1.0/applications/{app_object_id}",
            "--headers",
            "Content-Type=application/json",
            "--body",
            json.dumps(payload),
        ]
    )


def _ensure_identifier_uri(app_id: str, current_uris: list[Any]) -> str:
    preferred = f"api://{app_id}"
    uris = [str(item).strip() for item in current_uris if str(item).strip()]
    if preferred in uris:
        return preferred
    return preferred


def _load_specs(environment: str) -> dict[str, AppSpec]:
    prefix = f"agent-identity-lab-{environment}"
    return {
        "bff": AppSpec("bff", f"{prefix}-bff", ("mcp.access", "access_as_user")),
        "agent": AppSpec("agent", f"{prefix}-agent-execution", ("mcp.access", "mcp.write")),
        "mcp": AppSpec("mcp", f"{prefix}-mcp", ("mcp.access", "mcp.write")),
        "smoke": AppSpec("smoke", f"{prefix}-smoke-client", tuple(), public_client=True),
    }


def bootstrap(environment: str) -> dict[str, str]:
    specs = _load_specs(environment)
    apps = {key: _ensure_application(spec) for key, spec in specs.items()}
    app_ids = {key: str(app["appId"]).strip() for key, app in apps.items()}
    app_object_ids = {key: str(app["id"]).strip() for key, app in apps.items()}

    for app_id in app_ids.values():
        _ensure_service_principal(app_id)

    audiences = {key: _ensure_identifier_uri(app_ids[key], apps[key].get("identifierUris", [])) for key in apps}
    scope_ids_by_app: dict[str, dict[str, str]] = {}

    for key, spec in specs.items():
        existing_api = apps[key].get("api", {}) if isinstance(apps[key].get("api"), dict) else {}
        existing_scopes = (
            existing_api.get("oauth2PermissionScopes", [])
            if isinstance(existing_api.get("oauth2PermissionScopes"), list)
            else []
        )
        merged_scopes = _merge_scopes(spec.display_name, existing_scopes, spec.scopes)
        scope_ids_by_app[key] = {str(scope["value"]): str(scope["id"]) for scope in merged_scopes}

        patch_payload: dict[str, Any] = {
            "identifierUris": [audiences[key]],
            "api": {
                "oauth2PermissionScopes": merged_scopes,
                "preAuthorizedApplications": existing_api.get("preAuthorizedApplications", []),
                # Force v2.0 access tokens so aud claim is the appId UUID (not the identifier URI).
                "requestedAccessTokenVersion": 2,
            },
        }
        if spec.public_client:
            patch_payload["isFallbackPublicClient"] = True
            patch_payload["publicClient"] = {"redirectUris": []}
        _patch_application(app_object_ids[key], patch_payload)

    bff_scopes = [scope_ids_by_app["bff"]["mcp.access"]]
    bff_all_scopes = [scope_ids_by_app["bff"]["mcp.access"], scope_ids_by_app["bff"]["access_as_user"]]
    agent_scopes = [scope_ids_by_app["agent"]["mcp.access"], scope_ids_by_app["agent"]["mcp.write"]]
    mcp_scopes = [scope_ids_by_app["mcp"]["mcp.access"], scope_ids_by_app["mcp"]["mcp.write"]]

    bff_api = apps["bff"].get("api", {}) if isinstance(apps["bff"].get("api"), dict) else {}
    agent_api = apps["agent"].get("api", {}) if isinstance(apps["agent"].get("api"), dict) else {}
    mcp_api = apps["mcp"].get("api", {}) if isinstance(apps["mcp"].get("api"), dict) else {}

    _patch_application(
        app_object_ids["bff"],
        {
            "api": {
                "oauth2PermissionScopes": _merge_scopes(
                    specs["bff"].display_name,
                    bff_api.get("oauth2PermissionScopes", []) if isinstance(bff_api.get("oauth2PermissionScopes"), list) else [],
                    specs["bff"].scopes,
                ),
                # Pre-authorize smoke-client (mcp.access only) and Azure CLI (all BFF scopes so
                # delegated token requests via 'az account get-access-token' work without admin consent).
                "preAuthorizedApplications": _merge_preauthorized(
                    _merge_preauthorized(
                        bff_api.get("preAuthorizedApplications", []) if isinstance(bff_api.get("preAuthorizedApplications"), list) else [],
                        app_ids["smoke"],
                        bff_scopes,
                    ),
                    AZURE_CLI_APP_ID,
                    bff_all_scopes,
                ),
                "requestedAccessTokenVersion": 2,
            }
        },
    )
    _patch_application(
        app_object_ids["agent"],
        {
            "requiredResourceAccess": _merge_required_resource_access(
                apps["agent"].get("requiredResourceAccess", [])
                if isinstance(apps["agent"].get("requiredResourceAccess"), list)
                else [],
                app_ids["mcp"],
                mcp_scopes,
            ),
            "api": {
                "oauth2PermissionScopes": _merge_scopes(
                    specs["agent"].display_name,
                    agent_api.get("oauth2PermissionScopes", []) if isinstance(agent_api.get("oauth2PermissionScopes"), list) else [],
                    specs["agent"].scopes,
                ),
                "preAuthorizedApplications": _merge_preauthorized(
                    agent_api.get("preAuthorizedApplications", []) if isinstance(agent_api.get("preAuthorizedApplications"), list) else [],
                    app_ids["bff"],
                    agent_scopes,
                ),
            },
        },
    )
    _patch_application(
        app_object_ids["mcp"],
        {
            "api": {
                "oauth2PermissionScopes": _merge_scopes(
                    specs["mcp"].display_name,
                    mcp_api.get("oauth2PermissionScopes", []) if isinstance(mcp_api.get("oauth2PermissionScopes"), list) else [],
                    specs["mcp"].scopes,
                ),
                "preAuthorizedApplications": _merge_preauthorized(
                    mcp_api.get("preAuthorizedApplications", []) if isinstance(mcp_api.get("preAuthorizedApplications"), list) else [],
                    app_ids["agent"],
                    mcp_scopes,
                ),
            }
        },
    )
    _patch_application(
        app_object_ids["bff"],
        {
            "requiredResourceAccess": _merge_required_resource_access(
                apps["bff"].get("requiredResourceAccess", [])
                if isinstance(apps["bff"].get("requiredResourceAccess"), list)
                else [],
                app_ids["agent"],
                agent_scopes,
            )
        },
    )
    _patch_application(
        app_object_ids["smoke"],
        {
            "requiredResourceAccess": _merge_required_resource_access(
                apps["smoke"].get("requiredResourceAccess", [])
                if isinstance(apps["smoke"].get("requiredResourceAccess"), list)
                else [],
                app_ids["bff"],
                bff_scopes,
            ),
            "isFallbackPublicClient": True,
            "publicClient": {"redirectUris": []},
        },
    )

    return {
        # With requestedAccessTokenVersion=2, access tokens carry aud=<appId UUID>.
        # Include both the identifier URI (api://...) and the raw UUID so container apps
        # with ALLOWED_AUDIENCES accept both v1.0 and v2.0 token formats.
        "bff_audience": f"{audiences['bff']},{app_ids['bff']}",
        "agent_execution_audience": f"{audiences['agent']},{app_ids['agent']}",
        "mcp_audience": f"{audiences['mcp']},{app_ids['mcp']}",
        "blueprint_audience": audiences["bff"],
        "bff_scope_mcp_access": f"{audiences['bff']}/mcp.access",
        "bff_scope_access_as_user": f"{audiences['bff']}/access_as_user",
        "agent_execution_scope_mcp_access": f"{audiences['agent']}/mcp.access",
        "agent_execution_scope_mcp_write": f"{audiences['agent']}/mcp.write",
        "mcp_scope_mcp_access": f"{audiences['mcp']}/mcp.access",
        "mcp_scope_mcp_write": f"{audiences['mcp']}/mcp.write",
        "bff_client_id": app_ids["bff"],
        "agent_execution_client_id": app_ids["agent"],
        "mcp_client_id": app_ids["mcp"],
        "smoke_client_id": app_ids["smoke"],
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bootstrap strict M9 Entra app registrations and scopes.")
    parser.add_argument("--environment", default="dev", help="Environment slug (default: dev).")
    parser.add_argument("--output-json", required=True, help="Output JSON path for resolved audiences/scopes.")
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    output_path = Path(args.output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results = bootstrap(args.environment)
    output_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print("M9 Entra bootstrap completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
