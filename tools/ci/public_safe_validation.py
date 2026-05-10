from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS_DIR = ROOT / ".github" / "workflows"
SPEC_DESIGN = ROOT / ".squad" / "specs" / "008-live-azure-e2e-gate" / "design.md"
TELEMETRY_TEST = ROOT / "tests" / "security" / "test_telemetry.py"
KQL_DIR = ROOT / "tools" / "telemetry" / "kql"
RBAC_DOCS = [
    ROOT / "docs" / "deployment" / "azure-container-apps.md",
    ROOT / "docs" / "deployment" / "aca" / "README.md",
]
M8_DEPLOY_WORKFLOW = WORKFLOWS_DIR / "m8-deploy-live.yml"
M8_START_RESUME_WORKFLOW = WORKFLOWS_DIR / "m8-start-resume.yml"
M8_NIGHTLY_SHUTDOWN_WORKFLOW = WORKFLOWS_DIR / "m8-nightly-shutdown.yml"
M8_OIDC_CONTRACT_WORKFLOW = WORKFLOWS_DIR / "m8-live-oidc-contract.yml"
M8_SMOKE_TRACE_WORKFLOW = WORKFLOWS_DIR / "m8-smoke-trace.yml"
M8_SMOKE_HARNESS = ROOT / "tools" / "ci" / "m8_browser_smoke_harness.py"
M8_SMOKE_CONTRACT = ROOT / "tools" / "ci" / "m8_smoke_trace_contract.py"
M9_LIVE_PREFLIGHT = ROOT / "tools" / "ci" / "m9_live_preflight.py"

