from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Mapping


def _require_tokens(source: str, path: Path, tokens: tuple[str, ...], offenders: list[str]) -> None:
    for token in tokens:
        if token not in source:
            offenders.append(f"{path}: missing token '{token}'")


def _forbid_tokens(source: str, path: Path, tokens: tuple[str, ...], offenders: list[str]) -> None:
    for token in tokens:
        if token in source:
            offenders.append(f"{path}: forbidden token '{token}' detected")


_PLAYWRIGHT_REQUIRED_ENV = ("M9_PLAYWRIGHT_CHAT_URL", "M9_PLAYWRIGHT_ACCESS_TOKEN")
_MANUAL_REQUIRED_ENV = ("M9_BROWSER_EVIDENCE_JSON",)
_ALLOWED_TRANSPORTS = ("playwright", "agent-browser", "manual-artifact")
_PLACEHOLDER_HINTS = ("placeholder", "{", "}", "<", ">", "changeme")
_SENSITIVE_ARTIFACT_KEY_HINTS = (
    "token",
    "authorization",
    "cookie",
    "tenant",
    "client_id",
    "clientid",
    "endpoint",
    "claims",
    "trace_payload",
    "headers",
)
_SENSITIVE_ARTIFACT_VALUE_HINTS = ("bearer ", "authorization", "set-cookie", "cookie=", "http://", "https://")


def _create_traceparent() -> str:
    random_hex = os.urandom(24).hex()
    return f"00-{random_hex[:32]}-{random_hex[32:48]}-01"


def _opaque_digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def _load_playwright() -> tuple[object | None, type[Exception]]:
    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import sync_playwright
    except ModuleNotFoundError:
        return None, Exception
    return sync_playwright, PlaywrightError


def _resolve_transport(env: Mapping[str, str], transport_override: str | None = None) -> str:
    transport = (transport_override or env.get("M9_BROWSER_TRANSPORT", "playwright") or "playwright").strip()
    return transport.lower()


def _check_required_protected_input(env: Mapping[str, str], name: str, offenders: list[str]) -> None:
    value = env.get(name, "").strip()
    if not value:
        offenders.append(f"[live] missing required protected input: {name}")
        return
    lowered = value.lower()
    if any(hint in lowered for hint in _PLACEHOLDER_HINTS):
        offenders.append(f"[live] protected input appears placeholder-like: {name}")


def _contains_sensitive_value(value: object) -> bool:
    if not isinstance(value, str):
        return False
    lowered = value.lower()
    if any(hint in lowered for hint in _SENSITIVE_ARTIFACT_VALUE_HINTS):
        return True
    if lowered.count(".") >= 2 and "eyj" in lowered:
        return True
    return False


def _find_sensitive_artifact_paths(payload: object, path: str = "$") -> list[str]:
    offenders: list[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            key_text = str(key).lower()
            child_path = f"{path}.{key}"
            if any(hint in key_text for hint in _SENSITIVE_ARTIFACT_KEY_HINTS):
                offenders.append(child_path)
                continue
            offenders.extend(_find_sensitive_artifact_paths(value, child_path))
    elif isinstance(payload, list):
        for index, item in enumerate(payload):
            offenders.extend(_find_sensitive_artifact_paths(item, f"{path}[{index}]"))
    elif _contains_sensitive_value(payload):
        offenders.append(path)
    return offenders


def _to_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "y")
    if isinstance(value, (int, float)):
        return bool(value)
    return False


def _to_int(value: object, fallback: int = 0) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return fallback


def _normalize_live_result(raw_result: Mapping[str, object]) -> dict[str, object]:
    return {
        "ok": _to_bool(raw_result.get("ok", False)),
        "status": _to_int(raw_result.get("status", raw_result.get("observed_status", 0)), 0),
        "sessionIdPresent": _to_bool(
            raw_result.get("sessionIdPresent", raw_result.get("session_id_present", False))
        ),
        "expiresAtPresent": _to_bool(
            raw_result.get("expiresAtPresent", raw_result.get("expires_at_present", False))
        ),
        "targetUrlDigest": str(raw_result.get("targetUrlDigest", raw_result.get("target_url_digest", ""))).strip(),
        "resultSource": str(raw_result.get("resultSource", raw_result.get("result_source", ""))).strip(),
    }


