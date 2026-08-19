**[繁體中文](../zh/optimization-guide.md)** | **English**

# Harness Optimization Guide: Get the Agent Up to Speed with Less Context Each Session

> Harnesses bloat over time. This teaches you to keep the "operational files read every session" lean, so context doesn't fill up with historical noise.

## Core Concept

There's exactly one test for whether a file should be slimmed:

> **Does this file need to enter the agent's context every session?**

- **Yes (operational files)**: `CLAUDE.md`, `ARCHITECTURE.md`, `feature_list.json`, `session-handoff.md` → keep lean, prune regularly.
- **No (archive files)**: `DEVLOG.md`, `DECISIONS.md` → read only at wrap-up, **don't shrink**. The process record is fuel for onboarding and incident retros; cutting it destroys evidence.

Conflating the two is the main cause of harness bloat.

---

## 1. Keep `CLAUDE.md` Index-ified

`CLAUDE.md` holds only: rules, commands, boundaries. Details (deploy steps, API notes, gotchas) go in `docs/` with a link pointing there.

Before adding anything, ask: **does the agent need to read this every session?** If not, it goes in `docs/`.

---

## 2. Archive `feature_list.json` at Wrap-Up

At every wrap-up, check for newly passing entries and move each one **whole** into `feature_archive.json` (same format). Don't batch them up. The main file keeps only failing.

Don't move just the acceptance text and leave the other fields behind as a skeleton. Fields like `touches` look like data your coupling or impact analysis needs, but that analysis only ever looks at work **not yet done** — completed entries contribute nothing to it. Before keeping a copy of anything, go read the source and confirm who actually consumes it: "it should be useful" and "it has a consumer" are different claims.

Always write `evidence` as a pointer (test output file path, commit hash), never the full text — the full text lives in a file, the list holds only the pointer.

---

## 3. `session-handoff.md`: Overwrite, Don't Append

It should only ever hold "the current state." If it's growing, you're using it wrong — last session's handoff expires once this session consumes it; overwrite it.

---

## 4. `ARCHITECTURE.md`: Current State Only

When the structure changes, rewrite it — don't keep "how it used to be." History and evolution go in `DECISIONS.md`; the architecture file only answers "how it looks now."

---

## 5. Archive Files: Don't Shrink, but You May Split

`DEVLOG.md` and `DECISIONS.md` aren't slimmed — their value is in being complete. But when a project spans quarters and gets genuinely long, split by time:

```
DEVLOG.md                       ← current quarter
docs/archive/DEVLOG-2026Q3.md   ← archived, main file keeps a link
```

Splitting is relocation, not reduction.

---

## Execution Order

When context pressure hits, clear in this order:

1. Overwrite `session-handoff.md` to the current state (bloats most often)
2. Archive passing entries in `feature_list.json`
3. Move details out of `CLAUDE.md` into `docs/`
4. Cut stale descriptions from `ARCHITECTURE.md`

## When to Do This

- Prune `session-handoff.md` at every wrap-up.
- At every wrap-up, check `feature_list.json` for newly passing entries and archive them on the spot. Don't batch.
- Review the whole set once at wrap-up.
