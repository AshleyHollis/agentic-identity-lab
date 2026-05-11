from __future__ import annotations

from typing import Mapping

from fastapi import Depends, Header, HTTPException, Request, status

from identity_lab_auth import (
    AuthContext,
    AuthMode,
    classify_claims_token_type,
    load_auth_claims,
    load_auth_settings,
    load_strict_claims_from_authorization,
    require_audience,
    require_delegated_token,
    require_scope,
    validate_claims,
)
from identity_lab_diagnostics import get_correlation_id

from .config import load_settings

settings = load_settings()

ACCESS_SCOPE = "mcp.access"
WRITE_SCOPE = "mcp.write"


def _header_value(headers: Mapping[str, str], name: str) -> str | None:
    direct = headers.get(name)
    if direct is not None:
        return direct
    lowered = name.lower()
    for key, value in headers.items():
        if key.lower() == lowered:
            return value
    return None


def _resolve_required_scopes(scope: str) -> list[str]:
    if not settings.required_scopes:
        return [scope]
    if scope in settings.required_scopes:
        return [scope]
    return list(settings.required_scopes)


def _build_auth_context(request: Request) -> AuthContext:
    auth_settings = load_auth_settings(headers=request.headers)
    if auth_settings.mode == AuthMode.STRICT:
        try:
            claims = load_strict_claims_from_authorization(
                _header_value(request.headers, "authorization"),
                jwks_url=settings.auth_jwks_url,
                allowed_audiences=settings.allowed_audiences,
                issuer=settings.auth_issuer,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid_token",
            ) from exc
    else:
        claims = load_auth_claims(auth_settings)
    correlation_id = get_correlation_id(request.headers)
    if claims is None:
        return AuthContext.from_claims(
            {},
            token_type="none",
            authenticated=False,
            authorized=False,
            failure_reasons=["claims_unavailable"],
            correlation_id=correlation_id,
        )
    token_type = classify_claims_token_type(claims)
    authenticated = auth_settings.mode != AuthMode.DISABLED and bool(claims)
    authorized = auth_settings.mode == AuthMode.DISABLED
    return AuthContext.from_claims(
        claims,
        token_type=token_type,
        authenticated=authenticated,
        authorized=authorized,
        correlation_id=correlation_id,
    )


def _enforce_mcp_auth(context: AuthContext, required_scopes: list[str]) -> AuthContext:
    if settings.auth_mode == AuthMode.DISABLED:
        return AuthContext.from_claims(
            context.claims,
            token_type=context.token_type,
            authenticated=False,
            authorized=True,
            correlation_id=context.correlation_id,
        )
    if not context.authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="authentication_required",
        )
    claim_failures = validate_claims(
        context.claims,
        issuer=settings.auth_issuer,
        trusted_tenants=settings.trusted_tenants,
    )
    if claim_failures:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=claim_failures[0],
        )
    if not require_audience(context.claims, settings.allowed_audiences):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_audience",
        )
    if not require_delegated_token(context.claims):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="delegated_token_required",
        )
    if not require_scope(context.claims, required_scopes):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="missing_scope",
        )
    return AuthContext.from_claims(
        context.claims,
        token_type=context.token_type,
        authenticated=True,
        authorized=True,
        correlation_id=context.correlation_id,
    )

def get_auth_context(
    request: Request,
    authorization: str | None = Header(default=None),
) -> AuthContext:
    _ = authorization
    return _build_auth_context(request)


def require_mcp_access(
    auth_context: AuthContext = Depends(get_auth_context),
) -> AuthContext:
    return _enforce_mcp_auth(auth_context, _resolve_required_scopes(ACCESS_SCOPE))


def require_mcp_write(
    auth_context: AuthContext = Depends(get_auth_context),
) -> AuthContext:
    return _enforce_mcp_auth(auth_context, _resolve_required_scopes(WRITE_SCOPE))
