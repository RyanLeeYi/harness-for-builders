**[繁體中文](../zh/architecture.md)** | **English**

# Harness for Builders: Architecture & Design Trade-offs

> This explains "why it's designed this way." You don't need it to follow the setup guide; but if you want to adapt it, or convince your team to adopt it, the reasons are here.

## Design Principle

**An agent's reliability doesn't come from how well the prompt is written — it comes from the structured artifacts in the repo.**

This is the foundation of the whole framework. A prompt is volatile memory: it gets truncated by context, it drifts, it must be re-explained every session, and it leaves no audit trail. A file is durable memory: it lives in the repo, it's version-controlled, it's the single source of truth. Any fresh agent opening the repo — without conversation history — should be able to answer four questions:

1. **How do I run it?** → `init.sh`
2. **Where are we?** → `feature_list.json` + `session-handoff.md`
3. **What's next?** → the first failing entry in `feature_list.json`
4. **What counts as done?** → that feature's `acceptance`

Can't answer one of them? The harness has a gap — patch it with a file, not with a prompt.

---

## Why Pain-Triggered Instead of All at Once

Every harness component has a maintenance cost: it needs updating, it goes stale, it eats context. Building everything up front means carrying burdens you don't need yet — which is itself a form of cargo-culting.

Each artifact's trigger maps to **when its pain first appears**:

- The **kickoff three** (`CLAUDE.md` + `init.sh` + `feature_list.json`) solve "scope runs wild" and "fake done" — they hurt from day one, so they're mandatory at kickoff.
- **Handoff files** solve "cross-session amnesia" — it only hurts once a session ends unfinished, so build them then.
- **Feedback & verification artifacts** solve "hard-to-trace bugs" and "the same class of error recurring" — they hurt once an incident happens, not once feature count grows.

Earlier versions arranged these as numbered levels (L1/L2/L3) with an upgrade-and-downgrade protocol. Weeks of real use showed the leveling ceremony itself changed nothing — the per-artifact triggers did all the work — so the levels are gone and the triggers remain.

Rule: **don't pre-build a component before its pain appears.** A small tool living on the kickoff three forever is correct, not lazy.

---

## Why Freeze Acceptance

This is the most counterintuitive and most important design choice.

AI agents have a structural tendency: when "passing verification" conflicts with "achieving the goal," they lean toward adjusting the verification to fit the artifact — loosening the test, rewriting acceptance to be easier to meet. It's not malice; it's the natural result of optimization pressure.

Freezing acceptance cuts off that shortcut: **the goal is defined and signed off by the requester before work starts, and the implementer has no authority to change it.** Finding a gap in acceptance is normal — but you handle it by "adding an entry and getting sign-off," not "loosening it in place." This guarantees the definition of "done" is never set by "the party that wants to claim it's done."

> Advanced: if the platform supports hooks, you can make "editing existing acceptance" an automatic block (DENY), turning the freeze from a rule into a mechanism.
>
> If you build one, key the check on **the file being protected**, not on a tool type. A failure mode observed in practice: the rule only asked "is this an edit operation?", so a full-file overwrite or a shell script rewriting the same JSON slipped past both guards while the log still showed everything as fine. The other half matters just as much — a guard that catches too much pushes people onto unguarded detours, so the test should be "was this value changed?" rather than "does this text mention the field?"

---

## Why Generator ≠ Verifier

Within the same model and the same context, "is what I just wrote correct" is the question it's least able to answer honestly — every decision it just made becomes a reason it's now defending itself.

So verification always goes to **another fresh-context agent or a different model**, fed only two things: **the PRD + the artifact**, not the development process. The verifier doesn't know "why it was written this way" — it can only check, against acceptance, "was it done, and where's the evidence."

Role split:

| Role | The question it answers | Who does it |
|------|-------------------------|-------------|
| Planner | how to break it down | main thread / plan mode |
| Generator | how to build it | main agent |
| Evaluator (quality) | is it well-written | code review |
| Evaluator (acceptance) | is it correct | **another fresh-context agent/model** |

"Quality" and "acceptance" are two different things: code review asks "is it well-written," verification asks "is it correct." You need both, at different moments.

---

## Why the Status Field Has an Evidence Gate

`failing → passing` always requires evidence (test output path, screenshot, commit hash), or it can't flip.

Reason: the cheapest lie an AI can tell is "I'm done." Requiring evidence turns a "claim" into "proof." Evidence needn't be the full text — a pointer (file path, hash) is enough; the point is **traceability**: anyone who sees passing can follow the evidence and verify it.

