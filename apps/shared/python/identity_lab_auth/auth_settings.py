from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
import os
from pathlib import Path
from typing import Any, Iterable, Mapping

AUTH_MODE_ENV = "AUTH_MODE"
AUTH_FIXTURE_ENV = "AUTH_FIXTURE"
AUTH_FIXTURE_HEADER = "X-Identity-Lab-Fixture"
AUTH_ISSUER_ENV = "AUTH_ISSUER"
AUTH_JWKS_URL_ENV = "AUTH_JWKS_URL"
TRUSTED_TENANTS_ENV = "TRUSTED_TENANTS"
ALLOWED_AUDIENCES_ENV = "ALLOWED_AUDIENCES"
REQUIRED_SCOPES_ENV = "REQUIRED_SCOPES"

ISSUER_PLACEHOLDER = "https://login.microsoftonline.com/{tenant_id}/v2.0"
JWKS_URL_PLACEHOLDER = "https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"
TRUSTED_TENANT_PLACEHOLDER = "00000000-0000-0000-0000-000000000000"


class AuthMode(str, Enum):
    DISABLED = "disabled"
    MOCK = "mock"
    STRICT = "strict"


@dataclass(frozen=True)
class AuthSettings:
    mode: AuthMode
    fixture: str | None = None


def load_auth_mode(env: Mapping[str, str] | None = None) -> AuthMode:
    source = env or os.environ
    raw_value = source.get(AUTH_MODE_ENV, AuthMode.DISABLED.value)
    if not isinstance(raw_value, str):
        return AuthMode.DISABLED
    normalized = raw_value.strip().lower()
    if normalized in AuthMode._value2member_map_:
        return AuthMode(normalized)
    return AuthMode.DISABLED


def _normalize(value: str | None) -> str | None:
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed or None


def _get_header_value(headers: Mapping[str, str] | None, header_name: str) -> str | None:
    if not headers:
        return None
    direct = headers.get(header_name)
    if direct is not None:
        return direct
    header_name_lower = header_name.lower()
    for key, value in headers.items():
        if key.lower() == header_name_lower:
            return value
    return None


def _looks_like_placeholder(value: str | None) -> bool:
    if value is None:
        return True
    trimmed = value.strip()
    if not trimmed:
        return True
    lowered = trimmed.lower()
    if "{tenant_id}" in lowered or "tenant_id_placeholder" in lowered:
        return True
    if "00000000-0000-0000-0000-000000000" in lowered:
        return True
    return False


def _has_non_placeholder(values: Iterable[str]) -> bool:
    for value in values:
        if not _looks_like_placeholder(value):
            return True
    return False


def validate_strict_config(
    *,
    issuer: str | None,
    jwks_url: str | None,
    allowed_audiences: Iterable[str],
    required_scopes: Iterable[str],
    trusted_tenants: Iterable[str],
) -> None:
    missing: list[str] = []
    if _looks_like_placeholder(issuer):
        missing.append("issuer")
    if _looks_like_placeholder(jwks_url):
        missing.append("jwks_url")
    if not allowed_audiences or not _has_non_placeholder(allowed_audiences):
        missing.append("allowed_audiences")
    if not required_scopes:
        missing.append("required_scopes")
    if not trusted_tenants or not _has_non_placeholder(trusted_tenants):
        missing.append("trusted_tenants")
    if missing:
        fields = ", ".join(missing)
        raise ValueError(f"Strict auth mode requires configured {fields}.")


def select_fixture_name(
    headers: Mapping[str, str] | None = None,
    env: Mapping[str, str] | None = None,
    default_fixture: str | None = None,
) -> str | None:
    header_value = _normalize(_get_header_value(headers, AUTH_FIXTURE_HEADER))
    if header_value:
        return header_value
    source = env or os.environ
    env_value = _normalize(source.get(AUTH_FIXTURE_ENV))
    if env_value:
        return env_value
    return _normalize(default_fixture)


def load_auth_settings(
    headers: Mapping[str, str] | None = None,
    env: Mapping[str, str] | None = None,
    default_fixture: str | None = None,
) -> AuthSettings:
    mode = load_auth_mode(env)
    fixture = select_fixture_name(headers=headers, env=env, default_fixture=default_fixture)
    return AuthSettings(mode=mode, fixture=fixture)


def _default_fixture_dir() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "tests" / "fixtures" / "sample-claims"
        if candidate.is_dir():
            return candidate
    return here.parent


def load_fixture_claims(
    name: str | None,
    fixtures_path: Path | None = None,
) -> dict[str, Any] | None:
    fixture_name = _normalize(name)
    if not fixture_name:
        return None
    fixture_dir = Path(fixtures_path) if fixtures_path else _default_fixture_dir()
    fixture_file = fixture_dir / f"{fixture_name}.json"
    if not fixture_file.is_file():
        return None
    return json.loads(fixture_file.read_text(encoding="utf-8"))


def load_auth_claims(
    settings: AuthSettings,
    fixtures_path: Path | None = None,
) -> dict[str, Any] | None:
    if settings.mode == AuthMode.DISABLED:
        return {}
    if settings.mode == AuthMode.MOCK:
        return load_fixture_claims(settings.fixture, fixtures_path)
    if settings.mode == AuthMode.STRICT:
        raise NotImplementedError("Strict auth mode is not implemented yet.")
    return None
