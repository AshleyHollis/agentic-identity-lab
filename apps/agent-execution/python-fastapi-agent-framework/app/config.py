from __future__ import annotations

from dataclasses import dataclass
import os

from identity_lab_auth import (
    AuthMode,
    EntraOboConfig,
    ISSUER_PLACEHOLDER,
    JWKS_URL_PLACEHOLDER,
    TRUSTED_TENANT_PLACEHOLDER,
    load_auth_mode,
    validate_entra_obo_config,
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
    obo_token_url: str
    obo_client_id: str
    obo_client_secret: str
    enable_debug_claims: bool
    correlation_header: str
    blueprint_audience: str
    mcp_chain_enabled: bool
    mcp_protected_api_base_url: str
    mcp_authorization_check_path: str
    downstream_timeout_seconds: float


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
        obo_token_url=os.getenv("OBO_TOKEN_URL", ""),
        obo_client_id=os.getenv("OBO_CLIENT_ID", ""),
        obo_client_secret=os.getenv("OBO_CLIENT_SECRET", ""),
        enable_debug_claims=_parse_bool(os.getenv("ENABLE_DEBUG_CLAIMS"), False),
        correlation_header=os.getenv("CORRELATION_HEADER", "x-correlation-id"),
        blueprint_audience=os.getenv("BLUEPRINT_AUDIENCE", BLUEPRINT_AUDIENCE_PLACEHOLDER),
        mcp_chain_enabled=_parse_bool(
            os.getenv("MCP_CHAIN_ENABLED"),
            default=False,
        ),
        mcp_protected_api_base_url=os.getenv("MCP_PROTECTED_API_BASE_URL", "").rstrip("/"),
        mcp_authorization_check_path=os.getenv(
            "MCP_AUTHORIZATION_CHECK_PATH",
            "/tools/authorization-check",
        ),
        downstream_timeout_seconds=float(os.getenv("DOWNSTREAM_TIMEOUT_SECONDS", "10")),
    )
    if settings.mcp_chain_enabled and not settings.mcp_protected_api_base_url:
        raise ValueError(
            "MCP_CHAIN_ENABLED requires MCP_PROTECTED_API_BASE_URL to be configured."
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
        if settings.mcp_chain_enabled:
            validate_entra_obo_config(
                EntraOboConfig(
                    token_url=settings.obo_token_url,
                    client_id=settings.obo_client_id,
                    client_secret=settings.obo_client_secret,
                    scopes=settings.obo_required_scopes,
                    timeout_seconds=settings.downstream_timeout_seconds,
                ),
                context="Strict Agent to MCP chain",
            )
    return settings
