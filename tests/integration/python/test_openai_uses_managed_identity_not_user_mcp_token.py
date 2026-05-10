from pathlib import Path
import json


def load_fixture(name: str) -> dict:
    fixture_path = Path(__file__).resolve().parents[2] / "fixtures" / "sample-claims" / name
    return json.loads(fixture_path.read_text())


def test_openai_uses_managed_identity_not_user_mcp_token():
    app_only = load_fixture("app-only.json")
    assert "roles" in app_only
    assert "scp" not in app_only
    assert "appid" in app_only
