---
name: Plain-Language Interview Pattern
description: How to conduct interviews using ask_user with concrete, plain-language framing. Used by all spec sub-agents (spec-constitution, spec-prd, spec-feature) and any agent running interactive scoping interviews.
confidence: high
when_to_use: When asking the user a non-obvious question with multiple choices — especially at scoping, design, or trade-off decision points. Replaces terse domain-jargon questions.
---

## The pattern

All interview questions MUST use `ask_user` with pre-populated choices wherever possible. This makes interviews fast and tappable instead of forcing the user to type paragraphs.

### Rules

- For questions with common answers (tech stack, testing philosophy, architecture style), provide 2-4 choices as options. Copilot CLI automatically adds a freeform input option — do NOT add an explicit "Other" choice.
- For truly open-ended questions ("describe your app", "walk me through the first session"), use plain text — no choices.
- Lead with a recommended option where one exists — mark it "(Recommended)" in the choice label.
- Ask ONE question at a time using a separate `ask_user` call. Group related questions into rounds, but ask each in turn and wait for the answer.
- If the user already provided the answer in their initial message, skip the question entirely.
- When a question can be answered with multiple selections (e.g., "which domains does your app cover?"), note that the user can describe multiple items in freeform.

### Critical — explain every question in plain language

The user is an engineer, not a domain expert in your spec terminology. Every `ask_user` question MUST include:

1. **Context sentence** — what the question is about and why it matters, in simple terms.
2. **Option explanations** — what each option MEANS in practice, with a concrete example. Put these ABOVE the choices in the question text, not in the choice labels (labels must stay short and scannable).
3. **Concrete examples** — use real scenarios from THIS project, not abstract descriptions.

### Bad example (too terse — user can't evaluate without domain knowledge)

```
question: "Inventory matching strategy?"
choices: ["Exact match only", "Exact + unit normalization", "Fuzzy inference"]
```

### Good example (explains each option from the user's perspective)

```
question: "Which experience do you want for MVP when the app checks your inventory against a recipe?\n\nOption 1 means: only skip a grocery item automatically when the match is obvious, like the exact same item and unit. If it is unclear, the app shows it for your review.\n\nOption 2 means: the app can also handle a few simple conversions automatically, like 1000 g = 1 kg.\n\nOption 3 means: the app tries to infer most matches on its own, which is easier but riskier.\n\nWhat feels right for MVP?"
choices: ["Be conservative: only obvious matches auto-count; unclear cases stay for review (Recommended)", "Allow a few simple conversions automatically", "Let the app infer most matches automatically"]
```

### The structure

Lead with a plain-language framing → explain each option with "Option N means: ..." and a concrete example → end with a simple question → provide short scannable choice labels.

## Why this matters

Users abandon interviews when they don't understand the question. Concrete framing keeps them engaged and produces better answers. This pattern is squad's distinctive UX advantage — preserve it across every interview, every agent.
