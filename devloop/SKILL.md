---
name: devloop
description: Unified development orchestrator that combines Jira/Figma integration (from codepilot) with iterative quality loops (from trycycle). Auto-detects UI vs backend tickets and routes accordingly. Use when the user provides a Jira ticket link and wants high-quality autonomous development. Trigger on "devloop", "go", "implement this ticket with quality", or when the user wants the best of both codepilot and trycycle.
context: fork
agent: general-purpose
allowed-tools: Bash, Read, Edit, Write, Glob, Grep, Agent, Skill, mcp__atlassian__getJiraIssue, mcp__atlassian__editJiraIssue, mcp__atlassian__addCommentToJiraIssue, mcp__atlassian__getTransitionsForJiraIssue, mcp__atlassian__transitionJiraIssue
---

# DevLoop — Unified Development Orchestrator

Combines Codepilot's Jira/Figma/PR pipeline with Trycycle's iterative quality loops.
Auto-detects whether a ticket is UI or backend and routes to the appropriate workflow.

**Note on approval:** unlike the shared CodePilot flow (`codepilot-common.md` Shared
Phase C, "always ask before committing"), invoking `/devloop` or `/go` is itself the
user's explicit upfront consent to a fully autonomous commit → push → PR flow — see
Phase 6. This is a deliberate, documented exception scoped to this skill only.

## Required Inputs
- Jira ticket URL
- (Optional) User availability: `available` | `unavailable`

---

## Phase 0: Repository Initialization Check

Before starting any work, check if a `CLAUDE.md` file exists at the repository root:

```bash
test -f CLAUDE.md && echo "exists" || echo "missing"
```

- **If `CLAUDE.md` is missing** → run `/init` to initialize the repository context before proceeding. This ensures the AI has proper project context for all subsequent phases.
- **If `CLAUDE.md` exists** → skip this phase and proceed to Phase 1.

---

## Phase 0.5: Qodo Toolbox Preflight

Check whether Qodo's agentic toolbox (Get Rules, Codebase Wisdom, Review, Finding Resolver) is available in this environment. It is an optional enhancement, never a hard dependency — every phase below that references it must degrade silently if it's absent.

```bash
command -v qodo >/dev/null 2>&1 && echo "qodo-cli:yes" || echo "qodo-cli:no"
ls ~/.claude/skills .claude/skills 2>/dev/null | grep -qi '^qodo-get-rules$' && echo "get-rules:yes" || echo "get-rules:no"
ls ~/.claude/skills .claude/skills 2>/dev/null | grep -qi '^qodo-pr-resolver$' && echo "pr-resolver:yes" || echo "pr-resolver:no"
```

Store the results as `qodoAvailable.cli`, `qodoAvailable.getRules`, `qodoAvailable.prResolver`. Codebase Wisdom and Review have no dedicated installed-skill marker documented — treat them as available only if `qodoAvailable.cli` is true, and skip gracefully (log once, move on) if any call to them errors, including entitlement/access errors (Review is gated behind a Research Preview entitlement).

If none of the above are available, log a single line noting Qodo integration is skipped for this run, and proceed exactly as this skill behaved before Phase 0.5 existed.

---

## Phase 1: Retrieve & Parse Ticket

Fetch ticket from Jira MCP using `mcp__atlassian__getJiraIssue`.

```
Fields to extract:
- ticket.title
- ticket.description
- ticket.acceptanceCriteria
- ticket.figmaLinks[]
- ticket.apiContracts[]
- ticket.relatedComponents[]
- ticket.relatedServices[]
- ticket.databaseChanges[]
- ticket.labels[]
- ticket.type (Story, Bug, Task, etc.)
```

If critical fields are missing and user is unavailable → send clarification question, poll for response every 30 seconds.

Transition ticket to **In Progress** using `mcp__atlassian__getTransitionsForJiraIssue` + `mcp__atlassian__transitionJiraIssue` (look for a transition named "In Progress" or "In Progress - Direct").

---

## Phase 1.5: Branch Setup

**Never implement a ticket directly on a protected branch.** Protected branches are, by
default:

```
main, master, staging, develop, development, production, prod, release
```

