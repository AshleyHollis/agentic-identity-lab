from __future__ import annotations

from dataclasses import dataclass
import os

from identity_lab_auth import (
    AuthMode,
    ISSUER_PLACEHOLDER,
    JWKS_URL_PLACEHOLDER,
    TRUSTED_TENANT_PLACEHOLDER,
    load_auth_mode,
    validate_strict_config,
)


def _split_csv(value: str | None, default: list[str] | None = None) -> list[str]:
    if value is None:
        return list(default) if default else []
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    service_name: str
    port: int
    log_level: str
    auth_mode: AuthMode
    auth_issuer: str
    auth_jwks_url: str
    allowed_audiences: list[str]
    required_scopes: list[str]
    trusted_tenants: list[str]
    enable_debug_claims: bool
    correlation_header: str
    # Comma-separated origins; empty list disables CORS middleware entirely.
    # Defaults to ["http://localhost:3000"] in AUTH_MODE=mock only.
    cors_allowed_origins: list[str]


def load_settings() -> Settings:
    auth_mode = load_auth_mode()

    cors_env = os.getenv("CORS_ALLOWED_ORIGINS")
    if cors_env is not None:
        cors_allowed_origins = _split_csv(cors_env)
    elif auth_mode == AuthMode.MOCK:
        cors_allowed_origins = ["http://localhost:3000"]
    else:
        cors_allowed_origins = []

    settings = Settings(
        service_name=os.getenv("SERVICE_NAME", "identity-lab-bff"),
        port=int(os.getenv("PORT", "8000")),
        log_level=os.getenv("LOG_LEVEL", "info"),
        auth_mode=auth_mode,
        auth_issuer=os.getenv("AUTH_ISSUER", ISSUER_PLACEHOLDER),
        auth_jwks_url=os.getenv("AUTH_JWKS_URL", JWKS_URL_PLACEHOLDER),
        allowed_audiences=_split_csv(
            os.getenv("ALLOWED_AUDIENCES"),
            ["api://00000000-0000-0000-0000-000000000101"],
        ),
        required_scopes=_split_csv(
            os.getenv("REQUIRED_SCOPES"),
            ["mcp.access"],
        ),
        trusted_tenants=_split_csv(
            os.getenv("TRUSTED_TENANTS"),
            [TRUSTED_TENANT_PLACEHOLDER],
        ),
        enable_debug_claims=_parse_bool(os.getenv("ENABLE_DEBUG_CLAIMS"), False),
        correlation_header=os.getenv("CORRELATION_HEADER", "x-correlation-id"),
        cors_allowed_origins=cors_allowed_origins,
    )
    if settings.auth_mode == AuthMode.STRICT:
        validate_strict_config(
            issuer=settings.auth_issuer,
            jwks_url=settings.auth_jwks_url,
            allowed_audiences=settings.allowed_audiences,
            required_scopes=settings.required_scopes,
            trusted_tenants=settings.trusted_tenants,
        )
    return settings
