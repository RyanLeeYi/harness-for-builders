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

## Why "Progressive Levels" Instead of All at Once

Every harness component has a maintenance cost: it needs updating, it goes stale, it eats context. Building everything up front means carrying burdens you don't need yet — which is itself a form of cargo-culting.

The level boundaries aren't arbitrary — they map to **when a pain first appears**:

- **L1** solves "scope runs wild" and "fake done" — it hurts from day one, so it's mandatory at kickoff.
- **L2** solves "cross-session amnesia" — it only hurts once a session ends unfinished, so build it then.
- **L3** solves "hard-to-trace bugs" and "chaos as features grow" — it hurts only at scale.

Rule: **don't pre-build a component before its pain appears.** A small tool staying at L1 forever is correct, not lazy.

---

## Why Freeze Acceptance

This is the most counterintuitive and most important design choice.

AI agents have a structural tendency: when "passing verification" conflicts with "achieving the goal," they lean toward adjusting the verification to fit the artifact — loosening the test, rewriting acceptance to be easier to meet. It's not malice; it's the natural result of optimization pressure.

Freezing acceptance cuts off that shortcut: **the goal is defined and signed off by the requester before work starts, and the implementer has no authority to change it.** Finding a gap in acceptance is normal — but you handle it by "adding an entry and getting sign-off," not "loosening it in place." This guarantees the definition of "done" is never set by "the party that wants to claim it's done."

> Advanced: if the platform supports hooks, you can make "editing existing acceptance" an automatic block (DENY), turning the freeze from a rule into a mechanism.

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

## The Ablation Review (Meta Loop)

At wrap-up, look back and ask: **which component in this harness actually blocked a problem this time? Which was pure overhead?**

Drop the ones that didn't earn their keep from the next project. This step keeps the harness itself from becoming cargo-cult — the framework must also submit to being tested by its own standard. If L3's trace is enabled, this judgment can be backed by real data (how many overreaches it caught, which acceptances failed) rather than impressions.

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
