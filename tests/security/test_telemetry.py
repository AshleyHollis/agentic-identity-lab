"""T18 — OTEL telemetry tests (offline).

Covers (per tasks.md §T18 and design.md §End-to-End Tracing Design):

1. No-op baseline — when ``OTEL_SDK_DISABLED=true`` or no OTLP endpoint is
   set, ``setup_telemetry`` installs a NoOpTracerProvider; ``get_tracer``
   returns a usable tracer; span attribute helpers do not raise.
2. Safe span attribute behaviour — ``record_auth_attributes`` sets
   ``identity_lab.*`` attributes; no PII key is ever set.
3. Strict-mode ``fixture_name`` suppression — the attribute is always ``""``
   when ``strict_mode=True`` regardless of the value passed (T03 §9).
4. PII key guard — ``safe_span_attribute_key`` rejects all PII keys listed in
   the safe-claims design; all non-PII keys are accepted.
5. ``record_obo_attributes`` sets ``identity_lab.obo_hop`` safely.
6. ``instrument_fastapi`` is a no-op when OTEL is disabled; it does not raise.

All tests are fully offline — no Jaeger, no OTLP collector, no network calls.
The tests explicitly set ``OTEL_SDK_DISABLED=true`` before each call to ensure
no exporter is ever initialised.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
SHARED_PYTHON = ROOT / "apps" / "shared" / "python"
sys.path.insert(0, str(SHARED_PYTHON))

from identity_lab_auth.telemetry import (  # noqa: E402
    _PII_KEYS,
    get_tracer,
    instrument_fastapi,
    record_auth_attributes,
    record_obo_attributes,
    safe_span_attribute_key,
    setup_telemetry,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _disabled_env() -> dict[str, str]:
    """Return an env snapshot with OTEL_SDK_DISABLED=true."""
    return {**os.environ, "OTEL_SDK_DISABLED": "true", "OTEL_EXPORTER_OTLP_ENDPOINT": ""}


# ---------------------------------------------------------------------------
# 1. No-op baseline
# ---------------------------------------------------------------------------


class TestNoOpBaseline:
    def test_setup_telemetry_disabled_does_not_raise(self):
        """setup_telemetry with OTEL_SDK_DISABLED=true must not raise."""
        with patch.dict(os.environ, {"OTEL_SDK_DISABLED": "true"}, clear=False):
            setup_telemetry("test-service")  # must not raise

    def test_setup_telemetry_no_endpoint_does_not_raise(self):
        """setup_telemetry with no OTLP endpoint must not raise."""
        env = {k: v for k, v in os.environ.items() if k != "OTEL_EXPORTER_OTLP_ENDPOINT"}
        env["OTEL_SDK_DISABLED"] = "false"
        env.pop("OTEL_EXPORTER_OTLP_ENDPOINT", None)
        with patch.dict(os.environ, env, clear=True):
            setup_telemetry("test-service")  # no endpoint → no-op; must not raise

    def test_get_tracer_returns_usable_tracer(self):
        """get_tracer must return something usable (has start_as_current_span)."""
        with patch.dict(os.environ, {"OTEL_SDK_DISABLED": "true"}, clear=False):
            tracer = get_tracer("test.scope")
        assert tracer is not None
        assert hasattr(tracer, "start_as_current_span")

    def test_record_auth_attributes_noop_does_not_raise(self):
        """record_auth_attributes must silently succeed when OTEL is disabled."""
        with patch.dict(os.environ, {"OTEL_SDK_DISABLED": "true"}, clear=False):
            record_auth_attributes(
                auth_mode="mock",
                authorized=True,
                aud="api://test",
                fixture_name="delegated-user",
            )  # must not raise

    def test_record_obo_attributes_noop_does_not_raise(self):
        """record_obo_attributes must silently succeed when OTEL is disabled."""
        with patch.dict(os.environ, {"OTEL_SDK_DISABLED": "true"}, clear=False):
            record_obo_attributes(obo_hop="user_obo")  # must not raise

    def test_instrument_fastapi_disabled_does_not_raise(self):
        """instrument_fastapi must be a no-op when OTEL_SDK_DISABLED=true."""
        mock_app = MagicMock()
        with patch.dict(os.environ, {"OTEL_SDK_DISABLED": "true"}, clear=False):
            instrument_fastapi(mock_app)  # must not raise


# ---------------------------------------------------------------------------
# 2. Safe span attribute behaviour
# ---------------------------------------------------------------------------


class TestSafeSpanAttributes:
    def test_record_auth_attributes_sets_identity_lab_attributes(self):
        """record_auth_attributes must call set_attribute with identity_lab.* keys."""
        mock_span = MagicMock()
        with (
            patch("identity_lab_auth.telemetry._is_disabled", return_value=False),
            patch("opentelemetry.trace.get_current_span", return_value=mock_span),
        ):
            record_auth_attributes(
                auth_mode="mock",
                authorized=True,
                aud="api://00000000-0000-0000-0000-000000000102",
                fixture_name="delegated-user",
                strict_mode=False,
            )

        calls = {call.args[0] for call in mock_span.set_attribute.call_args_list}
        assert "identity_lab.auth_mode" in calls
        assert "identity_lab.authorized" in calls
        assert "identity_lab.aud" in calls
        assert "identity_lab.fixture_name" in calls

    def test_record_auth_attributes_no_pii_keys_ever_set(self):
        """record_auth_attributes must never set PII claim keys as span attributes."""
        mock_span = MagicMock()
        with (
            patch("identity_lab_auth.telemetry._is_disabled", return_value=False),
            patch("opentelemetry.trace.get_current_span", return_value=mock_span),
        ):
            record_auth_attributes(
                auth_mode="mock",
                authorized=True,
                aud="api://test",
            )

        set_keys = {call.args[0] for call in mock_span.set_attribute.call_args_list}
        for pii_key in _PII_KEYS:
            assert pii_key not in set_keys, (
                f"PII key '{pii_key}' must never appear as a span attribute"
            )

    def test_record_auth_attributes_aud_is_string(self):
        """identity_lab.aud must be set as a string value."""
        mock_span = MagicMock()
        with (
            patch("identity_lab_auth.telemetry._is_disabled", return_value=False),
            patch("opentelemetry.trace.get_current_span", return_value=mock_span),
        ):
            record_auth_attributes(
                auth_mode="mock",
                aud="api://00000000-0000-0000-0000-000000000102",
            )

        aud_calls = [
            call for call in mock_span.set_attribute.call_args_list
            if call.args[0] == "identity_lab.aud"
        ]
        assert aud_calls, "identity_lab.aud attribute must be set"
        assert isinstance(aud_calls[0].args[1], str)

    def test_record_auth_attributes_omits_aud_when_none(self):
        """identity_lab.aud must NOT be set when aud is None."""
        mock_span = MagicMock()
        with (
            patch("identity_lab_auth.telemetry._is_disabled", return_value=False),
            patch("opentelemetry.trace.get_current_span", return_value=mock_span),
        ):
            record_auth_attributes(auth_mode="mock", aud=None)

        set_keys = {call.args[0] for call in mock_span.set_attribute.call_args_list}
        assert "identity_lab.aud" not in set_keys


# ---------------------------------------------------------------------------
# 3. Strict-mode fixture_name suppression (T03 §9)
# ---------------------------------------------------------------------------


class TestStrictModeFixtureNameSuppression:
    def test_fixture_name_is_empty_in_strict_mode(self):
        """identity_lab.fixture_name must be '' when strict_mode=True."""
        mock_span = MagicMock()
        with (
            patch("identity_lab_auth.telemetry._is_disabled", return_value=False),
            patch("opentelemetry.trace.get_current_span", return_value=mock_span),
        ):
            record_auth_attributes(
                auth_mode="strict",
                fixture_name="some-fixture",  # would normally be set
                strict_mode=True,  # must suppress it
            )

        fixture_calls = [
            call for call in mock_span.set_attribute.call_args_list
            if call.args[0] == "identity_lab.fixture_name"
        ]
        assert fixture_calls, "identity_lab.fixture_name must still be set (as empty string)"
        assert fixture_calls[0].args[1] == "", (
            "identity_lab.fixture_name must be '' in strict mode, not the actual fixture name"
        )

    def test_fixture_name_non_empty_in_mock_mode(self):
        """identity_lab.fixture_name must contain the fixture name in mock mode."""
        mock_span = MagicMock()
        with (
            patch("identity_lab_auth.telemetry._is_disabled", return_value=False),
            patch("opentelemetry.trace.get_current_span", return_value=mock_span),
        ):
            record_auth_attributes(
                auth_mode="mock",
                fixture_name="delegated-user",
                strict_mode=False,
            )

        fixture_calls = [
            call for call in mock_span.set_attribute.call_args_list
            if call.args[0] == "identity_lab.fixture_name"
        ]
        assert fixture_calls
        assert fixture_calls[0].args[1] == "delegated-user"

    def test_fixture_name_omitted_when_both_none_and_not_strict(self):
        """identity_lab.fixture_name must be omitted when fixture_name=None and not strict."""
        mock_span = MagicMock()
        with (
            patch("identity_lab_auth.telemetry._is_disabled", return_value=False),
            patch("opentelemetry.trace.get_current_span", return_value=mock_span),
        ):
            record_auth_attributes(
                auth_mode="mock",
                fixture_name=None,
                strict_mode=False,
            )

        set_keys = {call.args[0] for call in mock_span.set_attribute.call_args_list}
        assert "identity_lab.fixture_name" not in set_keys


# ---------------------------------------------------------------------------
# 4. PII key guard
# ---------------------------------------------------------------------------


class TestPiiKeyGuard:
    @pytest.mark.parametrize("pii_key", sorted(_PII_KEYS))
    def test_safe_span_attribute_key_rejects_pii(self, pii_key: str):
        """safe_span_attribute_key must return False for all PII claim keys."""
        assert safe_span_attribute_key(pii_key) is False, (
            f"PII key '{pii_key}' should be rejected by safe_span_attribute_key"
        )

    @pytest.mark.parametrize("safe_key", [
        "identity_lab.auth_mode",
        "identity_lab.authorized",
        "identity_lab.aud",
        "identity_lab.obo_hop",
        "identity_lab.fixture_name",
        "http.route",
        "http.method",
        "http.status_code",
        "service.name",
    ])
    def test_safe_span_attribute_key_accepts_non_pii(self, safe_key: str):
        """safe_span_attribute_key must return True for all allowed span attribute keys."""
        assert safe_span_attribute_key(safe_key) is True

    def test_pii_keys_set_contains_all_prohibited_claims(self):
        """The PII key set must cover all prohibited claims from the spec."""
        required_pii_keys = {"oid", "sub", "email", "upn", "name", "preferred_username",
                             "given_name", "family_name"}
        assert required_pii_keys.issubset(_PII_KEYS), (
            f"Missing PII keys: {required_pii_keys - _PII_KEYS}"
        )


# ---------------------------------------------------------------------------
# 5. record_obo_attributes
# ---------------------------------------------------------------------------


class TestRecordOboAttributes:
    def test_record_obo_attributes_sets_obo_hop(self):
        """record_obo_attributes must set identity_lab.obo_hop on the active span."""
        mock_span = MagicMock()
        with (
            patch("identity_lab_auth.telemetry._is_disabled", return_value=False),
            patch("opentelemetry.trace.get_current_span", return_value=mock_span),
        ):
            record_obo_attributes(obo_hop="agent_obo")

        obo_calls = [
            call for call in mock_span.set_attribute.call_args_list
            if call.args[0] == "identity_lab.obo_hop"
        ]
        assert obo_calls, "identity_lab.obo_hop must be set"
        assert obo_calls[0].args[1] == "agent_obo"

    def test_record_obo_attributes_user_obo(self):
        """record_obo_attributes with user_obo value must set the correct value."""
        mock_span = MagicMock()
        with (
            patch("identity_lab_auth.telemetry._is_disabled", return_value=False),
            patch("opentelemetry.trace.get_current_span", return_value=mock_span),
        ):
            record_obo_attributes(obo_hop="user_obo")

        obo_calls = [
            call for call in mock_span.set_attribute.call_args_list
            if call.args[0] == "identity_lab.obo_hop"
        ]
        assert obo_calls[0].args[1] == "user_obo"

    def test_record_obo_attributes_noop_no_pii(self):
        """record_obo_attributes must not set any PII keys."""
        mock_span = MagicMock()
        with (
            patch("identity_lab_auth.telemetry._is_disabled", return_value=False),
            patch("opentelemetry.trace.get_current_span", return_value=mock_span),
        ):
            record_obo_attributes(obo_hop="user_obo")

        set_keys = {call.args[0] for call in mock_span.set_attribute.call_args_list}
        for pii_key in _PII_KEYS:
            assert pii_key not in set_keys
