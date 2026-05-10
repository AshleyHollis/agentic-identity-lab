from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SHARED_PYTHON = ROOT / "apps" / "shared" / "python"
sys.path.append(str(SHARED_PYTHON))

from identity_lab_auth.guards import AuthContext  # noqa: E402
from identity_lab_auth.obo import exchange_on_behalf_of  # noqa: E402
from identity_lab_auth.token_type import classify_claims_token_type  # noqa: E402

FIXTURES_DIR = ROOT / "tests" / "fixtures" / "sample-claims"
DOWNSTREAM_AUD = "api://00000000-0000-0000-0000-000000000103"


def _load_fixture(name: str) -> dict[str, object]:
    payload = (FIXTURES_DIR / f"{name}.json").read_text(encoding="utf-8")
    return json.loads(payload)


def test_obo_exchange_mints_downstream_claims() -> None:
    inbound = _load_fixture("delegated-user")
    token_type = classify_claims_token_type(inbound)
    context = AuthContext.from_claims(inbound, token_type=token_type)

    obo_claims = exchange_on_behalf_of(
        context,
        downstream_audience=DOWNSTREAM_AUD,
        downstream_scopes=["mcp.write"],
    )

    assert obo_claims["aud"] == DOWNSTREAM_AUD
    assert obo_claims["scp"] == "mcp.write"
    assert context.claims["aud"] == inbound["aud"]
    assert obo_claims["aud"] != context.claims["aud"]
    assert "sub" not in obo_claims
    assert "oid" not in obo_claims


def test_obo_exchange_rejects_app_only_token() -> None:
    inbound = _load_fixture("app-only")
    token_type = classify_claims_token_type(inbound)
    context = AuthContext.from_claims(inbound, token_type=token_type)

    with pytest.raises(ValueError, match="delegated user token"):
        exchange_on_behalf_of(context, downstream_audience=DOWNSTREAM_AUD)
