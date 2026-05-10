"""Shared OpenTelemetry telemetry helpers (Spec 002 / T18).

Provides a reusable, no-op-safe tracer setup for all Identity Lab Python
services.  When ``OTEL_EXPORTER_OTLP_ENDPOINT`` is unset **or**
``OTEL_SDK_DISABLED=true``, every call silently resolves to a no-op tracer so
tests and offline runs are never blocked by a missing Jaeger/collector endpoint.

Usage in each FastAPI service's ``main.py``::

    from identity_lab_auth.telemetry import setup_telemetry, instrument_fastapi
    setup_telemetry(service_name="agent-execution")
    instrument_fastapi(app)

Span attribute helpers::

    from identity_lab_auth.telemetry import record_auth_attributes, record_obo_attributes
    record_auth_attributes(auth_mode="mock", authorized=True, aud="api://...")
    record_obo_attributes(obo_hop="agent_obo")

Security constraints (T03 §9, ADR-002):

- ``identity_lab.fixture_name`` MUST be set to ``""`` (empty) in strict mode.
- PII claim keys (``oid``, ``sub``, ``email``, ``upn``, ``name``,
  ``preferred_username``, ``given_name``, ``family_name``) MUST NOT be set as
  span attributes.
- Raw bearer token strings MUST NOT be set as span attributes.
- All lab-specific attributes use the ``identity_lab.*`` namespace.
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from fastapi import FastAPI

logger = logging.getLogger(__name__)

# Environment variable names
_OTEL_DISABLED_ENV = "OTEL_SDK_DISABLED"
_OTEL_ENDPOINT_ENV = "OTEL_EXPORTER_OTLP_ENDPOINT"
_APPLICATIONINSIGHTS_CONNECTION_STRING_ENV = "APPLICATIONINSIGHTS_CONNECTION_STRING"

# PII claim keys that must never appear as span attributes.
_PII_KEYS: frozenset[str] = frozenset({
    "oid",
    "sub",
    "email",
    "upn",
    "name",
    "preferred_username",
    "given_name",
    "family_name",
})


def _is_disabled() -> bool:
    """Return True when the OTEL SDK should behave as a no-op."""
    disabled_env = os.environ.get(_OTEL_DISABLED_ENV, "").strip().lower()
    if disabled_env in ("true", "1", "yes"):
        return True
    connection_string = os.environ.get(_APPLICATIONINSIGHTS_CONNECTION_STRING_ENV, "").strip()
    if connection_string:
        return False
    endpoint = os.environ.get(_OTEL_ENDPOINT_ENV, "").strip()
    return not endpoint


def setup_telemetry(service_name: str) -> None:
    """Initialise the global ``TracerProvider`` for *service_name*.

    - When ``OTEL_SDK_DISABLED=true`` **or** neither Azure Monitor nor OTLP
      export is configured, installs a ``NoOpTracerProvider`` so spans are
      discarded.
    - When ``APPLICATIONINSIGHTS_CONNECTION_STRING`` is configured, installs an
      Azure Monitor exporter.
    - Otherwise, when an OTLP endpoint is configured, installs an OTLP gRPC
      exporter with a ``BatchSpanProcessor``.

    This function is idempotent: calling it multiple times (e.g., in tests)
    will not raise.  Only the first call that reaches provider installation
    takes effect; subsequent calls to the same provider are ignored by the SDK.

    Args:
        service_name: Value for the ``service.name`` resource attribute
            (e.g. ``"agent-execution"``, ``"bff"``, ``"mcp-protected-api"``).
    """
    if _is_disabled():
        try:
            from opentelemetry import trace
            from opentelemetry.trace import NoOpTracerProvider

            trace.set_tracer_provider(NoOpTracerProvider())
        except ImportError:
            pass
        return

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource, SERVICE_NAME
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource(attributes={SERVICE_NAME: service_name})
        provider = TracerProvider(resource=resource)
        connection_string = os.environ.get(_APPLICATIONINSIGHTS_CONNECTION_STRING_ENV, "").strip()
        if connection_string:
            from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter

            exporter = AzureMonitorTraceExporter(connection_string=connection_string)
        else:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

            endpoint = os.environ.get(_OTEL_ENDPOINT_ENV, "").strip()
            exporter = OTLPSpanExporter(endpoint=endpoint)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
    except ImportError:
        logger.warning(
            "opentelemetry packages not installed; tracing disabled for %s",
            service_name,
        )
    except Exception as exc:  # pragma: no cover — runtime only
        logger.warning("Failed to initialise OTEL tracer for %s: %s", service_name, exc)


def get_tracer(name: str) -> Any:
    """Return an OpenTelemetry tracer for *name*.

    Falls back to a no-op tracer if the SDK is not installed or disabled.

    Args:
        name: Instrumentation scope name (e.g. ``"identity_lab.bff"``).
    """
    try:
        from opentelemetry import trace

        return trace.get_tracer(name)
    except ImportError:
        return _NoOpTracer()


def instrument_fastapi(app: Any) -> None:
    """Attach ``FastAPIInstrumentor`` to *app*, creating HTTP spans automatically.

    Safe to call when OTEL is disabled or not installed — becomes a no-op.

    Args:
        app: A :class:`fastapi.FastAPI` application instance.
    """
    if _is_disabled():
        return
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor.instrument_app(app)
    except ImportError:
        logger.debug("opentelemetry-instrumentation-fastapi not installed; HTTP spans disabled.")
    except Exception as exc:  # pragma: no cover — runtime only
        logger.warning("Failed to instrument FastAPI app: %s", exc)


def record_auth_attributes(
    *,
    auth_mode: str,
    authorized: bool | None = None,
    aud: str | None = None,
    fixture_name: str | None = None,
    strict_mode: bool = False,
) -> None:
    """Set ``identity_lab.*`` auth attributes on the currently active span.

    Attributes set (when values are non-None):

    - ``identity_lab.auth_mode`` — value of ``AUTH_MODE`` (``"mock"`` or ``"strict"``)
    - ``identity_lab.authorized`` — boolean outcome
    - ``identity_lab.aud`` — ``aud`` claim value from the validated token
    - ``identity_lab.fixture_name`` — fixture name in mock mode; **always ``""``
      in strict mode** (Security Design Notes §9)

    No PII keys are ever set.  Raw bearer token strings must not be passed as
    any argument.

    Args:
        auth_mode: Value of ``AUTH_MODE`` env var.
        authorized: Whether the request was authorized.
        aud: Audience value from the validated token.
        fixture_name: The fixture name selected for this request (mock mode
            only).  Pass ``None`` to omit the attribute entirely.
        strict_mode: When ``True``, ``identity_lab.fixture_name`` is forced to
            ``""`` regardless of *fixture_name* value (T03 §9).
    """
    try:
        from opentelemetry import trace

        span = trace.get_current_span()
        if span is None:
            return
        span.set_attribute("identity_lab.auth_mode", auth_mode)
        if authorized is not None:
            span.set_attribute("identity_lab.authorized", authorized)
        if aud is not None:
            span.set_attribute("identity_lab.aud", str(aud))
        # fixture_name: always blank in strict mode (T03 §9)
        if fixture_name is not None or strict_mode:
            safe_fixture = "" if strict_mode else (fixture_name or "")
            span.set_attribute("identity_lab.fixture_name", safe_fixture)
    except ImportError:
        pass
    except Exception:  # pragma: no cover
        pass


def record_obo_attributes(*, obo_hop: str) -> None:
    """Set ``identity_lab.obo_hop`` on the currently active span.

    Args:
        obo_hop: OBO path identifier — ``"agent_obo"`` or ``"user_obo"``.
    """
    try:
        from opentelemetry import trace

        span = trace.get_current_span()
        if span is None:
            return
        span.set_attribute("identity_lab.obo_hop", obo_hop)
    except ImportError:
        pass
    except Exception:  # pragma: no cover
        pass


def safe_span_attribute_key(key: str) -> bool:
    """Return ``True`` if *key* is safe to use as a span attribute key.

    Rejects any key that maps to a PII claim per the safe-claims rules.

    Args:
        key: Candidate span attribute key.
    """
    return key not in _PII_KEYS


# ---------------------------------------------------------------------------
# Internal no-op fallback (used when opentelemetry package is absent)
# ---------------------------------------------------------------------------

class _NoOpSpan:
    """Minimal no-op span used when the OTEL SDK is not available."""

    def set_attribute(self, key: str, value: object) -> None:  # noqa: ARG002
        pass

    def __enter__(self) -> _NoOpSpan:
        return self

    def __exit__(self, *args: object) -> None:
        pass


class _NoOpTracer:
    """Minimal no-op tracer used when the OTEL SDK is not available."""

    def start_as_current_span(self, name: str, **kwargs: Any) -> _NoOpSpan:  # noqa: ARG002
        return _NoOpSpan()

    def start_span(self, name: str, **kwargs: Any) -> _NoOpSpan:  # noqa: ARG002
        return _NoOpSpan()
