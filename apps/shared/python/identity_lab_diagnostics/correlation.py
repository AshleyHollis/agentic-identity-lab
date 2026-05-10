from __future__ import annotations

from typing import Mapping
from uuid import uuid4


def get_correlation_id(headers: Mapping[str, str], header_name: str = "x-correlation-id") -> str:
    if not headers:
        return uuid4().hex
    correlation_id = (
        headers.get(header_name)
        or headers.get(header_name.lower())
        or headers.get(header_name.upper())
        or headers.get("x-request-id")
        or headers.get("X-Request-ID")
    )
    if correlation_id:
        return str(correlation_id)
    return uuid4().hex
