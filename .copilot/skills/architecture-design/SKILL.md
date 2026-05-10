---
name: Architecture Design (project-level)
description: How to produce project-level architecture documentation as a fan-out across domain concerns. Owned by Lead during the architecture phase.
confidence: high
when_to_use: After PRD is approved, when entering the `architecture` phase. Lead reads this and orchestrates fan-out to domain specialists for each architecture concern.
---

## Phase context

The `architecture` phase runs **after** PRD approval and **before** roadmap (per Phase Routing in `packages/squad-cli/templates/squad.agent.md.template`). It is **High-impact** by definition — every major decision produces an ADR (`.squad/architecture/decisions/`).

**Owner:** Lead (per `.squad/routing.md`).
**Routing:** Fan-out — Lead orchestrates, domain specialists own concerns.

## Output structure

Architecture is split into separate files by concern. Create the directory `.squad/project/architecture/` and write one file per topic. Start with these core files, then add more as the project requires:

- `overview.md` — system overview, architecture principles, key decisions table, tech stack rationale
- `data-model.md` — entity definitions, relationships, diagrams (mermaid)
- `api-design.md` — endpoints, request/response shapes, error formats, versioning
- `infrastructure.md` — deployment, CI/CD, monitoring, environment config

Additional files as needed: `auth-flow.md`, `caching-strategy.md`, `event-architecture.md`, `ai-integration.md`. Each file should be self-contained with cross-references to related files.

## Domain ownership during fan-out

Per `.squad/routing.md`:

| Concern | Primary owner | Output |
|---------|---------------|--------|
| `overview.md` | Lead | Synthesizes others; decision table |
| `data-model.md` | Backend / data specialist | Entities, relationships |
| `api-design.md` | Backend | Endpoint shapes, error format |
| `infrastructure.md` | DevOps / Platform | Deploy, monitoring |
| `auth-flow.md` | Security specialist | Auth model, session handling |
| `caching-strategy.md` | Backend / Performance | Cache layers, invalidation |

## Process

1. **Read** PRD + constitution before starting.
2. **Decompose** architecture concerns from the PRD scope. Lead identifies which files are needed.
3. **Fan-out** to domain specialists in parallel (one spawn per concern). Each specialist writes their file.
4. **Synthesize** in `overview.md` — Lead writes this last, referencing the others.
5. **Produce ADRs** for each major architectural decision (database choice, framework, API style, etc.). Use `.squad/templates/architecture/decisions/adr-template.md`.
6. **Present for confirmation** — Comprehension Checkpoint before advancing to roadmap phase.

## ADR triggers

A decision belongs in an ADR (not just inline in architecture/*.md) when:
- It would survive a rewrite
- Reversing it would take more than a sprint
- It's a public-contract or framework choice
- It has security or compliance implications
- The team disagrees and the choice needs traceable rationale

Otherwise, lightweight decisions go to the inbox (`.squad/decisions/inbox/`).

## Approach proposals

When a domain specialist faces a non-obvious architectural choice, propose 2-3 distinct approaches:
- Always present at least 2 approaches (never just 1)
- Maximum 3 approaches (more causes decision fatigue)
- Lead with your recommendation
- Trade-offs must be honest — no straw-man alternatives
- Apply YAGNI: strip unnecessary complexity from all approaches
- Store chosen approach in the relevant ADR

## Boundaries

- Architecture files describe shape and structure — they do NOT contain implementation code
- Specs and ADRs reference these files; this directory is the canonical architecture record
- Updates after initial creation require ADRs (architecture is High-impact; never silently amend)