def _evaluate_live_result(result: Mapping[str, object], expected_status: int) -> list[str]:
    offenders: list[str] = []
    observed_status = _to_int(result.get("status", 0), 0)
    if observed_status != expected_status:
        offenders.append(
            f"[live] chat/session status mismatch: expected {expected_status}, observed {observed_status}"
        )
    if not _to_bool(result.get("ok", False)):
        offenders.append("[live] chat/session response was not successful")
    if not _to_bool(result.get("sessionIdPresent", False)):
        offenders.append("[live] chat/session response missing session_id")
    return offenders


def _create_redacted_evidence(
    *,
    transport: str,
    result: Mapping[str, object],
    expected_status: int,
    fallback_chat_url: str = "",
    artifact_digest: str = "",
) -> dict[str, object]:
    target_url_digest = str(result.get("targetUrlDigest", "")).strip()
    if not target_url_digest and fallback_chat_url:
        target_url_digest = _opaque_digest(fallback_chat_url)

    evidence = {
        "transport": transport,
        "result_source": str(result.get("resultSource", "")).strip() or transport,
        "expected_status": expected_status,
        "observed_status": _to_int(result.get("status", 0), 0),
        "session_id_present": _to_bool(result.get("sessionIdPresent", False)),
        "expires_at_present": _to_bool(result.get("expiresAtPresent", False)),
        "target_url_digest": target_url_digest,
    }
    if artifact_digest:
        evidence["artifact_digest"] = artifact_digest
    return evidence


def validate_live_inputs(
    env: Mapping[str, str], transport_override: str | None = None
) -> list[str]:
    offenders: list[str] = []
    transport = _resolve_transport(env, transport_override)
    if transport not in _ALLOWED_TRANSPORTS:
        offenders.append(
            f"[live] M9_BROWSER_TRANSPORT must be one of: {', '.join(_ALLOWED_TRANSPORTS)}"
        )
        return offenders

    if transport in ("playwright", "agent-browser"):
        for name in _PLAYWRIGHT_REQUIRED_ENV:
            _check_required_protected_input(env, name, offenders)

    if transport == "manual-artifact":
        for name in _MANUAL_REQUIRED_ENV:
            _check_required_protected_input(env, name, offenders)

    if transport == "agent-browser":
        _check_required_protected_input(env, "M9_AGENT_BROWSER_COMMAND", offenders)
        command_timeout = env.get("M9_AGENT_BROWSER_TIMEOUT_SECONDS", "120").strip()
        if command_timeout:
            try:
                parsed_timeout = int(command_timeout)
                if parsed_timeout <= 0:
                    offenders.append("[live] M9_AGENT_BROWSER_TIMEOUT_SECONDS must be a positive integer")
            except ValueError:
                offenders.append("[live] M9_AGENT_BROWSER_TIMEOUT_SECONDS must be an integer")

    expected_status = env.get("M9_PLAYWRIGHT_EXPECTED_STATUS", "200").strip()
    if expected_status:
        try:
            parsed_status = int(expected_status)
            if parsed_status < 100 or parsed_status > 599:
                offenders.append("[live] M9_PLAYWRIGHT_EXPECTED_STATUS must be a valid HTTP status code")
        except ValueError:
            offenders.append("[live] M9_PLAYWRIGHT_EXPECTED_STATUS must be an integer")

    timeout_seconds = env.get("M9_PLAYWRIGHT_TIMEOUT_SECONDS", "30").strip()
    if timeout_seconds:
        try:
            parsed_timeout = int(timeout_seconds)
            if parsed_timeout <= 0:
                offenders.append("[live] M9_PLAYWRIGHT_TIMEOUT_SECONDS must be a positive integer")
        except ValueError:
            offenders.append("[live] M9_PLAYWRIGHT_TIMEOUT_SECONDS must be an integer")

    return offenders


