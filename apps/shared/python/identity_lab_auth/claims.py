from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping
import json

DEFAULT_SAFE_CLAIM_KEYS = {
    "aud",
    "azp",
    "appid",
    "exp",
    "iat",
    "iss",
    "nbf",
    "roles",
    "scp",
    "tid",
    "ver",
    "xms_act_fct",  # actor metadata — JSON object {"appid": "<uuid>"}, no user PII
}


def _find_allowlist_path() -> Path | None:
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "config" / "claims" / "safe-claims-allowlist.json"
        if candidate.is_file():
            return candidate
    return None


def load_safe_claims_allowlist(path: Path | None = None) -> set[str]:
    allowlist_path = path or _find_allowlist_path()
    if allowlist_path:
        try:
            payload = json.loads(allowlist_path.read_text(encoding="utf-8"))
            raw_allowlist = payload.get("allowlist", [])
            if isinstance(raw_allowlist, list):
                return {str(item) for item in raw_allowlist if item}
        except (OSError, json.JSONDecodeError, TypeError):
            pass
    return set(DEFAULT_SAFE_CLAIM_KEYS)


SAFE_CLAIM_KEYS = load_safe_claims_allowlist()


def _sanitize_value(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        trimmed = value.strip()
        if len(trimmed) > 256:
            return f"{trimmed[:256]}…"
        return trimmed
    if isinstance(value, (list, tuple, set)):
        return [_sanitize_value(item) for item in list(value)[:20]]
    if isinstance(value, dict):
        # Sanitize only scalar string-valued keys; drop nested dicts to prevent PII leakage.
        # Result is bounded to 512 chars serialised — actor metadata objects are small.
        sanitized_dict: dict[str, Any] = {}
        for k, v in value.items():
            if not isinstance(k, str):
                continue
            sv = _sanitize_value(v)
            if sv is not None:
                sanitized_dict[k] = sv
        serialised = json.dumps(sanitized_dict, separators=(",", ":"))
        if len(serialised) > 512:
            return f"{serialised[:512]}…"
        return sanitized_dict
    return None


def sanitize_claims(claims: Mapping[str, Any] | None) -> dict[str, Any]:
    if not claims:
        return {}
    sanitized: dict[str, Any] = {}
    for key, value in claims.items():
        if key in SAFE_CLAIM_KEYS:
            sanitized_value = _sanitize_value(value)
            if sanitized_value is not None:
                sanitized[key] = sanitized_value
    return sanitized
