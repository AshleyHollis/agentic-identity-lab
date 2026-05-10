from __future__ import annotations

from typing import Any

from fastapi import Depends, FastAPI, Request
from pydantic import BaseModel, Field

from identity_lab_diagnostics import get_correlation_id

from .auth import AuthContext, require_mcp_access, require_mcp_write
from .config import load_settings
from .diagnostics import build_health_payload, build_ready_payload

from identity_lab_auth import AUTH_FIXTURE_HEADER, AuthMode
from identity_lab_auth.telemetry import (
    setup_telemetry,
    instrument_fastapi,
    record_auth_attributes,
)

settings = load_settings()
setup_telemetry(settings.service_name)
app = FastAPI(title=settings.service_name, version="0.1.0")
instrument_fastapi(app)


class EchoRequest(BaseModel):
    payload: dict[str, Any] | None = Field(default=None, description="Payload to echo.")


class EchoResponse(BaseModel):
    correlation_id: str
    echo: dict[str, Any] | None


class AuthorizationCheckResponse(BaseModel):
    authorized: bool
    reason: str
    token_type: str
    claims: dict[str, Any]
    correlation_id: str


@app.get("/healthz")
def healthz(request: Request) -> dict[str, str]:
    correlation_id = get_correlation_id(
        request.headers, header_name=settings.correlation_header
    )
    return build_health_payload(settings, correlation_id)


@app.get("/readyz")
def readyz(request: Request) -> dict[str, str]:
    correlation_id = get_correlation_id(
        request.headers, header_name=settings.correlation_header
    )
    return build_ready_payload(settings, correlation_id)


@app.middleware("http")
async def _trace_identity_lab_auth(request: Request, call_next):
    """Middleware: set identity_lab.auth_mode and fixture_name on the active span."""
    fixture_name = request.headers.get(AUTH_FIXTURE_HEADER)
    strict = settings.auth_mode == AuthMode.STRICT
    record_auth_attributes(
        auth_mode=settings.auth_mode.value,
        fixture_name=fixture_name,
        strict_mode=strict,
    )
    return await call_next(request)


@app.get("/whoami")
def whoami(auth_context: AuthContext = Depends(require_mcp_access)) -> dict[str, object]:
    record_auth_attributes(
        auth_mode=settings.auth_mode.value,
        authorized=auth_context.authorized,
        aud=auth_context.audiences[0] if auth_context.audiences else None,
    )
    return {
        "authenticated": auth_context.authenticated,
        "authorized": auth_context.authorized,
        "token_type": auth_context.token_type,
        "claims": auth_context.claims,
        "scopes": auth_context.scopes,
        "audiences": auth_context.audiences,
        "correlation_id": auth_context.correlation_id,
        "failure_reasons": list(auth_context.failure_reasons),
    }


@app.get("/debug/claims")
def debug_claims(auth_context: AuthContext = Depends(require_mcp_access)) -> dict[str, object]:
    claims = auth_context.claims if settings.enable_debug_claims else {}
    return {
        "debug_enabled": settings.enable_debug_claims,
        "token_type": auth_context.token_type,
        "claims": claims,
        "correlation_id": auth_context.correlation_id,
    }


@app.post("/tools/echo")
def tools_echo(
    request: EchoRequest,
    auth_context: AuthContext = Depends(require_mcp_write),
) -> EchoResponse:
    return EchoResponse(
        correlation_id=auth_context.correlation_id,
        echo=request.payload,
    )


@app.post("/tools/authorization-check")
def tools_authorization_check(
    auth_context: AuthContext = Depends(require_mcp_write),
) -> AuthorizationCheckResponse:
    record_auth_attributes(
        auth_mode=settings.auth_mode.value,
        authorized=auth_context.authorized,
        aud=auth_context.audiences[0] if auth_context.audiences else None,
    )
    return AuthorizationCheckResponse(
        authorized=auth_context.authorized,
        reason="authorized" if auth_context.authorized else "unauthorized",
        token_type=auth_context.token_type,
        claims=auth_context.claims,
        correlation_id=auth_context.correlation_id,
    )
