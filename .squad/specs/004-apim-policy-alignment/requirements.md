# Requirements: APIM Policy Alignment

**Status:** Complete  
**Milestone:** M3  
**Spec Phase:** requirements  
**Created:** 2026-05-10  
**Updated:** 2026-05-10  
**Impact:** Medium

## User stories

### US-1: Ingress policy matches delegated-token rules
**As a** lab maintainer  
**I want to** verify the APIM ingress XML validates delegated user tokens  
**So that** documentation and examples match the implemented BFF/agent-gateway auth boundaries.

**Acceptance Criteria:**
- [ ] AC-1.1: Ingress policy validates the `Authorization` header with bearer scheme.
- [ ] AC-1.2: Ingress policy includes BFF and/or agent-gateway audience guidance.
- [ ] AC-1.3: Ingress policy requires delegated `scp` and trusted `tid` claims.

### US-2: Egress policy matches OBO boundary rules
**As a** security reviewer  
**I want to** verify egress validates OBO tokens before forwarding  
**So that** MCP never receives a replayed inbound token.

**Acceptance Criteria:**
- [ ] AC-2.1: Egress policy validates `x-obo-authorization`.
- [ ] AC-2.2: Egress policy requires the MCP audience.
- [ ] AC-2.3: Egress policy sets downstream `Authorization` from `x-obo-authorization`.

### US-3: Managed identity anti-pattern remains explicit
**As a** lab reader  
**I want to** see that managed identity token replacement is intentionally broken for delegated flows  
**So that** I do not copy it into a user-delegated path.

**Acceptance Criteria:**
- [ ] AC-3.1: Anti-pattern XML remains clearly marked as intentionally broken.
- [ ] AC-3.2: Managed identity warning docs explain loss of user context and OBO bypass.

## Functional requirements
| ID | Requirement | Priority | Verify |
|----|-------------|----------|--------|
| FR-1 | Add policy-file tests for ingress APIM validation semantics. | Must | `python -m pytest tests\integration\python\test_apim_ingress_validates_token.py` |
| FR-2 | Add policy-file tests for egress OBO validation semantics. | Must | `python -m pytest tests\integration\python\test_apim_egress_validates_obo_token.py` |
| FR-3 | Add policy/doc tests for managed identity replacement warning. | Must | `python -m pytest tests\integration\python\test_apim_managed_identity_replacement_breaks_delegation.py` |
| FR-4 | Update APIM docs if tests reveal drift or ambiguity. | Should | File review and pytest |

## Non-functional requirements
| ID | Requirement | Metric | Target |
|----|-------------|--------|--------|
| NFR-1 | Public-safe examples | Secrets/live IDs committed | 0 |
| NFR-2 | Offline-safe verification | Network calls | 0 |
| NFR-3 | Policy drift detection | XML examples covered by tests | Ingress, egress, anti-pattern |

## Dependencies
- Spec 001 validation and OBO boundary rules.
- Spec 003 local delegated-flow integration results.

## Success criteria
- APIM tests inspect actual policy/docs files.
- Full Python tests pass.
- Terraform format and single-tenant validation pass or any pre-existing blocker is documented.

