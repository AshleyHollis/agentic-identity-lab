# ADR-{NNN}: {Decision title}

> **Status:** Proposed | Accepted | Superseded by ADR-{NNN} | Deprecated
> **Date:** {YYYY-MM-DD}
> **Deciders:** {agent names — Lead, plus consulted specialists}
> **Phase:** {architecture | design | implement}
> **Impact:** High *(ADRs are reserved for High-impact decisions; see [Impact Classification](../../../packages/squad-cli/templates/squad.agent.md.template#impact-classification))*

## Context

What's the situation that requires a decision? What are the constraints? What's *not* in scope?

Keep this section to the facts a reader needs to evaluate the decision. Avoid hindsight; capture the situation as it was when the decision was made.

## Ranked priorities

What matters most when choosing? List in order, most important first. This list is the criteria used to evaluate options.

1. {priority — e.g., "Operational simplicity over feature richness"}
2. {priority — e.g., "Reversibility — must be undoable in 1 sprint"}
3. {priority — e.g., "Existing-stack compatibility"}
4. {priority — e.g., "Cost"}

> **DevSquad alignment:** ADRs in this format follow [DevSquad's ranked-priorities pattern](https://microsoft.github.io/devsquad-copilot/decisions) — decisions are evaluated against project-specific priorities, not generic trade-offs.

## Options considered

### Option 1: {short name}

{1-2 paragraph description}

**Pros:**
- {pro}
- {pro}

**Cons:**
- {con}
- {con}

**Score against ranked priorities:**
- Priority 1: {assessment}
- Priority 2: {assessment}
- Priority 3: {assessment}

### Option 2: {short name}

(same structure)

### Option 3: {short name} *(if applicable)*

(same structure)

## Decision

We chose **Option {N}: {name}**.

### Rationale

Why this option won against the ranked priorities. Be specific — name the priorities it satisfies and the ones it trades off.

### Consequences

**Positive:**
- {what we gain}

**Negative / costs:**
- {what we trade away}

**Neutral / informational:**
- {downstream changes this implies}

## Implementation notes

What needs to change in the codebase to enact this decision? Link to:
- Specs that depend on this decision
- Tasks that implement it
- Skills or charters affected

## Review checkpoints

- [ ] Decision reviewed at next architecture sync (date: {YYYY-MM-DD + 14 days})
- [ ] Comprehension Checkpoint after first implementation that depends on this ADR
- [ ] Re-review trigger: {condition that would invalidate this — e.g., "if {tech} hits {scale limit}"}

## References

- Related ADRs: {ADR-{NNN}, ...}
- Source discussions: {decision inbox entries, links}
- External docs: {links to authoritative sources}
- Spec(s) this decision serves: {`.squad/specs/{NNN}-{slug}/...`}

---

> **Naming:** ADR files use 3-digit numeric prefix matching insertion order: `001-{kebab-slug}.md`, `002-{kebab-slug}.md`. Numbers are never reused.
>
> **Location:** `.squad/architecture/decisions/{NNN}-{slug}.md`. Project-level ADRs go here. Per-feature design decisions of similar weight may also live in `.squad/specs/{NNN}-{slug}/decisions/` and reference back to project-level ADRs.
>
> **vs decisions inbox:** Use this template for High-impact, architectural decisions that would survive a rewrite. For routine team agreements (naming conventions, test patterns, "we picked X over Y for this module"), use the lightweight decisions inbox at `.squad/decisions/inbox/{agent}-{slug}.md` — Scribe merges into `.squad/decisions.md`. See [the Rosetta Stone](../../../docs/ralph-specum/devsquad-mapping.md#decisions--records) for the tier rule.
