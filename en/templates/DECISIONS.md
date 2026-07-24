---
updated: YYYY-MM-DD
---

# <project name> — DECISIONS

> **Usage**
> 1. What counts as a "decision": a **hard-to-reverse choice** (framework, database, architecture pattern, API boundary). Renaming a variable is not a decision
> 2. One decision = one numbered block, reverse order; don't delete overturned ones — mark ~~overturned~~ and link to the one that replaced it. The evolution itself is team knowledge
> 3. "Rejected options" is required: six months later you must be able to answer "why not the other one"
> 4. Keep each under 10 lines; if you can't, you haven't thought it through — go back and think

---

## D2 (YYYY/MM/DD): <the decision in one line, e.g. use sqlite-vec not Qdrant for the vector store>

- **Context**: <what you faced, what constraints (time/cost/scale)>
- **Options**: A <rejected>, B <chosen>
- **Chose B because**: <the key reason, ideally with a number or concrete constraint>
- **Cost**: <what this choice gives up, when to re-evaluate>

## D1 (YYYY/MM/DD): ...
