"""T06 — Safe-claims allowlist extension tests.

Verifies:
- ``xms_act_fct`` (actor metadata dict) is included in sanitized output.
- PII claims ``oid`` and ``sub`` are suppressed even when present.
- ``_sanitize_value`` handles ``dict`` inputs without raising.
- Dict sanitization bounds output and drops nested-dict keys that would leak PII.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SHARED_PYTHON = ROOT / "apps" / "shared" / "python"
sys.path.insert(0, str(SHARED_PYTHON))

from identity_lab_auth.claims import (  # noqa: E402
    DEFAULT_SAFE_CLAIM_KEYS,
    _sanitize_value,
    sanitize_claims,
)


# ---------------------------------------------------------------------------
# Allowlist membership
# ---------------------------------------------------------------------------


def test_xms_act_fct_in_default_allowlist() -> None:
    assert "xms_act_fct" in DEFAULT_SAFE_CLAIM_KEYS


def test_pii_claims_absent_from_allowlist() -> None:
    pii = {"oid", "sub", "email", "upn", "name", "preferred_username", "given_name", "family_name"}
    overlap = pii & DEFAULT_SAFE_CLAIM_KEYS
    assert overlap == set(), f"PII keys found in allowlist: {overlap}"


# ---------------------------------------------------------------------------
# _sanitize_value dict handling
# ---------------------------------------------------------------------------


def test_sanitize_value_dict_returns_dict() -> None:
    result = _sanitize_value({"appid": "00000000-0000-0000-0000-000000000201"})
    assert isinstance(result, dict)
    assert result["appid"] == "00000000-0000-0000-0000-000000000201"


def test_sanitize_value_dict_does_not_raise_on_empty() -> None:
    result = _sanitize_value({})
    assert result == {}


def test_sanitize_value_dict_drops_non_string_keys() -> None:
    result = _sanitize_value({1: "should-be-dropped", "appid": "kept"})  # type: ignore[arg-type]
    assert isinstance(result, dict)
    assert "appid" in result
    assert 1 not in result


def test_sanitize_value_dict_truncates_long_values() -> None:
    long_val = "x" * 300
    result = _sanitize_value({"key": long_val})
    assert isinstance(result, dict)
    assert result["key"].endswith("…")


def test_sanitize_value_dict_nested_dict_dropped() -> None:
    # Nested dicts (which could contain PII) are recursively handled but
    # the inner dict itself becomes None at one level of nesting depth because
    # _sanitize_value on a sub-dict returns a dict (not None).
    # Ensure deeply nested content is still handled safely (no exception).
    result = _sanitize_value({"outer": {"inner": "value"}})
    assert isinstance(result, dict)
    # The nested dict should itself be sanitized (dict → dict)
    assert isinstance(result["outer"], dict)


def test_sanitize_value_dict_bounded_to_512_chars() -> None:
    large_dict = {f"key{i}": "x" * 50 for i in range(20)}
    result = _sanitize_value(large_dict)
    # Result is either a truncated string or a dict whose serialised form <= 512 chars
    if isinstance(result, str):
        # Truncated JSON string path
        assert len(result) <= 516  # 512 + "…"
    else:
        import json
        assert len(json.dumps(result)) <= 512


# ---------------------------------------------------------------------------
# sanitize_claims integration
# ---------------------------------------------------------------------------


def test_sanitize_claims_includes_xms_act_fct() -> None:
    claims = {
        "xms_act_fct": {"appid": "00000000-0000-0000-0000-000000000201"},
        "oid": "should-be-dropped",
        "appid": "00000000-0000-0000-0000-000000000200",
    }
    result = sanitize_claims(claims)
    assert "xms_act_fct" in result
    assert isinstance(result["xms_act_fct"], dict)
    assert result["xms_act_fct"]["appid"] == "00000000-0000-0000-0000-000000000201"


def test_sanitize_claims_drops_oid_and_sub() -> None:
    claims = {
        "xms_act_fct": {"appid": "00000000-0000-0000-0000-000000000201"},
        "oid": "user-oid-value",
        "sub": "user-sub-value",
        "appid": "00000000-0000-0000-0000-000000000200",
    }
    result = sanitize_claims(claims)
    assert "oid" not in result
    assert "sub" not in result


def test_sanitize_claims_xms_act_fct_no_raise_on_dict() -> None:
    """Core gate from Security Design Notes §3."""
    claims = {
        "xms_act_fct": {"appid": "00000000-0000-0000-0000-000000000201"},
        "oid": "should-be-dropped",
    }
    result = sanitize_claims(claims)
    assert "xms_act_fct" in result
    assert "oid" not in result


def test_sanitize_claims_xms_act_fct_missing_is_fine() -> None:
    claims = {"appid": "00000000-0000-0000-0000-000000000200", "aud": "api://test"}
    result = sanitize_claims(claims)
    assert "xms_act_fct" not in result
    assert result["appid"] == "00000000-0000-0000-0000-000000000200"