---

## Why Features Declare `prerequisites`

Every feature in `feature_list.json` can carry a `prerequisites` field: an array of feature ids that must already be `passing` before this one can be implemented or verified. No dependency means an empty array.

Declaring this isn't process theater — it's what lets an agent (or a human) answer two questions: **what's next, and which two can run in parallel?** Without this field, order can only be guessed from id numbers — but id order isn't dependency order; F3 being filed first doesn't mean it doesn't depend on F5.

Running two features in parallel requires all three conditions at once — missing any one blocks it:

- Neither is in the other's `prerequisites`
- The files they touch don't overlap
- The resources they depend on (DB schema, external services, shared state) don't overlap

**Fail-closed**: an older entry with no `prerequisites` field must be treated as "undeclared," not as "no dependency" — its absence can't be used to greenlight ordering or parallel work. This is the same principle as "no evidence doesn't mean it passed": a missing field is missing information, not a default green light.

If the platform supports it, add tooling checks: every id referenced in `prerequisites` must exist, must not point to itself, and must not form a cycle; before a feature can flip to `passing`, everything in its `prerequisites` must already be `passing`.

---

## Why Large Work Gets an Envelope Before Its Slices

Splitting while the spec is still forming is cheap; discovering you need to split after work has started — after acceptance is frozen — is expensive: splitting then means going through the "supersede" (`superseded_by`) flow, which costs far more than cutting the work into pieces up front. That's the reason envelope + slice exists.

Threshold: a piece of work spanning three or more features, or crossing multiple facets (frontend, backend, data). Small work doesn't get an envelope — a single feature is enough.

An envelope isn't a second ID system — **a slice is a feature.** It's a shared constraint layer sitting on top of a group of features:

- `outcome`: the externally visible change once the whole envelope is done
- `constraints`: technical, interface, or compatibility constraints shared by every slice
- `non_goals`: what the whole envelope explicitly won't do

Once signed off, `constraints` and `non_goals` freeze at the same level as acceptance — the implementer can't change them.

Process-wise, **sign off the envelope first, then the slices** — and only review "the next slice that's ready to execute"; you don't have to talk through every slice up front. A slice that hasn't come up yet only needs three fields settled: a stable `id`, `outcome`, and `prerequisites`. Missing any one of those three is a blocker you can't wave off with "fill it in later" — without `prerequisites` there's no way to tell whether it can run in parallel with another slice.

On the schema: the `features` array stays flat — don't nest it, or every tool that reads `feature_list.json` has to change too. An envelope is just an extra top-level array; each feature points back to the envelope it belongs to via an `envelope` field (leave it `null` if it doesn't belong to one):

```json
{
  "envelopes": [
    {
      "id": "E1",
      "outcome": "<the externally visible change once the whole envelope is done>",
      "constraints": ["<technical/interface/compatibility constraints shared by every slice>"],
      "non_goals": ["<what the whole envelope explicitly won't do>"],
      "signed_off": "<sign-off date; constraints and non_goals freeze once this is set>"
    }
  ],
  "features": [
    {
      "id": "F12",
      "envelope": "E1",
      "prerequisites": ["F11"]
    }
  ]
}
```

---

## The Ablation Review (Meta Loop)

At wrap-up, look back and ask: **which component in this harness actually blocked a problem this time? Which was pure overhead?**

Drop the ones that didn't earn their keep from the next project. This step keeps the harness itself from becoming cargo-cult — the framework must also submit to being tested by its own standard. If structured trace is enabled, this judgment can be backed by real data (how many overreaches it caught, which acceptances failed) rather than impressions.

---

## Agent Startup Sequence

The fixed opening for every new session:

> "Read `CLAUDE.md`, `session-handoff.md`, `feature_list.json`, then tell me which feature you'll do and how you'll verify it."

This sentence is a **probe**: if the agent can answer, the harness is intact; if it can't, some file is missing or stale — patch the harness before working, don't push ahead with a gap.

---

## How This Differs from Other Approaches

- **vs. just a good prompt / rules file**: those are still volatile, reloaded every session; the harness externalizes state (where we are, whether it's done) into files.
- **vs. just good tests**: tests verify "is the code correct," but miss the failure modes specific to AI collaboration — scope creep, cross-session amnesia, fake done, overreach. The harness covers exactly that layer.
- **vs. a larger agent framework / orchestration tool**: the harness isn't a system to install — it's a few plain-text files plus a few rules. It's independent of which agent or model you use — switch tools and the harness doesn't change.
