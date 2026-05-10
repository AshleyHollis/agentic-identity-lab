# Spec 008 — Requirements

**Spec:** 008-live-azure-e2e-gate  
**Milestone:** M8  
**Updated:** 2026-05-10

---

## Functional Requirements

### FR-01 — Opt-in live Azure gate only

M8 live deployment and smoke testing MUST be opt-in only:

- no live Azure deploy/test workflow may run by default on `push` or `pull_request`
- live execution MUST require `workflow_dispatch`, a protected schedule, or both
- live smoke execution MUST require a positive opt-in such as `LIVE_AZURE_TESTS=true`
- `.github\workflows\ci.yml` and any M8 PR validation workflow MUST remain validation-only

### FR-02 — PR validation pipeline

M8 MUST define a PR validation pipeline for `pull_request` and optional manual execution that runs only public-safe checks:

1. existing test/lint/validation commands
2. Terraform `fmt -check`, `init -backend=false`, and `validate` for the target environment
3. workflow policy checks that fail if live deploy/apply/destroy behavior appears in public CI
4. scans for non-placeholder Azure identifiers, secret-like material, and unsafe `LIVE_AZURE_TESTS=true` defaults

### FR-03 — Manual environment-approved deploy pipeline

M8 MUST define a manual protected deploy pipeline with all of the following:

- `workflow_dispatch` trigger
- protected GitHub Environment approval
- Azure OIDC authentication
- live smoke stage gated by explicit `LIVE_AZURE_TESTS=true`
- no default live execution from public CI

### FR-04 — Pipeline-first delivery scope

The deploy pipeline family MUST cover pipeline-driven delivery for:

1. IaC apply/update
2. environment/config injection
3. image build/publish or tagged image selection
4. container/app deployment or update
5. smoke orchestration
6. lifecycle control workflows for start, stop, and optional destroy

Manual portal or ad-hoc CLI steps may exist only as documented break-glass guidance.

### FR-05 — Start/resume and nightly shutdown pipelines

M8 MUST define:

- a manual start/resume pipeline for bringing the lab online from a stopped or scaled-down state
- a nightly shutdown pipeline that is idempotent, scoped, and cost-focused
- an optional manual destroy/recreate path for resources that cannot stop safely or remain too expensive while idle

### FR-06 — Smoke + trace verification pipeline

M8 MUST define a smoke/trace verification pipeline that proves the full live chain:

```text
browser client -> APIM -> BFF -> Agent Execution Service -> MCP Protected API
```

The same pipeline, or a tightly-coupled follow-up workflow, MUST also verify Azure Monitor / Application Insights correlation for the smoke window.

### FR-07 — Canonical browser smoke driver

The automated M8 smoke driver SHOULD use the M7 SPA/public client as the canonical browser path because it is the least tenant-coupled automation target. SPFx and SharePoint classic remain supplemental/manual paths unless a protected tenant-specific automation path is approved later.

### FR-08 — Cost-control matrix by resource type

M8 documentation MUST explicitly define cost-control handling for:

- ACA-hosted services
- APIM
- Log Analytics / App Insights
- ACR if image publishing is used
- optional AKS / Agent Gateway path if that future option is activated
- destroy/recreate considerations for non-stoppable or expensive resources

Each resource type MUST be classified as stoppable, scale-to-zero, left-running-with-reporting, or destroy/recreate only.

### FR-09 — Least-privilege Azure OIDC boundary

M8 MUST assume GitHub Actions authenticates to Azure using OIDC/federated identity, not long-lived secrets, wherever federation is supported. Live workflow identities MUST be least-privilege and scoped by purpose:

- deploy/apply
- smoke verification
- nightly shutdown / start-resume

This purpose split is binding: workflows MUST use separate principals per purpose, or an equivalently constrained model that enforces the same least-privilege boundaries with explicit scope and denied capabilities.

The shutdown/start-resume identity MUST be unable to run broad deploy/apply/destroy actions and MUST be limited to explicit lab stop/start/scale operations at resource-group scope or narrower.

Routine deploy and smoke identities MUST NOT require subscription-wide Owner rights, and no routine M8 workflow principal may use broad subscription Owner access.

### FR-10 — Protected environment and public CI separation