plus anything matching `release/*` or `hotfix/*`. If the repo's `CLAUDE.md` or
`.claude/settings.json` declares its own protected list, that list **replaces the names
above** — so a repo can make `develop` non-protected. It does not switch the guard off:
the remote default branch is always protected, whatever the list says.

### 1. Check the working tree, the current branch, and whether it is protected

Do this **before** any branch decision — a `git checkout -b` with a dirty tree drags
unrelated changes onto the ticket branch (or fails outright), which then breaks Phase 6's
"stage only this ticket's files" rule.

```bash
git status --short
CURRENT_BRANCH=$(git branch --show-current)
git fetch origin --quiet
git remote set-head origin -a >/dev/null 2>&1
DEFAULT_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')
DEFAULT_BRANCH=${DEFAULT_BRANCH:-main}
```

If `git status --short` is non-empty, **stop and report** rather than carrying the
changes onto a new branch — unless they are clearly part of this ticket, in which case
carry them over and say so explicitly.

Treat the branch as protected if it is in the effective name list (the repo's list if it
declares one, otherwise the defaults above), matches `release/*` or `hotfix/*`, **or**
equals `$DEFAULT_BRANCH` — the remote default is always protected, whatever the repo's
list says, because some repos default to `staging` rather than `main`.

### 2. Determine whether this session is autonomous

```bash
CLAUDE_ARGS=$(ps -o args= -p "${CLAUDE_PID:-$PPID}" 2>/dev/null)
```

Match **whole arguments**, never substrings: `-p` appears inside `--plugin-dir` and
`--permission-mode`, so a substring test would read `claude --permission-mode plan` — the
*most* restrictive mode there is — as autonomous and branch without asking.

```bash
AUTONOMOUS=false
# Pad with spaces so each pattern matches a whole argument, not a substring.
# (Don't loop with `for arg in $CLAUDE_ARGS` — zsh does not word-split unquoted
# expansions, so that silently matches nothing.)
case " $CLAUDE_ARGS " in
  *" --dangerously-skip-permissions "*|*" -p "*|*" --print "*) AUTONOMOUS=true ;;
esac
# --permission-mode takes a value, so match the pair, not the flag alone
case " $CLAUDE_ARGS " in
  *" --permission-mode bypassPermissions "*|*" --permission-mode acceptEdits "*) AUTONOMOUS=true ;;
esac
```

The session is also autonomous if your own session context says bypass-permissions or
auto-accept mode is active, or the run was started by a scheduler, cron, hook, or parent
agent rather than a live user.

Otherwise the session is **interactive**. `--permission-mode plan` and `--permission-mode
default` are interactive — they are more restrictive than normal, not less.

### 3. Choose the branch

| Session | Current branch | Behavior |
|---|---|---|
| **Autonomous** | anything | **Create a new branch. Do not ask.** Announce the name and continue. |
| Interactive | protected | **Create a new branch.** Staying is not an option. |
| Interactive | non-protected feature branch | Ask: use current branch, or create a new one. |

**Autonomous is the important case:** when `--dangerously-skip-permissions` or any
auto/headless mode is active there is nobody to answer a prompt, so *always* cut a fresh
branch — even from a non-protected feature branch — and never fall through to "use
current branch". Print one line so the user can see it later:

> `Auto mode — working on new branch \`feature/PROJ-1234-add-widget\` (from \`origin/main\`).`

**Interactive on a protected branch:** do **not** offer "use current branch" at all.
There is no override — announce the new branch and continue:

> "You're on `<current-branch>`, which is protected. I'll create
> `<prefix>/<TICKET-KEY>-<short-description>` from the latest `<default-branch>` instead."

If the user insists on committing directly to a protected branch, that is a decision to
make outside this skill — stop and hand back rather than pushing there, because Phase 6
commits and pushes without prompting and has no safe point to ask.

**Interactive on a non-protected branch:** ask as before:

> "You're currently on branch `<current-branch>`. How would you like to proceed?"
>
> - **Use current branch** (`<current-branch>`) — continue working here
> - **Create a new branch** — I'll create `<prefix>/<TICKET-KEY>-<short-description>` from the latest default branch

### 4. Create the branch

**Always** create the branch from the up-to-date default branch (never from the current
branch), using the `$DEFAULT_BRANCH` resolved in step 1:

