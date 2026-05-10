from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
POLICY_PATH = ROOT / "infra" / "terraform" / "policies" / "apim" / "egress-validate-obo-token.xml"
DOC_PATH = ROOT / "docs" / "apim" / "egress-policy.md"
MCP_AUD = "api://00000000-0000-0000-0000-000000000103"


def _policy_root() -> ET.Element:
    return ET.fromstring(POLICY_PATH.read_text(encoding="utf-8"))


def _required_claim_values(validate_jwt: ET.Element, claim_name: str) -> set[str]:
    values: set[str] = set()
    for claim in validate_jwt.findall("./required-claims/claim"):
        if claim.attrib.get("name") == claim_name:
            values.update(value.text or "" for value in claim.findall("./value"))
    return values


def test_apim_egress_validates_obo_header_for_mcp_audience() -> None:
    validate_jwt = _policy_root().find("./outbound/validate-jwt")

    assert validate_jwt is not None
    assert validate_jwt.attrib["header-name"] == "x-obo-authorization"
    assert validate_jwt.attrib["require-scheme"] == "Bearer"
    assert validate_jwt.attrib["failed-validation-httpcode"] == "401"
    audiences = {audience.text for audience in validate_jwt.findall("./audiences/audience")}
    assert MCP_AUD in audiences


def test_apim_egress_enforces_delegated_scope_and_tenant_claims() -> None:
    validate_jwt = _policy_root().find("./outbound/validate-jwt")
    assert validate_jwt is not None

    assert {"mcp.access", "mcp.write"}.issubset(
        _required_claim_values(validate_jwt, "scp")
    )
    tenant_values = _required_claim_values(validate_jwt, "tid")
    assert "00000000-0000-0000-0000-000000000001" in tenant_values
    assert "00000000-0000-0000-0000-000000000002" in tenant_values


def test_apim_egress_replaces_downstream_authorization_from_obo_header() -> None:
    root = _policy_root()
    set_header = root.find("./outbound/set-header[@name='Authorization']")

    assert set_header is not None
    assert set_header.attrib["exists-action"] == "override"
    value = set_header.findtext("./value") or ""
    assert 'GetValueOrDefault("x-obo-authorization", "")' in value
    fragments = {
        fragment.attrib.get("fragment-id")
        for fragment in root.findall("./outbound/include-fragment")
    }
    assert "safe-logging" in fragments


def test_apim_egress_docs_warn_not_to_forward_original_user_token() -> None:
    doc = DOC_PATH.read_text(encoding="utf-8").lower()

    assert "not the original user token" in doc
    assert "x-obo-authorization" in doc
    assert "validate mcp audience" in doc
