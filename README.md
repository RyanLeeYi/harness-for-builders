**English** | **[繁體中文](zh/README.md)**

# Harness for Builders: Make Any AI Agent Reliably Ship Your Project

> By [Ryan Lee](https://github.com/RyanLeeYi)
>
> **You can hand this entire document to any AI and it will guide you through building the harness.**
>
> **v1.0** · Last updated: 2026-07-24 · [Changelog](CHANGELOG.md)

> 💡 **Inspired by [Vault for Founders](https://github.com/cwlin0131/Vault-for-Founders)** by CW Lin — this repo borrows its "hand it to any AI and it sets itself up" format and applies it to *agent harnesses* instead of a founder's knowledge base. The underlying method is adapted from [Learn Harness Engineering](https://walkinglabs.github.io/learn-harness-engineering/zh-TW/projects/).

---

## For AI Agents

If you're an AI agent reading this to help a user set up their development environment:

Harness for Builders is a framework for managing an AI coding agent's working environment using structured artifacts in the repo. Your job is to help the user build it. **Scaffolding can be done directly** (the shell of `init.sh`, `feature_list.json`); but **core content — a feature's acceptance, architectural boundaries, project rules — must be discussed with the user first, not filled in like a form.**

**Suggested reading order:**

1. Read this README for the overall architecture and philosophy
2. Read [setup-guide.md](en/setup-guide.md) for step-by-step setup
3. Read [architecture.md](en/architecture.md) for design decisions and trade-offs (why three levels, why freeze acceptance)
4. Use [templates/](en/templates/) to scaffold the user's project
5. **Important**: You cannot guess `acceptance` or architectural boundaries for the user. Follow the discussion flow in setup-guide to walk them, layer by layer, through defining "what counts as done." If the acceptance is wrong, the whole harness fails
6. After setup, read [optimization-guide.md](en/optimization-guide.md) to help keep the operational files (read every session) lean

---

## What Is This

Harness for Builders is a complete framework for building a repo where an AI agent can work reliably, from scratch — including the why, the how, and ready-to-use templates.

As you delegate more work to AI (writing features, fixing bugs, refactoring), it needs a place to "know the current state": how the project runs, what the rules are, what's in scope, where you left off last time. That place is your **harness**.

**Core claim: an agent's reliability doesn't come from how well the prompt is written — it comes from the structured artifacts in the repo.** Prompts get forgotten, drift, and must be re-explained every session; files don't — they sit in the repo as the single source of truth.

```
 A fresh agent opening your repo, with no conversation history,
 must be able to answer four questions:

   ┌ How do I run it?   ─────→  init.sh
   │
   ├ Where are we?      ─────→  feature_list.json  +  session-handoff.md
   │
   ├ What's next?       ─────→  the first failing entry in feature_list.json
   │
   └ What counts as done? ───→  that feature's acceptance (frozen)

 Can't answer one = the harness has a gap → patch it with a file, not a prompt
```

### Key Terms

- **Harness**: a set of files in the repo that tell the agent how to run, what to do, and whether it's done. Not framework code — a working environment.
- **feature_list.json**: the state machine for scope and acceptance. One entry per feature, status is only `failing` / `passing`, flipping to passing always requires evidence, and dependencies between features are declared via `prerequisites` — undeclared is treated as unknown, not as "no dependency."
- **acceptance**: "how to verify it's done." Written before work starts, signed off, then **frozen** — the single most important word in the harness.
- **session**: one continuous stretch of dev work. The agent's context resets, so each session ends with a handoff.

---

## Why You Need a Harness

Without a harness, you've probably hit these:

| Symptom | How the harness blocks it |
|---------|---------------------------|
| Agent forgets where it left off, re-explores every time | `session-handoff.md` + a fixed opening prompt |
| Claims "done" without actually verifying | the evidence gate on `feature_list` |
| Touches things it shouldn't, expands scope on its own | `ARCHITECTURE.md` boundaries + "don't do anything outside the list" |
| Loosens the bar so tests pass | **frozen acceptance** |
| Re-reads the whole codebase every session, burning context | an index-ified `CLAUDE.md` + file slimming |

The harness nails these down with **files**, instead of reminding via prompt every time.

---

## Three Progressive Levels (core philosophy: level up on demand, don't do it all at once)

| Level | When | What you build |
|-------|------|----------------|
| **L1 Minimal harness** | Project kickoff day, before the first line of code | `CLAUDE.md` + `init.sh` + `feature_list.json` |
| **L2 Handoff & continuity** | Before the first session that ends unfinished | `session-handoff.md` + `docs/ARCHITECTURE.md` |
| **L3 Feedback & verification** | First "hard-to-trace bug" or feature count > 5 | Structured logs + boundary guard script + verifier role separation |

```
 your repo
 │
 ├─ L1 ── mandatory at kickoff, ~20 min ───────────────────────────
 │   ├─ CLAUDE.md ............ rules, commands, boundaries (read every session)
 │   ├─ init.sh .............. one command back to "ready to develop & verify"
 │   └─ feature_list.json .... the state machine for scope and acceptance
 │                            ★ acceptance frozen after sign-off, before work
 │                            ★ no evidence, no flipping to passing
 │                            ★ prerequisites declared; undeclared ≠ no dependency
 │
 ├─ L2 ── first session that ends unfinished ──────────────────────
 │   ├─ session-handoff.md ... where we left off (overwrite, don't append)
 │   └─ docs/ARCHITECTURE.md . structure, data flow, boundaries (current only)
 │
 ├─ L3 ── first hard-to-trace bug, or feature count > 5 ───────────
 │   ├─ structured logs ...... so the agent can see why it failed
 │   ├─ check-architecture.sh  boundary rules as an executable check
 │   └─ independent verifier .. another fresh-context agent/model
 │
 └─ docs/ ── read at wrap-up, never in the daily context ──────────
     ├─ PLAN.md ............. why, scope, success metrics
     ├─ prd/<feature>.md .... what exactly, and what counts as correct
     ├─ DEVLOG.md ........... blockers & fixes (onboarding / retro fuel)
     └─ DECISIONS.md ........ hard-to-reverse choices and their reasons


 Role separation (L3): whoever generates it must not be the one who verifies it

   Planner ──→ Generator ──→ Evaluator(quality) ──→ Evaluator(acceptance)
   how to      how to        is it well-written      is it correct
   split       build it                                    ▲
                                        fed only PRD + artifact, no process;
                                        run by another fresh-context model
```

> **Don't cargo-cult.** A small tool can stay at L1 forever. Every component has a maintenance cost — add it only when it actually blocks a problem. At wrap-up, do an **ablation review**: which component actually earned its keep this time? Drop the ones that didn't from the next project. Rationale in [architecture.md](en/architecture.md).

---

## What You Need to Start

- A git repo (new or existing)
- An AI coding agent (Claude Code, Cursor, Codex, or anything that can read/write files)
- 20 minutes to build L1

Next → [setup-guide.md](en/setup-guide.md)

---

## How This Differs from "Just Write Tests" or "Just Write a Good Prompt"

- **More durable than a prompt**: prompts restart every session; the harness is files, living in the repo.
- **One layer beyond tests**: tests verify "is the code correct"; the harness also governs scope, handoff, context, and overreach — failure modes specific to AI collaboration that tests don't cover.
- **Independent verification**: the generating agent is biased toward its own output, so verification goes to a different fresh-context agent/model. See "Generator ≠ Verifier" in [architecture.md](en/architecture.md).

---

## License & Credits

Method adapted from [Learn Harness Engineering](https://walkinglabs.github.io/learn-harness-engineering/zh-TW/projects/). Repo format inspired by [Vault for Founders](https://github.com/cwlin0131/Vault-for-Founders). Released under the MIT License — see [LICENSE](LICENSE).
