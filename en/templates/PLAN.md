---
updated: YYYY-MM-DD
status: idea confirmed   # idea confirmed → MVP in progress → iterating → wrapping up
repo: <repo link>
---

# <project name> — PLAN

> This governs "why, scope, what counts as success." It's a living document: change it when scope changes.
> "What exactly, and what counts as correct" goes in `docs/prd/`; "where we are" is in `feature_list.json`.

## The Problem to Solve
<whose pain, and what it is>

## Success Metrics (measurable, check against these at wrap-up)
- <e.g. answer accuracy ≥ 80% (self-built 20-question test set)>
- <e.g. single-query latency < 3s>

## MVP Scope
**Do**:
- [ ] <core feature 1>
- [ ] <core feature 2>

**Don't** (cross out explicitly to prevent scope creep):
- <e.g. no UI, CLI is enough>

## Tech Choices
<a table is enough; "why A not B" goes in DECISIONS.md, keep only the conclusion here>

| Layer | Choice |
|-------|--------|
|       |        |

## Milestones
- [ ] M1 (date): <verifiable output>
- [ ] M2 (date): <verifiable output>

## Agent Harness
- [ ] Build L1 on kickoff day: `CLAUDE.md` + `init.sh` + `feature_list.json` (turn each MVP scope item into feature + acceptance)
- [ ] For ambiguous features, write a PRD first (`docs/prd/`)
- [ ] Add L2 before the first unfinished session; go to L3 when bugs get hard or features grow

## Quality Bar (applies to every feature)
- TDD: RED → GREEN → IMPROVE, coverage ≥ 80%
- Code review after each feature; a second agent verifies before status flips to passing
- Before commit: no hardcoded secrets, inputs validated, error messages don't leak sensitive data
- Conventional commits

## Wrap-up Checklist
- [ ] Check success metrics, put the numbers in the last DEVLOG entry
- [ ] Harness ablation review: which components actually blocked problems, which were overhead
- [ ] README complete: problem → architecture → install → demo
