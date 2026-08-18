**English** | **[繁體中文](zh/README.md)**

# Harness for Builders

> An AI coding agent's reliability doesn't come from how well the prompt is
> written — it comes from the structured artifacts in the repo. This framework
> tells you which files to build, when to build them, and lets your agent do
> the setup itself.

**Harness for Builders** is a tool-neutral framework for building a repo where
an AI agent can work reliably: Claude Code, Cursor, Codex, or anything that can
read and write files. It installs files into your repo, not a runtime or a
service. Three files are mandatory at kickoff; every other artifact has its own
trigger — you add it when its pain appears, and drop it when it stops earning
its keep.

> By [Ryan Lee](https://github.com/RyanLeeYi) · **v1.4** · Last updated
> 2026-08-18 · [Changelog](CHANGELOG.md)

## Contents

- [Why](#why)
- [How it works](#how-it-works)
- [Get started](#get-started)
- [Operate](#operate)
- [Documentation](#documentation)
- [Limits](#limits)
- [License & credits](#license--credits)

## Why

As you delegate more work to an AI agent — features, bug fixes, refactors — it
needs a place to know the current state: how the project runs, what the rules
are, what's in scope, where the last session left off. That place is your
**harness**. Without one, you hit a set of failure modes that tests don't
cover, because they're failures of *collaboration*, not of code:

| Symptom | What blocks it |
|---------|----------------|
| Agent forgets where it left off, re-explores every session | `session-handoff.md` + a fixed opening prompt |
| Claims "done" without actually verifying | the evidence gate on `feature_list.json` |
| Touches things it shouldn't, expands scope on its own | `ARCHITECTURE.md` boundaries + "nothing outside the list" |
| Loosens the bar so tests pass | **frozen acceptance** |
| Burns context re-reading the whole codebase every session | an index-ified `CLAUDE.md` + file slimming |

Prompts get forgotten, drift, and must be re-explained every session. Files
don't — they sit in the repo as the single source of truth. The harness nails
each failure mode down with a file, instead of reminding via prompt every time.

## How it works

A fresh agent opening your repo, with no conversation history, must be able to
answer four questions:

```
   How do I run it?      ----->  init.sh
   Where are we?         ----->  feature_list.json + session-handoff.md
   What's next?          ----->  the first failing entry in feature_list.json
   What counts as done?  ----->  that feature's acceptance (frozen)

   Can't answer one = the harness has a gap -> patch it with a file, not a prompt
```

Three files answer them from day one. Everything else is **pain-triggered**:
each artifact has an explicit "add when" — and an explicit "drop when", because
a harness with only an upgrade path grows fat in one direction. Adding feels
safe, deleting feels risky, and stale layers silt up. There are no stages to
climb and no ceremony; the trigger is the whole rule.

| Artifact | Add when | Drop when |
|----------|----------|-----------|
| `CLAUDE.md` + `init.sh` + `feature_list.json` | Kickoff day, before the first line of code (~20 min) | Never — this is the harness |
| `session-handoff.md` | Before the first session that ends unfinished | Several sessions in a row go by without it being read |
| `docs/ARCHITECTURE.md` | A fresh agent can't see the boundaries and data flow from code alone | The code now shows them |
| Structured logs, boundary guard script, independent verifier | An incident: a recurring error class, a bug the logs can't locate, an actual boundary violation. Feature count is **never** a trigger | Enough samples accumulate without catching a single real overreach |

```
 your repo
 |
 |- mandatory at kickoff ------------------------------------------
 |   |- CLAUDE.md ............ rules, commands, boundaries (read every session)
 |   |- init.sh .............. one command back to "ready to develop & verify"
 |   |- feature_list.json .... the state machine for scope and acceptance
 |                             * acceptance frozen after sign-off, before work
 |                             * no evidence, no flipping to passing
 |                             * prerequisites declared; undeclared != none
 |
 |- pain-triggered, each on its own clock -------------------------
 |   |- session-handoff.md ... where we left off (overwrite, don't append)
 |   |- docs/ARCHITECTURE.md . structure, data flow, boundaries (current only)
 |   |- structured logs ...... so the agent can see why it failed
 |   |- check-architecture.sh  boundary rules as an executable check
 |   |- independent verifier .. another fresh-context agent, fed only the
 |                              frozen acceptance + the artifact, no process
 |
 |- docs/ -- read at wrap-up, never in the daily context ----------
     |- PLAN.md ............. why, scope, success metrics
     |- DEVLOG.md ........... blockers & fixes (onboarding / retro fuel)
     |- DECISIONS.md ........ hard-to-reverse choices and their reasons
     |- prd/ (optional) ..... narrative spec for team / non-engineer readers
     |- archive/ ............ acceptance of passing features, moved verbatim
```

Key terms, in one breath: the **harness** is the set of files above — a working
environment, not framework code. **feature_list.json** is the state machine for
scope: one entry per feature, status only `failing`/`passing`, flipping to
passing always requires evidence. **acceptance** is "how to verify it's done" —
written before work starts, signed off, then **frozen**: the single most
important word in the harness.

One rule about where the spec lives: **acceptance is the authority, and it must
be self-sufficient** — decidable item by item without opening another document.
A PRD is welcome as narrative for team members and non-engineer readers, but if
your freeze protection only covers `feature_list.json`, declaring "the PRD
wins" hands authority to the one file nothing protects. The full failure story
is in the [setup guide](en/setup-guide.md).

## Get started

You need: a git repo (new or existing), an AI coding agent, and 20 minutes for
the three kickoff files.

**You can hand this entire repository to your agent and it will guide you
through the build.** Open your agent in your project and paste:

```text
Read https://github.com/RyanLeeYi/harness-for-builders — start with README.md,
then follow en/setup-guide.md step by step to build a minimal harness in this
repo.
Scaffold the shells (init.sh, feature_list.json) directly, but do NOT guess the
core content: interview me for each feature's acceptance, the architectural
boundaries, and the project rules, layer by layer. Show me the full plan of
files before writing anything.
```

The one thing the agent cannot do for you is decide **what counts as done**.
If the acceptance is wrong, the whole harness verifies the wrong thing — that's
why the setup guide is an interview, not a form.

## Operate

| Task | Where to go |
|------|-------------|
| Build the minimal harness, then add artifacts as pain appears | [Setup guide](en/setup-guide.md) |
| Understand the design: why pain-triggered, why freeze acceptance | [Architecture](en/architecture.md) |
| Keep the every-session files lean as the project grows | [Optimization guide](en/optimization-guide.md) |
| Scaffold from ready-made templates | [templates/](en/templates/) |
| Adopt in a team repo with mixed AI tools and no CI | [project-harness-kit](https://github.com/RyanLeeYi/project-harness-kit) — the executable-gate variant |
| See a personal deployment of the full method | [ai-dev-harness](https://github.com/RyanLeeYi/ai-dev-harness) — the live map |

## Documentation

| Topic | Document |
|-------|----------|
| Step-by-step setup, with the discussion flow | [en/setup-guide.md](en/setup-guide.md) · [繁體中文](zh/setup-guide.md) |
| Design decisions and trade-offs | [en/architecture.md](en/architecture.md) · [繁體中文](zh/architecture.md) |
| Keeping operational files lean | [en/optimization-guide.md](en/optimization-guide.md) · [繁體中文](zh/optimization-guide.md) |
| Templates to copy | [en/templates/](en/templates/) · [繁體中文](zh/templates/) |
| Version history | [CHANGELOG.md](CHANGELOG.md) |

## Limits

Stated up front, because knowing them is how you use the harness correctly:

- **Frozen does not mean correct.** A frozen acceptance can describe reality
  wrong. When verification fails against a spec bug, go back through sign-off
  to fix the spec — don't bend the implementation to a wrong target.
- **The harness governs process, not correctness.** It's one layer beyond
  tests: scope, handoff, context, overreach. Whether the feature itself is
  right still comes down to the acceptance you wrote.
- **Files can't stop deliberate deception.** The evidence gate blocks casual
  "it's done"; an agent with write access can fabricate. Real enforcement
  needs a check outside the agent's reach — a script, a hook, a PR gate
  (see the boundary guard and project-harness-kit).
- **Don't cargo-cult.** A small tool can live on the three kickoff files
  forever — that's correct, not lazy. At wrap-up, ask
  which component actually earned its keep this time, and drop the ones that
  didn't from the next project.

## License & credits

Method adapted from
[Learn Harness Engineering](https://walkinglabs.github.io/learn-harness-engineering/zh-TW/projects/).
The "hand it to any AI and it sets itself up" format is borrowed from
[Vault for Founders](https://github.com/cwlin0131/Vault-for-Founders) by CW
Lin. Narrative structure of this README follows
[pilotfish](https://github.com/Nanako0129/pilotfish).

Released under the MIT License — see [LICENSE](LICENSE).
