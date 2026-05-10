from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SHARED_PYTHON = ROOT / "apps" / "shared" / "python"
sys.path.append(str(SHARED_PYTHON))

from identity_lab_auth import (  # noqa: E402
    AuthMode,
    ISSUER_PLACEHOLDER,
    JWKS_URL_PLACEHOLDER,
    TRUSTED_TENANT_PLACEHOLDER,
)

SERVICE_CONFIGS = {
    "bff": ROOT / "apps" / "bff" / "python-fastapi" / "app" / "config.py",
    "agent_gateway": ROOT
    / "apps"
    / "agent-execution"
    / "python-fastapi-agent-framework"
    / "app"
    / "config.py",
    "mcp_protected_api": ROOT / "apps" / "mcp-protected-api" / "python-fastapi" / "app" / "config.py",
}


def _load_config_module(service: str, path: Path):
    module_name = f"identity_lab_{service}_config"
    if module_name in sys.modules:
        return sys.modules[module_name]
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load config module for {service}.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("service, path", SERVICE_CONFIGS.items())
def test_default_placeholders_are_public_safe(
    monkeypatch: pytest.MonkeyPatch,
    service: str,
    path: Path,
) -> None:
    for key in [
        "AUTH_MODE",
        "AUTH_ISSUER",
        "AUTH_JWKS_URL",
        "TRUSTED_TENANTS",
        "ALLOWED_AUDIENCES",
        "REQUIRED_SCOPES",
    ]:
        monkeypatch.delenv(key, raising=False)

    module = _load_config_module(service, path)
    settings = module.load_settings()

    assert settings.auth_mode == AuthMode.DISABLED
    assert settings.auth_issuer == ISSUER_PLACEHOLDER
    assert settings.auth_jwks_url == JWKS_URL_PLACEHOLDER
    assert settings.trusted_tenants == [TRUSTED_TENANT_PLACEHOLDER]
    assert all(
        "00000000-0000-0000-0000-000000000" in audience
        for audience in settings.allowed_audiences
    )


@pytest.mark.parametrize("service, path", SERVICE_CONFIGS.items())
def test_strict_mode_requires_config(
    monkeypatch: pytest.MonkeyPatch,
    service: str,
    path: Path,
) -> None:
    for key in [
        "AUTH_ISSUER",
        "AUTH_JWKS_URL",
        "TRUSTED_TENANTS",
        "ALLOWED_AUDIENCES",
        "REQUIRED_SCOPES",
    ]:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("AUTH_MODE", "strict")

    module = _load_config_module(service, path)

    with pytest.raises(ValueError, match="Strict auth mode requires configured"):
        module.load_settings()
