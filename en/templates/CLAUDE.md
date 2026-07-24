# <project name>

## Run & Verify
- Restore environment: `./init.sh`
- Run: <command>; Test: <command>
- Before claiming any feature done, you MUST run both commands above and paste the output

## Structure & Boundaries
- <directory responsibilities, e.g. src/api must not import src/db directly — go through src/services>
- Full architecture: `docs/ARCHITECTURE.md` (from L2)

## Work Rules
1. One feature at a time (check `feature_list.json`, pick the first failing)
2. Status can only go failing → passing, and must attach verification evidence (test output / screenshot path)
3. Don't do anything outside feature_list; new items get added as failing first, not done directly
4. Do not modify an existing feature's acceptance after work starts (found a gap → add a new failing entry, back to sign-off)
5. Update `session-handoff.md` before the session ends (from L2)
6. At wrap-up, check `git status` + unpushed commits: if code changed, commit and push (remote: <repo URL>)

## Dev Rules
See `docs/CODING-RULES.md` (immutability, small files, error handling, TDD, 80% coverage, conventional commits).

## Project-specific
<only what the global rules don't cover, e.g. must reuse the existing repository pattern, no new dependencies>
