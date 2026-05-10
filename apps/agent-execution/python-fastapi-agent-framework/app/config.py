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
from identity_lab_auth.agent_obo import BLUEPRINT_AUDIENCE_PLACEHOLDER


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
    obo_downstream_audience: str
    obo_required_scopes: list[str]
    enable_debug_claims: bool
    correlation_header: str
    blueprint_audience: str


def load_settings() -> Settings:
    auth_mode = load_auth_mode()
    settings = Settings(
        service_name=os.getenv("SERVICE_NAME", "identity-lab-agent-execution"),
        port=int(os.getenv("PORT", "8000")),
        log_level=os.getenv("LOG_LEVEL", "info"),
        auth_mode=auth_mode,
        auth_issuer=os.getenv("AUTH_ISSUER", ISSUER_PLACEHOLDER),
        auth_jwks_url=os.getenv("AUTH_JWKS_URL", JWKS_URL_PLACEHOLDER),
        allowed_audiences=_split_csv(
            os.getenv("ALLOWED_AUDIENCES"),
            ["api://00000000-0000-0000-0000-000000000102"],
        ),
        required_scopes=_split_csv(
            os.getenv("REQUIRED_SCOPES"),
            ["mcp.access", "mcp.write"],
        ),
        trusted_tenants=_split_csv(
            os.getenv("TRUSTED_TENANTS"),
            [TRUSTED_TENANT_PLACEHOLDER],
        ),
        obo_downstream_audience=os.getenv(
            "OBO_DOWNSTREAM_AUDIENCE",
            "api://00000000-0000-0000-0000-000000000103",
        ),
        obo_required_scopes=_split_csv(
            os.getenv("OBO_REQUIRED_SCOPES"),
            ["mcp.access", "mcp.write"],
        ),
        enable_debug_claims=_parse_bool(os.getenv("ENABLE_DEBUG_CLAIMS"), False),
        correlation_header=os.getenv("CORRELATION_HEADER", "x-correlation-id"),
        blueprint_audience=os.getenv("BLUEPRINT_AUDIENCE", BLUEPRINT_AUDIENCE_PLACEHOLDER),
    )
    if settings.auth_mode == AuthMode.STRICT:
        validate_strict_config(
            issuer=settings.auth_issuer,
            jwks_url=settings.auth_jwks_url,
            allowed_audiences=settings.allowed_audiences,
            required_scopes=settings.required_scopes,
            trusted_tenants=settings.trusted_tenants,
        )
        if settings.blueprint_audience == BLUEPRINT_AUDIENCE_PLACEHOLDER:
            raise ValueError(
                "Strict auth mode requires BLUEPRINT_AUDIENCE to be set to a real "
                "audience URI. The placeholder value is not permitted in strict mode "
                "(T12 binding condition C1)."
            )
    return settings
