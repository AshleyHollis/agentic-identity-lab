from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.ci.m9_entra_app_bootstrap import (  # noqa: E402
    _merge_preauthorized,
    _merge_required_resource_access,
    _merge_scopes,
    _stable_scope_id,
)


def test_stable_scope_id_is_deterministic() -> None:
    first = _stable_scope_id("agent-identity-lab-dev-bff", "mcp.access")
    second = _stable_scope_id("agent-identity-lab-dev-bff", "mcp.access")
    assert first == second


def test_merge_required_resource_access_is_idempotent() -> None:
    existing = [
        {
            "resourceAppId": "resource-1",
            "resourceAccess": [{"id": "scope-a", "type": "Scope"}],
        }
    ]
    merged = _merge_required_resource_access(existing, "resource-1", ["scope-a", "scope-b"])
    resource_entries = [entry for entry in merged if entry["resourceAppId"] == "resource-1"]
    assert len(resource_entries) == 1
    scope_ids = {entry["id"] for entry in resource_entries[0]["resourceAccess"]}
    assert scope_ids == {"scope-a", "scope-b"}


def test_merge_preauthorized_is_idempotent() -> None:
    merged = _merge_preauthorized(
        [{"appId": "client-1", "delegatedPermissionIds": ["scope-a"]}],
        "client-1",
        ["scope-a", "scope-b"],
    )
    entry = next(item for item in merged if item["appId"] == "client-1")
    assert set(entry["delegatedPermissionIds"]) == {"scope-a", "scope-b"}


def test_merge_scopes_preserves_existing_scope_ids() -> None:
    existing = [
        {
            "value": "mcp.access",
            "id": "existing-id",
            "type": "User",
            "isEnabled": True,
            "adminConsentDisplayName": "existing",
            "adminConsentDescription": "existing",
            "userConsentDisplayName": "existing",
            "userConsentDescription": "existing",
        }
    ]
    merged = _merge_scopes("agent-identity-lab-dev-bff", existing, ("mcp.access", "access_as_user"))
    by_value = {item["value"]: item for item in merged}
    assert by_value["mcp.access"]["id"] == "existing-id"
    assert by_value["access_as_user"]["id"]
