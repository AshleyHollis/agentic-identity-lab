---
name: Roadmap Planning (project-level)
description: How to decompose a project into ordered, scoped features with milestones. Includes the Spec Status Dashboard and project-level status.json.
confidence: high
when_to_use: After architecture is approved, when entering the `roadmap` phase. Owned by Lead.
---

## Phase context

The `roadmap` phase runs **after** architecture is approved (per Phase Routing). It produces a feature decomposition that drives all subsequent per-feature work.

**Owner:** Lead.
**Routing:** Solo (Lead writes; specialists may consult).
**Impact:** Medium — strategic but reversible (re-decomposition is normal as the project evolves).

## Output: `.squad/project/roadmap.md`

Decompose the app into features:

- F000 is ALWAYS "Project Foundation" — scaffolding, CI, dev tooling
- Order by dependency: features others depend on come first
- Each feature completable in a single Squad session
- Tags: `[MVP]` must-have, `[NEXT]` after MVP, `[LATER]` Phase 2+

### Format

```
# Roadmap: {app-name}

## Phase 1 — Foundation
- F000 | Project Foundation | Repo, scaffolding, CI, base config | [MVP]

## Phase 2 — Core
- F001 | {feature} | {one-line description} | [MVP]

## Phase 3 — Polish
- F004 | {feature} | {one-line description} | [NEXT]
```

After roadmap is presented for confirmation, the coordinator can auto-generate F000 spec and signal: `"Roadmap approved — {N} features. Starting F000."`

## Spec Status Dashboard

After generating the roadmap, append a **Spec Status Table** at the bottom of `roadmap.md`. This table maps every roadmap feature to its spec status so the user can see coverage and progress at a glance.

```
## Spec Status

| Feature | Milestone | Spec Directory | Status | Phase |
|---------|-----------|----------------|--------|-------|
| F000 Project Foundation | M0 | `000-project-foundation/` | N/A | — |
| F001 {feature} | M1 | `001-{feature-slug}/` | ⬜ Not started | — |
| F002 {feature} | M2 | `002-{feature-slug}/` | ⬜ Not started | — |
```

**Status values** (in order):
`⬜ Not started` → `📋 Discovery` → `🔬 Research` → `📝 Requirements` → `🏗️ Design` → `✅ Specced` → `🚧 Implementing` → `✅ Complete`

**Update rules:**
- Update this table whenever a spec phase completes (e.g., after Discovery, change status to `📋 Discovery`).
- When the coordinator asks for overall project status, refresh from the current state of `.squad/specs/`.
- The Phase column tracks the current spec phase (discovery, research, requirements, design, tasks, execution).

## Project Status File: `.squad/project/status.json`

Lead maintains `.squad/project/status.json` for external monitoring tools.

**Create** this file when generating the first roadmap. **Update** whenever:
- A spec phase completes (the spec sub-agent updates the feature's `phase` field via Scribe)
- A task completes (coordinator updates via Scribe — see coordinator's Task State Update Protocol)
- A feature completes (coordinator updates feature status to `"complete"`)

```json
{
  "projectName": "{app-name}",
  "updatedAt": "2026-03-08T12:00:00Z",
  "summary": {
    "totalFeatures": 7,
    "specComplete": 6,
    "implementing": 1,
    "complete": 3,
    "notStarted": 1
  },
  "milestones": [
    {
      "id": "M1",
      "name": "Household + Inventory",
      "status": "complete",
      "features": ["F001"]
    }
  ],
  "features": [
    {
      "id": "F001",
      "name": "Inventory Foundation",
      "milestone": "M1",
      "specDir": "001-inventory-foundation",
      "phase": "complete",
      "totalTasks": 12,
      "completedTasks": 12,
      "updatedAt": "2026-03-08T10:00:00Z"
    }
  ]
}
```

When updating `status.json`, also recompute the `summary` counts from the `features` array.

## Spec directory naming convention (referenced from feature specs)

Spec directories use a **3-digit numeric prefix** matching the feature ID from the roadmap, followed by a kebab-case slug:

```
.squad/specs/
  000-project-foundation/
  001-inventory-foundation/
  002-ai-plan-acceptance/
  003-grocery-derivation/
```

The numeric prefix provides instant ordering and visual progress.

## Boundaries

- Roadmap describes WHAT and IN-WHAT-ORDER — it does NOT contain technical design
- Per-feature specs live under `.squad/specs/{NNN}-{slug}/` and own their own design and tasks
- Roadmap revisions during implementation: route through Spec Amendment flow rather than silently editing
