from pathlib import Path
import json


def load_fixture(name: str) -> dict:
    fixture_path = Path(__file__).resolve().parents[2] / "fixtures" / "sample-claims" / name
    return json.loads(fixture_path.read_text())


def test_app_only_token_rejected():
    claims = load_fixture("app-only.json")
    assert "roles" in claims
    assert "scp" not in claims