```bash
git checkout -q -b <prefix>/<TICKET-KEY>-<kebab-short-title> --no-track "origin/$DEFAULT_BRANCH"
```

**Branch naming.** Use `<prefix>/<TICKET-KEY>-<kebab-short-title>`: one lowercase prefix
segment, then the ticket key, then a mandatory kebab-case summary. Only the ticket key is
uppercase; the prefix and the summary are lowercase `[a-z0-9]` with single hyphens. Never
`feat/`, `fix/` or `feat-<TICKET-KEY>` — those legacy forms are deprecated.

Pick `<prefix>` from `ticket.type` (already fetched): **Bug → `bugfix`**, everything else →
`feature`. `docs`, `hotfix` and `chore` are also conventional where they fit the work. Any
lowercase single-segment prefix is valid, so honour a prefix the repo already uses.

Derive `<kebab-short-title>` from the ticket title: lowercase, hyphen-separated, at most
five meaningful words, with no double or trailing hyphens. In interactive mode present the
suggested name and let the user override it (an override must still match the shape above);
in autonomous mode just use it.

The working tree was already verified clean in step 1, so the checkout carries nothing
unrelated onto the new branch.

---

## Phase 2: Classify Ticket — UI or Backend

Analyze the ticket content to determine the type. Use these signals:

### UI Ticket Signals
- Has Figma links in description or attachments
- Labels contain: `frontend`, `ui`, `angular`, `component`, `design`, `css`, `ux`
- Description mentions: components, UI, layout, styles, design, responsive, view, page, modal, dialog, form (in UI context)
- Related components are Angular components/modules
- Ticket type/summary suggests visual work

### Backend Ticket Signals
- Has API contracts, Swagger, or OpenAPI links
- Labels contain: `backend`, `api`, `nestjs`, `service`, `database`, `migration`, `endpoint`
- Description mentions: API, endpoint, controller, service, database, migration, schema, DTO, guard, interceptor, queue, event
- Related services are NestJS modules/services
- Ticket mentions data models, queries, or integrations

### Decision Logic
1. If clear signals for one type → auto-classify and inform user
2. If mixed signals (e.g., full-stack ticket) → ask user: "This ticket has both UI and backend elements. Which should I focus on — **UI** or **Backend**?"
3. If unclear → ask user to clarify

Store result as `ticketType: 'ui' | 'backend'`.

---

## Phase 2.5: Detect Framework

Once the ticket is classified as `ui` or `backend`, determine **which concrete framework** the work targets, so Phase 3 can gather the right patterns and Phase 4 can hand trycycle the right context.

- **UI** → `Angular` | `React`
- **Backend** → `NestJS` | `Next.js` | `Python`

### Detection

Follow **`../_shared/references/framework-detection.md`** — the single source of
truth for framework fingerprints, secondary signals, and decision logic. Inspect the
repo first; ask the user only when signals are missing or conflicting.

Store as `uiFramework` (`Angular` | `React` | `default`) when `ticketType === 'ui'`,
or `beFramework` (`NestJS` | `Next.js` | `Python` | `default`) when `ticketType === 'backend'`.

### Framework → pattern-source mapping

Each framework has a dedicated per-language CodePilot skill whose patterns/best-practices
inform Phase 3 architecture and the trycycle context in Phase 4. (devloop runs its own
trycycle quality loop — these skills are used as **pattern references**, not dispatched.)

| Framework | Pattern reference | Golden-repo search |
|-----------|-------------------|--------------------|
| **Angular** (UI) | `codepilot-ui-angular`, `frontend-patterns`, `webcode`, `vibe-coder` | Angular golden repo |
| **React** (UI) | `codepilot-ui-react` | Mirror the working repo's conventions |
| **NestJS** (BE) | `codepilot-be-nestjs`, `unit-testing` | NestJS golden repo |
| **Next.js** (BE) | `codepilot-be-nextjs` | Mirror the working repo's conventions |
| **Python** (BE) | `codepilot-be-python` | Mirror the working repo's conventions |
| **default** (undetected) | Generic flow — see `codepilot-common.md` `## Default / Generic Flow` | Mirror the working repo's conventions |

