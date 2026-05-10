from __future__ import annotations

import importlib.util
from importlib.machinery import ModuleSpec
import sys
from pathlib import Path
from typing import Mapping

import pytest
from fastapi import HTTPException
from starlette.requests import Request

ROOT = Path(__file__).resolve().parents[2]
SHARED_PYTHON = ROOT / "apps" / "shared" / "python"
BFF_PYTHON = ROOT / "apps" / "bff" / "python-fastapi"

sys.path.append(str(SHARED_PYTHON))

from identity_lab_auth.claims import SAFE_CLAIM_KEYS  # noqa: E402

ISSUER = "https://login.microsoftonline.com/00000000-0000-0000-0000-000000000001/v2.0"
TRUSTED_TENANTS = "00000000-0000-0000-0000-000000000001"


def _load_bff_auth():
    app_dir = BFF_PYTHON / "app"
    package_name = "bff_app"
    if package_name not in sys.modules:
        package_spec = ModuleSpec(package_name, loader=None)
        package = importlib.util.module_from_spec(package_spec)
        package.__path__ = [str(app_dir)]
        sys.modules[package_name] = package

    for module_name in [f"{package_name}.auth", f"{package_name}.config"]:
        if module_name in sys.modules:
            del sys.modules[module_name]

    config_spec = importlib.util.spec_from_file_location(
        f"{package_name}.config", app_dir / "config.py"
    )
    if config_spec is None or config_spec.loader is None:
        raise RuntimeError("Unable to load BFF config module.")
    config_module = importlib.util.module_from_spec(config_spec)
    sys.modules[config_spec.name] = config_module
    config_spec.loader.exec_module(config_module)

    auth_spec = importlib.util.spec_from_file_location(
        f"{package_name}.auth", app_dir / "auth.py"
    )
    if auth_spec is None or auth_spec.loader is None:
        raise RuntimeError("Unable to load BFF auth module.")
    auth_module = importlib.util.module_from_spec(auth_spec)
    sys.modules[auth_spec.name] = auth_module
    auth_spec.loader.exec_module(auth_module)
    return auth_module


def _make_request(headers: Mapping[str, str]) -> Request:
    return Request(
        {
            "type": "http",
            "headers": [
                (key.lower().encode("utf-8"), value.encode("utf-8"))
                for key, value in headers.items()
            ],
        }
    )


def test_bff_delegated_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUTH_MODE", "mock")
    monkeypatch.setenv("AUTH_FIXTURE", "wrong-audience")
    monkeypatch.setenv("AUTH_ISSUER", ISSUER)
    monkeypatch.setenv("TRUSTED_TENANTS", TRUSTED_TENANTS)
    monkeypatch.setenv("ALLOWED_AUDIENCES", "api://00000000-0000-0000-0000-000000000101")
    monkeypatch.setenv("REQUIRED_SCOPES", "mcp.access")

    auth = _load_bff_auth()
    request = _make_request({"X-Identity-Lab-Fixture": "delegated-user"})
    context = auth.get_auth_context(request)

    assert context.authenticated
    assert context.authorized
    assert context.token_type == "delegated"
    assert context.claims["aud"] == "api://00000000-0000-0000-0000-000000000101"
    assert set(context.claims).issubset(SAFE_CLAIM_KEYS)
    assert "sub" not in context.claims
    assert "oid" not in context.claims


def test_bff_rejects_wrong_audience(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUTH_MODE", "mock")
    monkeypatch.setenv("AUTH_ISSUER", ISSUER)
    monkeypatch.setenv("TRUSTED_TENANTS", TRUSTED_TENANTS)
    monkeypatch.setenv("ALLOWED_AUDIENCES", "api://00000000-0000-0000-0000-000000000101")

    auth = _load_bff_auth()
    request = _make_request({"X-Identity-Lab-Fixture": "wrong-audience"})

    with pytest.raises(HTTPException) as excinfo:
        auth.get_auth_context(request)

    assert excinfo.value.status_code == 401


def test_bff_rejects_missing_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUTH_MODE", "mock")
    monkeypatch.setenv("AUTH_ISSUER", ISSUER)
    monkeypatch.setenv("TRUSTED_TENANTS", TRUSTED_TENANTS)
    monkeypatch.setenv("ALLOWED_AUDIENCES", "api://00000000-0000-0000-0000-000000000101")
    monkeypatch.setenv("REQUIRED_SCOPES", "mcp.write")

    auth = _load_bff_auth()
    request = _make_request({"X-Identity-Lab-Fixture": "delegated-user"})

    with pytest.raises(HTTPException) as excinfo:
        auth.get_auth_context(request)

    assert excinfo.value.status_code == 403


def test_bff_rejects_app_only(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUTH_MODE", "mock")
    monkeypatch.setenv("AUTH_ISSUER", ISSUER)
    monkeypatch.setenv("TRUSTED_TENANTS", TRUSTED_TENANTS)
    monkeypatch.setenv("ALLOWED_AUDIENCES", "api://00000000-0000-0000-0000-000000000101")
    monkeypatch.setenv("REQUIRED_SCOPES", "mcp.access")

    auth = _load_bff_auth()
    request = _make_request({"X-Identity-Lab-Fixture": "app-only"})

    with pytest.raises(HTTPException) as excinfo:
        auth.get_auth_context(request)

    assert excinfo.value.status_code == 403