Live deploy and live smoke MUST run only in protected GitHub Environments with required reviewers. Public CI MUST remain validation-only and MUST NOT:

- fetch real Azure tokens
- run live browser sign-in
- call real APIM/BFF endpoints
- run `terraform apply` or `terraform destroy`

### FR-11 — Authentication and service-boundary preservation

M8 planning MUST preserve these live-boundary rules:

- `AUTH_MODE=strict` only
- no fixture header or mock-token path in live execution
- APIM preserves the inbound delegated `Authorization` header to the BFF
- BFF validates the inbound user token but does not perform the MCP OBO exchange
- Agent Execution Service is the only OBO boundary for MCP downstream access
- MCP Protected API accepts only the proper downstream token and rejects the original user token

### FR-12 — No token, PII, or unsafe tracestate leakage

Live telemetry, workflow logs, traces, and artifacts MUST NOT contain:

- raw bearer tokens, JWTs, auth codes, refresh tokens, cookies, or secrets
- PII claim values such as `oid`, `sub`, `email`, `upn`, `preferred_username`, `name`, `given_name`, `family_name`
- unsafe `Authorization`, `Cookie`, `Set-Cookie`, token-bearing query strings, or unsafe `tracestate` content

Existing sanitization rules remain mandatory in M8.

### FR-13 — Required negative tests and static scans

M8 planning MUST include the following validation gates:

1. workflow policy scan
2. secret / identifier scan
3. client token-handling scan
4. delegated-auth negative tests
5. OBO-boundary tests
6. telemetry leakage tests, including KQL negative checks
7. artifact hygiene checks
8. static workflow checks that enforce deploy/smoke/shutdown principal separation (or explicitly equivalent constrained model) and verify RBAC scope documentation is present

### FR-14 — Trace verification recipe with negative KQL checks

M8 MUST define a saved KQL query, workbook, or equivalent verification recipe that proves:

- positive correlation across APIM/BFF/Agent Execution Service/MCP for a smoke run
- negative absence of forbidden keys or token-like values across requests, dependencies, traces, and logs

### FR-15 — Review gates before implementation

M8 implementation MUST NOT begin until all three pre-implementation reviews are accepted and recorded in `.progress.md`:

- T10 Tank deployment review
- T11 Morpheus architecture review
- T12 Trinity security review

### FR-16 — Public-safe placeholders only

All M8 spec artifacts MUST use placeholder/example values only. Real subscription, tenant, client, resource-group, or environment identifiers MUST NOT appear in committed files.

### FR-17 — ADR coverage for major choices

Major M8 deployment and cost-control choices MUST be represented as ADRs before implementation, including:

- opt-in workflow boundary
- pipeline-first deployment model
- low-cost lifecycle strategy
- live trace verification + telemetry safety strategy

### FR-18 — Naming clarity for Agent Execution Service vs AKS Agent Gateway

If AKS or `agentgateway.dev` is mentioned anywhere in M8 design or implementation, documentation MUST explicitly distinguish it from the Agent Execution Service. The Agent Execution Service remains the lab service under test; the AKS Agent Gateway is optional infrastructure only.

---

## Non-Functional Requirements

### NFR-01 — Public-safe at all times

Every M8 commit MUST remain safe for a public repository. No intermediate commit may include a live secret or real Azure identifier.

### NFR-02 — Cost-safe by default

M8 defaults MUST bias toward the lowest reasonable lab spend rather than always-on convenience.

### NFR-03 — Idempotent lifecycle operations

Start/resume and shutdown workflows MUST tolerate already-started or already-stopped resources and report final state clearly.

### NFR-04 — Repeatable smoke verification

Smoke-test execution and trace verification MUST be repeatable across multiple runs against the same private environment.

### NFR-05 — Validation-only public CI preserved

Existing validation workflows (`python -m pytest`, compose config, Terraform validate, docs/security scans) MUST continue to run without live Azure credentials.

### NFR-06 — Placeholder/example naming preferred

Environment naming questions should not block M8 planning. Placeholder/example names are preferred unless a private environment owner later chooses a naming standard.

---

## Constraints

- This spec change is planning only.
- No live Azure changes are authorized here.
- Public CI remains non-live.
- ACA remains the default deployment target from M6.
- Optional AKS/Agent Gateway references do not change the default M8 path.