For React / Next.js / Python, golden repos may not exist yet — in Phase 3, study the
working repo's own conventions and mirror them (the per-language skills describe exactly
what to look for). For `default`, warn the user, proceed with a generic language-appropriate
flow, and leave a `TODO(devloop): add <framework> support` marker in `architecture.md`.
Trycycle's review loop (Phase 4) provides quality for every path — it is framework-agnostic.

---

## Phase 3: Domain-Specific Context Gathering

### If UI ticket:

**3a. Pull Figma Designs**
For each URL in `ticket.figmaLinks[]`:
- Fetch full-page screenshots
- Capture developer frame links
- Store as `figmaContext: { frameUrls: string[]; screenshots: string[] }` — the
  keys `/webcode` and `/output-validator` read

**3a.5. Search Golden Repos & Internal Docs**
- **If `uiFramework === 'Angular'`**: search the frontend golden repo for Angular patterns matching the ticket's UI concepts
  (See: `../_shared/references/sourcegraph-search.md`)
- **If `uiFramework === 'React'`** (unsupported): skip the Angular golden-repo search; instead search the working repo itself for its established React conventions (component structure, state management, styling) and mirror them.
- Search shared libraries for shared UI utilities or components
- Search Confluence for relevant design system docs or conventions
  (See: `../_shared/references/documentation-search.md`)
- **If `qodoAvailable.getRules`**: call Get Rules for the files/framework in scope and fold the returned global/team/repo rules into the same pattern/docs log below
- **If `qodoAvailable.cli`**: query Codebase Wisdom for dependency/impact/history context on the components this ticket touches, to sharpen the architecture plan in 3b
- Log all patterns and docs found for use in architecture planning

**3b. Architecture Planning (Frontend)**
Produce component architecture:
```typescript
{
  componentPath: string;
  components: Array<{
    name: string;
    responsibility: string;
    inputs?: string[];
    outputs?: string[];
  }>;
  state: {
    signals: string[];
    services: string[];
    communication: string[];
  };
  events: string[];
  sharedModules: string[];
}
```

### If Backend ticket:

**3a. Analyze Existing Codebase & API Contracts**
- Scan NestJS project structure (apps/, libs/, module boundaries)
- Identify existing modules, services, controllers related to the ticket
- Review existing API contracts (Swagger decorators, DTOs, OpenAPI specs)
- Check for existing database entities/schemas
- Identify shared libraries and common patterns
- **If `qodoAvailable.cli`**: query Codebase Wisdom for dependency/impact/history context on the modules/services this ticket touches, to sharpen the architecture plan in 3b
- **Search golden repos** for established patterns matching the ticket's technical concepts
  (See: `../_shared/references/sourcegraph-search.md`)
  - **If `beFramework === 'NestJS'`**: search the backend golden repo for NestJS patterns (guards, interceptors, services, DTOs)
  - **If `beFramework === 'Next.js'` or `'Python'`** (unsupported): skip the NestJS golden-repo search; instead study the working repo's own conventions — Next.js route handlers / server actions, or the Python web framework's routers, dependency injection, and schema/validation patterns — and mirror them.
  - Search shared libraries for reusable shared utilities
  - Log patterns found for use in architecture planning
- **Search internal documentation** for relevant ADRs and guidelines
  (See: `../_shared/references/documentation-search.md`)
  - Search Confluence for architecture decisions in this feature area
  - Log documentation references
- **If `qodoAvailable.getRules`**: call Get Rules for the files/framework in scope and fold the returned global/team/repo rules into the pattern/docs log above

**3b. Architecture Planning (Backend)**
Produce API architecture:
```typescript
{
  modulePath: string;
  module: { name, imports, controllers, providers, exports };
  controllers: Array<{ name, basePath, endpoints[] }>;
  services: Array<{ name, responsibility, dependencies[], methods[] }>;
  dtos: Array<{ name, purpose, validationRules[] }>;
  entities: Array<{ name, tableName, fields[], relations[] }>;
  guards: string[];
  interceptors: string[];
  migrations: string[];
}
```

> The shape above is **NestJS-oriented**. For `Next.js`, map it to route handlers / server actions, request-validation, and typed responses. For `Python`, map it to routers/views, dependency injection, and Pydantic/serializer schemas. Keep the same intent — modules, boundaries, contracts, validation — in the target framework's idioms.

