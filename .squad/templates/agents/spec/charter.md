# Spec — Family Index (Router)

> ⚠️ **This agent is now a family of four narrowly-scoped sub-agents.** The original Spec agent's responsibilities have been split. This file is an index pointing at the new sub-agents and the skills that absorbed Spec's project-level responsibilities.
>
> If a spawn prompt addresses "Spec" without specifying a sub-agent, the coordinator should use [Phase Routing](../../../packages/squad-cli/templates/squad.agent.md.template#phase-routing) state-detection to route to the correct sub-agent — or ask the user.

## Why the split

The original Spec agent operated at four levels in a single charter (constitution, project-level PRD+architecture+roadmap, indexing, feature-level). Every Spec invocation risked absorbing all four. Splitting into narrowly-scoped sub-agents per phase eliminates this scope-bleed.

This split is part of the [DevSquad alignment](../../../docs/ralph-specum/devsquad-mapping.md) refactor. Each sub-agent now owns exactly one phase from [Phase Routing](../../../packages/squad-cli/templates/squad.agent.md.template#phase-routing).

## The four sub-agents

| Sub-agent | Phase owned | Output | Charter |
|-----------|-------------|--------|---------|
| **spec-constitution** | `constitution` | `.squad/project/constitution.md` | [`spec-constitution/charter.md`](../spec-constitution/charter.md) |
| **spec-prd** | `prd` | `.squad/project/prd.md` | [`spec-prd/charter.md`](../spec-prd/charter.md) |
| **spec-feature** | `spec.feature` + `tasks` | `.squad/specs/{NNN}-{slug}/{goals,research,requirements,tasks}.md` + state | [`spec-feature/charter.md`](../spec-feature/charter.md) |
| **spec-index** | `index` | `.squad/specs/.index/` | [`spec-index/charter.md`](../spec-index/charter.md) |

## Responsibilities that moved out of Spec

The original Spec agent owned three responsibilities that no longer belong to the Spec family. These are now owned by Lead via skills:

| Original Spec content | New owner | Skill |
|-----------------------|-----------|-------|
| Project architecture (Level 2 architecture sections) | Lead + domain specialists (fan-out) | [`.squad/skills/architecture-design/`](../../skills/architecture-design/SKILL.md) |
| Project roadmap + Spec Status Dashboard + status.json | Lead | [`.squad/skills/roadmap-planning/`](../../skills/roadmap-planning/SKILL.md) |
| Per-feature design.md (Level 4 Phase 4) | Domain specialists (fan-out) | [`.squad/skills/feature-design/`](../../skills/feature-design/SKILL.md) |

## Shared skills

All four sub-agents use:
- [`.squad/skills/plain-language-interview/SKILL.md`](../../skills/plain-language-interview/SKILL.md) — interview UX pattern (mandatory)

## State-detection summary

The coordinator picks which sub-agent to spawn based on repository state (per Phase Routing):

| State | Phase | Sub-agent |
|-------|-------|-----------|
| `.squad/project/constitution.md` missing | `constitution` | `spec-constitution` |
| Constitution exists, `.squad/project/prd.md` missing | `prd` | `spec-prd` |
| PRD exists, no `.squad/project/architecture/` | `architecture` | **Lead** (not Spec) — uses architecture-design skill |
| Architecture exists, no `.squad/project/roadmap.md` | `roadmap` | **Lead** (not Spec) — uses roadmap-planning skill |
| Roadmap exists, feature has no `goals.md` | `spec.feature` | `spec-feature` |
| Feature spec done, no `design.md` | `design` | **Domain specialists fan-out** — use feature-design skill |
| Design done, no `tasks.md` | `tasks` | `spec-feature` (re-spawned) |
| User says `"index"` | `index` | `spec-index` |

## What this index does NOT do

- It does NOT run any spec workflow itself — it routes to the correct sub-agent
- It is NOT a spawn target — never spawn "Spec" directly; spawn one of the four sub-agents

## Migration note

Existing `.squad/specs/{feature}/` directories continue to work — `spec-feature` is backwards-compatible with the prior format. Existing `.squad/project/architecture/` and `.squad/project/roadmap.md` are owned by Lead going forward; future amendments route to Lead, not Spec.

## Boundaries

- Conversations about "Spec" as a single agent are historical — refer users to the appropriate sub-agent
- Charter updates to Spec must be applied to the relevant sub-agent's charter, not this index
- This index is documentation; it has no model preference, no boundaries of its own, and is never invoked
