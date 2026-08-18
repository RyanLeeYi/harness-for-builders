**[繁體中文](../zh/setup-guide.md)** | **English**

# Harness for Builders: Setup Guide

> This walks you through building the harness step by step. If you're an AI agent reading this: scaffold directly, but discuss `acceptance` and architectural boundaries with the user first (see "⚠️ Discuss, don't guess" in each step).

## Prerequisites

- A git repo (new or existing)
- An AI coding agent (Claude Code / Cursor / Codex / …)
- Familiarity with your project's run and test commands

---

## Step 1: Confirm the Repo and Scope

Work in the project repo root. First ask yourself (or the user) one thing: **for this MVP, what's in scope and what's explicitly out?** Crossing out what you won't do is the single most effective guard against scope creep.

⚠️ **Discuss, don't guess**: MVP scope is the user's product decision. The agent shouldn't decide it alone.

---

## Step 2: Build L1 — the minimal harness (~20 min)

Copy three files from [templates/](templates/) into the repo root and fill in the blanks:

1. `templates/CLAUDE.md` → `CLAUDE.md`
2. `templates/init.sh` → `init.sh` (fill in install deps, prepare env, smoke test)
3. `templates/feature_list.json` → `feature_list.json`

Don't touch the work rules in `CLAUDE.md` — they're the harness's core constraints:

1. Do one feature at a time (pick the first `failing`)
2. Status can only go `failing → passing`, and must attach verification evidence
3. Don't do anything outside the list; new items get added as `failing` first
4. Do not modify an existing feature's acceptance after work has started
5. Before claiming done, run the run/test commands and paste the output

---

## Step 3: Turn MVP Scope into features + acceptance, Then Freeze

This is the most critical step in the whole harness. Turn Step 1's "in scope" into `feature_list.json` features, each with a decidable `acceptance`.

Vague acceptance is useless to an agent:

- ❌ "Should have good error handling"
- ✅ "When the email field is missing, return 400 + `{error: \"email required\"}`"

For features with ambiguity, write a PRD first (`templates/PRD.md` → `docs/prd/<feature>.md`): pin down Given/When/Then, interface contracts, and edge cases, then derive acceptance.

> **Where the spec lives is a choice, and it has a failure mode.** A PRD plus a
> one-line acceptance pointing at it means one spec in two files, and the two
> drift. Whichever one you name as authoritative, ask a second question: which
> of the two is harder to change unnoticed? If your freeze protects
> `feature_list.json` and nothing protects `docs/prd/`, then "the PRD wins" hands
> authority to the unprotected copy, and the mismatch only surfaces during
> verification, after the work is built.
>
> Solo, or when everyone who judges the work reads `feature_list.json` directly:
> skip the PRD and write acceptance that stands on its own, self-sufficient
> enough to be judged clause by clause. Archive it once the feature passes, so
> the file stays scannable.
>
> With a team, or non-engineer stakeholders, or an approval that happens outside
> the repo: keep the PRD — those readers are exactly who it exists for. Then
> make acceptance the authority anyway, treat the PRD as the narrative, and never
> let a verifier judge against a file your freeze does not cover.

Same step: write down each feature's dependencies in `prerequisites` — which features must already be `passing` before this one can be implemented or verified. No dependency means an empty array; don't leave it out. A field that was never declared must be treated as "undeclared," not used to decide whether things can run in parallel (see [architecture.md](architecture.md)).

**Freeze**: once the requester signs off on acceptance, the implementer must not quietly change it mid-work. Found a gap? Add a new entry, mark it failing, go back for sign-off — don't touch existing entries.

⚠️ **Discuss, don't guess**: wrong acceptance = a failed harness. When the agent is unsure "what counts as passing," it stops and asks — it does not invent a lax bar.

💡 **Work spanning 3+ features, or crossing multiple facets (frontend, backend, data)**: before starting, wrap it in an envelope and talk slices second (a slice is a feature, not a new ID) — sign off the envelope's `outcome`/`constraints`/`non_goals` first, then approve slices one at a time. Details and a JSON example are in [architecture.md](architecture.md).

---

## Step 4: The Daily Dev Loop

```
1. Opening: read CLAUDE.md, session-handoff.md, feature_list.json
   → state "which feature I'm doing and how I'll verify it"
     (can't answer = harness has a gap, fix it first)
2. Pick the first failing feature
3. TDD: test first (RED) → implement (GREEN) → refactor (IMPROVE), coverage ≥ 80%
4. Run a code review
5. Before flipping to passing: hand it to "another fresh-context agent/model" to verify
   → feed only the PRD + the artifact, check against acceptance item by item
6. Attach evidence, flip status to passing
7. Wrap up: update session-handoff.md, add a DEVLOG entry, commit + push
```

---

## Step 5: Add L2 — Handoff & Continuity

Before the first session that ends unfinished, create:

- `templates/session-handoff.md` → `session-handoff.md`: updated before wrap-up, **overwrite, don't append**, only the current state.
- `templates/ARCHITECTURE.md` → `docs/ARCHITECTURE.md`: structure, layer responsibilities, data flow, and **explicit boundary rules**. A new session's agent reads this instead of re-exploring.

---

## Step 6: Level Up to L3 — Feedback & Verification

Add these only when an incident or high risk calls for it — the same class of error recurring, a bug the existing logs cannot locate, a boundary violation that actually happened, or entering `strict` risk territory. **Feature count is not a reason**; drop any L3 component that never proved its value in the closing retro:

- **Structured logs**: startup, key operations, and error paths all need logs — before fixing a bug, confirm the logs can point at the failure.
- **Boundary guard script**: turn `ARCHITECTURE.md`'s boundary rules into an executable check with grep/linter, `exit 1` on violation, run in CI or pre-commit.
- **Verifier role separation**: generator ≠ verifier. The implementing model is biased toward its own output; verification always goes to another fresh-context agent/model.
- **(Optional) agent action trace**: if the platform supports hooks (e.g. Claude Code's PreToolUse), record every Edit/Write/Bash to catch overreach in real time and replay it later for improvement. Not required — add it only if you have the bandwidth.

---

## Daily Use

- Start every session with the fixed opening prompt.
- One feature at a time; flip to passing only with evidence.
- Three things at wrap-up: `session-handoff.md`, a DEVLOG entry (the blocker and the fix), `git commit + push`.

## Maintenance Principles

Keep the operational files (read every session) lean — see [optimization-guide.md](optimization-guide.md). At wrap-up, run the ablation review and drop components that didn't earn their keep.
