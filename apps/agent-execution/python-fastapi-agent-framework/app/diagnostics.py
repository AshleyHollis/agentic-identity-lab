from __future__ import annotations

from typing import Any

from .config import Settings


def build_health_payload(settings: Settings, correlation_id: str) -> dict[str, Any]:
    return {
        "status": "ok",
        "service": settings.service_name,
        "correlation_id": correlation_id,
    }


def build_ready_payload(settings: Settings, correlation_id: str) -> dict[str, Any]:
    return {
        "status": "ready",
        "service": settings.service_name,
        "correlation_id": correlation_id,
    }