def _load_manual_artifact(path: Path) -> tuple[dict[str, object], list[str], str]:
    offenders: list[str] = []
    if not path.exists():
        return {}, [f"[live] manual artifact file not found: {path}"], ""
    try:
        content = path.read_text(encoding="utf-8")
        payload = json.loads(content)
    except json.JSONDecodeError:
        return {}, [f"[live] manual artifact is not valid JSON: {path.name}"], ""

    if not isinstance(payload, dict):
        return {}, [f"[live] manual artifact JSON must be an object: {path.name}"], ""

    sensitive_paths = _find_sensitive_artifact_paths(payload)
    if sensitive_paths:
        offenders.extend(
            f"[live] artifact contains non-redacted sensitive data at {artifact_path}"
            for artifact_path in sensitive_paths
        )
    return payload, offenders, _opaque_digest(content)


def run_live_playwright_smoke(env: Mapping[str, str]) -> tuple[dict[str, object], list[str]]:
    offenders: list[str] = []
    evidence: dict[str, object] = {}
    sync_playwright, PlaywrightError = _load_playwright()
    if sync_playwright is None:
        offenders.append(
            "[live] Playwright dependency is missing. Install with: "
            "python -m pip install playwright && python -m playwright install chromium"
        )
        return evidence, offenders

    chat_url = env["M9_PLAYWRIGHT_CHAT_URL"].strip()
    access_token = env["M9_PLAYWRIGHT_ACCESS_TOKEN"].strip()
    expected_status = int(env.get("M9_PLAYWRIGHT_EXPECTED_STATUS", "200").strip() or "200")
    timeout_ms = int(env.get("M9_PLAYWRIGHT_TIMEOUT_SECONDS", "30").strip() or "30") * 1000
    display_name = env.get("M9_PLAYWRIGHT_DISPLAY_NAME", "M9 Browser Smoke")
    traceparent = _create_traceparent()

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            page.goto("about:blank", wait_until="load")
            response = page.evaluate(
                """
                async ({ chatUrl, accessToken, displayName, traceparent, timeoutMs }) => {
                  const controller = new AbortController();
                  const timeout = setTimeout(() => controller.abort('timeout'), timeoutMs);
                  try {
                    const result = await fetch(chatUrl, {
                      method: 'POST',
                      headers: {
                        Authorization: `Bearer ${accessToken}`,
                        'Content-Type': 'application/json',
                        traceparent
                      },
                      body: JSON.stringify({ display_name: displayName ?? null }),
                      signal: controller.signal
                    });
                    let payload = null;
                    try {
                      payload = await result.json();
                    } catch (_error) {
                      payload = null;
                    }
                    return {
                      ok: result.ok,
                      status: result.status,
                      sessionIdPresent: Boolean(payload && payload.session_id),
                      expiresAtPresent: Boolean(payload && payload.expires_at)
                    };
                  } finally {
                    clearTimeout(timeout);
                  }
                }
                """,
                {
                    "chatUrl": chat_url,
                    "accessToken": access_token,
                    "displayName": display_name,
                    "traceparent": traceparent,
                    "timeoutMs": timeout_ms,
                },
            )
            context.clear_cookies()
            context.close()
            browser.close()
    except PlaywrightError as exc:
        offenders.append(f"[live] Playwright browser check failed: {exc.__class__.__name__}")
        return evidence, offenders
    except Exception as exc:  # pragma: no cover - defensive fallback
        offenders.append(f"[live] Playwright browser check failed: {exc.__class__.__name__}")
        return evidence, offenders

    if not isinstance(response, dict):
        offenders.append("[live] Playwright browser check returned an invalid response payload")
        return evidence, offenders

    normalized = _normalize_live_result(response)
    normalized["targetUrlDigest"] = _opaque_digest(chat_url)
    normalized["resultSource"] = "playwright-runtime-fetch"
    offenders.extend(_evaluate_live_result(normalized, expected_status))
    evidence = _create_redacted_evidence(
        transport="playwright",
        result=normalized,
        expected_status=expected_status,
        fallback_chat_url=chat_url,
    )
    return evidence, offenders


