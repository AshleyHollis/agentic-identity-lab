from pathlib import Path
import json


TRUSTED_TENANTS = {
    "00000000-0000-0000-0000-000000000001",
    "00000000-0000-0000-0000-000000000002",
}


def load_fixture(name: str) -> dict:
    fixture_path = Path(__file__).resolve().parents[2] / "fixtures" / "sample-claims" / name
    return json.loads(fixture_path.read_text())


def test_cross_tenant_trusted_tenant_allowed():
    claims = load_fixture("delegated-user.json")
    assert claims["tid"] in TRUSTED_TENANTS
