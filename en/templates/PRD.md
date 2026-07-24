---
updated: YYYY-MM-DD
feature: <the feature_list.json id range, e.g. F1–F4>
---

# <feature name> — PRD

> **Core principle: the harness performs best when it can verify itself.** Write every requirement in a form that's executable and decidable — vague "should have good error handling" is useless to an agent; "missing email field returns 400 + `{error: \"email required\"}`" is what works.
> One PRD maps to one feature group; each "requirement & acceptance" becomes a feature + acceptance in `feature_list.json`.
> **Don't put dev rules in the PRD** (immutability, TDD, commit format go in `CLAUDE.md`) — duplicating them causes drift and eats context.

## Background & Goal
<a line or two: why now. Link back to the problem in PLAN.>

## Non-goals (not this time)
<more important than the goals — the most effective anti-scope-creep tool>
- Won't do <X>
- Won't touch <existing Y file / API>

## Requirements & Acceptance
<write each requirement in a decidable form — this is the most critical part of the PRD for the harness>
<use a user story for the title (the shell) to keep role and intent; keep acceptance as Given/When/Then (the core), testable>

### R1: As a <role>, I want <action>, so that <value>
- Given <precondition>
- When <action>
- Then <observable result, specific enough to write as a test assertion>

### R2: ...

## Interface Contract
<data models, types, API endpoint specs. Pin these down and the agent won't invent an incompatible structure.>

## Concrete Examples (input → output)
<examples beat a thousand words, give 2-3. request/response JSON, before/after transforms>

## Edge Cases & Error Behavior
<what you don't write, the agent will guess>
- Empty / missing field: <behavior>
- Duplicate submission: <behavior>
- External service failure: <behavior>

## Definition of Done (commands that must pass)
<the feedback loop for the harness: run the command, see the result, fix itself>
- `<test command>` all pass, coverage ≥ 80%
- `<lint command>` no errors
- `<build command>` succeeds

## Open Questions
<clear these before work starts, or mark "stop and ask when hit">
- [ ] <question> (decider: <who>)
