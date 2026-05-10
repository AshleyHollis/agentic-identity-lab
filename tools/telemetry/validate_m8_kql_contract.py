from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KQL_DIR = ROOT / "tools" / "telemetry" / "kql"

POSITIVE_QUERY = KQL_DIR / "m8-positive-chain.kql"
NEGATIVE_QUERY = KQL_DIR / "m8-negative-leakage.kql"

POSITIVE_REQUIRED = (
    "requests",
    "apprequests",
    "dependencies",
    "appdependencies",
    "traces",
    "apptraces",
    "operation_id",
)
NEGATIVE_REQUIRED = (
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


def run_checks() -> list[str]:
    offenders: list[str] = []
    if not POSITIVE_QUERY.exists():
        offenders.append(f"{POSITIVE_QUERY}: missing required file")
    if not NEGATIVE_QUERY.exists():
        offenders.append(f"{NEGATIVE_QUERY}: missing required file")
    if offenders:
        return offenders

    positive = POSITIVE_QUERY.read_text(encoding="utf-8", errors="ignore").lower()
    negative = NEGATIVE_QUERY.read_text(encoding="utf-8", errors="ignore").lower()

    for token in POSITIVE_REQUIRED:
        if token not in positive:
            offenders.append(f"{POSITIVE_QUERY}: missing token '{token}'")
    for token in NEGATIVE_REQUIRED:
        if token not in negative:
            offenders.append(f"{NEGATIVE_QUERY}: missing token '{token}'")
    return offenders


def main() -> int:
    offenders = run_checks()
    if offenders:
        for offender in offenders:
            print(offender)
        return 1
    print("M8 KQL contract checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
