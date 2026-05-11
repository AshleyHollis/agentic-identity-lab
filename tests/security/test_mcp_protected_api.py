from __future__ import annotations

import importlib
import importlib.machinery
import importlib.util
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
SHARED_PYTHON = ROOT / "apps" / "shared" / "python"
MCP_PYTHON = ROOT / "apps" / "mcp-protected-api" / "python-fastapi"
sys.path.append(str(SHARED_PYTHON))

from identity_lab_auth.claims import SAFE_CLAIM_KEYS  # noqa: E402

FIXTURE_HEADER = "X-Identity-Lab-Fixture"
ISSUER = "https://login.microsoftonline.com/00000000-0000-0000-0000-000000000001/v2.0"
TRUSTED_TENANTS = "00000000-0000-0000-0000-000000000001"


def _bootstrap_package(name: str, package_path: Path) -> None:
    spec = importlib.machinery.ModuleSpec(name, loader=None, is_package=True)
    module = importlib.util.module_from_spec(spec)
    module.__path__ = [str(package_path)]
    sys.modules[name] = module


def _build_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("AUTH_MODE", "mock")
    monkeypatch.setenv("AUTH_ISSUER", ISSUER)
    monkeypatch.setenv("TRUSTED_TENANTS", TRUSTED_TENANTS)
    monkeypatch.setenv(
        "ALLOWED_AUDIENCES",
        "api://00000000-0000-0000-0000-000000000103",
    )
    monkeypatch.setenv("REQUIRED_SCOPES", "mcp.access,mcp.write")
    monkeypatch.setenv("ENABLE_DEBUG_CLAIMS", "false")
    for module_name in list(sys.modules):
        if module_name == "mcp_app" or module_name.startswith("mcp_app."):
            sys.modules.pop(module_name, None)
    _bootstrap_package("mcp_app", MCP_PYTHON / "app")
    app_module = importlib.import_module("mcp_app.main")
    return TestClient(app_module.app)


def test_mcp_tools_echo_success(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _build_client(monkeypatch)
    response = client.post(
        "/tools/echo",
        json={"payload": {"ok": True}},
        headers={FIXTURE_HEADER: "mcp-delegated"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["echo"] == {"ok": True}


def test_mcp_whoami_sanitizes_claims(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _build_client(monkeypatch)
    response = client.get(
        "/whoami",
        headers={FIXTURE_HEADER: "mcp-delegated"},
    )

    assert response.status_code == 200
    payload = response.json()
    claims = payload["claims"]
    assert set(claims).issubset(SAFE_CLAIM_KEYS)
    assert "sub" not in claims
    assert "oid" not in claims


def test_mcp_wrong_audience_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _build_client(monkeypatch)
    response = client.get(
        "/whoami",
        headers={FIXTURE_HEADER: "wrong-audience"},
    )

    assert response.status_code == 401


def test_mcp_missing_scope_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _build_client(monkeypatch)
    response = client.post(
        "/tools/echo",
        json={"payload": {"ok": True}},
        headers={FIXTURE_HEADER: "mcp-missing-scope"},
    )

    assert response.status_code == 403


def test_mcp_app_only_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _build_client(monkeypatch)
    response = client.get(
        "/whoami",
        headers={FIXTURE_HEADER: "mcp-app-only"},
    )

    assert response.status_code == 403


def test_mcp_whoami_uses_configured_correlation_header(monkeypatch: pytest.MonkeyPatch) -> None:
    expected_correlation = "corr-mcp-custom-header"
    custom_header = "x-trace-correlation-id"
    monkeypatch.setenv("CORRELATION_HEADER", custom_header)
    client = _build_client(monkeypatch)
    response = client.get(
        "/whoami",
        headers={
            FIXTURE_HEADER: "mcp-delegated",
            custom_header: expected_correlation,
        },
    )

    assert response.status_code == 200
    assert response.json()["correlation_id"] == expected_correlation
