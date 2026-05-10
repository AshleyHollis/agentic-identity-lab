from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
POLICY_PATH = ROOT / "infra" / "terraform" / "policies" / "apim" / "ingress-validate-user-token.xml"
BFF_AUD = "api://00000000-0000-0000-0000-000000000101"
GATEWAY_AUD = "api://00000000-0000-0000-0000-000000000102"


def _policy_root() -> ET.Element:
    return ET.fromstring(POLICY_PATH.read_text(encoding="utf-8"))


def _required_claim_values(validate_jwt: ET.Element, claim_name: str) -> set[str]:
    values: set[str] = set()
    for claim in validate_jwt.findall("./required-claims/claim"):
        if claim.attrib.get("name") == claim_name:
            values.update(value.text or "" for value in claim.findall("./value"))
    return values


def test_apim_ingress_validates_authorization_bearer_token() -> None:
    validate_jwt = _policy_root().find("./inbound/validate-jwt")

    assert validate_jwt is not None
    assert validate_jwt.attrib["header-name"] == "Authorization"
    assert validate_jwt.attrib["require-scheme"] == "Bearer"
    assert validate_jwt.attrib["failed-validation-httpcode"] == "401"
    assert validate_jwt.find("./openid-config") is not None


def test_apim_ingress_enforces_audience_scope_and_tenant_allowlist() -> None:
    root = _policy_root()
    validate_jwt = root.find("./inbound/validate-jwt")
    assert validate_jwt is not None

    audiences = {audience.text for audience in validate_jwt.findall("./audiences/audience")}
    assert BFF_AUD in audiences
    assert GATEWAY_AUD in POLICY_PATH.read_text(encoding="utf-8")
    assert {"mcp.access", "mcp.write"}.issubset(
        _required_claim_values(validate_jwt, "scp")
    )
    tenant_values = _required_claim_values(validate_jwt, "tid")
    assert "00000000-0000-0000-0000-000000000001" in tenant_values
    assert "00000000-0000-0000-0000-000000000002" in tenant_values


def test_apim_ingress_preserves_delegated_authorization_header() -> None:
    root = _policy_root()
    set_header = root.find("./inbound/set-header[@name='Authorization']")

    assert set_header is not None
    assert set_header.attrib["exists-action"] == "override"
    value = set_header.findtext("./value") or ""
    assert 'GetValueOrDefault("Authorization", "")' in value
    fragments = {
        fragment.attrib.get("fragment-id")
        for fragment in root.findall("./inbound/include-fragment")
    }
    assert {"correlation-id", "rate-limit"}.issubset(fragments)