Write the architecture plan to `architecture.md`.

**If a major architectural decision is needed** → present 2-4 options to user before proceeding.

---

## Phase 4: Delegate to Trycycle for Iterative Quality Loop

Now hand off to `/trycycle` for the iterative planning, implementation, and review cycle.

Invoke `/trycycle` with the following context prepended to the user's original request:

```
CONTEXT FROM DEVLOOP ORCHESTRATOR:
- Jira Ticket: [TICKET-KEY] - [ticket.title]
- Ticket Type: [ui|backend]
- Framework: [Angular|React | NestJS|Next.js|Python]  (⚠️ note if unsupported: use generic patterns)
- Description: [ticket.description]
- Acceptance Criteria: [ticket.acceptanceCriteria]
- Architecture Plan: See architecture.md at [path]
[If UI]: - Figma Designs: [figmaContext summary]
[If Backend]: - API Contracts: [apiContracts summary]
[If Backend]: - Database Changes: [databaseChanges summary]

TASK: Implement the feature described above following the architecture plan.
The architecture plan is already written — use it as the implementation contract.

TESTING REQUIREMENT: For every source file this ticket adds or modifies, ensure a
colocated test/spec file exists. If there isn't one (e.g. no `.spec.ts` next to a
NestJS/Angular source file), create it and add the relevant tests to it — never leave
new or changed code without a matching spec. Follow the framework's spec conventions
(for NestJS/Angular, `*.spec.ts` next to the source per the `unit-testing` skill). This
is in addition to trycycle's behavior/integration coverage, not a replacement for it, and
still respects trycycle's rebalance rule (unit tests stay support material, not the bulk
of the plan).
```

Trycycle will handle:
- Testing strategy (Phase 3 of trycycle)
- Worktree creation (Phase 4)
- Multi-round planning refinement (Phases 6-7, up to 5 rounds)
- Test plan creation (Phase 8)
- Implementation (Phase 9)
- Post-implementation review loop (Phase 10, up to 8 rounds)
- Finish & integration options (Phase 11)

**Important:** Let trycycle run its full cycle. Do not interfere with its internal loops.

---

## Phase 5: Post-Trycycle Validation

After trycycle completes and the user has approved the implementation:

### If UI ticket:
Invoke `/output-validator` to validate against Figma designs:
```typescript
{
  ticketContext,
  figmaContext,
  liveUrl: "http://localhost:PORT/feature-route"
}
```

Validator checks:
- Visual match against Figma
- All `acceptanceCriteria` satisfied
- Accessibility basics

If rejected → report issues to user and ask how to proceed.

### If Backend ticket:
Run final validation using the **framework-appropriate** build/test commands:
```bash
# NestJS / Nx
npx nx build <project-name> && npx nx test <project-name>

# Next.js
# npm run build && npm test

# Python (pick what the repo uses)
# ruff check . && mypy . && pytest
```

Verify (adapt to `beFramework`):
- All acceptance criteria satisfied
- **NestJS**: Swagger decorators present on all endpoints; DTOs have `class-validator` decorators; no circular dependencies
- **Next.js**: route handlers validate input (e.g. zod); typed responses
- **Python**: request/response schemas validated (Pydantic/serializers); type checks pass
- Error handling follows project conventions

---

## Phase 5.5: Qodo Local Review (Optional Pre-PR Gate)

**Skip this phase entirely if `qodoAvailable.cli` is false.** When available, run Qodo's local review engine on the diff before anything is pushed:

```bash
qodo review
```

If the command fails with an entitlement/access error (Review is gated behind a Research Preview entitlement — an org admin must request access), log it once and skip to Phase 6 without blocking.

For each finding returned, triage with the same severity priority used in Phase 7.5:
- Critical / Medium → fix before proceeding to Phase 6
- Low → fix if straightforward, otherwise note for the PR description
- Minor → fix if trivial, otherwise skip

Commit any fixes made here as part of the normal implementation commit in Phase 6 — this phase runs before the first push, so there is no separate commit/push step.

---

## Phase 6: Auto Commit, Push & Open PR

