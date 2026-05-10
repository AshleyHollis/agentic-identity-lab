from pathlib import Path
import json


AUD_A = "api://00000000-0000-0000-0000-000000000101"
AUD_B = "api://00000000-0000-0000-0000-000000000103"


def load_fixture(name: str) -> dict:
    fixture_path = Path(__file__).resolve().parents[2] / "fixtures" / "sample-claims" / name
    return json.loads(fixture_path.read_text())


def test_same_user_identity_visible_with_changing_audience():
    claims = load_fixture("delegated-user.json")
    token_a = {**claims, "aud": AUD_A}
    token_b = {**claims, "aud": AUD_B}
    assert token_a["oid"] == token_b["oid"]
    assert token_a["aud"] != token_b["aud"]
