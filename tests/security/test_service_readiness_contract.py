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
sys.path.append(str(SHARED_PYTHON))

SERVICE_APP_PATHS = {
    "bff": ROOT / "apps" / "bff" / "python-fastapi",
    "agent-execution": ROOT / "apps" / "agent-execution" / "python-fastapi-agent-framework",
    "mcp-protected-api": ROOT / "apps" / "mcp-protected-api" / "python-fastapi",
}

FIXTURE_HEADER = "X-Identity-Lab-Fixture"
CUSTOM_CORRELATION_HEADER = "x-trace-correlation-id"
CUSTOM_CORRELATION_VALUE = "corr-m9-12345"


def _bootstrap_package(name: str, package_path: Path) -> None:
    spec = importlib.machinery.ModuleSpec(name, loader=None, is_package=True)
    module = importlib.util.module_from_spec(spec)
    module.__path__ = [str(package_path)]
    sys.modules[name] = module


def _clear_package_modules(prefix: str) -> None:
    for module_name in list(sys.modules):
        if module_name == prefix or module_name.startswith(f"{prefix}."):
            sys.modules.pop(module_name, None)


def _build_client(
    monkeypatch: pytest.MonkeyPatch,
    service_name: str,
    app_root: Path,
) -> TestClient:
    monkeypatch.setenv("AUTH_MODE", "mock")
    monkeypatch.setenv("AUTH_FIXTURE", "delegated-user")
    monkeypatch.setenv(
        "AUTH_ISSUER",
        "https://login.microsoftonline.com/00000000-0000-0000-0000-000000000001/v2.0",
    )
    monkeypatch.setenv(
        "AUTH_JWKS_URL",
        "https://login.microsoftonline.com/00000000-0000-0000-0000-000000000001/discovery/v2.0/keys",
    )
    monkeypatch.setenv("TRUSTED_TENANTS", "00000000-0000-0000-0000-000000000001")
    monkeypatch.setenv("ALLOWED_AUDIENCES", "api://00000000-0000-0000-0000-000000000101")
    monkeypatch.setenv("REQUIRED_SCOPES", "mcp.access,mcp.write")
    monkeypatch.setenv("CORRELATION_HEADER", CUSTOM_CORRELATION_HEADER)
    monkeypatch.setenv("OTEL_SDK_DISABLED", "true")
    monkeypatch.setenv("SERVICE_NAME", f"identity-lab-{service_name}")

    package_name = f"readiness_{service_name.replace('-', '_')}_app"
    _clear_package_modules(package_name)
    _bootstrap_package(package_name, app_root / "app")
    app_module = importlib.import_module(f"{package_name}.main")
    return TestClient(app_module.app)


@pytest.mark.parametrize("service_name, app_root", SERVICE_APP_PATHS.items())
def test_healthz_uses_configured_correlation_header(
    monkeypatch: pytest.MonkeyPatch,
    service_name: str,
    app_root: Path,
) -> None:
    client = _build_client(monkeypatch, service_name, app_root)
    response = client.get(
        "/healthz",
        headers={
            CUSTOM_CORRELATION_HEADER: CUSTOM_CORRELATION_VALUE,
            FIXTURE_HEADER: "delegated-user",
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == f"identity-lab-{service_name}"
    assert payload["correlation_id"] == CUSTOM_CORRELATION_VALUE


@pytest.mark.parametrize("service_name, app_root", SERVICE_APP_PATHS.items())
def test_readyz_uses_configured_correlation_header(
    monkeypatch: pytest.MonkeyPatch,
    service_name: str,
    app_root: Path,
) -> None:
    client = _build_client(monkeypatch, service_name, app_root)
    response = client.get(
        "/readyz",
        headers={
            CUSTOM_CORRELATION_HEADER: CUSTOM_CORRELATION_VALUE,
            FIXTURE_HEADER: "delegated-user",
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["service"] == f"identity-lab-{service_name}"
    assert payload["correlation_id"] == CUSTOM_CORRELATION_VALUE
