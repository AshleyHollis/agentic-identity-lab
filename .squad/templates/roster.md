# Team Roster

> {One-line project description}

> **Tier column:** Each agent is tagged with one of `Conductor` / `Delivery` / `Support` / `Advisory` (see [Agent Taxonomy](../squad.agent.md.template) and `docs/ralph-specum/devsquad-mapping.md`). Tier is metadata used for routing decisions; cast names stay as the primary identifier.

## Coordinator

| Name | Role | Tier | Notes |
|------|------|------|-------|
| Squad | Coordinator / Conductor | Conductor | Routes work, enforces handoffs and reviewer gates. Does not generate domain artifacts. |

## Members

| Name | Role | Tier | Charter | Status |
|------|------|------|---------|--------|
| {Name} | {Role} | Delivery | `.squad/agents/{name}/charter.md` | ✅ Active |
| {Name} | {Role} | Delivery | `.squad/agents/{name}/charter.md` | ✅ Active |
| {Name} | {Role} | Delivery | `.squad/agents/{name}/charter.md` | ✅ Active |
| {Name} | {Role} | Delivery | `.squad/agents/{name}/charter.md` | ✅ Active |
| Scribe | Session Logger | Support | `.squad/agents/scribe/charter.md` | 📋 Silent |
| Ralph | Work Monitor | Support | — | 🔄 Monitor |

## Coding Agent

<!-- copilot-auto-assign: false -->

| Name | Role | Charter | Status |
|------|------|---------|--------|
| @copilot | Coding Agent | — | 🤖 Coding Agent |

### Capabilities

**🟢 Good fit — auto-route when enabled:**
- Bug fixes with clear reproduction steps
- Test coverage (adding missing tests, fixing flaky tests)
- Lint/format fixes and code style cleanup
- Dependency updates and version bumps
- Small isolated features with clear specs
- Boilerplate/scaffolding generation
- Documentation fixes and README updates

**🟡 Needs review — route to @copilot but flag for squad member PR review:**
- Medium features with clear specs and acceptance criteria
- Refactoring with existing test coverage
- API endpoint additions following established patterns
- Migration scripts with well-defined schemas

**🔴 Not suitable — route to squad member instead:**
- Architecture decisions and system design
- Multi-system integration requiring coordination
- Ambiguous requirements needing clarification
- Security-critical changes (auth, encryption, access control)
- Performance-critical paths requiring benchmarking
- Changes requiring cross-team discussion

## Project Context

- **Owner:** {user name}
- **Stack:** {languages, frameworks, tools}
- **Description:** {what the project does, in one sentence}
- **Created:** {timestamp}
