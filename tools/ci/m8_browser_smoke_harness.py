from __future__ import annotations

import argparse
import json
from pathlib import Path


def _require_tokens(source: str, path: Path, tokens: tuple[str, ...], offenders: list[str]) -> None:
    for token in tokens:
        if token not in source:
            offenders.append(f"{path}: missing token '{token}'")


def _forbid_tokens(source: str, path: Path, tokens: tuple[str, ...], offenders: list[str]) -> None:
    for token in tokens:
        if token in source:
            offenders.append(f"{path}: forbidden token '{token}' detected")


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
    parser.add_argument("--mode", choices=("static", "live"), default="static")
    parser.add_argument("--output-json", default="")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    offenders = validate_browser_smoke_wiring(repo_root)

    result = {
        "mode": args.mode,
        "chain": "browser -> APIM -> BFF -> Agent Execution Service -> MCP",
        "status": "ok" if not offenders else "failed",
        "offenders": offenders,
        "live_execution": args.mode == "live",
        "notes": [
            "No live browser or endpoint calls are made by this harness.",
            "Live mode is a workflow contract placeholder for protected environments.",
        ],
    }

    if args.output_json:
        Path(args.output_json).write_text(json.dumps(result, indent=2), encoding="utf-8")

    if offenders:
        for offender in offenders:
            print(offender)
        return 1

    print("M8 browser smoke harness wiring checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
