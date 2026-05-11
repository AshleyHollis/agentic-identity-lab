from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from fastapi import Header, HTTPException, Request, status

from identity_lab_auth import (
    AuthContext,
    AuthMode,
    EntraOboConfig,
    classify_claims_token_type,
    exchange_entra_on_behalf_of,
    exchange_on_behalf_of,
    load_auth_claims,
    load_auth_settings,
    load_strict_claims_from_authorization,
    require_audience,
    require_delegated_token,
    require_scope,
    validate_claims,
)
from identity_lab_auth.agent_obo import AgentSidecarClient
from identity_lab_diagnostics import get_correlation_id

from .config import Settings, load_settings


@dataclass(frozen=True)
class OboExchange:
    authorization: str
    claims: dict[str, Any]


def _extract_scopes(claims: Mapping[str, Any]) -> list[str]:
    raw = claims.get("scp") or claims.get("scope") or []
    if isinstance(raw, str):
        return [item for item in raw.split() if item]
    if isinstance(raw, list):
        return [str(item) for item in raw if item]
    return []


def _status_for_failures(failures: Iterable[str]) -> int:
    failure_set = set(failures)
    if failure_set.intersection(
        {
            "invalid_audience",
            "missing_claims",
            "missing_issuer",
            "invalid_issuer",
            "missing_tenant",
            "untrusted_tenant",
            "missing_exp",
            "invalid_exp",
            "token_expired",
            "missing_nbf",
            "invalid_nbf",
            "token_not_yet_valid",
            "invalid_iat",
            "token_issued_in_future",
        }
    ):
        return status.HTTP_401_UNAUTHORIZED
    return status.HTTP_403_FORBIDDEN


def _header_value(headers: Mapping[str, str], name: str) -> str | None:
    direct = headers.get(name)
    if direct is not None:
        return direct
    lowered = name.lower()
    for key, value in headers.items():
        if key.lower() == lowered:
            return value
    return None


def resolve_auth_context(headers: Mapping[str, str]) -> AuthContext:
    settings = load_settings()
    correlation_id = get_correlation_id(headers, settings.correlation_header)
    auth_settings = load_auth_settings(headers=headers)
    if settings.auth_mode == AuthMode.DISABLED:
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
                _header_value(headers, "authorization"),
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
    if not claims:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid token claims.",
        )

    token_type = classify_claims_token_type(claims)
    authenticated = token_type != "none"
    failure_reasons: list[str] = []
    if not authenticated:
        failure_reasons.append("missing_claims")
    if authenticated:
        failure_reasons.extend(
            validate_claims(
                claims,
                issuer=settings.auth_issuer,
                trusted_tenants=settings.trusted_tenants,
            )
        )
        if not require_delegated_token(claims):
            failure_reasons.append("delegated_required")
        if not require_audience(claims, settings.allowed_audiences):
            failure_reasons.append("invalid_audience")
        if not require_scope(claims, settings.required_scopes):
            failure_reasons.append("missing_scope")

    authorized = authenticated and not failure_reasons
    context = AuthContext.from_claims(
        claims,
        token_type=token_type,
        authenticated=authenticated,
        authorized=authorized,
        failure_reasons=failure_reasons,
        correlation_id=correlation_id,
    )
    if not authorized:
        raise HTTPException(
            status_code=_status_for_failures(failure_reasons),
            detail="Authorization failed.",
        )
    return context


def exchange_for_mcp(
    context: AuthContext,
    settings: Settings | None = None,
    authorization: str | None = None,
) -> OboExchange:
    active_settings = settings or load_settings()
    if active_settings.auth_mode == AuthMode.STRICT:
        return exchange_strict_for_mcp(context, authorization, active_settings)
    obo_claims = exchange_on_behalf_of(
        context,
        downstream_audience=active_settings.obo_downstream_audience,
        downstream_scopes=active_settings.obo_required_scopes,
    )
    return OboExchange(authorization="Bearer obo-token", claims=obo_claims)