_GUID_PATTERN = re.compile(
    r"\b([0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})\b",
    re.IGNORECASE,
)
_LIVE_DEFAULT_PATTERN = re.compile(
    r"(?im)^\s*LIVE_AZURE_TESTS\s*[:=]\s*(?:\"?true\"?)\s*$", re.IGNORECASE
)
_FORBIDDEN_PUBLIC_PATTERNS = [
    re.compile(r"uses:\s*azure/login@", re.IGNORECASE),
    re.compile(r"id-token\s*:\s*write", re.IGNORECASE),
    re.compile(r"\benvironment\s*:", re.IGNORECASE),
    re.compile(r"\bterraform\s+(?:-[^\s]+\s+)*(?:apply|destroy)\b", re.IGNORECASE),
    re.compile(r"\baz\s+login\b", re.IGNORECASE),
    re.compile(r"\baz\s+account\s+get-access-token\b", re.IGNORECASE),
    re.compile(r"\baz\s+deployment\s+\w+\s+(?:create|what-if|validate)\b", re.IGNORECASE),
]
_FORBIDDEN_SHUTDOWN_PATTERNS = [
    re.compile(r"\bterraform\s+(?:-[^\s]+\s+)*(?:apply|destroy)\b", re.IGNORECASE),
    re.compile(r"\baz\s+deployment\s+\w+\s+(?:create|what-if|validate)\b", re.IGNORECASE),
    re.compile(r"\baz\s+group\s+delete\b", re.IGNORECASE),
    re.compile(r"\baz\s+resource\s+delete\b", re.IGNORECASE),
    re.compile(r"\baz\s+containerapp\s+delete\b", re.IGNORECASE),
]
_SENSITIVE_LITERAL_PATTERNS = [
    re.compile(r"authorization\s*:\s*bearer\s+[a-z0-9_\-\.=]+", re.IGNORECASE),
    re.compile(r"\bbearer\s+[a-z0-9_\-\.=]{20,}", re.IGNORECASE),
    re.compile(r"\beyj[a-z0-9_-]{10,}\.[a-z0-9_-]{10,}\.[a-z0-9_-]{10,}\b", re.IGNORECASE),
    re.compile(r"\bgh[pousr]_[a-z0-9]{20,}\b", re.IGNORECASE),
]
_ALLOWED_GUIDS = {"00000000-0000-0000-0000-000000000000"}
_PLACEHOLDER_HINTS = (
    "placeholder",
    "{tenant-id}",
    "{subscription-id}",
    "{client-id}",
    "<tenant-guid-placeholder>",
    "<subscription-guid-placeholder>",
    "<client-id-placeholder>",
)
_IDENTIFIER_SCAN_DIRS = [
    ROOT / ".github" / "workflows",
    ROOT / "infra" / "terraform" / "environments" / "single-tenant-aca",
]
_IDENTIFIER_SCAN_FILE_SUFFIXES = {".yml", ".yaml", ".tf", ".tfvars", ".example", ".json"}
_UNSAFE_ARTIFACT_PATTERNS = [
    re.compile(r"\.har(\b|$)", re.IGNORECASE),
    re.compile(r"\.trace(\b|$)", re.IGNORECASE),
    re.compile(r"\.log(\b|$)", re.IGNORECASE),
    re.compile(r"\b(jwt|cookie|secret|screenshot|video)\b", re.IGNORECASE),
]
_AZ_ACCOUNT_SHOW_PATTERN = re.compile(r"\baz\s+account\s+show\b", re.IGNORECASE)
_AZ_ACCOUNT_SHOW_SAFE_OUTPUT_PATTERN = re.compile(
    r"\baz\s+account\s+show\b(?:(?!\n).)*(?:--output|-o)\s+none\b",
    re.IGNORECASE,
)
_AZ_ACCOUNT_SHOW_SAFE_QUERY_PATTERN = re.compile(
    r"\baz\s+account\s+show\b(?:(?!\n).)*(?:--query)\s+"
    r"(?:(?!\n).)*(?:tenantid|subscriptionid|id|name|user)",
    re.IGNORECASE,
)
_LIVE_ENDPOINT_VAR_PATTERN = re.compile(
    r"\$(?:\{)?([A-Z][A-Z0-9_]*(?:URL|URI|ENDPOINT|HOST)[A-Z0-9_]*)\}?"
)
_LIVE_ENDPOINT_EXPRESSION_PATTERN = re.compile(
    r"\$\{\{\s*(?:vars|env)\.([A-Z][A-Z0-9_]*(?:URL|URI|ENDPOINT|HOST)[A-Z0-9_]*)\s*\}\}"
)
_UNSAFE_OUTPUT_COMMAND_PATTERN = re.compile(r"\b(?:echo|printf|cat)\b", re.IGNORECASE)
_REQUIRED_WORKFLOW_PHRASES: dict[Path, tuple[str, ...]] = {
    M8_DEPLOY_WORKFLOW: ("environment: lab-live-azure-deploy", "id-token: write", "azure/login@v2"),
    M8_START_RESUME_WORKFLOW: ("environment: lab-live-azure-ops", "id-token: write", "azure/login@v2"),
    M8_NIGHTLY_SHUTDOWN_WORKFLOW: ("environment: lab-live-azure-ops", "id-token: write", "azure/login@v2"),
    M8_OIDC_CONTRACT_WORKFLOW: ("lab-live-azure-deploy", "lab-live-azure-smoke", "lab-live-azure-ops"),
}
_REQUIRED_RBAC_DOC_PHRASES = (
    "deploy and smoke identities must be separate",
    "lifecycle identity is stop/start/scale focused",
    "must not perform broad deploy/apply/destroy",
    "scoped to the lab resource group",
)
_TELEMETRY_REQUIRED_TOKENS = [
    "requests",
    "dependencies",
    "traces",
    "logs",
    "authorization",
    "oid",
    "sub",
    "email",
    "upn",
    "preferred_username",
    "given_name",
    "family_name",
    "tracestate",
]
_KQL_REQUIRED_FILES = {
    "m8-positive-chain.kql",
    "m8-negative-leakage.kql",
}
_KQL_POSITIVE_REQUIRED_TOKENS = (
    "requests",
    "apprequests",
    "dependencies",
    "appdependencies",
    "traces",
    "apptraces",
    "operation_id",
)
_KQL_NEGATIVE_REQUIRED_TOKENS = (
    "requests",
    "dependencies",
    "traces",
    "apptraces",
    "containerappconsolelogs_cl",
    "authorization",
    "bearer ",
    "eyj",
    "access_token",
    "refresh_token",
    "id_token",
    "\"oid\"",
    "\"sub\"",
    "\"email\"",
    "\"upn\"",
    "\"preferred_username\"",
    "\"name\"",
    "\"given_name\"",
    "\"family_name\"",
    "tracestate",
)


def _is_public_workflow(workflow_text: str) -> bool:
    return "pull_request:" in workflow_text or re.search(
        r"(^|\n)\s*push\s*:", workflow_text, re.IGNORECASE
    ) is not None


def _is_placeholder_line(line: str) -> bool:
    lowered = line.lower()
    return any(hint in lowered for hint in _PLACEHOLDER_HINTS)


