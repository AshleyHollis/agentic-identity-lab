from pathlib import Path
import json


REQUIRED_SCOPE = "mcp.write"


def load_fixture(name: str) -> dict:
    fixture_path = Path(__file__).resolve().parents[2] / "fixtures" / "sample-claims" / name
    return json.loads(fixture_path.read_text())


def test_missing_scope_rejected():
    claims = load_fixture("delegated-user.json")
    scopes = claims.get("scp", "")
    assert REQUIRED_SCOPE not in scopes.split()
