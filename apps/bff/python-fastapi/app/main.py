from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from identity_lab_diagnostics import get_correlation_id

from .auth import AuthContext, get_auth_context
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

_cors_origins = settings.cors_allowed_origins
if _cors_origins:
    # Security guard: wildcard MUST NOT be combined with allow_credentials=True.
    if "*" in _cors_origins:
        raise RuntimeError(
            "CORS_ALLOWED_ORIGINS must not contain '*' when credentials are enabled. "
            "Set explicit origins (e.g. http://localhost:3000) instead."
        )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type", "x-correlation-id"],
    )
# If _cors_origins is empty, CORS middleware is not registered.


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


@app.get("/healthz")
def healthz(request: Request) -> dict[str, str]:
    correlation_id = get_correlation_id(request.headers)
    return build_health_payload(settings, correlation_id)


@app.get("/readyz")
def readyz(request: Request) -> dict[str, str]:
    correlation_id = get_correlation_id(request.headers)
    return build_ready_payload(settings, correlation_id)


@app.get("/whoami")
def whoami(auth_context: AuthContext = Depends(get_auth_context)) -> dict[str, object]:
    record_auth_attributes(
        auth_mode=settings.auth_mode.value,
        authorized=auth_context.authorized,
        aud=auth_context.audiences[0] if auth_context.audiences else None,
    )
    return {
        "authenticated": auth_context.authenticated,
        "token_type": auth_context.token_type,
        "claims": auth_context.claims,
        "scopes": auth_context.scopes,
        "audiences": auth_context.audiences,
        "correlation_id": auth_context.correlation_id,
    }


@app.get("/debug/claims")
def debug_claims(auth_context: AuthContext = Depends(get_auth_context)) -> dict[str, object]:
    claims = auth_context.claims if settings.enable_debug_claims else {}
    return {
        "debug_enabled": settings.enable_debug_claims,
        "token_type": auth_context.token_type,
        "claims": claims,
        "correlation_id": auth_context.correlation_id,
    }


@app.post("/chat/session")
def create_chat_session(
    auth_context: AuthContext = Depends(get_auth_context),
) -> dict[str, str]:
    # userId from token claims (sub, oid, preferred_username) is a display hint ONLY.
    # It MUST NOT be used as an authorization gate, database key, or downstream trust signal.
    # Session authorization is based solely on aud, scp, tid, and iss validation.
    session_id = str(uuid.uuid4())
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    return {
        "session_id": session_id,
        "expires_at": expires_at,
    }