def _upload_artifact_step_blocks(workflow_text: str) -> list[str]:
    lines = workflow_text.splitlines()
    blocks: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if re.search(r"uses:\s*actions/upload-artifact@", line, re.IGNORECASE) is None:
            i += 1
            continue

        uses_indent = len(line) - len(line.lstrip())
        step_indent = max(uses_indent - 2, 0)
        block_lines = [line]
        i += 1

        while i < len(lines):
            candidate = lines[i]
            stripped = candidate.strip()
            candidate_indent = len(candidate) - len(candidate.lstrip())
            if stripped and candidate_indent < step_indent:
                break
            if re.match(rf"^\s{{{step_indent}}}-\s+name:", candidate):
                break
            block_lines.append(candidate)
            i += 1

        blocks.append("\n".join(block_lines))
    return blocks


def _scan_workflow_policies(workflows_dir: Path) -> list[str]:
    offenders: list[str] = []
    for workflow in sorted(workflows_dir.glob("*.yml")):
        text = workflow.read_text(encoding="utf-8", errors="ignore")
        if _LIVE_DEFAULT_PATTERN.search(text):
            offenders.append(f"{workflow}: defaults LIVE_AZURE_TESTS=true")
        if not _is_public_workflow(text):
            continue
        for pattern in _FORBIDDEN_PUBLIC_PATTERNS:
            if pattern.search(text):
                offenders.append(
                    f"{workflow}: public CI contains forbidden pattern '{pattern.pattern}'"
                )
    for required_workflow, required_phrases in _REQUIRED_WORKFLOW_PHRASES.items():
        if not required_workflow.exists():
            offenders.append(f"{required_workflow}: required M8 workflow is missing")
            continue
        required_text = required_workflow.read_text(encoding="utf-8", errors="ignore").lower()
        for phrase in required_phrases:
            if phrase.lower() not in required_text:
                offenders.append(f"{required_workflow}: missing required policy phrase '{phrase}'")

    if M8_DEPLOY_WORKFLOW.exists():
        deploy_text = M8_DEPLOY_WORKFLOW.read_text(encoding="utf-8", errors="ignore")
        if "secrets.AZURE_CLIENT_ID_DEPLOY" not in deploy_text:
            offenders.append(f"{M8_DEPLOY_WORKFLOW}: missing deploy identity placeholder")
        if (
            "validate_m8_kql_contract.py" not in deploy_text
            and "./.github/workflows/m8-smoke-trace.yml" not in deploy_text
        ):
            offenders.append(
                f"{M8_DEPLOY_WORKFLOW}: smoke stage must delegate to m8-smoke-trace or run local telemetry contract validation"
            )

    if M8_START_RESUME_WORKFLOW.exists():
        start_text = M8_START_RESUME_WORKFLOW.read_text(encoding="utf-8", errors="ignore")
        if "secrets.AZURE_CLIENT_ID_SHUTDOWN" not in start_text:
            offenders.append(f"{M8_START_RESUME_WORKFLOW}: missing shutdown identity placeholder")
        if "AZURE_CLIENT_ID_DEPLOY" in start_text or "AZURE_CLIENT_ID_SMOKE" in start_text:
            offenders.append(
                f"{M8_START_RESUME_WORKFLOW}: lifecycle workflow must not reference deploy/smoke identities"
            )

    if M8_NIGHTLY_SHUTDOWN_WORKFLOW.exists():
        shutdown_text = M8_NIGHTLY_SHUTDOWN_WORKFLOW.read_text(encoding="utf-8", errors="ignore")
        if "secrets.AZURE_CLIENT_ID_SHUTDOWN" not in shutdown_text:
            offenders.append(
                f"{M8_NIGHTLY_SHUTDOWN_WORKFLOW}: missing shutdown identity placeholder"
            )
        if "AZURE_CLIENT_ID_DEPLOY" in shutdown_text or "AZURE_CLIENT_ID_SMOKE" in shutdown_text:
            offenders.append(
                f"{M8_NIGHTLY_SHUTDOWN_WORKFLOW}: lifecycle workflow must not reference deploy/smoke identities"
            )
        for pattern in _FORBIDDEN_SHUTDOWN_PATTERNS:
            if pattern.search(shutdown_text):
                offenders.append(
                    f"{M8_NIGHTLY_SHUTDOWN_WORKFLOW}: forbidden broad mutation '{pattern.pattern}' in shutdown path"
                )

    if M8_SMOKE_TRACE_WORKFLOW.exists():
        smoke_text = M8_SMOKE_TRACE_WORKFLOW.read_text(encoding="utf-8", errors="ignore")
        if "secrets.AZURE_CLIENT_ID_SMOKE" not in smoke_text:
            offenders.append(f"{M8_SMOKE_TRACE_WORKFLOW}: missing smoke identity placeholder")
        if "live_azure_tests" not in smoke_text.lower() or "workflow_call" not in smoke_text.lower():
            offenders.append(
                f"{M8_SMOKE_TRACE_WORKFLOW}: smoke workflow must enforce live_azure_tests and support workflow_call"
            )
        if "m8_browser_smoke_harness.py" not in smoke_text:
            offenders.append(
                f"{M8_SMOKE_TRACE_WORKFLOW}: smoke workflow must run canonical browser smoke harness wiring check"
            )
        if (
            "validate_m8_kql_contract.py" not in smoke_text
            and "m8_smoke_trace_contract.py validate" not in smoke_text
        ):
            offenders.append(
                f"{M8_SMOKE_TRACE_WORKFLOW}: smoke workflow must run local telemetry contract validation"
            )
        if (
            "m8_smoke_trace_contract.py evaluate" not in smoke_text
            and "--negative-results-json" not in smoke_text
        ):
            offenders.append(
                f"{M8_SMOKE_TRACE_WORKFLOW}: smoke workflow must represent hard-fail leakage evaluation"
            )
    else:
        offenders.append(f"{M8_SMOKE_TRACE_WORKFLOW}: required M8 workflow is missing")

    if not M8_SMOKE_HARNESS.exists():
        offenders.append(f"{M8_SMOKE_HARNESS}: required T07 harness is missing")
    if not M8_SMOKE_CONTRACT.exists():
        offenders.append(f"{M8_SMOKE_CONTRACT}: required T07 trace contract runner is missing")
    if not M9_LIVE_PREFLIGHT.exists():
        offenders.append(f"{M9_LIVE_PREFLIGHT}: required M9 preflight checker is missing")

    preflight_required_workflows = (
        M8_DEPLOY_WORKFLOW,
        M8_START_RESUME_WORKFLOW,
        M8_NIGHTLY_SHUTDOWN_WORKFLOW,
        M8_SMOKE_TRACE_WORKFLOW,
    )
    for workflow in preflight_required_workflows:
        if not workflow.exists():
            continue
        workflow_text = workflow.read_text(encoding="utf-8", errors="ignore")
        if "m9_live_preflight.py" not in workflow_text:
            offenders.append(f"{workflow}: missing m9_live_preflight.py protected preflight gate")

    for workflow in sorted(workflows_dir.glob("m8-*.yml")):
        text = workflow.read_text(encoding="utf-8", errors="ignore")
        if workflow.name != "m8-validate.yml" and _is_public_workflow(text):
            offenders.append(f"{workflow}: M8 live workflows must not use push/pull_request triggers")
        offenders.extend(_scan_workflow_runtime_exposure(workflow, text))

        for block in _upload_artifact_step_blocks(text):
            lowered = block.lower()
            if "retention-days:" not in lowered:
                offenders.append(f"{workflow}: artifact upload must set retention-days for hygiene")
            for unsafe_pattern in _UNSAFE_ARTIFACT_PATTERNS:
                if unsafe_pattern.search(lowered):
                    offenders.append(
                        f"{workflow}: artifact upload references unsafe pattern '{unsafe_pattern.pattern}'"
                    )

    return offenders


