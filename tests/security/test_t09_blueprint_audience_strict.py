"""Tests for T09 — BLUEPRINT_AUDIENCE strict-mode validation (T12 binding condition C1).

Spec 006 / M6 T09 — Neo
T12 binding condition C1: Agent Execution Service must reject the
BLUEPRINT_AUDIENCE_PLACEHOLDER in AUTH_MODE=strict.

Tests cover:
- Strict mode rejects the BLUEPRINT_AUDIENCE_PLACEHOLDER value (not set / explicitly placeholder).
- Strict mode accepts a non-placeholder audience URI alongside valid strict config.
- Non-strict modes (mock, disabled) are unaffected by the blueprint audience check.

No network calls are made (NFR-02).
"""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SHARED_PYTHON = ROOT / "apps" / "shared" / "python"
AGENT_EXECUTION_APP = (
    ROOT / "apps" / "agent-execution" / "python-fastapi-agent-framework" / "app" / "config.py"
)

sys.path.insert(0, str(SHARED_PYTHON))

from identity_lab_auth.agent_obo import BLUEPRINT_AUDIENCE_PLACEHOLDER  # noqa: E402


# ---------------------------------------------------------------------------
# Env var helpers
# ---------------------------------------------------------------------------

_REAL_ISSUER = "https://login.microsoftonline.com/real-tenant-id/v2.0"
_REAL_JWKS = "https://login.microsoftonline.com/real-tenant-id/discovery/v2.0/keys"
_REAL_AUDIENCE = "api://real-app-client-id"
_REAL_SCOPE = "mcp.access"
_REAL_TENANT = "real-tenant-id"
_REAL_BLUEPRINT_AUDIENCE = "api://real-blueprint-app-id/access_as_user"


def _set_valid_strict_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set all mandatory strict-mode env vars to non-placeholder values."""
    monkeypatch.setenv("AUTH_MODE", "strict")
    monkeypatch.setenv("AUTH_ISSUER", _REAL_ISSUER)
    monkeypatch.setenv("AUTH_JWKS_URL", _REAL_JWKS)
    monkeypatch.setenv("ALLOWED_AUDIENCES", _REAL_AUDIENCE)
    monkeypatch.setenv("REQUIRED_SCOPES", _REAL_SCOPE)
    monkeypatch.setenv("TRUSTED_TENANTS", _REAL_TENANT)


def _load_agent_config():
    """Load (or reload) the agent-execution config module under a unique name."""
    module_name = "identity_lab_agent_execution_config_t09"
    # Always reload so monkeypatched env vars take full effect.
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, AGENT_EXECUTION_APP)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load agent-execution config module.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# T09 / C1 — strict mode rejects placeholder BLUEPRINT_AUDIENCE
# ---------------------------------------------------------------------------


def test_strict_mode_rejects_placeholder_blueprint_audience_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Strict mode must raise ValueError when BLUEPRINT_AUDIENCE is unset (defaults to placeholder).

    T12 binding condition C1: placeholder startup must fail in strict mode.
    """
    _set_valid_strict_env(monkeypatch)
    monkeypatch.delenv("BLUEPRINT_AUDIENCE", raising=False)

    module = _load_agent_config()

    with pytest.raises(ValueError, match="BLUEPRINT_AUDIENCE"):
        module.load_settings()


def test_strict_mode_rejects_explicit_placeholder_blueprint_audience(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Strict mode must raise ValueError when BLUEPRINT_AUDIENCE is explicitly the placeholder.

    Confirms that explicitly setting the env var to the placeholder constant is
    also rejected — not just the default-absent case.
    """
    _set_valid_strict_env(monkeypatch)
    monkeypatch.setenv("BLUEPRINT_AUDIENCE", BLUEPRINT_AUDIENCE_PLACEHOLDER)

    module = _load_agent_config()

    with pytest.raises(ValueError, match="BLUEPRINT_AUDIENCE"):
        module.load_settings()


def test_strict_mode_accepts_real_blueprint_audience(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Strict mode must NOT raise when BLUEPRINT_AUDIENCE is a real (non-placeholder) URI.

    Proves that a properly configured deployment is accepted.
    """
    _set_valid_strict_env(monkeypatch)
    monkeypatch.setenv("BLUEPRINT_AUDIENCE", _REAL_BLUEPRINT_AUDIENCE)

    module = _load_agent_config()

    settings = module.load_settings()
    assert settings.blueprint_audience == _REAL_BLUEPRINT_AUDIENCE


# ---------------------------------------------------------------------------
# Non-strict modes — blueprint audience placeholder is allowed (offline/dev)
# ---------------------------------------------------------------------------


def test_mock_mode_allows_placeholder_blueprint_audience(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mock mode must NOT reject the placeholder BLUEPRINT_AUDIENCE.

    The placeholder is valid for offline/dev use.  Only strict mode enforces real values.
    """
    monkeypatch.setenv("AUTH_MODE", "mock")
    monkeypatch.delenv("BLUEPRINT_AUDIENCE", raising=False)

    module = _load_agent_config()

    settings = module.load_settings()
    assert settings.blueprint_audience == BLUEPRINT_AUDIENCE_PLACEHOLDER


def test_disabled_mode_allows_placeholder_blueprint_audience(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Disabled mode must NOT reject the placeholder BLUEPRINT_AUDIENCE."""
    monkeypatch.setenv("AUTH_MODE", "disabled")
    monkeypatch.delenv("BLUEPRINT_AUDIENCE", raising=False)

    module = _load_agent_config()

    settings = module.load_settings()
    assert settings.blueprint_audience == BLUEPRINT_AUDIENCE_PLACEHOLDER


# ---------------------------------------------------------------------------
# Error message quality — must name the field clearly
# ---------------------------------------------------------------------------


def test_strict_rejection_error_mentions_strict_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The ValueError raised for placeholder BLUEPRINT_AUDIENCE must mention strict mode.

    This ensures the error is actionable: operators can identify the cause
    from startup logs alone, without source inspection.
    """
    _set_valid_strict_env(monkeypatch)
    monkeypatch.delenv("BLUEPRINT_AUDIENCE", raising=False)

    module = _load_agent_config()

    with pytest.raises(ValueError) as exc_info:
        module.load_settings()

    message = str(exc_info.value)
    assert "strict" in message.lower()
    assert "BLUEPRINT_AUDIENCE" in message
