---
name: Feature State Tracking
description: state.json and .progress.md write triggers for per-feature spec/implementation state. Used by spec-feature, the coordinator, Lead, and Scribe — multiple agents update these files.
confidence: high
when_to_use: Whenever an agent transitions feature state — phase change, task dispatch, task completion, feature complete. Multi-agent — coordinate via the write-trigger table.
---

## Files maintained per feature

Each feature maintains state in `.squad/specs/{feature}/`:

- **`state.json`** — machine-readable, consumed by external monitoring tools
- **`.progress.md`** — narrative context accumulated across phases (prevents re-asking questions)

## `state.json`

Created on Phase 1 (Discovery) entry by spec-feature; updated at every transition by whichever agent triggers the change.

```json
{
  "featureName": "Inventory Foundation",
  "featureId": "F001",
  "phase": "discovery|research|requirements|design|tasks|execution|complete",
  "intent": "GREENFIELD|TRIVIAL|REFACTOR|MID_SIZED|BUG_FIX",
  "workflow": "poc|tdd|bug-tdd",
  "milestone": "M1",
  "taskIndex": 0,
  "totalTasks": 0,
  "completedTasks": 0,
  "currentAgent": null,
  "awaitingApproval": false,
  "updatedAt": "2026-03-08T12:00:00Z"
}
```

### Write triggers (multi-agent)

| Trigger | Owner | Fields to update |
|---------|-------|------------------|
| spec-feature enters a feature directory for the first time | spec-feature | CREATE `state.json` with featureName, featureId, phase="discovery", intent, workflow, milestone |
| spec-feature completes a phase (discovery → research, etc.) | spec-feature | Update `phase`, `updatedAt` |
| spec-feature generates `tasks.md` | spec-feature | Update `phase="tasks"`, `totalTasks` (count of T* items), `completedTasks=0` |
| Coordinator dispatches a task | Coordinator | Update `taskIndex`, `currentAgent`, `updatedAt` |
| Coordinator confirms task completion | Coordinator | Increment `completedTasks`, advance `taskIndex`, clear `currentAgent`, update `updatedAt` |
| Feature implementation complete | Coordinator | Update `phase="complete"`, `completedTasks=totalTasks`, `updatedAt` |

**Always update `updatedAt`** to the current ISO timestamp on every write. External monitoring tools rely on this for staleness detection.

## `.progress.md`

**Critical:** Create at the START of Phase 1 (Discovery), not after. Accumulates context and prevents re-asking questions across phases and sessions. If it doesn't exist when you enter a spec directory, create it immediately.

### Accumulates

- **Intent Classification** — type, confidence, keywords matched
- **Interview Responses** per phase — topic-response pairs + chosen approach
- **Learnings** discovered during each phase
- **Task completion status** during execution
- **Errors and recovery actions**

### Initial template (created at Discovery start)

```
# Progress: {Feature Name}

## Intent
- **Type**: {GREENFIELD|TRIVIAL|REFACTOR|MID_SIZED|BUG_FIX}
- **Confidence**: {high|medium|low}
- **Keywords**: {matched keywords}

## Phase: Discovery
- **Started**: {date}
- **Status**: In Progress

### Interview Responses
(filled as user answers questions)

### Learnings
(filled as context is discovered)

## Task Log

| Task | Summary | Agent | Completed | Verify |
|------|---------|-------|-----------|--------|
```

The Task Log table is populated during execution. Each row is appended by the coordinator (via Scribe) when a task completes. This structured format is parseable by monitoring tools.

## Project-level aggregation

For project-level state (across all features), see [`.squad/skills/roadmap-planning/SKILL.md`](../roadmap-planning/SKILL.md) — Lead maintains `.squad/project/status.json` aggregating feature-level `state.json` files.

## See also

- `.squad/skills/task-workflow-selection/SKILL.md` — sets the `workflow` field
- `.squad/skills/task-decomposition-format/SKILL.md` — `totalTasks` count comes from tasks.md
- `.squad/skills/roadmap-planning/SKILL.md` — project status.json aggregates feature state.json files
