from __future__ import annotations

from typing import Any, Mapping


def _has_scopes(value: Any) -> bool:
    if isinstance(value, str):
        return any(item for item in value.split())
    if isinstance(value, (list, tuple, set)):
        return any(item for item in value)
    return False


def _has_roles(value: Any) -> bool:
    if isinstance(value, str):
        return any(item for item in value.split())
    if isinstance(value, (list, tuple, set)):
        return any(item for item in value)
    return False


def classify_claims_token_type(claims: Mapping[str, Any] | None) -> str:
    if not claims:
        return "none"
    if _has_scopes(claims.get("scp") or claims.get("scope")):
        return "delegated"
    if _has_roles(claims.get("roles")):
        return "app-only"
    return "unknown"


def classify_token_type(authorization: str | None) -> str:
    if not authorization:
        return "none"
    parts = authorization.split()
    if not parts:
        return "none"
    scheme = parts[0].strip().lower()
    if scheme == "bearer":
        return "bearer"
    if scheme:
        return scheme
    return "unknown"
