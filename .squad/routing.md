# Work Routing

How to decide who handles what.

## Routing Table

| Work Type | Route To | Examples |
|-----------|----------|----------|
| Architecture, scope, repo structure | Morpheus | Monorepo shape, ADRs, cross-cutting design, review gates |
| Identity, OAuth2/OIDC, Entra ID, security | Trinity | OBO flow, token audiences, delegated vs app-only, public repo safety |
| Azure, Terraform, APIM, Docker, CI/CD | Tank | Azure Container Apps, APIM policies, Terraform modules, GitHub Actions |
| Python services, Agent Framework, APIs | Neo | FastAPI BFF, agent gateway, MCP protected API, shared auth helpers |
| SharePoint, SPFx, SPA, TypeScript | Mouse | Classic loader, SPFx placeholder, React/Vite and Next.js comparison |
| Code review | Morpheus | Review PRs, check quality, suggest improvements |
| Testing | Trinity | Security tests, identity negative tests, validation strategy |
| Scope & priorities | Morpheus | What to build next, trade-offs, decisions |
| Session logging | Scribe | Automatic — never needs routing |

## Issue Routing

| Label | Action | Who |
|-------|--------|-----|
| `squad` | Triage: analyze issue, assign `squad:{member}` label | Lead |
| `squad:{name}` | Pick up issue and complete the work | Named member |

### How Issue Assignment Works

1. When a GitHub issue gets the `squad` label, the **Lead** triages it — analyzing content, assigning the right `squad:{member}` label, and commenting with triage notes.
2. When a `squad:{member}` label is applied, that member picks up the issue in their next session.
3. Members can reassign by removing their label and adding another member's label.
4. The `squad` label is the "inbox" — untriaged issues waiting for Lead review.

## Rules

1. **Eager by default** — spawn all agents who could usefully start work, including anticipatory downstream work.
2. **Scribe always runs** after substantial work, always as `mode: "background"`. Never blocks.
3. **Quick facts → coordinator answers directly.** Don't spawn an agent for "what port does the server run on?"
4. **When two agents could handle it**, pick the one whose domain is the primary concern.
5. **"Team, ..." → fan-out.** Spawn all relevant agents in parallel as `mode: "background"`.
6. **Anticipate downstream work.** If a feature is being built, spawn the tester to write test cases from requirements simultaneously.
7. **Issue-labeled work** — when a `squad:{member}` label is applied to an issue, route to that member. The Lead handles all `squad` (base label) triage.