**Do NOT stop or ask for approval here.** After the implementation has passed trycycle's quality loop and Phase 5 validation, automatically commit, push, and open a PR.

0. **Pre-push protected-branch check.** Re-verify the branch you are about to push — the
   worktree or a rebase may have moved you since Phase 1.5:

```bash
git branch --show-current
```

   If it is a protected branch (see Phase 1.5 for the list), **stop before pushing** and
   hand back to the user. Move the work onto a proper `<prefix>/<TICKET-KEY>-<slug>` branch and push that
   instead. There is no exception: neither `/go`, nor a generic "go ahead", nor
   `--dangerously-skip-permissions` is consent to push to a protected branch. This is the
   one place Phase 6 stops — it is a hard guard, not an approval prompt.

1. Inspect the commit convention from recent `git log --oneline -20` and follow it.
2. Stage only the files changed by this ticket (never `git add -A`):
```bash
git add <specific files>
git commit -m "feat: [TICKET-KEY] <feature description>"
git push --set-upstream origin <branch-name>
```

3. Open a PR against the appropriate base branch and **capture the URL**:
```bash
PR_URL=$(gh pr create --title "feat: [TICKET-KEY] ..." --body "..." --base staging)
```

4. **Display the PR URL in bold orange so the user can clearly see it.** Print it via bash using ANSI escape codes (orange = 38;5;208, bold = 1):
```bash
printf '\n\033[1;38;5;208m PR: %s\033[0m\n\n' "$PR_URL"
```

Also emit the URL in the assistant text output as **`PR: <url>`** in bold markdown, so it is visible both in the terminal stream and in the conversation.

5. After the PR is created, transition the Jira ticket to **Code Review** using `mcp__atlassian__getTransitionsForJiraIssue` + `mcp__atlassian__transitionJiraIssue` (look for a transition named "Code Review", "In Review", or "Review").

**Never** skip this phase. **Never** prompt the user before committing, pushing, or opening the PR — invoking `/go` was the user's upfront consent to this (see the approval note at the top of this file), and is the whole point of `/go`.

---

## Phase 6.5: Update Documentation

After the main commit and push, update project documentation in a **separate commit**:

1. **Update README** — invoke `/update-docs` to sync the README with any new features, endpoints, components, or setup changes introduced by this ticket.
2. **Update CLAUDE.md** — reflect any new conventions, key files, patterns, or architectural decisions discovered during implementation.

Commit and push documentation updates separately:
```bash
git add README.md CLAUDE.md
git commit -m "docs: [TICKET-KEY] update README and CLAUDE.md"
git push
```

This keeps feature code and documentation changes in distinct commits for cleaner git history.

---

## Phase 7: Qodo Automated Review Scan

After the PR is created, resolve Qodo's automated review findings.

**If `qodoAvailable.prResolver`**: invoke the Finding Resolver skill/tool against the opened PR instead of the manual steps below. Follow the scope of its default behavior exactly — it fixes, skips-with-reason, or reports each finding, and does not expand scope beyond what it's given. Once it completes, proceed to Phase 7.5.

**Otherwise**, fall back to polling and parsing the PR comment directly:

```bash
for i in $(seq 1 20); do
  BODY=$(gh api "repos/<owner>/<repo>/issues/<pr_number>/comments?per_page=100" --hostname <github_hostname> \
    --jq '[.[] | select(.user.login | test("qodo"; "i")) | select(.body | contains("Code Review by Qodo"))] | (.[length-1].body // "")')
  if [ -n "$BODY" ]; then break; fi
  sleep 30
done
```

Poll every 30 seconds for up to ~10 minutes. If no Qodo comment appears in that window, proceed to Phase 7.5.

`per_page=100` covers the vast majority of PRs; issue comments are paginated in ascending-ID order, so if a PR can accumulate more than 100 comments before Qodo posts, add `--paginate` and accumulate matches across pages instead. Select the full `.body` via the `jq` array indexing above rather than `tail -1` — the comment is multi-line, and truncating it to one line breaks the "Parse the comment" steps below.

### Parse the comment

The comment (from a `qodo` bot login, titled "Code Review by Qodo") groups findings under badge headers, in this order:
1. `Action required`
2. `Review recommended`
3. `Optional`

