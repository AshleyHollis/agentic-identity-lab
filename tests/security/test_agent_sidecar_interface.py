"""Unit tests for T10 — AgentSidecarClient ABC and SidecarConfig boundary.

Spec 002 / M5 T10 — Neo
Owner: Neo
Depends on: T02 + T03 complete

Tests cover:
- SidecarConfig localhost enforcement (FR-06)
- SidecarConfig accepts valid localhost URLs
- SidecarConfig rejects blank blueprint_audience
- AgentSidecarClient is abstract (cannot be instantiated directly)
- A minimal concrete subclass satisfies the ABC contract
- config property is accessible on a concrete subclass instance
- Module exports AgentSidecarClient and SidecarConfig from package __init__

These tests make no network calls (NFR-02).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

SHARED_PYTHON = Path(__file__).resolve().parents[2] / "apps" / "shared" / "python"
sys.path.insert(0, str(SHARED_PYTHON))

from identity_lab_auth.agent_obo import (  # noqa: E402
    BLUEPRINT_AUDIENCE_PLACEHOLDER,
    AgentSidecarClient,
    SidecarConfig,
)
import identity_lab_auth  # noqa: E402


# ---------------------------------------------------------------------------
# SidecarConfig — localhost enforcement
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad_url",
    [
        "https://localhost:5000",  # HTTPS not allowed (only http)
        "http://0.0.0.0:5000",
        "http://sidecar-service:5000",
        "http://10.0.0.1:5000",
        "http://192.168.1.1:5000",
        "",
        "localhost:5000",
        "//localhost:5000",
    ],
)
def test_sidecar_config_rejects_non_localhost_url(bad_url: str) -> None:
    """SidecarConfig raises ValueError for any non-localhost sidecar URL."""
    with pytest.raises(ValueError, match="sidecar_url must start with"):
        SidecarConfig(sidecar_url=bad_url, blueprint_audience=BLUEPRINT_AUDIENCE_PLACEHOLDER)


@pytest.mark.parametrize(
    "good_url",
    [
        "http://localhost:5000",
        "http://localhost:5000/",
        "http://localhost",
        "http://127.0.0.1:5000",
        "http://127.0.0.1",
        "http://127.0.0.1:9999/api",
    ],
)
def test_sidecar_config_accepts_localhost_urls(good_url: str) -> None:
    """SidecarConfig accepts http://localhost and http://127.0.0.1 URLs."""
    cfg = SidecarConfig(sidecar_url=good_url, blueprint_audience=BLUEPRINT_AUDIENCE_PLACEHOLDER)
    assert cfg.sidecar_url == good_url


def test_sidecar_config_rejects_blank_blueprint_audience() -> None:
    """SidecarConfig raises ValueError when blueprint_audience is blank."""
    with pytest.raises(ValueError, match="blueprint_audience"):
        SidecarConfig(sidecar_url="http://localhost:5000", blueprint_audience="")


def test_sidecar_config_rejects_whitespace_only_audience() -> None:
    """SidecarConfig raises ValueError when blueprint_audience is whitespace only."""
    with pytest.raises(ValueError, match="blueprint_audience"):
        SidecarConfig(sidecar_url="http://localhost:5000", blueprint_audience="   ")


def test_sidecar_config_is_frozen() -> None:
    """SidecarConfig is immutable (frozen dataclass)."""
    cfg = SidecarConfig(
        sidecar_url="http://localhost:5000",
        blueprint_audience=BLUEPRINT_AUDIENCE_PLACEHOLDER,
    )
    with pytest.raises((AttributeError, TypeError)):
        cfg.sidecar_url = "http://localhost:9999"  # type: ignore[misc]


def test_sidecar_config_stores_blueprint_audience() -> None:
    """SidecarConfig stores the blueprint audience verbatim."""
    audience = "api://00000000-0000-0000-0000-000000000201/access_as_user"
    cfg = SidecarConfig(sidecar_url="http://127.0.0.1:5000", blueprint_audience=audience)
    assert cfg.blueprint_audience == audience


# ---------------------------------------------------------------------------
# AgentSidecarClient — abstract contract
# ---------------------------------------------------------------------------


def test_agent_sidecar_client_is_abstract() -> None:
    """AgentSidecarClient cannot be instantiated directly."""
    cfg = SidecarConfig(
        sidecar_url="http://localhost:5000",
        blueprint_audience=BLUEPRINT_AUDIENCE_PLACEHOLDER,
    )
    with pytest.raises(TypeError):
        AgentSidecarClient(cfg)  # type: ignore[abstract]


