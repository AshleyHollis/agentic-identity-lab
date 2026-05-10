from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
POLICY_PATH = (
    ROOT
    / "infra"
    / "terraform"
    / "policies"
    / "apim"
    / "broken-managed-identity-replacement.xml"
)
DOC_PATH = ROOT / "docs" / "apim" / "managed-identity-token-replacement-warning.md"


def test_broken_managed_identity_policy_is_marked_as_anti_pattern() -> None:
    policy = POLICY_PATH.read_text(encoding="utf-8")
    root = ET.fromstring(policy)
    set_header = root.find("./inbound/set-header[@name='Authorization']")

    assert "ANTI-PATTERN" in policy
    assert "intentionally broken" in policy
    assert set_header is not None
    assert set_header.attrib["exists-action"] == "override"
    assert "ManagedIdentity" in (set_header.findtext("./value") or "")


def test_managed_identity_warning_explains_delegation_breakage() -> None:
    doc = DOC_PATH.read_text(encoding="utf-8").lower()

    assert "replaces" in doc
    assert "user context" in doc
    assert "breaks the obo boundary" in doc
    assert "x-obo-authorization" in doc
    assert "service-to-service" in doc
