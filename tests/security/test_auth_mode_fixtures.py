from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SHARED_PYTHON = ROOT / "apps" / "shared" / "python"
sys.path.append(str(SHARED_PYTHON))

from identity_lab_auth.auth_settings import (  # noqa: E402
    AUTH_FIXTURE_ENV,
    AUTH_FIXTURE_HEADER,
    AUTH_MODE_ENV,
    AuthMode,
    extract_bearer_token,
    load_auth_claims,
    load_auth_settings,
    load_fixture_claims,
    load_strict_claims_from_authorization,
)

FIXTURES_DIR = ROOT / "tests" / "fixtures" / "sample-claims"


def test_fixture_header_takes_precedence() -> None:
    settings = load_auth_settings(
        headers={AUTH_FIXTURE_HEADER: "wrong-audience"},
        env={AUTH_FIXTURE_ENV: "delegated-user"},
    )

    assert settings.fixture == "wrong-audience"
    claims = load_fixture_claims(settings.fixture, FIXTURES_DIR)
    assert claims is not None
    assert claims["aud"] == "api://00000000-0000-0000-0000-000000000999"


def test_unknown_fixture_returns_none() -> None:
    assert load_fixture_claims("missing-fixture", FIXTURES_DIR) is None


def test_auth_mode_behavior() -> None:
    disabled_settings = load_auth_settings(env={AUTH_MODE_ENV: "disabled"})
    assert disabled_settings.mode == AuthMode.DISABLED
    assert load_auth_claims(disabled_settings, FIXTURES_DIR) == {}

    mock_settings = load_auth_settings(
        env={AUTH_MODE_ENV: "mock", AUTH_FIXTURE_ENV: "delegated-user"}
    )
    claims = load_auth_claims(mock_settings, FIXTURES_DIR)
    assert claims is not None
    assert claims["aud"] == "api://00000000-0000-0000-0000-000000000101"

    strict_settings = load_auth_settings(env={AUTH_MODE_ENV: "strict"})
    with pytest.raises(NotImplementedError):
        load_auth_claims(strict_settings, FIXTURES_DIR)


def test_extract_bearer_token_requires_bearer_scheme() -> None:
    assert extract_bearer_token("Bearer placeholder-token") == "placeholder-token"
    assert extract_bearer_token("bearer placeholder-token") == "placeholder-token"
    assert extract_bearer_token("Basic placeholder-token") is None
    assert extract_bearer_token(None) is None


def test_strict_claim_loader_does_not_return_claims_without_bearer() -> None:
    assert (
        load_strict_claims_from_authorization(
            None,
            jwks_url="https://login.microsoftonline.com/common/discovery/v2.0/keys",
            allowed_audiences=["api://placeholder"],
            issuer="https://login.microsoftonline.com/common/v2.0",
        )
        is None
    )
