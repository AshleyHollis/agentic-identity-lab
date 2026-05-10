# Tasks: APIM Policy Alignment

**Status:** Complete  
**Milestone:** M3  
**Spec Phase:** execution  
**Created:** 2026-05-10  
**Updated:** 2026-05-10  
**Impact:** Medium

## Overview
- **Total Tasks:** 6
- **Workflow:** TDD
- **Intent:** MID_SIZED

## Task table
| ID | Task | Owner Agent | Impact | Dependencies | Output Files | Validation | Status |
|----|------|-------------|--------|--------------|--------------|------------|--------|
| T-01 | Replace ingress APIM fixture-only test with policy XML checks. | Trinity | Medium | - | `tests\integration\python\test_apim_ingress_validates_token.py` | `python -m pytest tests\integration\python\test_apim_ingress_validates_token.py` | Complete |
| T-02 | Replace egress APIM fixture-only test with OBO policy XML checks. | Trinity | Medium | - | `tests\integration\python\test_apim_egress_validates_obo_token.py` | `python -m pytest tests\integration\python\test_apim_egress_validates_obo_token.py` | Complete |
| T-03 | Replace managed identity anti-pattern fixture test with policy/doc checks. | Trinity | Medium | - | `tests\integration\python\test_apim_managed_identity_replacement_breaks_delegation.py` | `python -m pytest tests\integration\python\test_apim_managed_identity_replacement_breaks_delegation.py` | Complete |
| T-04 | Align APIM docs and XML comments with Spec 001/003 boundaries if tests reveal drift. | Morpheus/Tank | Medium | T-01, T-02, T-03 | `docs\apim\*`; `infra\terraform\policies\apim\*` | `python -m pytest tests\integration\python\test_apim_*.py` | Complete |
| T-05 | Run full Python test suite. | Trinity | Medium | T-04 | n/a | `python -m pytest` | Complete |
| T-06 | Run Terraform policy-adjacent validation target. | Tank | Medium | T-04 | n/a | `terraform -chdir=infra\terraform fmt -check -recursive`; `terraform -chdir=infra\terraform\environments\single-tenant validate` | Complete |

## Completion criteria
- [x] APIM tests inspect policy XML/docs instead of only fixtures.
- [x] Ingress and egress examples match delegated/OBO boundaries.
- [x] Managed identity replacement remains clearly documented as unsafe for delegated flows.
- [x] Validation commands complete or blockers are documented.

