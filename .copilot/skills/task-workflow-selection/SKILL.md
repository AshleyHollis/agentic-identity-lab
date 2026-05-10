---
name: Task Workflow Selection
description: Decide the implementation workflow (POC-first / TDD / Bug-TDD) based on feature intent. Used by spec-feature during the tasks phase.
confidence: high
when_to_use: When entering the `tasks` phase of per-feature work — pick the right workflow before decomposing into tasks. Intent classification (from spec-feature Discovery) drives the selection.
---

## Workflow selection (based on intent)

Intent classification from `spec-feature` Discovery determines the workflow used during the `tasks` phase.

### GREENFIELD → POC-first (5 phases)

For new features built from scratch — prove the end-to-end path first, then harden.

| Phase | Goal | Distribution |
|-------|------|--------------|
| 1. Make It Work (POC) | Working prototype, skip tests, validate end-to-end | 50-60% |
| 2. Refactoring | Clean up, error handling, follow patterns | 15-20% |
| 3. Testing | Unit, integration, E2E tests | 15-20% |
| 4. Quality Gates | Lint, types, CI, PR creation | 10-15% |
| 5. PR Lifecycle | CI monitoring, review resolution, final validation | 5-10% |

### Non-GREENFIELD → TDD Red-Green-Yellow (4 phases)

For changes to existing code (REFACTOR, MID_SIZED, TRIVIAL, BUG_FIX-with-existing-test) — tests come first.

| Phase | Goal | Distribution |
|-------|------|--------------|
| 1. Red-Green-Yellow Cycles | Test-first implementation in triplets | 60-70% |
| 2. Additional Testing | Integration/E2E beyond unit tests | 10-15% |
| 3. Quality Gates | Local CI, PR creation | 10-15% |
| 4. PR Lifecycle | CI monitoring, review resolution | 5-10% |

### BUG_FIX → Phase 0 (Reproduce) + TDD phases

Bug fixes get an extra Phase 0 — reproduce the failure with a test before any other work.

| Phase | Goal | Distribution |
|-------|------|--------------|
| 0. Reproduce | Failing test that demonstrates the bug | 10-15% |
| 1. Red-Green-Yellow Cycles | Test-first fix | 50-60% |
| 2. Additional Testing | Regression coverage, edge cases | 10-15% |
| 3. Quality Gates | Local CI, PR creation | 10-15% |
| 4. PR Lifecycle | CI monitoring, review resolution | 5-10% |

## Picking workflow at runtime

Read `intent` from `state.json` (set during Discovery):

- `GREENFIELD` → POC-first
- `TRIVIAL`, `REFACTOR`, `MID_SIZED` → TDD
- `BUG_FIX` → BUG_FIX (Phase 0 + TDD)

Set `state.json` `workflow` field to `poc | tdd | bug-tdd` after selection.

## See also

- `.squad/skills/task-decomposition-format/SKILL.md` — how to format individual tasks within these phases
- `.squad/skills/feature-state-tracking/SKILL.md` — `state.json` write triggers and `.progress.md` format