def _scan_workflow_runtime_exposure(workflow: Path, workflow_text: str) -> list[str]:
    offenders: list[str] = []

    for line_number, line in enumerate(workflow_text.splitlines(), start=1):
        if _AZ_ACCOUNT_SHOW_PATTERN.search(line) is not None:
            if _AZ_ACCOUNT_SHOW_SAFE_OUTPUT_PATTERN.search(line) is None:
                offenders.append(
                    f"{workflow}:{line_number}: az account show must not emit account metadata to logs"
                )
            elif _AZ_ACCOUNT_SHOW_SAFE_QUERY_PATTERN.search(line) is not None:
                offenders.append(
                    f"{workflow}:{line_number}: az account show query may expose account metadata"
                )

        if _UNSAFE_OUTPUT_COMMAND_PATTERN.search(line) is None:
            continue

        match = _LIVE_ENDPOINT_VAR_PATTERN.search(line) or _LIVE_ENDPOINT_EXPRESSION_PATTERN.search(line)
        if match is None:
            continue
        var_name = match.group(1)
        offenders.append(
            f"{workflow}:{line_number}: workflow output must not print live endpoint variable '{var_name}'"
        )

    return offenders


def _scan_identifiers() -> list[str]:
    offenders: list[str] = []
    for root in _IDENTIFIER_SCAN_DIRS:
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in _IDENTIFIER_SCAN_FILE_SUFFIXES:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for line_number, line in enumerate(text.splitlines(), start=1):
                for guid in _GUID_PATTERN.findall(line):
                    normalized = guid.lower()
                    if normalized in _ALLOWED_GUIDS or _is_placeholder_line(line):
                        continue
                    offenders.append(f"{path}:{line_number}: non-placeholder GUID {guid}")
                for pattern in _SENSITIVE_LITERAL_PATTERNS:
                    if pattern.search(line):
                        offenders.append(
                            f"{path}:{line_number}: forbidden secret/token-like literal '{pattern.pattern}'"
                        )
    return offenders