def run_live_manual_artifact_smoke(env: Mapping[str, str]) -> tuple[dict[str, object], list[str]]:
    offenders: list[str] = []
    expected_status = int(env.get("M9_PLAYWRIGHT_EXPECTED_STATUS", "200").strip() or "200")
    artifact_path = Path(env["M9_BROWSER_EVIDENCE_JSON"].strip())
    payload, artifact_offenders, artifact_digest = _load_manual_artifact(artifact_path)
    offenders.extend(artifact_offenders)
    if artifact_offenders:
        return {}, offenders

    normalized = _normalize_live_result(payload)
    if not normalized["resultSource"]:
        normalized["resultSource"] = "manual-browser-artifact"
    offenders.extend(_evaluate_live_result(normalized, expected_status))
    evidence = _create_redacted_evidence(
        transport="manual-artifact",
        result=normalized,
        expected_status=expected_status,
        fallback_chat_url=env.get("M9_PLAYWRIGHT_CHAT_URL", "").strip(),
        artifact_digest=artifact_digest,
    )
    return evidence, offenders


def run_live_agent_browser_smoke(env: Mapping[str, str]) -> tuple[dict[str, object], list[str]]:
    command = env["M9_AGENT_BROWSER_COMMAND"].strip()
    timeout_seconds = int(env.get("M9_AGENT_BROWSER_TIMEOUT_SECONDS", "120").strip() or "120")
    expected_status = int(env.get("M9_PLAYWRIGHT_EXPECTED_STATUS", "200").strip() or "200")
    offenders: list[str] = []
    evidence: dict[str, object] = {}
    try:
        completed = subprocess.run(
            command,
            shell=True,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            env=dict(os.environ),
        )
    except subprocess.TimeoutExpired:
        offenders.append("[live] agent-browser command timed out")
        return evidence, offenders
    except OSError as exc:
        offenders.append(f"[live] agent-browser command failed to start: {exc.__class__.__name__}")
        return evidence, offenders

    if completed.returncode != 0:
        offenders.append(f"[live] agent-browser command exited with code {completed.returncode}")
        return evidence, offenders

    stdout = (completed.stdout or "").strip()
    if not stdout:
        offenders.append("[live] agent-browser command returned empty stdout")
        return evidence, offenders

    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        offenders.append("[live] agent-browser command must emit JSON to stdout")
        return evidence, offenders

    if not isinstance(payload, dict):
        offenders.append("[live] agent-browser command JSON payload must be an object")
        return evidence, offenders

    sensitive_paths = _find_sensitive_artifact_paths(payload)
    if sensitive_paths:
        offenders.extend(
            f"[live] agent-browser output contains non-redacted sensitive data at {artifact_path}"
            for artifact_path in sensitive_paths
        )
        return evidence, offenders

    normalized = _normalize_live_result(payload)
    if not normalized["resultSource"]:
        normalized["resultSource"] = "agent-browser-command"
    offenders.extend(_evaluate_live_result(normalized, expected_status))
    evidence = _create_redacted_evidence(
        transport="agent-browser",
        result=normalized,
        expected_status=expected_status,
        fallback_chat_url=env.get("M9_PLAYWRIGHT_CHAT_URL", "").strip(),
    )
    return evidence, offenders


def run_live_transport_smoke(env: Mapping[str, str], transport: str) -> tuple[dict[str, object], list[str]]:
    if transport == "playwright":
        return run_live_playwright_smoke(env)
    if transport == "agent-browser":
        return run_live_agent_browser_smoke(env)
    if transport == "manual-artifact":
        return run_live_manual_artifact_smoke(env)
    return {}, [f"[live] unsupported transport: {transport}"]


