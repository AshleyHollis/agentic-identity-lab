from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

import httpx

from .claims import sanitize_claims
from .guards import AuthContext


def _normalize_scopes(scopes: Iterable[str] | str | None) -> list[str]:
    if scopes is None:
        return []
    if isinstance(scopes, str):
        raw = scopes.replace(",", " ")
        return [item for item in raw.split() if item]
    return [str(item) for item in scopes if str(item).strip()]


def exchange_on_behalf_of(
    context: AuthContext,
    *,
    downstream_audience: str,
    downstream_scopes: Iterable[str] | str | None = None,
) -> dict[str, Any]:
    if not context.authenticated or not context.authorized:
        raise ValueError("OBO exchange requires an authenticated, authorized context.")
    if context.token_type != "delegated":
        raise ValueError("OBO exchange requires a delegated user token.")
    if not isinstance(downstream_audience, str) or not downstream_audience.strip():
        raise ValueError("Downstream audience is required for OBO exchange.")

    obo_claims = dict(context.claims)
    obo_claims["aud"] = downstream_audience.strip()

    normalized_scopes = _normalize_scopes(downstream_scopes)
    if normalized_scopes:
        obo_claims["scp"] = " ".join(normalized_scopes)

    return sanitize_claims(obo_claims)


@dataclass(frozen=True)
class EntraOboConfig:
    token_url: str
    client_id: str
    client_secret: str
    scopes: list[str]
    timeout_seconds: float = 10


def _missing_obo_fields(config: EntraOboConfig) -> list[str]:
    missing: list[str] = []
    if not config.token_url.strip():
        missing.append("OBO_TOKEN_URL")
    if not config.client_id.strip():
        missing.append("OBO_CLIENT_ID")
    if not config.client_secret.strip():
        missing.append("OBO_CLIENT_SECRET")
    if not config.scopes:
        missing.append("OBO_REQUIRED_SCOPES")
    return missing


def validate_entra_obo_config(config: EntraOboConfig, *, context: str) -> None:
    missing = _missing_obo_fields(config)
    if missing:
        names = ", ".join(missing)
        raise ValueError(
            f"{context} requires Entra OBO configuration: {names}. "
            "Wire protected values in the deployment environment; do not commit them."
        )


def _extract_bearer_assertion(authorization: str | None) -> str:
    if not authorization:
        raise ValueError("OBO exchange requires an inbound delegated bearer token.")
    scheme, _, value = authorization.partition(" ")
    if scheme.lower() != "bearer" or not value.strip():
        raise ValueError("OBO exchange requires an inbound delegated bearer token.")
    return value.strip()


def exchange_entra_on_behalf_of(
    authorization: str | None,
    *,
    config: EntraOboConfig,
    context: str = "Strict delegated chain",
) -> str:
    validate_entra_obo_config(config, context=context)
    assertion = _extract_bearer_assertion(authorization)
    try:
        response = httpx.post(
            config.token_url,
            data={
                "client_id": config.client_id,
                "client_secret": config.client_secret,
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": assertion,
                "requested_token_use": "on_behalf_of",
                "scope": " ".join(config.scopes),
            },
            headers={
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            timeout=config.timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise ValueError(
            "OBO token endpoint is unreachable. Verify protected OBO configuration."
        ) from exc
    if response.status_code >= 400:
        raise ValueError(
            "OBO token endpoint rejected the exchange. Verify protected OBO "
            "client configuration and downstream scopes."
        )
    try:
        payload = response.json()
    except ValueError as exc:
        raise ValueError("OBO token endpoint returned an invalid payload.") from exc
    access_token = payload.get("access_token") if isinstance(payload, dict) else None
    if not isinstance(access_token, str) or not access_token.strip():
        raise ValueError("OBO token endpoint response did not include an access token.")
    token_type = payload.get("token_type") if isinstance(payload, dict) else None
    scheme = token_type.strip() if isinstance(token_type, str) and token_type.strip() else "Bearer"
    return f"{scheme} {access_token.strip()}"