def _scan_frontend_placeholders() -> list[str]:
    offenders: list[str] = []
    spa_env = (ROOT / "apps" / "spa-public-client" / "react-vite" / ".env.example").read_text(
        encoding="utf-8"
    )
    if ".default" in spa_env:
        offenders.append("apps/spa-public-client/react-vite/.env.example: contains .default scope")

    pkg = json.loads(
        (
            ROOT
            / "apps"
            / "spfx-webpart"
            / "identity-chat-webpart"
            / "config"
            / "package-solution.json"
        ).read_text(encoding="utf-8")
    )
    requests = pkg["solution"].get("webApiPermissionRequests", [])
    if requests != [{"resource": "api://{client-id}", "scope": "access_as_user"}]:
        offenders.append(
            "apps/spfx-webpart/identity-chat-webpart/config/package-solution.json: "
            "webApiPermissionRequests must contain only BFF placeholder scope"
        )
    return offenders


def _scan_telemetry_contract() -> list[str]:
    offenders: list[str] = []
    design_text = SPEC_DESIGN.read_text(encoding="utf-8", errors="ignore").lower()
    telemetry_test_text = TELEMETRY_TEST.read_text(encoding="utf-8", errors="ignore").lower()

    for token in _TELEMETRY_REQUIRED_TOKENS:
        if token not in design_text:
            offenders.append(f"{SPEC_DESIGN}: missing telemetry contract token '{token}'")
    for token in ("oid", "sub", "email", "upn", "preferred_username"):
        if token not in telemetry_test_text:
            offenders.append(f"{TELEMETRY_TEST}: missing telemetry static coverage for '{token}'")
    missing_kql_files = sorted(name for name in _KQL_REQUIRED_FILES if not (KQL_DIR / name).exists())
    if missing_kql_files:
        offenders.append(
            f"{KQL_DIR}: missing required KQL contract files {', '.join(missing_kql_files)}"
        )
        return offenders

    positive_text = (KQL_DIR / "m8-positive-chain.kql").read_text(
        encoding="utf-8", errors="ignore"
    ).lower()
    negative_text = (KQL_DIR / "m8-negative-leakage.kql").read_text(
        encoding="utf-8", errors="ignore"
    ).lower()

    for token in _KQL_POSITIVE_REQUIRED_TOKENS:
        if token not in positive_text:
            offenders.append(
                f"{KQL_DIR / 'm8-positive-chain.kql'}: missing required token '{token}'"
            )
    for token in _KQL_NEGATIVE_REQUIRED_TOKENS:
        if token not in negative_text:
            offenders.append(
                f"{KQL_DIR / 'm8-negative-leakage.kql'}: missing required token '{token}'"
            )

    return offenders


def _scan_rbac_scope_signals() -> list[str]:
    offenders: list[str] = []
    combined = ""
    for doc in RBAC_DOCS:
        if not doc.exists():
            offenders.append(f"{doc}: required RBAC scope documentation file is missing")
            continue
        combined += "\n" + doc.read_text(encoding="utf-8", errors="ignore").lower()
    for phrase in _REQUIRED_RBAC_DOC_PHRASES:
        if phrase not in combined:
            offenders.append(f"RBAC documentation missing required phrase '{phrase}'")
    return offenders


def run_all_checks() -> list[str]:
    offenders: list[str] = []
    offenders.extend(_scan_workflow_policies(WORKFLOWS_DIR))
    offenders.extend(_scan_identifiers())
    offenders.extend(_scan_frontend_placeholders())
    offenders.extend(_scan_telemetry_contract())
    offenders.extend(_scan_rbac_scope_signals())
    return offenders


def main() -> int:
    offenders = run_all_checks()
    if offenders:
        for offender in offenders:
            print(offender)
        return 1
    print("Public-safe M8 validation checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
