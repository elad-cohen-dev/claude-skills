# CodePilot — Shared Orchestration Flow

Framework-agnostic phases shared by every `codepilot-be-*` and `codepilot-ui-*`
skill. Each language skill owns the framework-specific phases (codebase
analysis, architecture shape, implementation idioms, testing, validation) and
defers to **this file** for the phases below. Keep the shared orchestration in
one place so all language skills stay consistent.

## Required Inputs
- Jira ticket URL
- (Optional) User availability: `available` | `unavailable`

---

## Shared Phase A: Retrieve & Parse Ticket

Fetch ticket from Jira MCP using `mcp__atlassian__getJiraIssue`. Extract at least:
- `ticket.title`, `ticket.description`, `ticket.acceptanceCriteria`
- `ticket.relatedComponents[]`, `ticket.relatedServices[]`, `ticket.labels[]`, `ticket.type`
- **UI tickets**: `ticket.figmaLinks[]`
- **Backend tickets**: `ticket.apiContracts[]` (Swagger/OpenAPI), `ticket.databaseChanges[]`

If critical fields are missing and the user is unavailable → send a clarification
question and poll for a response every 30 seconds.

Transition the ticket to **In Progress** via `mcp__atlassian__getTransitionsForJiraIssue`
+ `mcp__atlassian__transitionJiraIssue` (look for "In Progress" or "In Progress - Direct").

---

## Shared Phase B: Setup Git Branch

**Branch naming.** Use `<prefix>/<TICKET-KEY>-<kebab-short-title>`: one lowercase prefix
segment, then the ticket key, then a mandatory kebab-case summary. Only the ticket key is
uppercase; the prefix and the summary are lowercase `[a-z0-9]` with single hyphens. Never
`feat/`, `fix/` or `feat-<TICKET-KEY>` — those legacy forms are deprecated.

Pick `<prefix>` from `ticket.type` (already fetched): **Bug → `bugfix`**, everything else →
`feature`. `docs`, `hotfix` and `chore` are also conventional where they fit the work. Any
lowercase single-segment prefix is valid, so honour a prefix the repo already uses.

Branch off the up-to-date default branch:
```bash
git fetch origin
git remote set-head origin -a
DEFAULT_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@')
git checkout -b <prefix>/<TICKET-KEY>-<kebab-short-title> --no-track "origin/$DEFAULT_BRANCH"
```
Derive `<kebab-short-title>` from the ticket summary: lowercase, hyphen-separated, at
most five meaningful words. Present the name and let the user override it — an override
must still match the shape above.

---

## Shared Phase C: Commit & Push (With Approval)

**Always ask the user before committing:**
> "Are you happy with the final implementation? Should I commit and push the code?"

**Exception:** `devloop`'s `/go` flow is a documented, explicit opt-in exception to this
rule — invoking `/go` is itself the user's upfront consent to skip this prompt (see
`devloop/SKILL.md` Phase 6). This exception is scoped to `/go` only; it never applies
when a `codepilot-be-*`/`codepilot-ui-*` skill is invoked directly.

If the user is unavailable → send via the notification channel, poll every 30s.

Only after explicit approval, follow the commit convention from recent
`git log --oneline -20` (typically `feat: [TICKET-KEY] description`). Stage only the
files this ticket touched — **never** `git add -A`:
```bash
git add <specific files>
git commit -m "feat: [TICKET-KEY] <feature description>"
git push -u origin HEAD
```
Open a PR against the project's integration branch (commonly `staging`):
```bash
gh pr create --title "feat: [TICKET-KEY] ..." --body "..." --base staging
```
After the PR is created, transition the Jira ticket to **Code Review**
(`mcp__atlassian__getTransitionsForJiraIssue` + `mcp__atlassian__transitionJiraIssue`;
look for "Code Review", "In Review", or "Review").

---

## Shared Phase D: CR Review & Fix

After the PR is created, poll for review comments:
```bash
gh api repos/<owner>/<repo>/pulls/<pr_number>/reviews --hostname <github_hostname>
```
For each finding: identify severity (critical/medium/low/minor), locate the file(s),
apply the fix, note what changed. Then:
```bash
git add <changed files>
git commit -m "fix: [TICKET-KEY] address CR findings"
git push
```
Re-fetch reviews to confirm no new blockers remain.

**Severity priority:**
- Critical / Medium → must fix before merge
- Low → fix if straightforward, otherwise note in a PR comment
- Minor → fix if trivial, otherwise acknowledge in a PR comment

---

## Shared Key Rules

- Always get user approval before committing; never push without sign-off (except `devloop`'s `/go`, see Shared Phase C).
- Use `architecture.md` as the implementation contract.
- Re-validate (build + tests) after every fix cycle.
- Never skip components/services defined in the architecture plan.
- Always transition the Jira ticket to In Progress at the start, Code Review after the PR.
- Always follow the project's existing **commit** naming convention; branch naming is fixed by Shared Phase B.
- Stage only the files this ticket touched — never `git add -A`.
- Never force-push, never `--no-verify`, never amend published commits.
- Always search golden repos and internal docs before designing the architecture
  (see `sourcegraph-search.md`, `documentation-search.md`).
- Log all patterns and documentation referenced in the architecture plan.

---

## Default / Generic Flow

Used by the routers (`codepilot-be`, `codepilot-ui`) when the detected framework is
**not** one of the supported five (Angular, React, NestJS, Next.js, Python) — or when
detection is inconclusive and the user can't disambiguate.

1. **Warn the user clearly**, e.g.:
   > ⚠️ No dedicated CodePilot skill for this framework/stack. Proceeding with a generic, language-appropriate flow and skipping framework-specific golden-repo search. Review still applies.
2. Run **Shared Phase A** (ticket) and **Shared Phase B** (branch).
3. **Study the working repo's own conventions** instead of golden repos: directory
   layout, module/component boundaries, state/data patterns, validation, error handling,
   test framework and naming. Mirror them faithfully.
4. **Architecture planning**: write an `architecture.md` capturing the same intent as the
   framework-specific skills — units, boundaries, contracts, validation — expressed in the
   target stack's idioms.
5. **Implement** following the repo's established patterns. Prefer the smallest change that
   satisfies the acceptance criteria.
6. **Validate** with the repo's own build/test commands (detect from `package.json` scripts,
   `Makefile`, `pyproject.toml`, CI config, etc.). Get the build green and tests passing.
7. Run **Shared Phase C** (commit/PR) and **Shared Phase D** (CR review).
8. Leave a `TODO(codepilot): add <framework> skill` marker in `architecture.md` so a
   dedicated skill can be added later.
