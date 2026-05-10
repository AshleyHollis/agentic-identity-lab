"""Agent OBO sidecar boundary interface (Spec 002 / T10, T11).

This module defines the ``AgentSidecarClient`` ABC and ``SidecarConfig``
dataclass that form the contract between the Agent Execution Service
(``apps/agent-execution/``) and the Entra Agent ID sidecar container.

In AKS the sidecar runs co-located in the same pod and is reachable only via
``localhost``. In offline/mock mode (``AUTH_MODE=mock``) no HTTP connection to
the sidecar is ever made; ``MockAgentSidecarClient`` resolves all calls from
fixture claims only (T11).

**Separation from other auth paths:**

This module is the *only* entry point for the Agent OBO path.  It MUST NOT
be imported from, or share token variables or configuration state with:

- ``identity_lab_auth.obo.exchange_on_behalf_of`` — MCP user OBO (Spec 001/003)
- Azure OpenAI/Foundry managed identity path (no shared state)
- Any direct MSAL call that bypasses this sidecar mock boundary interface

**Security Design Notes §10 (Trinity, T03 review):**

All concrete implementations of ``AgentSidecarClient`` MUST route all claim
outputs through ``sanitize_claims()`` before returning.  The ABC docstrings
document this as a *binding contract obligation*, not an implementation choice,
so future HTTP adapter implementers cannot inadvertently expose raw Entra token
claims, ``oid``, ``sub``, ``email``, or other PII.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from .claims import sanitize_claims

_LOCALHOST_PREFIXES: tuple[str, ...] = ("http://localhost", "http://127.0.0.1")

#: Placeholder blueprint audience for offline/test use only.
#: Real deployments must override via config; no all-zero GUIDs in production.
BLUEPRINT_AUDIENCE_PLACEHOLDER = "api://00000000-0000-0000-0000-000000000201/access_as_user"

#: Default trusted tenant ID matching T07 offline fixture GUIDs.
#: Not for production use — all-zero placeholder only.
_MOCK_DEFAULT_TRUSTED_TENANT = "00000000-0000-0000-0000-000000000001"


@dataclass(frozen=True)
class SidecarConfig:
    """Validated configuration for the Entra Agent ID sidecar connection.

    Attributes:
        sidecar_url: Base URL of the co-located sidecar container.  MUST begin
            with ``http://localhost`` or ``http://127.0.0.1``.  Any other value
            raises ``ValueError`` at construction time, enforcing the AKS
            network-policy rule that the sidecar port is accessible only from
            the co-located Agentic Layer container.
        blueprint_audience: Expected ``aud`` value on inbound bearer tokens
            before any Agent OBO exchange.  Tokens with a different ``aud``
            MUST be rejected before the exchange is attempted (FR-02).

    Raises:
        ValueError: If ``sidecar_url`` does not start with a recognised
            localhost prefix, or if ``blueprint_audience`` is blank.
    """

    sidecar_url: str
    blueprint_audience: str

    def __post_init__(self) -> None:
        # Require an exact localhost prefix: after the matched prefix the URL must
        # be empty, start with ':', or start with '/' — preventing lookalike names
        # such as 'http://localhostmalicious' from passing the check.
        _valid = False
        for _prefix in _LOCALHOST_PREFIXES:
            if self.sidecar_url.startswith(_prefix):
                _remainder = self.sidecar_url[len(_prefix):]
                if _remainder == "" or _remainder[0] in (":", "/"):
                    _valid = True
                    break
        if not _valid:
            raise ValueError(
                f"sidecar_url must start with 'http://localhost' or "
                f"'http://127.0.0.1'; got {self.sidecar_url!r}. "
                "The Entra Agent ID sidecar is a co-located pod container "
                "reachable only via localhost (AKS network-policy requirement)."
            )
        if not self.blueprint_audience or not self.blueprint_audience.strip():
            raise ValueError("blueprint_audience must be a non-empty string.")


class AgentSidecarClient(ABC):
    """Abstract boundary between the Agentic Layer and the Entra Agent ID sidecar.

    Models the three sidecar HTTP endpoints:

    - ``GET /Validate`` → :meth:`validate`
    - ``GET /AuthorizationHeader/{apiName}`` → :meth:`authorization_header`
    - ``POST /DownstreamApi/{apiName}`` → :meth:`downstream_api`

    Concrete implementations are swapped in by the application at startup:

    - ``MockAgentSidecarClient`` (T11) — offline/fixture-based, zero HTTP calls.
    - A future ``HttpAgentSidecarClient`` — live HTTP adapter for real AKS
      environments after Trinity approves live-testing opt-in (ADR-M5-02).

    **Binding implementation contract (Security Design Notes §10):**

    Every concrete subclass MUST pass all returned claim dicts through
    ``sanitize_claims()`` before returning them to callers.  Raw Entra token
    strings, ``oid``, ``sub``, ``email``, ``upn``, ``name``,
    ``preferred_username``, ``family_name``, and ``given_name`` MUST NOT appear
    in any return value.  This is an explicit security contract reviewed and
    approved by Trinity (T03, 2026-05-15) — it is not optional.

    Args:
        config: A :class:`SidecarConfig` instance whose ``sidecar_url`` has
            already been validated as a localhost-only URL.  Passing a config
            with a non-localhost URL raises ``ValueError`` inside
            :class:`SidecarConfig.__post_init__` before this constructor runs.
    """

    def __init__(self, config: SidecarConfig) -> None:
        self._config = config

    @property
    def config(self) -> SidecarConfig:
        """The validated sidecar configuration for this client instance."""
        return self._config

    @abstractmethod
    def validate(self, bearer_token: str) -> dict[str, Any]:
        """Validate an inbound bearer token (``GET /Validate``).

        Checks the token against the configured ``blueprint_audience``,
        validates the ``tid`` against the trusted-tenant allowlist, and
        verifies ``exp`` / ``nbf`` bounds.

        Args:
            bearer_token: The raw ``Authorization: Bearer <token>`` value
                received from the client.  This string is consumed by the
                sidecar and MUST NOT be logged or forwarded by the caller.

        Returns:
            A sanitized claim dict — the output of ``sanitize_claims()`` — on
            successful validation.  ``oid``, ``sub``, and all PII claims are
            absent from the returned dict.

        Raises:
            ValueError: If the token fails any validation check (wrong
                audience, untrusted tenant, expired, missing required scope,
                or rejected algorithm).

        **CONTRACT:** The returned dict MUST be the output of
        ``sanitize_claims()``.  Raw token strings and PII claims MUST NOT be
        present.  This obligation applies to all concrete implementations,
        including future HTTP adapters.
        """
        ...  # pragma: no cover

    @abstractmethod
    def authorization_header(self, api_name: str) -> str:
        """Return the ``Authorization`` header value for a downstream API
        (``GET /AuthorizationHeader/{apiName}``).

        The sidecar resolves a cached or freshly acquired token for the named
        API and returns it as a header-ready string.

        Args:
            api_name: Logical name of the downstream API (e.g.,
                ``"mcp-protected-api"``).  The sidecar uses this to look up
                the correct token scope configuration.

        Returns:
            A string of the form ``"Bearer <token>"`` suitable for direct use
            as an HTTP ``Authorization`` header value.

        **CONTRACT:** Implementations MUST NOT return a raw Entra-issued token
        string in offline or test modes.  The mock sentinel value MUST be
        ``"Bearer OFFLINE_MOCK_TOKEN"``.  Callers MUST NOT log, persistently
        cache, or forward the raw return value without review.
        """
        ...  # pragma: no cover

    @abstractmethod
    def downstream_api(
        self,
        api_name: str,
        user_assertion: str,
        scopes: list[str],
    ) -> dict[str, Any]:
        """Perform an Agent OBO exchange for a downstream API
        (``POST /DownstreamApi/{apiName}``).

        Sends the ``user_assertion`` (the inbound bearer token) to the sidecar
        for an On-Behalf-Of exchange targeting ``api_name``.  The sidecar
        validates the inbound token's ``aud`` against ``blueprint_audience``
        before attempting the exchange.

        Args:
            api_name: Logical name of the downstream API.
            user_assertion: The inbound bearer token string from the client
                request.  Passed to the sidecar; MUST NOT be logged by the
                caller after this call.
            scopes: List of scopes to request for the downstream token
                (e.g., ``["mcp.access"]``).

        Returns:
            A sanitized claim dict — the output of ``sanitize_claims()`` — for
            the OBO downstream token.  Includes ``appid`` and ``xms_act_fct``
            when present in the downstream token.

        Raises:
            ValueError: If the ``user_assertion`` audience does not match
                ``blueprint_audience``, or if the OBO exchange fails for any
                other reason.

        **CONTRACT:** The returned dict MUST be the output of
        ``sanitize_claims()``.  The raw OBO token string MUST NOT be returned.
        This is the *Agent OBO path* — it is strictly separate from
        ``identity_lab_auth.obo.exchange_on_behalf_of`` (MCP user OBO) and
        from Azure OpenAI/Foundry managed identity auth.  They share no token
        variables, module imports, or configuration state (NFR-06).
        """
        ...  # pragma: no cover


class MockAgentSidecarClient(AgentSidecarClient):
    """Offline mock implementation of ``AgentSidecarClient`` (Spec 002 / T11).

    Resolves all sidecar calls from pre-loaded fixture claim dicts without
    making any HTTP calls.  Intended for ``AUTH_MODE=mock`` and unit/offline
    tests only.

    Validation logic mirrors the real sidecar contract:

    - ``validate()`` checks ``aud``, ``tid``, ``exp``, and ``scp`` against the
      configured ``blueprint_audience`` and ``trusted_tenants`` allowlist.
    - ``authorization_header()`` returns the sentinel ``"Bearer OFFLINE_MOCK_TOKEN"``.
    - ``downstream_api()`` performs a best-effort inbound-assertion audience
      check (using the fixture aud as proxy) then returns sanitized OBO claims.

    All returned dicts are routed through ``sanitize_claims()`` (§10 contract).
    No raw Entra token strings or PII claims appear in any return value.

    Args:
        config: Validated ``SidecarConfig`` (localhost URL enforced).
        fixture_claims: Claims dict for the inbound blueprint user token
            (e.g., loaded from ``agent-blueprint-user-token.json``).
        obo_fixture_claims: Claims dict for the downstream OBO MCP token
            (e.g., loaded from ``agent-obo-mcp-token.json``).
        trusted_tenants: Allowlist of trusted tenant IDs.  Defaults to the
            single offline placeholder tenant
            (``00000000-0000-0000-0000-000000000001``).  Pass an explicit list
            to override.
    """

    _OFFLINE_MOCK_HEADER: str = "Bearer OFFLINE_MOCK_TOKEN"

    def __init__(
        self,
        config: SidecarConfig,
        fixture_claims: dict[str, Any],
        obo_fixture_claims: dict[str, Any],
        trusted_tenants: list[str] | None = None,
    ) -> None:
        super().__init__(config)
        self._fixture_claims: dict[str, Any] = dict(fixture_claims)
        self._obo_fixture_claims: dict[str, Any] = dict(obo_fixture_claims)
        self._trusted_tenants: frozenset[str] = frozenset(
            trusted_tenants if trusted_tenants is not None
            else [_MOCK_DEFAULT_TRUSTED_TENANT]
        )

    def validate(self, bearer_token: str) -> dict[str, Any]:
        """Validate using fixture claims; ignores the literal ``bearer_token`` string.

        Checks ``aud``, ``tid``, ``exp``, and ``scp`` on ``fixture_claims``.

        Args:
            bearer_token: The raw bearer string from the caller.  Consumed and
                discarded — never decoded, logged, or forwarded in mock mode.

        Returns:
            ``sanitize_claims(fixture_claims)`` on success.

        Raises:
            ValueError: Wrong audience, untrusted tenant, expired token, or
                missing/empty ``scp`` (app-only tokens rejected).
        """
        claims = self._fixture_claims

        aud = claims.get("aud")
        if aud != self._config.blueprint_audience:
            raise ValueError(
                f"Expected blueprint audience {self._config.blueprint_audience!r}; "
                f"got {aud!r}."
            )

        tid = claims.get("tid")
        if tid not in self._trusted_tenants:
            raise ValueError(
                f"Untrusted tenant {tid!r}; not in trusted_tenants allowlist."
            )

        exp = claims.get("exp")
        if exp is None or int(exp) < int(time.time()):
            raise ValueError(
                f"Token is expired or missing exp claim (exp={exp!r})."
            )

        if not claims.get("scp"):
            raise ValueError(
                "Token is missing required 'scp' claim; "
                "app-only tokens are not accepted on the delegated blueprint endpoint."
            )

        return sanitize_claims(claims)

    def authorization_header(self, api_name: str) -> str:
        """Return the offline mock authorization header.

        Never makes HTTP calls.  The sentinel value ``"Bearer OFFLINE_MOCK_TOKEN"``
        is the only valid return from mock implementations (§10 contract).

        Args:
            api_name: Logical downstream API name (unused in mock mode).

        Returns:
            ``"Bearer OFFLINE_MOCK_TOKEN"``
        """
        return self._OFFLINE_MOCK_HEADER

    def downstream_api(
        self,
        api_name: str,
        user_assertion: str,
        scopes: list[str],
    ) -> dict[str, Any]:
        """Return sanitized OBO fixture claims; validates inbound assertion audience.

        The mock cannot decode the raw ``user_assertion`` JWT without network
        access.  It performs a best-effort check: the loaded ``fixture_claims``
        must carry the expected ``blueprint_audience`` as a proxy for the
        inbound assertion being valid before any OBO exchange is simulated.

        Args:
            api_name: Logical downstream API name (unused in mock mode).
            user_assertion: The inbound bearer token string.  Not decoded;
                MUST NOT be logged by callers after this call.
            scopes: Requested downstream scopes (unused in mock mode).

        Returns:
            ``sanitize_claims(obo_fixture_claims)`` on success.

        Raises:
            ValueError: If ``fixture_claims["aud"]`` does not match
                ``blueprint_audience`` (inbound assertion was not for the
                configured blueprint).
        """
        inbound_aud = self._fixture_claims.get("aud")
        if inbound_aud != self._config.blueprint_audience:
            raise ValueError(
                f"user_assertion expected blueprint audience "
                f"{self._config.blueprint_audience!r}; "
                f"fixture aud is {inbound_aud!r}. "
                "Inbound assertion is not issued for the configured blueprint."
            )

        return sanitize_claims(self._obo_fixture_claims)