def validate_browser_smoke_wiring(repo_root: Path) -> list[str]:
    offenders: list[str] = []

    spa_client = repo_root / "apps" / "spa-public-client" / "react-vite" / "src" / "bffClient.ts"
    spa_auth = repo_root / "apps" / "spa-public-client" / "react-vite" / "src" / "authConfig.ts"
    spa_readme = repo_root / "apps" / "spa-public-client" / "react-vite" / "README.md"
    classic_loader = repo_root / "apps" / "sharepoint-classic" / "chat-loader-js" / "chat-loader.js"
    classic_config = repo_root / "apps" / "sharepoint-classic" / "chat-loader-js" / "config.example.json"
    classic_readme = repo_root / "apps" / "sharepoint-classic" / "chat-loader-js" / "README.md"
    spfx_webpart = (
        repo_root
        / "apps"
        / "spfx-webpart"
        / "identity-chat-webpart"
        / "src"
        / "webparts"
        / "identityChat"
        / "IdentityChatWebPart.ts"
    )
    spfx_solution = (
        repo_root
        / "apps"
        / "spfx-webpart"
        / "identity-chat-webpart"
        / "config"
        / "package-solution.json"
    )
    spfx_readme = repo_root / "apps" / "spfx-webpart" / "identity-chat-webpart" / "README.md"
    bff_main = repo_root / "apps" / "bff" / "python-fastapi" / "app" / "main.py"
    bff_readme = repo_root / "apps" / "bff" / "python-fastapi" / "README.md"

    required_files = [
        spa_client,
        spa_auth,
        spa_readme,
        classic_loader,
        classic_config,
        classic_readme,
        spfx_webpart,
        spfx_solution,
        spfx_readme,
        bff_main,
        bff_readme,
    ]
    for file in required_files:
        if not file.exists():
            offenders.append(f"missing required wiring file: {file}")

    if offenders:
        return offenders

    spa_text = spa_client.read_text(encoding="utf-8", errors="ignore")
    spa_auth_text = spa_auth.read_text(encoding="utf-8", errors="ignore")
    spa_readme_text = spa_readme.read_text(encoding="utf-8", errors="ignore").lower()
    classic_text = classic_loader.read_text(encoding="utf-8", errors="ignore")
    classic_config_text = classic_config.read_text(encoding="utf-8", errors="ignore")
    classic_readme_text = classic_readme.read_text(encoding="utf-8", errors="ignore").lower()
    spfx_text = spfx_webpart.read_text(encoding="utf-8", errors="ignore")
    spfx_solution_text = spfx_solution.read_text(encoding="utf-8", errors="ignore")
    spfx_readme_text = spfx_readme.read_text(encoding="utf-8", errors="ignore").lower()
    bff_text = bff_main.read_text(encoding="utf-8", errors="ignore")
    bff_readme_text = bff_readme.read_text(encoding="utf-8", errors="ignore").lower()

    _require_tokens(
        spa_text,
        spa_client,
        (
            "VITE_BFF_BASE_URL",
            "Authorization: `Bearer ${input.accessToken}`",
            "traceparent: createTraceparent()",
            "/chat/session",
            "display_name",
        ),
        offenders,
    )
    _require_tokens(
        spa_auth_text,
        spa_auth,
        ("cacheLocation: 'sessionStorage'", "VITE_BFF_API_SCOPE", "PublicClientApplication"),
        offenders,
    )
    _forbid_tokens(spa_auth_text, spa_auth, ("cacheLocation: 'localStorage'",), offenders)
    _forbid_tokens(spa_text, spa_client, ('"userId"', "userId:", "console.log(input.accessToken)"), offenders)

    _require_tokens(
        classic_text,
        classic_loader,
        (
            "Authorization: `Bearer ${config.accessToken}`",
            "traceparent: config.traceparent",
            "display_name",
            "bffBaseUrl is required.",
            "bffResourceUri is required.",
        ),
        offenders,
    )
    _require_tokens(classic_config_text, classic_config, ('"bffBaseUrl"', '"bffResourceUri"'), offenders)
    _forbid_tokens(
        classic_text,
        classic_loader,
        ("userId", "localStorage.setItem", "sessionStorage.setItem", "indexedDB"),
        offenders,
    )

    _require_tokens(
        spfx_text,
        spfx_webpart,
        (
            "AadHttpClient",
            ".aadHttpClientFactory.getClient(",
            "/chat/session",
            "display_name",
            "traceparent",
        ),
        offenders,
    )
    _require_tokens(
        spfx_solution_text,
        spfx_solution,
        ('"resource": "api://{client-id}"', '"scope": "access_as_user"'),
        offenders,
    )
    _forbid_tokens(
        spfx_text,
        spfx_webpart,
        ("AadTokenProvider", "SPHttpClient", "userId", "localStorage.setItem", "sessionStorage.setItem"),
        offenders,
    )

    _require_tokens(
        bff_text,
        bff_main,
        ('@app.get("/whoami")', '@app.get("/debug/claims")', '@app.post("/chat/session")'),
        offenders,
    )
    if "returns safe claim metadata only" not in bff_readme_text:
        offenders.append(f"{bff_readme}: missing safe claim metadata statement")

    if "console.log(input.accesstoken)" in spa_text.lower():
        offenders.append(f"{spa_client}: token logging pattern detected")

    if "authorization" in bff_text.lower() and "allow_headers" not in bff_text:
        offenders.append(f"{bff_main}: unexpected authorization handling pattern")

    for readme_path, readme_text in (
        (spa_readme, spa_readme_text),
        (classic_readme, classic_readme_text),
        (spfx_readme, spfx_readme_text),
    ):
        if "m9 protected live smoke setup" not in readme_text:
            offenders.append(f"{readme_path}: missing 'M9 protected live smoke setup' section")

    return offenders


