from pathlib import Path
import json


EXPECTED_AUD = "api://00000000-0000-0000-0000-000000000101"


def load_fixture(name: str) -> dict:
    fixture_path = Path(__file__).resolve().parents[2] / "fixtures" / "sample-claims" / name
    return json.loads(fixture_path.read_text())


def test_wrong_audience_rejected():
    claims = load_fixture("wrong-audience.json")
    assert claims["aud"] != EXPECTED_AUD
