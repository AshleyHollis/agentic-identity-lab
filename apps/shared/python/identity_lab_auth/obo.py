from __future__ import annotations

from typing import Any, Iterable

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
