# Dev Rules

> Link into `CLAUDE.md`, or paste the parts you need directly. These are the general "how" rules, separate from the PRD's "what."
> This is a **default**, not scripture — when it conflicts with your team's existing lint / style conventions, the team wins.

## Immutability
Always create new objects; never mutate existing ones in place — return a modified copy.
Immutable data avoids hidden side effects, makes debugging easier, and enables safe concurrency.

## File Organization
Many small files > few large files:
- High cohesion, low coupling
- 200–400 lines typical, 800 max
- Organize by feature/domain, not by type
- Keep functions small (< 50 lines), avoid deep nesting (> 4 levels)

## Error Handling
- Handle errors explicitly at every level; never silently swallow
- User-facing error messages are friendly; log detailed context server-side
- Error messages don't leak sensitive data

## Input Validation (at system boundaries)
- Validate all external input (user input, API responses, file content) before processing
- Use schema validation where available; fail fast with clear messages
- Never trust external data

## Testing (minimum 80% coverage)
- Unit: individual functions, utilities, components
- Integration: API endpoints, database operations
- E2E: critical user flows
- **TDD**: test first (RED) → run, should fail → minimal implementation (GREEN) → run, should pass → refactor (IMPROVE)
- Fix the implementation, don't change tests to make them pass (unless the test itself is wrong)

## Security (pre-commit checklist)
- [ ] No hardcoded secrets — always use env vars or a secret manager
- [ ] All user input validated
- [ ] Parameterized queries (prevent SQL injection)
- [ ] HTML sanitized (prevent XSS)
- [ ] Authentication/authorization verified
- [ ] Error messages don't leak sensitive data

## Git
Commit message format:
```
<type>: <description>

<optional body>
```
type: `feat` / `fix` / `refactor` / `docs` / `test` / `chore` / `perf` / `ci`
