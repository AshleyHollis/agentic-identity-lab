from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.ci.m9_live_preflight import run_checks  # noqa: E402


def test_live_preflight_accepts_non_placeholder_values(monkeypatch) -> None:
    monkeypatch.setenv("AZURE_CLIENT_ID", "11111111-1111-4111-8111-111111111111")
    monkeypatch.setenv("AZURE_TENANT_ID", "22222222-2222-4222-8222-222222222222")
    monkeypatch.setenv("AZURE_SUBSCRIPTION_ID", "33333333-3333-4333-8333-333333333333")
    monkeypatch.setenv("AZURE_RESOURCE_GROUP", "rg-agent-identity-lab-live")
    monkeypatch.setenv("ACA_APP_NAMES", "bff,agent-execution,mcp")

    offenders = run_checks(
        required=[
            "AZURE_CLIENT_ID",
            "AZURE_TENANT_ID",
            "AZURE_SUBSCRIPTION_ID",
            "AZURE_RESOURCE_GROUP",
            "ACA_APP_NAMES",
        ],
        context="test",
    )

    assert offenders == []


def test_live_preflight_rejects_placeholder_values(monkeypatch) -> None:
    monkeypatch.setenv("AZURE_CLIENT_ID", "<client-id-placeholder>")
    monkeypatch.setenv("AZURE_TENANT_ID", "00000000-0000-0000-0000-000000000000")
    monkeypatch.setenv("AZURE_SUBSCRIPTION_ID", "{subscription-id}")

    offenders = run_checks(
        required=["AZURE_CLIENT_ID", "AZURE_TENANT_ID", "AZURE_SUBSCRIPTION_ID"],
        context="test",
    )

    assert any("AZURE_CLIENT_ID" in offender for offender in offenders)
    assert any("AZURE_TENANT_ID" in offender for offender in offenders)
    assert any("AZURE_SUBSCRIPTION_ID" in offender for offender in offenders)
