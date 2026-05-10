from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SHARED_PYTHON = ROOT / "apps" / "shared" / "python"
sys.path.append(str(SHARED_PYTHON))

from identity_lab_auth.claims import SAFE_CLAIM_KEYS, sanitize_claims


def test_safe_claim_allowlist_matches_config():
    config_path = ROOT / "config" / "claims" / "safe-claims-allowlist.json"
    config = json.loads(config_path.read_text())
    assert set(config["allowlist"]) == SAFE_CLAIM_KEYS


def test_sanitize_claims_excludes_pii_and_subject():
    raw_claims = {
        "aud": "api://audience",
        "azp": "client",
        "appid": "app-id",
        "scp": "scope.one scope.two",
        "roles": ["role-a"],
        "iss": "https://issuer.example/",
        "tid": "tenant-id",
        "exp": 1700000000,
        "nbf": 1690000000,
        "iat": 1690000001,
        "ver": "2.0",
        "email": "user@example.com",
        "name": "Example User",
        "oid": "object-id",
        "sub": "subject-id",
    }

    sanitized = sanitize_claims(raw_claims)

    for key in ("email", "name", "oid", "sub"):
        assert key not in sanitized

    assert sanitized["aud"] == "api://audience"
    assert sanitized["azp"] == "client"
    assert sanitized["appid"] == "app-id"
    assert sanitized["scp"] == "scope.one scope.two"
    assert sanitized["roles"] == ["role-a"]
    assert sanitized["iss"] == "https://issuer.example/"
    assert sanitized["tid"] == "tenant-id"
    assert sanitized["exp"] == 1700000000
    assert sanitized["nbf"] == 1690000000
    assert sanitized["iat"] == 1690000001
    assert sanitized["ver"] == "2.0"
