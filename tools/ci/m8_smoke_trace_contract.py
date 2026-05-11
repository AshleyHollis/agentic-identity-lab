from __future__ import annotations

import argparse
import json
from pathlib import Path

_REQUIRED_WORKFLOW_TOKENS = (
    "workflow_dispatch",
    "workflow_call",
    "lab-live-azure-smoke",
    "live_azure_tests",
    "LIVE_AZURE_TESTS",
    "m8_browser_smoke_harness.py",
    "M9_PLAYWRIGHT_CHAT_URL",
    "M9_PLAYWRIGHT_ACCESS_TOKEN",
    "browser_transport",
    "M9_BROWSER_TRANSPORT",
    "M9_AGENT_BROWSER_COMMAND",
    "M9_BROWSER_EVIDENCE_JSON",
    "python -m playwright install chromium",
    "m8_smoke_trace_contract.py evaluate",
)

_REQUIRED_POSITIVE_KQL_TOKENS = (
    "requests",
    "AppRequests",
    "dependencies",
    "AppDependencies",
    "traces",
    "AppTraces",
    "operation_Id",
    "cloud_RoleName",
    "mcp-protected-api",
)

_REQUIRED_NEGATIVE_KQL_TOKENS = (
    "requests",
    "dependencies",
    "traces",
    "ContainerAppConsoleLogs_CL",
    "authorization",
    "bearer ",
    "eyj",
    "cookie",
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

_DEFAULT_REQUIRED_ROLES = ("apim", "bff", "agent-execution", "mcp-protected-api")


def _read_json_rows(path: Path) -> list[dict[str, object]]:
    content = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(content, list):
        return [row for row in content if isinstance(row, dict)]
    if isinstance(content, dict) and isinstance(content.get("tables"), list):
        rows: list[dict[str, object]] = []
        for table in content["tables"]:
            if not isinstance(table, dict):
                continue
            column_names = [col["name"] for col in table.get("columns", []) if isinstance(col, dict) and "name" in col]
            for row in table.get("rows", []):
                if isinstance(row, list):
                    rows.append(
                        {
                            column_names[index]: value
                            for index, value in enumerate(row)
                            if index < len(column_names)
                        }
                    )
        return rows
    return []


def validate_smoke_trace_scaffold(
    workflow_text: str,
    positive_kql_text: str,
    negative_kql_text: str,
) -> list[str]:
    offenders: list[str] = []
    workflow_lower = workflow_text.lower()
    positive_lower = positive_kql_text.lower()
    negative_lower = negative_kql_text.lower()

    for token in _REQUIRED_WORKFLOW_TOKENS:
        if token.lower() not in workflow_lower:
            offenders.append(f"workflow missing required token '{token}'")
    for token in _REQUIRED_POSITIVE_KQL_TOKENS:
        if token.lower() not in positive_lower:
            offenders.append(f"positive kql missing required token '{token}'")
    for token in _REQUIRED_NEGATIVE_KQL_TOKENS:
        if token.lower() not in negative_lower:
            offenders.append(f"negative kql missing required token '{token}'")
    return offenders


def evaluate_trace_results(
    positive_rows: list[dict[str, object]],
    negative_rows: list[dict[str, object]],
    required_roles: tuple[str, ...] = _DEFAULT_REQUIRED_ROLES,
    required_operations: tuple[str, ...] = (),
) -> list[str]:
    offenders: list[str] = []

    observed_roles = {
        str(row.get("cloud_RoleName") or row.get("AppRoleName") or row.get("roleName") or "").lower()
        for row in positive_rows
    }
    missing_roles = [role for role in required_roles if role not in observed_roles]
    if missing_roles:
        offenders.append(f"positive trace results missing required roles: {', '.join(missing_roles)}")

    if not positive_rows:
        offenders.append("positive trace results are empty")

    if required_operations:
        haystack = "\n".join(
            [
                " ".join(
                    str(row.get(key, ""))
                    for key in (
                        "name",
                        "Name",
                        "url",
                        "Url",
                        "target",
                        "Target",
                        "message",
                        "Message",
                        "data",
                        "Data",
                    )
                ).lower()
                for row in positive_rows
            ]
        )
        missing_operations = [
            operation for operation in required_operations if operation.lower() not in haystack
        ]
        if missing_operations:
            offenders.append(
                "positive trace results missing required operations: "
                + ", ".join(missing_operations)
            )

    if negative_rows:
        offenders.append(f"negative leakage query returned {len(negative_rows)} rows")

    return offenders


def _validate_command(args: argparse.Namespace) -> int:
    workflow_file = Path(args.workflow_file)
    positive_kql = Path(args.positive_kql)
    negative_kql = Path(args.negative_kql)

    offenders: list[str] = []
    for path in (workflow_file, positive_kql, negative_kql):
        if not path.exists():
            offenders.append(f"missing required file: {path}")
    if offenders:
        for offender in offenders:
            print(offender)
        return 1

    offenders.extend(
        validate_smoke_trace_scaffold(
            workflow_file.read_text(encoding="utf-8", errors="ignore"),
            positive_kql.read_text(encoding="utf-8", errors="ignore"),
            negative_kql.read_text(encoding="utf-8", errors="ignore"),
        )
    )
    if offenders:
        for offender in offenders:
            print(offender)
        return 1

    print("M8 smoke+trace scaffold contract validation passed.")
    return 0


def _evaluate_command(args: argparse.Namespace) -> int:
    positive_rows = _read_json_rows(Path(args.positive_results_json))
    negative_rows = _read_json_rows(Path(args.negative_results_json))
    required_roles = tuple(args.required_role) if args.required_role else _DEFAULT_REQUIRED_ROLES
    required_operations = tuple(args.required_operation or [])

    offenders = evaluate_trace_results(
        positive_rows,
        negative_rows,
        required_roles,
        required_operations,
    )
    if offenders:
        for offender in offenders:
            print(offender)
        return 1

    print("M8 smoke+trace live contract evaluation passed.")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="M8 smoke/trace contract validator")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="Validate workflow + KQL static contract")
    validate.add_argument("--workflow-file", required=True)
    validate.add_argument("--positive-kql", required=True)
    validate.add_argument("--negative-kql", required=True)
    validate.set_defaults(func=_validate_command)

    evaluate = subparsers.add_parser("evaluate", help="Evaluate live query result files")
    evaluate.add_argument("--positive-results-json", required=True)
    evaluate.add_argument("--negative-results-json", required=True)
    evaluate.add_argument("--required-role", action="append", default=[])
    evaluate.add_argument("--required-operation", action="append", default=[])
    evaluate.set_defaults(func=_evaluate_command)

    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
