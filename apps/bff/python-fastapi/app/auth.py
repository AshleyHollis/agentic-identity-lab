from __future__ import annotations

from fastapi import Header, HTTPException, Request, status

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


def _raise_auth_error(status_code: int, reason: str) -> None:
    raise HTTPException(status_code=status_code, detail=reason)


def get_auth_context(
    request: Request,
    authorization: str | None = Header(default=None),
) -> AuthContext:
    _ = authorization
    settings = load_settings()
    correlation_id = get_correlation_id(
        request.headers, header_name=settings.correlation_header
    )
    auth_settings = load_auth_settings(headers=request.headers)
    if auth_settings.mode == AuthMode.DISABLED:
        return AuthContext.from_claims(
            {},
            token_type="none",
            authenticated=False,
            authorized=True,
            correlation_id=correlation_id,
        )

    if auth_settings.mode == AuthMode.STRICT:
        try:
            claims = load_strict_claims_from_authorization(
                authorization,
                jwks_url=settings.auth_jwks_url,
                allowed_audiences=settings.allowed_audiences,
                issuer=settings.auth_issuer,
            )
        except ValueError:
            _raise_auth_error(status.HTTP_401_UNAUTHORIZED, "invalid_token")
    else:
        claims = load_auth_claims(auth_settings)

    if not claims:
        _raise_auth_error(status.HTTP_401_UNAUTHORIZED, "missing_claims")

    claim_failures = validate_claims(
        claims,
        issuer=settings.auth_issuer,
        trusted_tenants=settings.trusted_tenants,
    )
    if claim_failures:
        _raise_auth_error(status.HTTP_401_UNAUTHORIZED, claim_failures[0])

    if not require_audience(claims, settings.allowed_audiences):
        _raise_auth_error(status.HTTP_401_UNAUTHORIZED, "invalid_audience")
    if not require_delegated_token(claims):
        _raise_auth_error(status.HTTP_403_FORBIDDEN, "delegated_required")
    if not require_scope(claims, settings.required_scopes):
        _raise_auth_error(status.HTTP_403_FORBIDDEN, "missing_scope")

    return AuthContext.from_claims(
        claims,
        token_type=classify_claims_token_type(claims),
        correlation_id=correlation_id,
    )