def main() -> int:
    parser = argparse.ArgumentParser(description="M8 canonical browser smoke harness wiring validator")
    parser.add_argument(
        "--mode",
        choices=("static", "live"),
        default="static",
    )
    parser.add_argument(
        "--transport",
        choices=_ALLOWED_TRANSPORTS,
        default="",
        help="Live transport override (defaults to M9_BROWSER_TRANSPORT or playwright)",
    )
    parser.add_argument("--output-json", default="")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    offenders = validate_browser_smoke_wiring(repo_root)
    live_evidence: dict[str, object] = {}
    transport = "static"
    notes = ["Static wiring checks validated for browser -> APIM -> BFF -> Agent Execution Service -> MCP."]

    if args.mode == "live":
        transport = _resolve_transport(os.environ, args.transport or None)
        live_offenders = validate_live_inputs(os.environ, transport_override=transport)
        offenders.extend(live_offenders)
        if not live_offenders:
            live_evidence, execution_offenders = run_live_transport_smoke(os.environ, transport)
            offenders.extend(execution_offenders)
            if execution_offenders:
                notes.append(f"Live browser smoke execution failed for transport '{transport}'.")
            else:
                notes.append(f"Live browser smoke execution passed for transport '{transport}'.")
        else:
            notes.append("Live browser smoke skipped due to protected input validation failures.")

    result = {
        "mode": args.mode,
        "transport": transport,
        "chain": "browser -> APIM -> BFF -> Agent Execution Service -> MCP",
        "status": "ok" if not offenders else "failed",
        "offenders": offenders,
        "live_execution": args.mode == "live",
        "notes": notes,
        "live_evidence": live_evidence,
    }

    if args.output_json:
        Path(args.output_json).write_text(json.dumps(result, indent=2), encoding="utf-8")

    if offenders:
        for offender in offenders:
            print(offender)
        return 1

    if args.mode == "live":
        print(f"M8 browser smoke harness live checks passed ({transport}).")
    else:
        print("M8 browser smoke harness wiring checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