def test_agent_sidecar_client_concrete_subclass_instantiates() -> None:
    """A minimal concrete subclass satisfies the ABC and can be instantiated."""

    class _MinimalClient(AgentSidecarClient):
        def validate(self, bearer_token: str) -> dict[str, Any]:
            return {}

        def authorization_header(self, api_name: str) -> str:
            return "Bearer OFFLINE_MOCK_TOKEN"

        def downstream_api(
            self,
            api_name: str,
            user_assertion: str,
            scopes: list[str],
        ) -> dict[str, Any]:
            return {}

    cfg = SidecarConfig(
        sidecar_url="http://localhost:5000",
        blueprint_audience=BLUEPRINT_AUDIENCE_PLACEHOLDER,
    )
    client = _MinimalClient(cfg)
    assert client.config is cfg
    assert client.config.sidecar_url == "http://localhost:5000"


def test_agent_sidecar_client_subclass_requires_all_abstract_methods() -> None:
    """A subclass missing any abstract method cannot be instantiated."""

    class _IncompleteClient(AgentSidecarClient):
        def validate(self, bearer_token: str) -> dict[str, Any]:  # type: ignore[override]
            return {}
        # authorization_header and downstream_api not implemented

    cfg = SidecarConfig(
        sidecar_url="http://localhost:5000",
        blueprint_audience=BLUEPRINT_AUDIENCE_PLACEHOLDER,
    )
    with pytest.raises(TypeError):
        _IncompleteClient(cfg)  # type: ignore[abstract]


def test_agent_sidecar_client_config_property() -> None:
    """config property returns the SidecarConfig passed at construction."""

    class _MinimalClient(AgentSidecarClient):
        def validate(self, bearer_token: str) -> dict[str, Any]:
            return {}

        def authorization_header(self, api_name: str) -> str:
            return "Bearer OFFLINE_MOCK_TOKEN"

        def downstream_api(
            self,
            api_name: str,
            user_assertion: str,
            scopes: list[str],
        ) -> dict[str, Any]:
            return {}

    cfg = SidecarConfig(
        sidecar_url="http://127.0.0.1:8080",
        blueprint_audience=BLUEPRINT_AUDIENCE_PLACEHOLDER,
    )
    client = _MinimalClient(cfg)
    assert client.config.sidecar_url == "http://127.0.0.1:8080"
    assert client.config.blueprint_audience == BLUEPRINT_AUDIENCE_PLACEHOLDER


# ---------------------------------------------------------------------------
# Package-level exports
# ---------------------------------------------------------------------------


def test_package_exports_agent_sidecar_client() -> None:
    """identity_lab_auth exports AgentSidecarClient."""
    assert hasattr(identity_lab_auth, "AgentSidecarClient")
    assert identity_lab_auth.AgentSidecarClient is AgentSidecarClient


def test_package_exports_sidecar_config() -> None:
    """identity_lab_auth exports SidecarConfig."""
    assert hasattr(identity_lab_auth, "SidecarConfig")
    assert identity_lab_auth.SidecarConfig is SidecarConfig


def test_package_exports_blueprint_audience_placeholder() -> None:
    """identity_lab_auth exports BLUEPRINT_AUDIENCE_PLACEHOLDER."""
    assert hasattr(identity_lab_auth, "BLUEPRINT_AUDIENCE_PLACEHOLDER")
    assert identity_lab_auth.BLUEPRINT_AUDIENCE_PLACEHOLDER == BLUEPRINT_AUDIENCE_PLACEHOLDER


# ---------------------------------------------------------------------------
# Separation from MCP user OBO path (NFR-06)
# ---------------------------------------------------------------------------


def test_agent_obo_module_does_not_import_obo_exchange() -> None:
    """agent_obo module must NOT import exchange_on_behalf_of (path separation)."""
    import identity_lab_auth.agent_obo as agent_obo_module
    import identity_lab_auth.obo as obo_module

    # The agent_obo module's namespace must not contain the MCP user OBO function
    assert not hasattr(agent_obo_module, "exchange_on_behalf_of")
    # But the obo module itself should still be importable and intact
    assert hasattr(obo_module, "exchange_on_behalf_of")
