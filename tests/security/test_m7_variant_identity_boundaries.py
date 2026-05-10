"""M7 T07 variant identity boundary regression checks (offline/static)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPA_AUTH_CONFIG = ROOT / "apps" / "spa-public-client" / "react-vite" / "src" / "authConfig.ts"
CLASSIC_LOADER = ROOT / "apps" / "sharepoint-classic" / "chat-loader-js" / "chat-loader.js"
SPFX_WEBPART = (
    ROOT
    / "apps"
    / "spfx-webpart"
    / "identity-chat-webpart"
    / "src"
    / "webparts"
    / "identityChat"
    / "IdentityChatWebPart.ts"
)
SPFX_PACKAGE_SOLUTION = (
    ROOT
    / "apps"
    / "spfx-webpart"
    / "identity-chat-webpart"
    / "config"
    / "package-solution.json"
)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_spa_msal_cache_is_sessionstorage_only() -> None:
    """SPA must explicitly use sessionStorage and never localStorage for MSAL cache."""
    source = _read_text(SPA_AUTH_CONFIG)
    assert "cacheLocation: 'sessionStorage'" in source
    assert "cacheLocation: 'localStorage'" not in source


def test_classic_loader_no_storage_persistence_and_no_userid_auth_signal() -> None:
    """Classic loader must not persist token and must not send userId for auth."""
    source = _read_text(CLASSIC_LOADER)
    assert "localStorage.setItem" not in source
    assert "sessionStorage.setItem" not in source
    assert "indexedDB" not in source
    assert "userId:" not in source
    assert '"userId"' not in source


def test_spfx_uses_aadhttpclient_and_avoids_raw_token_clients() -> None:
    """SPFx BFF call path must use AadHttpClient and avoid AadTokenProvider/SPHttpClient."""
    source = _read_text(SPFX_WEBPART)
    assert "AadHttpClient" in source
    assert ".aadHttpClientFactory.getClient(" in source
    assert "AadTokenProvider" not in source
    assert "SPHttpClient" not in source
    assert "localStorage.setItem" not in source
    assert "sessionStorage.setItem" not in source
    assert "userId" not in source
    assert "display_name" in source


def test_spfx_permission_requests_are_placeholder_bff_scope_only() -> None:
    """T-SEC-12: package-solution permission requests must be placeholder-only and BFF-scoped."""
    package_solution = json.loads(_read_text(SPFX_PACKAGE_SOLUTION))
    requests = package_solution["solution"]["webApiPermissionRequests"]
    assert requests, "webApiPermissionRequests must include a BFF delegated scope"

    for request in requests:
        resource = str(request.get("resource", ""))
        scope = str(request.get("scope", ""))
        assert resource.startswith("api://"), f"Expected BFF app URI, got {resource!r}"
        assert "{client-id}" in resource, f"Expected placeholder client id, got {resource!r}"
        assert "graph" not in resource.lower(), f"Graph scope is out of bounds: {resource!r}"
        assert scope == "access_as_user", f"Unexpected scope {scope!r}"


def test_variant_code_has_no_pii_or_raw_token_trace_attributes() -> None:
    """Variant source should not stamp token/PII data into trace/log attributes."""
    sources = [
        _read_text(SPA_AUTH_CONFIG),
        _read_text(CLASSIC_LOADER),
        _read_text(SPFX_WEBPART),
    ]

    prohibited_attribute_snippets = [
        "setAttribute('oid'",
        'setAttribute("oid"',
        "setAttribute('sub'",
        'setAttribute("sub"',
        "setAttribute('email'",
        'setAttribute("email"',
        "setAttribute('upn'",
        'setAttribute("upn"',
        "setAttribute('preferred_username'",
        'setAttribute("preferred_username"',
        "tracestate",
    ]
    prohibited_token_snippets = [
        "console.log(token",
        "console.debug(token",
        "console.info(token",
        "logger.debug(token",
        "logger.info(token",
    ]

    joined = "\n".join(sources)
    for snippet in prohibited_attribute_snippets + prohibited_token_snippets:
        assert snippet not in joined
