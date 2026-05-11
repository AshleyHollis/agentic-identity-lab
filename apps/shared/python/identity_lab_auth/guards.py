from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any, Iterable, Mapping, Sequence

from .claims import sanitize_claims
from .token_type import classify_claims_token_type


def _normalize_required(values: Iterable[str] | str | None) -> set[str]:
    if values is None:
        return set()
    if isinstance(values, str):
        values = [values]
    return {value for value in values if isinstance(value, str) and value.strip()}


def _extract_scopes(claims: Mapping[str, Any]) -> list[str]:
    raw = claims.get("scp") or claims.get("scope") or []
    if isinstance(raw, str):
        return [item for item in raw.split() if item]
    if isinstance(raw, list):
        return [str(item) for item in raw if item]
    return []


def _extract_audiences(claims: Mapping[str, Any]) -> list[str]:
    raw = claims.get("aud") or []
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, list):
        return [str(item) for item in raw if item]
    return []


def _parse_timestamp(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        trimmed = value.strip()
        if not trimmed:
            return None
        try:
            return int(float(trimmed))
        except ValueError:
            return None
    return None


def require_scope(claims: Mapping[str, Any], required_scopes: Iterable[str] | str | None) -> bool:
    required = _normalize_required(required_scopes)
    if not required:
        return True
    scopes = set(_extract_scopes(claims))
    return bool(scopes.intersection(required))


def require_audience(
    claims: Mapping[str, Any], required_audiences: Iterable[str] | str | None
) -> bool:
    required = _normalize_required(required_audiences)
    if not required:
        return True
    audiences = set(_extract_audiences(claims))
    return bool(audiences.intersection(required))


def require_delegated_token(claims: Mapping[str, Any]) -> bool:
    return classify_claims_token_type(claims) == "delegated"


def require_actor_appid(claims: Mapping[str, Any]) -> bool:
    """Return True if the token carries a non-empty ``appid`` actor claim.

    The ``appid`` claim is required in Agent OBO tokens at the MCP protected
    API boundary.  Its presence proves the token was minted by the Entra Agent
    ID sidecar on behalf of the registered agent application, not by an
    arbitrary delegated user.

    Args:
        claims: Token claim dict (need not be sanitized before this call).

    Returns:
        ``True`` when ``appid`` is a non-empty string; ``False`` otherwise.
    """
    appid = claims.get("appid")
    return isinstance(appid, str) and bool(appid.strip())


def validate_claims(
    claims: Mapping[str, Any],
    *,
    issuer: str | None,
    trusted_tenants: Iterable[str] | str | None,
    clock_skew_seconds: int = 300,
    now: float | None = None,
    allowed_issuers: Sequence[str] | None = None,
) -> list[str]:
    failures: list[str] = []
    # Build the effective set of accepted issuers.
    # ``allowed_issuers`` (multi-value) takes precedence over ``issuer``
    # (single-value) so callers can accept both v1 sts.windows.net and
    # v2 login.microsoftonline.com issuers without a code rebuild.
    effective_issuers: set[str] = set()
    if allowed_issuers:
        effective_issuers = {v.strip() for v in allowed_issuers if isinstance(v, str) and v.strip()}
    elif isinstance(issuer, str) and issuer.strip():
        effective_issuers = {issuer.strip()}

    if effective_issuers:
        claim_issuer = claims.get("iss")
        if not isinstance(claim_issuer, str) or not claim_issuer.strip():
            failures.append("missing_issuer")
        elif claim_issuer.strip() not in effective_issuers:
            failures.append("invalid_issuer")

    trusted = _normalize_required(trusted_tenants)
    if trusted:
        tenant_id = claims.get("tid")
        if not isinstance(tenant_id, str) or not tenant_id.strip():
            failures.append("missing_tenant")
        elif tenant_id not in trusted:
            failures.append("untrusted_tenant")

    now_value = now if now is not None else time.time()

    exp_raw = claims.get("exp")
    exp_value = _parse_timestamp(exp_raw)
    if exp_value is None:
        failures.append("missing_exp" if exp_raw is None else "invalid_exp")
    elif now_value - clock_skew_seconds > exp_value:
        failures.append("token_expired")

    nbf_raw = claims.get("nbf")
    nbf_value = _parse_timestamp(nbf_raw)
    if nbf_value is None:
        failures.append("missing_nbf" if nbf_raw is None else "invalid_nbf")
    elif now_value + clock_skew_seconds < nbf_value:
        failures.append("token_not_yet_valid")

    if "iat" in claims:
        iat_value = _parse_timestamp(claims.get("iat"))
        if iat_value is None:
            failures.append("invalid_iat")
        elif iat_value > now_value + clock_skew_seconds:
            failures.append("token_issued_in_future")

    return failures


@dataclass(frozen=True)
class AuthContext:
    authenticated: bool
    authorized: bool
    failure_reasons: Sequence[str]
    claims: dict[str, Any]
    token_type: str
    scopes: list[str]
    audiences: list[str]
    correlation_id: str | None

    @classmethod
    def from_claims(
        cls,
        claims: Mapping[str, Any] | None,
        token_type: str,
        *,
        authenticated: bool = True,
        authorized: bool = True,
        failure_reasons: Iterable[str] | None = None,
        correlation_id: str | None = None,
    ) -> "AuthContext":
        sanitized = sanitize_claims(claims)
        return cls(
            authenticated=authenticated,
            authorized=authorized,
            failure_reasons=tuple(failure_reasons or []),
            claims=sanitized,
            token_type=token_type,
            scopes=_extract_scopes(sanitized),
            audiences=_extract_audiences(sanitized),
            correlation_id=correlation_id,
        )
