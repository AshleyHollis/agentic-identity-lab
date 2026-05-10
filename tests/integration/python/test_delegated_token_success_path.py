from __future__ import annotations

import importlib
import importlib.machinery
import importlib.util
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[3]
SHARED_PYTHON = ROOT / "apps" / "shared" / "python"
BFF_PYTHON = ROOT / "apps" / "bff" / "python-fastapi"

sys.path.append(str(SHARED_PYTHON))

FIXTURE_HEADER = "X-Identity-Lab-Fixture"
EXPECTED_AUD = "api://00000000-0000-0000-0000-000000000101"
ISSUER = "https://login.microsoftonline.com/00000000-0000-0000-0000-000000000001/v2.0"
TRUSTED_TENANTS = "00000000-0000-0000-0000-000000000001"


def _bootstrap_package(name: str, package_path: Path) -> None:
    spec = importlib.machinery.ModuleSpec(name, loader=None, is_package=True)
    module = importlib.util.module_from_spec(spec)
    module.__path__ = [str(package_path)]
    sys.modules[name] = module


def _build_bff_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("AUTH_MODE", "mock")
    monkeypatch.setenv("AUTH_ISSUER", ISSUER)
    monkeypatch.setenv("TRUSTED_TENANTS", TRUSTED_TENANTS)
    monkeypatch.setenv("ALLOWED_AUDIENCES", EXPECTED_AUD)
    monkeypatch.setenv("REQUIRED_SCOPES", "mcp.access")
    monkeypatch.setenv("ENABLE_DEBUG_CLAIMS", "false")
    for module_name in list(sys.modules):
        if module_name == "bff_app" or module_name.startswith("bff_app."):
            sys.modules.pop(module_name, None)
    _bootstrap_package("bff_app", BFF_PYTHON / "app")
    app_module = importlib.import_module("bff_app.main")
    return TestClient(app_module.app)


def test_bff_delegated_token_success_path(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _build_bff_client(monkeypatch)
    response = client.get("/whoami", headers={FIXTURE_HEADER: "delegated-user"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["authenticated"] is True
    assert payload["token_type"] == "delegated"
    assert payload["claims"]["aud"] == EXPECTED_AUD
    assert "mcp.access" in payload["scopes"]
    assert "roles" not in payload["claims"]
    assert "sub" not in payload["claims"]
