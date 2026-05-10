# ADR 0009: Optional `display_name` in BFF `/chat/session` Request Body

## Status
Accepted — Morpheus T11 architecture sign-off (M7)

## Context

Spec 007 (M7 — Variant Client Implementations) introduces three browser-facing client variants
(SPA, SharePoint classic loader, SPFx web part) that call the BFF `POST /chat/session` endpoint.
At spec-ready time, the endpoint accepted no request body. Spec 007 raised an open question
(OQ1): should an optional `display_name` string field be added to the request body to allow
clients to supply a human-readable session label for UI rendering?

This question is architecturally significant because:

1. Any body field added to `/chat/session` must not be treated as an identity or authorization
   signal — the identity invariant (`userId` and any body field are display/context only) is a
   non-negotiable lab invariant.
2. Adding a body field changes the `/chat/session` contract in a way that must be documented and
   backward-compatible.
3. The field must not propagate downstream to the Agent Execution Service or MCP Protected API as
   a trust signal.

## Decision

**Accepted.** The BFF `POST /chat/session` endpoint may accept an optional `display_name: str | None = None` body field via a `ChatSessionRequest` Pydantic model.

This is architecturally acceptable because:

- The field is `Optional[str]` with a `None` default — the endpoint remains fully backward-
  compatible. Existing callers that send no body are unaffected.
- The field has a purely cosmetic function: it allows client variants to label a session for
  display purposes (e.g., page title, component context). It has no effect on authorization,
  session scoping, or downstream token flows.
- The identity invariant is preserved. `display_name`, like `userId`, must never be used as an
  authorization gate, database key, or downstream trust signal.
- The field is logged at most as a display hint; it is never forwarded to the Agent Execution
  Service or MCP Protected API.

## Constraints (binding on T01 implementation)

1. **Identity invariant comment required in model definition:**
   ```python
   class ChatSessionRequest(BaseModel):
       display_name: str | None = None
       # display_name is a display hint only. It MUST NOT be used for authorization,
       # session scoping, database keys, or downstream trust signals.
       # Identity is established solely by the validated bearer token.
   ```

2. **`display_name` must not appear in the session response.** The response returns only
   `session_id` and `expires_at`. Echoing `display_name` back risks it being treated as a
   session property by callers.

3. **Negative test required (T01):** A test must assert that a request with `display_name` in
   the body but no valid bearer token receives a 401. This demonstrates the field has no effect
   on auth path.

4. **`display_name` must not be forwarded downstream.** If the BFF calls the Agent Execution
   Service, `display_name` must not be included in the forwarded payload.

5. **Length validation recommended:** Implement a max-length guard (e.g., 255 chars) in the
   Pydantic model to prevent oversized display strings reaching the BFF layer.

## Alternatives Considered

| Option | Description | Rejected reason |
|--------|-------------|-----------------|
| A | Keep `/chat/session` body-free | Limits client UX; no display context for session labelling. Acceptable but reduces variant richness. |
| B | Accept `display_name` (this decision) | Adds display utility without compromising the invariant when constraints above are enforced. |
| C | Accept `userId` + `display_name` | `userId` in a body field is a known invariant violation risk; out of scope per spec. |

## Consequences

- `T01` (BFF `/chat/session` body model) is unblocked. Neo may implement per spec 007 T01 scope.
- All three client variants (T02 SPA, T03 classic, T04 SPFx) may include `display_name` in
  their BFF call bodies as an optional field.
- The identity invariant comment must appear in the Pydantic model, the `/chat/session` endpoint
  docstring, and each client variant's BFF call site (per FR-07).
- `python -m pytest` must pass (235+ tests) after T01 changes.

## Related

- Spec 007 OQ1 (`design.md`, `.progress.md`)
- ADR-M7-01 (MSAL sessionStorage — confirmed T11)
- ADR-M7-02 (Classic loader pluggable callback — confirmed T11)
- ADR-M7-03 (Azure E2E gate as M8 — confirmed T11)
- FR-07 (userId display-only enforcement)
- NFR-03 (Python backend regression)
