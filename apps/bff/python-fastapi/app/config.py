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
    chat_session_chain_enabled: bool
    agent_execution_base_url: str
    agent_invoke_path: str
    downstream_timeout_seconds: float
    obo_token_url: str
    obo_client_id: str
    obo_client_secret: str
    obo_required_scopes: list[str]
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
        chat_session_chain_enabled=_parse_bool(
            os.getenv("CHAT_SESSION_CHAIN_ENABLED"),
            default=False,
        ),
        agent_execution_base_url=os.getenv("AGENT_EXECUTION_BASE_URL", "").rstrip("/"),
        agent_invoke_path=os.getenv("AGENT_EXECUTION_INVOKE_PATH", "/agent/invoke"),
        downstream_timeout_seconds=float(os.getenv("DOWNSTREAM_TIMEOUT_SECONDS", "10")),
        obo_token_url=os.getenv("OBO_TOKEN_URL", ""),
        obo_client_id=os.getenv("OBO_CLIENT_ID", ""),
        obo_client_secret=os.getenv("OBO_CLIENT_SECRET", ""),
        obo_required_scopes=_split_csv(os.getenv("OBO_REQUIRED_SCOPES")),
        cors_allowed_origins=cors_allowed_origins,
    )
    if settings.chat_session_chain_enabled and not settings.agent_execution_base_url:
        raise ValueError(
            "CHAT_SESSION_CHAIN_ENABLED requires AGENT_EXECUTION_BASE_URL to be configured."
        )
    if settings.auth_mode == AuthMode.STRICT:
        validate_strict_config(
            issuer=settings.auth_issuer,
            jwks_url=settings.auth_jwks_url,
            allowed_audiences=settings.allowed_audiences,
            required_scopes=settings.required_scopes,
            trusted_tenants=settings.trusted_tenants,
        )
        if settings.chat_session_chain_enabled:
            validate_entra_obo_config(
                EntraOboConfig(
                    token_url=settings.obo_token_url,
                    client_id=settings.obo_client_id,
                    client_secret=settings.obo_client_secret,
                    scopes=settings.obo_required_scopes,
                    timeout_seconds=settings.downstream_timeout_seconds,
                ),
                context="Strict BFF to Agent chain",
            )
    return settings