def exchange_strict_for_mcp(
    context: AuthContext,
    authorization: str | None,
    settings: Settings | None = None,
) -> OboExchange:
    active_settings = settings or load_settings()
    if active_settings.auth_mode != AuthMode.STRICT:
        return exchange_for_mcp(context, active_settings)
    authorization_header = exchange_entra_on_behalf_of(
        authorization,
        config=EntraOboConfig(
            token_url=active_settings.obo_token_url,
            client_id=active_settings.obo_client_id,
            client_secret=active_settings.obo_client_secret,
            scopes=active_settings.obo_required_scopes,
            timeout_seconds=active_settings.downstream_timeout_seconds,
        ),
        context="Strict Agent to MCP chain",
    )
    obo_claims = {
        "aud": active_settings.obo_downstream_audience,
        "scp": " ".join(active_settings.obo_required_scopes),
    }
    return OboExchange(authorization=authorization_header, claims=obo_claims)


def get_auth_context(
    request: Request,
    authorization: str | None = Header(default=None),
) -> AuthContext:
    _ = authorization
    return resolve_auth_context(request.headers)


def validate_agent_blueprint(
    bearer_token: str,
    sidecar_client: AgentSidecarClient,
) -> dict:
    """Validate blueprint audience via AgentSidecarClient before any Agent OBO exchange.

    FR-02: Tokens whose ``aud`` does not match the configured blueprint audience
    are rejected with HTTP 401 before any OBO exchange is attempted.  This
    function MUST be called before ``exchange_agent_obo``.

    This is the *Agent OBO path* — it is strictly separate from
    ``exchange_for_mcp`` (MCP user OBO) and shares no token variables,
    module imports, or configuration state with it (NFR-06).

    Args:
        bearer_token: Raw bearer string from the ``Authorization`` header.
            Consumed by the sidecar; must not be logged after this call.
        sidecar_client: ``AgentSidecarClient`` instance (``MockAgentSidecarClient``
            in offline/test mode; a future HTTP adapter in live AKS mode).

    Returns:
        Sanitized claim dict (output of ``sanitize_claims()``) on success.

    Raises:
        HTTPException(401): If the token audience, tenant, expiry, or scope
            validation fails inside ``AgentSidecarClient.validate()``.
    """
    try:
        return sidecar_client.validate(bearer_token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Blueprint audience validation failed: {exc}",
        ) from exc


def exchange_agent_obo(
    bearer_token: str,
    sidecar_client: AgentSidecarClient,
    api_name: str = "mcp-protected-api",
    scopes: list[str] | None = None,
) -> OboExchange:
    """Perform Agent OBO exchange via the sidecar client (T12 — Agent OBO path).

    Blueprint audience MUST be validated via ``validate_agent_blueprint`` before
    calling this function.  The Agent OBO path is strictly separate from the MCP
    user OBO path (``exchange_for_mcp``) — they share no token variables or state.

    Args:
        bearer_token: The validated inbound bearer string.  Passed to the
            sidecar as the ``user_assertion`` for the OBO exchange; must not
            be logged by callers after this call.
        sidecar_client: ``AgentSidecarClient`` instance.
        api_name: Logical downstream API name (default ``"mcp-protected-api"``).
        scopes: Requested downstream scopes.  Defaults to an empty list.

    Returns:
        ``OboExchange`` with ``authorization`` set to the sidecar's header
        value and ``claims`` set to the sanitized downstream claim dict.

    Raises:
        HTTPException(401): If the sidecar rejects the downstream exchange.
    """
    try:
        downstream_claims = sidecar_client.downstream_api(
            api_name=api_name,
            user_assertion=bearer_token,
            scopes=scopes or [],
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Agent OBO exchange failed: {exc}",
        ) from exc
    auth_header = sidecar_client.authorization_header(api_name)
    return OboExchange(authorization=auth_header, claims=downstream_claims)
