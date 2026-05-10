---
name: Task Decomposition Format
description: How to format tasks.md and checklists/ for a feature spec. Checkbox format, sub-fields, verification checkpoints, requirements linking.
confidence: high
when_to_use: When generating tasks.md during the `tasks` phase. Read alongside task-workflow-selection (which workflow shape) to produce well-formed tasks.
---

## Task format rules

- Max 4 Do steps, max 3 files per task
- `[P]` marks parallel-eligible tasks; `[VERIFY]` marks quality checkpoints
- ALL Verify fields must be automated commands (no manual checks)
- Quality checkpoints every 2-3 tasks
- Final sequence: V4 (local CI) → V5 (CI pipeline) → V6 (AC checklist)
- Each task specifies which Squad agent handles it (Lead, Frontend, Backend, Tester) — read `.squad/routing.md` to pick
- Reference actual quality commands from `research.md` (never hardcode)
- Link each task to requirements (FR-*, AC-*)
- Each task SHOULD include an `Impact:` line (Low/Medium/High) — High-impact tasks trigger ADRs and approval gates (per [Impact Classification](../../../packages/squad-cli/templates/squad.agent.md.template#impact-classification))

## Checkbox task format (CRITICAL)

Tasks MUST use **checkbox format** with task IDs, phase grouping, sub-fields, and verification checkpoints. This format is scannable, git-diffable, and shows progress at a glance.

```
## Phase 1: {Phase Name}

**Goal**: {One sentence describing what this phase achieves.}

- [ ] T01 [P] {Task description}
  - **Files**: `path/to/file.py`, `path/to/other.py`
  - **Done when**: {Concrete, testable completion condition}
  - **Verify**: `{automated command to verify}`
  - **Impact**: Low
  - _Requirements: FR-001, FR-002_

- [ ] T02 {Task description}
  - **Files**: `path/to/file.py`
  - **Done when**: {Concrete completion condition}
  - **Verify**: `{automated command}`
  - **Impact**: Medium
  - _Requirements: FR-003_

## [VERIFY] V01 — {Phase name} checkpoint
- [ ] Run: `{test command}`
- [ ] Check: {What must be true}

## Phase 2: {Phase Name}

**Goal**: {One sentence.}

- [ ] T03 {Task description}
  ...
```

### Format rules

- Task IDs are sequential across all phases: T01, T02, T03… (not restarting per phase)
- `[P]` after the task ID means the task can run in parallel with other `[P]` tasks in the same phase
- Every task has `Files`, `Done when`, `Verify`, and `Impact` sub-fields
- `_Requirements:_` links back to FR-* and AC-* from `requirements.md`
- `[VERIFY]` checkpoints (V01, V02…) appear every 2-3 tasks
- Mark tasks `[x]` when completed during execution — primary progress indicator

### Target task counts

| Workflow | Fine (default) | Coarse |
|----------|----------------|--------|
| POC-first | 40-60+ tasks | 10-20 tasks |
| TDD | 30-50+ tasks | 8-15 tasks |

## Output

`.squad/specs/{NNN}-{slug}/tasks.md` using template at `.squad/templates/spec/tasks.md`.

## Checklists (sibling artifacts)

After generating `tasks.md`, also generate a `checklists/` directory with two files:

**`checklists/requirements.md`** — one checkbox per functional requirement, mapped to the task(s) that implement it:

```
## Requirements Checklist

- [ ] FR-001: {requirement description} — T01, T02
- [ ] FR-002: {requirement description} — T03
- [ ] FR-003: {requirement description} — T04, T05
```

**`checklists/acceptance.md`** — one checkbox per acceptance criterion from the feature spec:

```
## Acceptance Criteria Checklist

- [ ] AC-01: {acceptance criterion} — T01
- [ ] AC-02: {acceptance criterion} — T03, T04
- [ ] AC-03: {acceptance criterion} — T05
```

These checklists provide a requirements-level progress view separate from the task-level view. Update them as tasks complete during execution.

## See also

- `.squad/skills/task-workflow-selection/SKILL.md` — pick the workflow shape (POC-first / TDD / Bug-TDD) before formatting tasks
- `.squad/skills/feature-state-tracking/SKILL.md` — `state.json` updates as tasks complete
- `.squad/routing.md` — agent column lookup for task assignment
