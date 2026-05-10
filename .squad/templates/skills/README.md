# Squad Skills — Index by Category

> **Skills** are reusable patterns and practices the team has captured. The coordinator does **skill-aware routing** — before spawning an agent, it scans this directory for relevant skills and includes them in the spawn prompt.

This index groups skills by category, [aligned with DevSquad's skill taxonomy](https://microsoft.github.io/devsquad-copilot/skills) and extended with a Squad-specific category for capabilities DevSquad doesn't have.

Skills live in flat directories under `.squad/skills/{skill-name}/SKILL.md` — categories are documentation, not filesystem hierarchy. To add a skill, create a new directory; to recategorize, update this file.

## Plan & Architecture

Skills for planning phases (envision, prd, architecture, roadmap, spec.feature, design).

| Skill | What it covers |
|-------|----------------|
| [`plain-language-interview`](plain-language-interview/SKILL.md) | The "Option N means..." interview pattern used by all spec sub-agents |
| [`architecture-design`](architecture-design/SKILL.md) | Project-level architecture by concern (data, API, infra) — Lead orchestrates fan-out |
| [`roadmap-planning`](roadmap-planning/SKILL.md) | Feature decomposition, milestones, Spec Status Dashboard, project status.json — owned by Lead |
| [`feature-design`](feature-design/SKILL.md) | Per-feature design fan-out across domain specialists during the `design` phase |

## Work Items & Estimation

Skills for translating specs into executable work and tracking it.

| Skill | What it covers |
|-------|----------------|
| [`task-workflow-selection`](task-workflow-selection/SKILL.md) | Pick implementation workflow (POC-first / TDD / Bug-TDD) from feature intent |
| [`task-decomposition-format`](task-decomposition-format/SKILL.md) | Checkbox task format, sub-fields, `[VERIFY]` checkpoints, sibling `checklists/` files |
| [`feature-state-tracking`](feature-state-tracking/SKILL.md) | `state.json` and `.progress.md` write triggers — multi-agent (spec-feature, coordinator, Lead) |

## Quality & Security

Skills for verification, review, security checks.

| Skill | What it covers |
|-------|----------------|
| [`fact-checking`](fact-checking/SKILL.md) | Validating claims and citations |
| [`pr-screenshots`](pr-screenshots/SKILL.md) | Capturing screenshots for PR review |

## Development

Skills for day-to-day development workflow.

| Skill | What it covers |
|-------|----------------|
| [`gh-auth-isolation`](gh-auth-isolation/SKILL.md) | Isolating GitHub auth across worktrees |
| [`session-recovery`](session-recovery/SKILL.md) | Recovering from interrupted sessions |
| [`ralph-two-pass-scan`](ralph-two-pass-scan/SKILL.md) | Ralph's two-pass scan pattern for backlog work |
| [`release-process`](release-process/SKILL.md) | Release workflow (semver, changelog, tag) |
| [`versioning-policy`](versioning-policy/SKILL.md) | Version-bump policy for the project |
| [`worktree-lifecycle`](worktree-lifecycle/SKILL.md) | Creating/reusing/cleaning up issue-based git worktrees (when worktree mode is enabled) |

## Project Setup

Skills for initial scaffolding and configuration.

*(No Squad-native skills in this category yet — DevSquad has `init-config`, `init-docs`, `init-scaffold`, `board-config`. Squad's init flow is currently coordinator-template-driven; could be extracted to skills if it grows.)*

## Squad Operations *(Squad-specific — not in DevSquad)*

Capabilities unique to Squad's execution layer (casting, personal squad, multi-machine coordination, model selection, tone). DevSquad has no equivalent category.

| Skill | What it covers |
|-------|----------------|
| [`personal-squad`](personal-squad/SKILL.md) | Personal Squad / Ghost Protocol — personal agents that overlay project agents |
| [`cross-squad`](cross-squad/SKILL.md) | Coordinating across multiple squads |
| [`cross-machine-coordination`](cross-machine-coordination/SKILL.md) | State sync across multiple machines |
| [`model-selection`](model-selection/SKILL.md) | Per-agent model selection (4-layer cost-first) |
| [`economy-mode`](economy-mode/SKILL.md) | Cost-conscious operation mode |
| [`external-comms`](external-comms/SKILL.md) | Communication outside the team (PRs, issues, public) |
| [`humanizer`](humanizer/SKILL.md) | Tone and voice adjustment for public artifacts |

## Adding a new skill

1. Create `.squad/skills/{skill-name}/SKILL.md` with frontmatter:
   ```
   ---
   name: {Display name}
   description: {one-line — used by skill-aware routing}
   confidence: low | medium | high
   when_to_use: {plain description of trigger conditions}
   ---
   ```
2. Add an entry to this README under the appropriate category.
3. If the skill is reusable across projects (vs project-specific), consider promoting to `.copilot/skills/` (the Copilot-level / cross-project skill directory).

## Skill confidence lifecycle

Skills evolve through three confidence levels — see [Skill Confidence Lifecycle](../../packages/squad-cli/templates/squad.agent.md.template#skill-confidence-lifecycle) in the coordinator template.

- `low` → first observation
- `medium` → confirmed by independent agents/sessions
- `high` → established, team-agreed

Confidence only goes up. Bumps happen when an agent independently validates an existing skill.

## See also

- [`docs/ralph-specum/devsquad-mapping.md`](../../docs/ralph-specum/devsquad-mapping.md) — Rosetta Stone mapping Squad ↔ DevSquad
- [Skill-aware Routing](../../packages/squad-cli/templates/squad.agent.md.template#skill-aware-routing) — how the coordinator selects and includes skills
- [DevSquad's Skills documentation](https://microsoft.github.io/devsquad-copilot/skills)
