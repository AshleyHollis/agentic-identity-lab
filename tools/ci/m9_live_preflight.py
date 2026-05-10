from __future__ import annotations

import argparse
import os
import re

_PLACEHOLDER_TOKENS = (
    "placeholder",
    "<",
    ">",
    "{",
    "}",
    "00000000-0000-0000-0000-000000000000",
    "example",
    "changeme",
    "todo",
)
_GUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def _looks_placeholder(value: str) -> bool:
    normalized = value.strip().lower()
    if not normalized:
        return True
    if any(token in normalized for token in _PLACEHOLDER_TOKENS):
        return True
    if normalized.startswith("api://{") or normalized.endswith("-placeholder"):
        return True
    return False


def _is_guid_var(name: str) -> bool:
    return name.endswith("_ID")


def run_checks(required: list[str], context: str) -> list[str]:
    offenders: list[str] = []
    for name in required:
        value = os.environ.get(name, "")
        if not value.strip():
            offenders.append(f"[{context}] missing required variable: {name}")
            continue
        if _looks_placeholder(value):
            offenders.append(f"[{context}] variable appears placeholder-like: {name}")
            continue
        if _is_guid_var(name) and _GUID_PATTERN.fullmatch(value.strip()) is None:
            offenders.append(f"[{context}] expected GUID-like value for: {name}")
    return offenders


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="M9 protected-live preflight checks (no metadata output)"
    )
    parser.add_argument(
        "--context",
        required=True,
        help="Operator context label (deploy-identity, smoke-identity, lifecycle-identity, etc.)",
    )
    parser.add_argument(
        "--require",
        nargs="+",
        required=True,
        help="Required environment variable names to validate",
    )
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    offenders = run_checks(required=args.require, context=args.context)
    if offenders:
        for offender in offenders:
            print(offender)
        return 1
    print(f"[{args.context}] live preflight checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
