---
name: Worktree Lifecycle Management
description: Creating, reusing, and cleaning up dedicated git worktrees for issue-based work. Used when worktree mode is enabled.
confidence: high
when_to_use: When the coordinator dispatches issue-based work and worktree mode is active (`worktrees: true` config or `SQUAD_WORKTREES=1` env). Skip when worktree mode is disabled — agents work in the main repo.
---

## Worktree mode activation

- Explicit: `worktrees: true` in project config (`squad.config.ts` or `package.json` `squad` section)
- Environment: `SQUAD_WORKTREES=1` set
- Default: `false` — agents work in the main repo

If worktree mode is off, this skill doesn't apply.

## Creating worktrees

- One worktree per issue number
- Multiple agents on the same issue share a worktree
- Path convention: `{repo-parent}/{repo-name}-{issue-number}`
  - Example: working on issue #42 in `C:\src\squad` → worktree at `C:\src\squad-42`
- Branch: `squad/{issue-number}-{kebab-case-slug}` (created from base branch, typically `main`)

## Dependency management

After creating a worktree, link `node_modules` from the main repo to avoid reinstalling.

| Platform | Command |
|----------|---------|
| Windows | `cmd /c "mklink /J {worktree}\node_modules {main-repo}\node_modules"` |
| Unix | `ln -s {main-repo}/node_modules {worktree}/node_modules` |

If linking fails (permissions, cross-device), fall back to `npm install` in the worktree.

## Reusing worktrees

Before creating a new worktree, check if one exists for the same issue:

1. `git worktree list` shows all active worktrees
2. If found for the issue, reuse it: `cd {path}`, verify branch is correct, `git pull` to sync
3. Multiple agents can work in the same worktree concurrently if they modify different files

## Cleanup

After a PR is merged, the worktree should be removed:

1. `git worktree remove {path}`
2. `git branch -d {branch}`

Ralph heartbeat can trigger cleanup checks for merged branches.

## Pre-spawn checklist

When dispatching an agent that will work on issue #N:

1. Determine if worktree mode is active (check config + env)
2. If yes:
   - Resolve / create the worktree per the path convention
   - Link `node_modules`
   - Pass `WORKTREE_PATH={path}` and `WORKTREE_MODE=true` in the spawn prompt
   - Pass `branch_name` for context
3. If no, agent works in the main repo (no special handling)

## See also

- Coordinator template `Worktree Awareness` section — session-start TEAM_ROOT resolution, worktree-local vs main-checkout strategy
- `.squad/templates/spawn-template.md` — `WORKTREE_PATH` / `WORKTREE_MODE` fields the spawn prompt carries
