---
name: Feature Design (per-feature)
description: How domain specialists produce per-feature design.md during the design phase fan-out. Read by Backend, Frontend, Tester, and other specialists when handling design work for a feature.
confidence: high
when_to_use: When entering the `design` phase of a per-feature workflow (after spec-feature has produced requirements.md, before spec-feature produces tasks.md). The coordinator fans out across domain specialists; each reads this skill for shape guidance.
---

## Phase context

The `design` phase runs **after** `requirements.md` is approved (per Phase Routing in `packages/squad-cli/templates/squad.agent.md.template`) and **before** the `tasks` phase.

**Routing:** Fan-out across domain specialists. Lead orchestrates, specialists own their concerns.
**Output:** `.squad/specs/{NNN}-{slug}/design.md`
**Impact:** Medium–High depending on feature scope.

## What design.md contains

A complete `design.md` covers:

- **Component diagram** (mermaid) and component responsibilities
- **Data flow** (sequence diagram in mermaid)
- **Technical decisions table** (Decision | Options | Choice | Rationale)
- **File structure table** (File | Create/Modify | Purpose)
- **Interfaces** (TypeScript types or equivalent)
- **Error handling table**, edge cases
- **Dependencies table**, security considerations, performance considerations
- **Test strategy** (unit, integration, E2E)
- **Existing patterns to follow** — reference patterns from the codebase

## Fan-out by concern

Lead identifies which concerns the feature touches and dispatches specialists in parallel:

| Concern | Owner | Section produced |
|---------|-------|-------------------|
| API design | Backend | Endpoints, request/response shapes, error format |
| Data model | Backend / data specialist | Entity changes, schema migrations |
| UI / interaction | Frontend | Component tree, interaction flow, state |
| Test strategy | Tester | Unit/integration/E2E plan, fixtures, coverage targets |
| Security | Security specialist | Auth, authz, input validation, audit (if security-touching) |
| Performance | Performance specialist | Caching, batching, lazy loading (if performance-critical) |
| Integration | Backend / integration specialist | External APIs, services, webhooks |

Lead writes the `Component Diagram` and `Technical Decisions` sections, synthesizing across specialist outputs.

## ADR triggers

Per the design phase, raise an ADR when a decision is High-impact:
- Choice between distinct architectural styles (REST vs GraphQL, monolith vs split, etc.)
- Data model changes that imply migrations
- Auth/authz model changes
- Public-contract changes
- Framework or major-library introductions

ADR template: `.squad/templates/architecture/decisions/adr-template.md`. Store at `.squad/architecture/decisions/{NNN}-{slug}.md` (project-level) or `.squad/specs/{NNN}-{slug}/decisions/` (feature-local) — promote feature-local ADRs to project-level if they have cross-feature implications.

## Process

1. **Read** `goals.md`, `research.md`, `requirements.md` for this feature. Read project `constitution.md` and `architecture/` for context.
2. **Decompose** the feature into design concerns. Lead identifies which specialists are needed.
3. **Fan out** specialists in parallel (one spawn per concern). Each writes to a section of `design.md` (or to staged drafts that Lead merges).
4. **Lead synthesizes** the sections into `design.md`, resolves cross-concern conflicts, writes the Component Diagram and Decisions table.
5. **Produce ADRs** for High-impact decisions identified during design.
6. **Comprehension Checkpoint:** Lead presents the design walkthrough; user confirms before tasks phase.

## Approach proposals

When facing a non-obvious design choice within your concern, propose 2-3 distinct approaches:
- Always present at least 2 approaches (never just 1)
- Maximum 3 approaches (more causes decision fatigue)
- Lead with your recommendation
- Trade-offs must be honest — no straw-man alternatives
- Apply YAGNI: strip unnecessary complexity from all approaches

Capture chosen approach in the design's Technical Decisions table; promote to ADR if High-impact.

## Quality bar

Before signing off on design:
- Every requirement (FR-*, AC-*) from `requirements.md` is addressed in design
- Edge cases enumerated
- Error handling defined
- Test strategy specified (which tests, where, what coverage target)
- Dependencies named with versions
- No "TBD" or "we'll figure this out later" — design is the place to figure it out

If design uncovers gaps in requirements, route to **Spec Amendment** (don't silently expand scope) — see Phase 3 of DevSquad alignment.

## Boundaries

- Design describes WHAT and HOW — it does NOT contain implementation code (that's `implement` phase)
- Design must reference requirements explicitly — every section ties back to FR-* / AC-*
- Cross-feature design implications produce ADRs at project level