Each finding is a numbered `<details>` block, e.g.:
```html
<summary>  7.  Wrong Jira user key <code>🐞 Bug</code> <code>≡ Correctness</code></summary>
```
A finding whose title is wrapped in `<s>...</s>` and tagged `✓ Resolved` was already fixed by a prior push — skip it regardless of section.

**Only act on findings listed under the `Action required` badge that are NOT already marked `✓ Resolved`.** Ignore everything under `Review recommended` and `Optional` — do not fix, comment on, or ask the user about those.

### For each unresolved "Action required" finding:
1. Read its `Description` and `Code` blocks to locate the file/line and understand the issue.
2. Apply the fix.
3. Commit and push:
```bash
git add <changed files>
git commit -m "fix: [TICKET-KEY] address Qodo action-required review comments"
git push
```

If there are no unresolved `Action required` findings, make no changes and proceed to Phase 7.5.

---

## Phase 7.5: Manual CR Review & Fix

Poll for human review comments:
```bash
gh api repos/<owner>/<repo>/pulls/<pr_number>/reviews --hostname <github_hostname>
```

For each finding:
1. Identify severity (critical/medium/low/minor)
2. Locate relevant file(s)
3. Apply the fix
4. Note what changed

After fixes:
```bash
git add <changed files>
git commit -m "fix: [TICKET-KEY] address CR findings"
git push
```

**Severity priority:**
- Critical / Medium → must fix before merge
- Low → fix if straightforward, otherwise note in PR comment
- Minor → fix if trivial, otherwise acknowledge in PR comment

---

## Key Rules

- **Always detect the framework (Phase 2.5) before gathering context.** UI → Angular|React; Backend → NestJS|Next.js|Python. Inspect the repo first; only ask the user when signals are missing or conflicting.
- **Only Angular (UI) and NestJS/TypeScript (BE) have dedicated skills today.** For React/Next.js/Python: proceed with generic patterns, warn the user, mirror the working repo's own conventions, and leave a `TODO(devloop)` marker — never stop.
- **Do NOT stop after coding.** After trycycle + Phase 5 validation pass, automatically commit, push, and open the PR without asking.
- Always display the PR URL in **bold orange** (ANSI `\033[1;38;5;208m`) via bash `printf` so the user can immediately see it.
- Use `architecture.md` as implementation contract
- Let trycycle handle the quality loop — don't shortcut it
- **Every source file this ticket touches gets a spec.** For each file added or changed, ensure a colocated test/spec file exists; if there isn't one, create it and add the relevant tests. Use the framework's spec convention (`*.spec.ts` next to the source for NestJS/Angular). Never leave new or changed code without a matching spec — but keep unit tests as support material per trycycle's rebalance rule, not the bulk of the plan.
- Always transition Jira ticket to In Progress at the start
- Always transition Jira ticket to Code Review after PR is created
- **Never implement or push on a protected branch** (`main`, `master`, `staging`, `develop`, `production`, `release/*`, `hotfix/*`, or the repo's actual remote default). Phase 1.5 guards entry; Phase 6 step 0 re-checks before the push.
- **In autonomous mode, always cut a new branch without asking.** If `--dangerously-skip-permissions`, `--permission-mode bypassPermissions|acceptEdits`, `-p`/`--print`, or any scheduler/hook/parent-agent invocation is in play, there is nobody to answer a prompt — create `<prefix>/<TICKET-KEY>-<slug>` from the remote default branch and announce it. Match whole arguments, not substrings: `--permission-mode plan` and `--plugin-dir` both contain `-p` and are **not** autonomous.
- Always follow the project's existing **commit** naming convention; branch naming is fixed by the rule in Phase 1.5
- Stage only the files this ticket touched — never `git add -A`
- Never force-push, never skip hooks (`--no-verify`), never amend published commits
- If UI: never start the dev server (app is already running)
- If Backend: never auto-run database migrations
- Always search canonical repos and internal docs during Phase 3 context gathering
- **Qodo toolbox steps (Get Rules, Codebase Wisdom, Review, Finding Resolver) are conditional on Phase 0.5's preflight check** — never treat them as hard dependencies; skip silently wherever they're unavailable or error
