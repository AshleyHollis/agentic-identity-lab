from __future__ import annotations

from typing import Any

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request, status
from pydantic import BaseModel, Field

from identity_lab_diagnostics import get_correlation_id

from .auth import AuthContext, exchange_for_mcp, get_auth_context
from .config import load_settings
from .diagnostics import build_health_payload, build_ready_payload

from identity_lab_auth import AUTH_FIXTURE_HEADER, AuthMode
from identity_lab_auth.telemetry import (
    get_tracer,
    setup_telemetry,
    instrument_fastapi,
    record_auth_attributes,
    record_obo_attributes,
)

settings = load_settings()
setup_telemetry(settings.service_name)
tracer = get_tracer("identity_lab.agent_execution")
app = FastAPI(title=settings.service_name, version="0.1.0")
instrument_fastapi(app)


class AgentInvokeRequest(BaseModel):
    payload: dict[str, Any] | None = Field(default=None, description="Agent input payload.")
    metadata: dict[str, Any] | None = Field(default=None, description="Call metadata.")


class AgentInvokeResponse(BaseModel):
    status: str
    message: str
    correlation_id: str
    token_type: str
    claims: dict[str, Any]
    payload_keys: list[str]
    obo_audience: str | None
    obo_scopes: list[str]
    chain_exercised: bool
    mcp_authorized: bool | None = None
    mcp_correlation_id: str | None = None


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
def whoami(auth_context: AuthContext = Depends(get_auth_context)) -> dict[str, object]:
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


def _extract_scopes(claims: dict[str, Any]) -> list[str]:
    raw = claims.get("scp") or claims.get("scope") or []
    if isinstance(raw, str):
        return [item for item in raw.split() if item]
    if isinstance(raw, list):
        return [str(item) for item in raw if item]
    return []


def _invoke_response(
    mode: str,
    request: AgentInvokeRequest,
    auth_context: AuthContext,
    http_request: Request,
) -> AgentInvokeResponse:
    payload_keys = sorted(request.payload.keys()) if request.payload else []
    record_auth_attributes(
        auth_mode=settings.auth_mode.value,
        authorized=auth_context.authorized,
        aud=auth_context.audiences[0] if auth_context.audiences else None,
    )
    obo_exchange = None
    if auth_context.authorized and auth_context.token_type == "delegated":
        record_obo_attributes(obo_hop="agent_obo")
        obo_exchange = exchange_for_mcp(auth_context, settings)
    obo_claims = obo_exchange.claims if obo_exchange else {}
    mcp_authorized = None
    mcp_correlation_id = None
    chain_exercised = False
    if settings.mcp_chain_enabled and obo_exchange:
        mcp_result = _invoke_mcp_authorization_check(http_request, auth_context, obo_exchange.authorization)
        mcp_authorized = bool(mcp_result.get("authorized"))
        correlation_value = mcp_result.get("correlation_id")
        mcp_correlation_id = str(correlation_value) if correlation_value else None
        chain_exercised = True
    return AgentInvokeResponse(
        status="accepted",
        message=f"{mode} placeholder - auth enforced",
        correlation_id=auth_context.correlation_id,
        token_type=auth_context.token_type,
        claims=auth_context.claims,
        payload_keys=payload_keys,
        obo_audience=obo_claims.get("aud") if obo_claims else None,
        obo_scopes=_extract_scopes(obo_claims) if obo_claims else [],
        chain_exercised=chain_exercised,
        mcp_authorized=mcp_authorized,
        mcp_correlation_id=mcp_correlation_id,
    )


def _invoke_mcp_authorization_check(
    request: Request,
    auth_context: AuthContext,
    obo_authorization: str,
) -> dict[str, Any]:
    url = f"{settings.mcp_protected_api_base_url}{settings.mcp_authorization_check_path}"
    headers = {
        "Authorization": obo_authorization,
        settings.correlation_header: auth_context.correlation_id or "",
    }
    traceparent = request.headers.get("traceparent")
    if traceparent:
        headers["traceparent"] = traceparent
    with tracer.start_as_current_span("identity_lab.agent_execution.call_mcp"):
        try:
            response = httpx.post(
                url,
                json={},
                headers=headers,
                timeout=settings.downstream_timeout_seconds,
            )
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="mcp_unreachable",
            ) from exc
    if response.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="mcp_error",
        )
    data = response.json()
    if not isinstance(data, dict):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="mcp_invalid_payload",
        )
    return data


@app.post("/agent/invoke")
def agent_invoke(
    http_request: Request,
    request: AgentInvokeRequest,
    auth_context: AuthContext = Depends(get_auth_context),
) -> AgentInvokeResponse:
    return _invoke_response("invoke", request, auth_context, http_request)


@app.post("/agent/invoke-modern")
def agent_invoke_modern(
    http_request: Request,
    request: AgentInvokeRequest,
    auth_context: AuthContext = Depends(get_auth_context),
) -> AgentInvokeResponse:
    return _invoke_response("invoke-modern", request, auth_context, http_request)


@app.post("/agent/invoke-low-change")
def agent_invoke_low_change(
    http_request: Request,
    request: AgentInvokeRequest,
    auth_context: AuthContext = Depends(get_auth_context),
) -> AgentInvokeResponse:
    return _invoke_response("invoke-low-change", request, auth_context, http_request)
