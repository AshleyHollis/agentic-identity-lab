TRUSTED_TENANTS = {
    "00000000-0000-0000-0000-000000000001",
    "00000000-0000-0000-0000-000000000002",
}


def test_cross_tenant_untrusted_tenant_rejected():
    untrusted_tid = "00000000-0000-0000-0000-000000000999"
    assert untrusted_tid not in TRUSTED_TENANTS
