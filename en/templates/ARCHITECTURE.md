---
updated: YYYY-MM-DD
---

# <project name> — ARCHITECTURE

> Current state only. When the structure changes, rewrite it — don't keep "how it used to be" (history goes in DECISIONS.md).
> This lets a new session's agent skip re-exploring the whole codebase.

## System Overview
<one paragraph + a simple diagram (ASCII is fine): main components and data flow>

## Directory Responsibilities
| Directory | Responsibility | Must not do |
|-----------|----------------|-------------|
| `src/api` | External endpoints | Must not import `src/db` directly — go through `src/services` |
| `src/services` | Business logic | |
| `src/db` | Data access | No business logic |

## Data Flow
<e.g. request → api → service → repository → db, and the reverse on the way back>

## Boundary Rules (verifiable by the check-architecture script)
<e.g. no SQL strings in the api layer>
<e.g. the db layer must not import the service layer>

## External Dependencies
<third-party services, APIs, and their expected behavior on failure>
