---
name: code-review-default
description: Review a GitHub PR with inline comments. Searches canonical repos and internal docs before reviewing, applies logging review criteria, and submits findings as a review with inline comments. Trigger on "review this PR", "code review PR #123", or when given a PR URL for review.
context: fork
agent: general-purpose
allowed-tools: Bash, Read, Grep, Glob, mcp__github__search_code, mcp__github__get_pull_request, mcp__github__get_pull_request_files, mcp__github__get_pull_request_reviews, mcp__github__get_pull_request_comments, mcp__github__create_pull_request_review, mcp__atlassian__searchConfluenceUsingCql
---

# PR Code Review — Inline Comments on GitHub

Full PR review workflow: search for context, review against criteria, submit inline comments.

## Required Inputs
- GitHub PR URL (e.g., `https://github.com/<owner>/<repo>/pull/<number>`)
  OR owner/repo and PR number

## Pre-Review Checklist

### 1. Decide if Search Tools Are Needed

Search tools are required when the PR:
- Introduces new technologies/libraries to the codebase
- Adds integrations with external APIs or services
- Implements patterns that might exist in golden repos

**Skip search tools for:**
- Trivial changes: typos, formatting, comments, README updates
- Simple changes: adding logs, renaming variables, version bumps
- Bug fixes with clear solutions

### 2. Search for Standards (if needed)

#### Golden Repos Code Search
Search golden repos for similar implementations.
**See:** [Golden Repos Search Guide](../_shared/references/sourcegraph-search.md)

#### Documentation Search
Query Confluence for relevant standards.
**See:** [Documentation Search Guide](../_shared/references/documentation-search.md)

### 3. Check for Additional Review Resources

- **Additional review skills** may exist in `.claude/skills/`. Check and use them when available.
- **Additional guidelines** may be defined in `CLAUDE.md` or `.claude/CLAUDE.md`.

Apply these in addition to the organization-wide standards in this skill.

## Review Workflow

### Phase 1: Fetch PR Context

Extract owner, repo, and PR number from the URL.

```bash
# Parse PR URL: https://github.com/<owner>/<repo>/pull/<number>
```

Fetch PR details:
- Use `mcp__github__get_pull_request` or `gh pr view <number> --json title,body,baseRefName,headRefName`
- Use `mcp__github__get_pull_request_files` or `gh pr diff <number>`

Store as `prContext`.

### Phase 1.5: Check for Qodo Merge's Automated Review

This org runs [Qodo Merge](https://github.com/apps/qodo-merge) as a GitHub App — it auto-reviews most PRs before a human (or Claude) looks at them. Check whether it already has:

```bash
gh api "/repos/{owner}/{repo}/pulls/{pull_number}/reviews" | jq '[.[] | select(.user.login | test("qodo"; "i"))]'
gh api "/repos/{owner}/{repo}/pulls/{pull_number}/comments" | jq '[.[] | select(.user.login | test("qodo"; "i"))]'
```

If Qodo has already commented, read its findings and store as `qodoContext`. Use it to avoid duplicate noise, not to skip reviewing:

- **Don't re-flag** what Qodo already caught well (it's strong on: typos/style, obvious bugs, common anti-patterns, PR-level summaries).
- **Do focus your review** on what Qodo is weaker at: correctness against the actual Jira ticket/acceptance criteria, cross-file and cross-service consistency, alignment with this org's golden-repo conventions, and the logging/cost checks below.
- If you disagree with a Qodo finding, or Qodo missed something material, say so explicitly in your review — don't silently overrule or silently duplicate.
- If Qodo hasn't reviewed yet (or isn't installed on this repo), proceed with the full checklist below as normal.

**Shared vocabulary** — to keep terminology consistent across both tools on the same PR, map this skill's severities to Qodo's priority tiers when writing findings:

| This skill | Qodo Merge tier |
|---|---|
| CRITICAL / HIGH | Action Required |
| MEDIUM | Review Recommended |
| LOW | Informational |

Also tag each finding with the Qodo-style quality-impact dimension it affects (`Correctness`, `Security`, `Reliability`, `Performance`, `Observability`) alongside its severity — see Phase 4c.

### Phase 2: Pre-Review Search

For each major pattern in the changed files:
1. Identify the pattern type (e.g., "NestJS controller", "React hook", "FastAPI router", "guard")
2. Search the appropriate canonical repo for the established implementation
3. Search Confluence for relevant ADRs or guidelines
4. Store findings as `searchContext`

### Phase 3: Review Changed Files

For each changed file, evaluate against the full checklist below.

#### Security (CRITICAL)
- Hardcoded credentials, API keys, tokens
- SQL injection vulnerabilities
- XSS vulnerabilities
- Path traversal risks
- CSRF gaps
- Authentication bypasses
- Sensitive data in logs

#### Code Quality (HIGH)
- Functions exceeding 50 lines
- Missing error handling
- Debug/console statements left in code
- Dead code / unused exports
- Missing input validation on endpoints

#### Framework Patterns (HIGH)

**Step 1 — Detect the framework** from changed file names and import patterns:
- **React**: `.tsx`/`.jsx`, imports from `react`, JSX syntax, hooks (`useState(`, `useEffect(`, `useQuery(`)
- **NestJS**: `.controller.ts`, `.module.ts`, `.service.ts`, imports from `@nestjs/`, `@Controller`, `@Injectable`, `@Module`
- **Python**: `.py` files, imports from `fastapi`, `pydantic`, `APIRouter`, `BaseModel`, `Depends`
- **Node.js / general**: `.ts`/`.js` files without React or NestJS markers
- **Mixed**: if multiple frameworks appear (e.g. a full-stack PR touching both a React app and its Python/NestJS backend), apply each relevant checklist to its own files

**Step 2 — Apply the framework-specific checklist:**
- React PRs → **See:** [React Review Checklist](../_shared/references/react-review-checklist.md)
- NestJS PRs → **See:** [NestJS Review Checklist](../_shared/references/nestjs-review-checklist.md)
- Python PRs → **See:** [Python Review Checklist](../_shared/references/python-review-checklist.md)

For each checklist item, report PASS/FAIL/N/A. Every FAIL becomes an inline comment with a corrected snippet.

**Step 3 — Cross-check against golden repo patterns** found in Phase 2:
- Does the implementation follow established conventions?
- Are shared utilities used where available?
- Does the module structure match golden repo organization?

#### Logging Review (HIGH)
When reviewing code that adds or modifies log statements, evaluate each log entry:
- **Log level appropriateness**: Ensure `ERROR` is not used for expected/recoverable conditions, `WARN` for truly exceptional cases only, and `INFO`/`DEBUG` for routine flow. Avoid elevating levels unnecessarily.
- **Log volume risk**: Flag any logs inside loops, frequently-called methods, hot code paths, or event listeners that could produce high-frequency output under normal production load.
- **Cardinality risk**: Warn about logs that include unbounded dynamic values (e.g., user IDs, request IDs, raw payloads) that could cause high cardinality in Datadog and inflate indexing costs.
- **Redundancy**: Identify duplicate or near-duplicate log lines that convey the same event (e.g., logging both entry and exit of a trivial method with no meaningful data).
- **Sensitive data**: Flag any log that may include PII, credentials, tokens, or other sensitive data that should never appear in log sinks.
- **Cost awareness**: Explicitly call out patterns that could lead to **log flooding** or **unexpected Datadog ingestion cost spikes** — e.g., logging full request/response bodies, logging on every retry attempt without a cap, or verbose debug logs left enabled in production configuration.

When flagging logging issues, suggest a concrete fix (e.g., remove the log, lower the level, add a rate-limit guard, or move outside a loop).

#### Performance (MEDIUM)
- Inefficient algorithms (O(n^2) where O(n) is possible)
- N+1 query patterns
- Missing caching opportunities
- Blocking synchronous I/O
- Unnecessary re-renders (frontend)

#### Best Practices (LOW)
- Poor naming conventions
- Magic numbers without constants
- Missing documentation on public interfaces

### Phase 4: Build Review Payload

#### 4a. Determine review event:
- `REQUEST_CHANGES` — only when the review uncovers **critical issues** that **must** be addressed before merging (e.g., bugs, security vulnerabilities, data loss risks, broken functionality)
- `COMMENT` — when the issues found are **not critical** but are still worth addressing, or for general feedback and suggestions
- `APPROVE` — when the PR looks good overall, even if there are minor issues that would be nice to improve but are not blocking

#### 4b. Build review body:
```markdown
## Code Review Summary

### Verdict: [APPROVE / COMMENT / REQUEST_CHANGES]

| Severity | Count |
|----------|-------|
| CRITICAL | X |
| HIGH     | X |
| MEDIUM   | X |
| LOW      | X |

### Review Basis
- Team standards: [rules/conventions found]
- Canonical repo patterns: [repos searched, files referenced]
- Documentation: [Confluence pages referenced]
- Qodo Merge: [already reviewed — key findings deferred to below / not yet reviewed]

### Key Findings
[Top findings with brief descriptions]
```

#### 4c. Build inline comments array:
For each finding, create a comment object. Tag severity with the matching quality-impact dimension
(`Correctness`, `Security`, `Reliability`, `Performance`, `Observability` — see Phase 1.5) so the
comment reads consistently next to any Qodo Merge findings on the same PR:
```json
{
  "path": "src/feature/feature.service.ts",
  "line": 42,
  "side": "RIGHT",
  "body": "**HIGH · Security**: Description.\n\n```suggestion\ncorrected code here\n```"
}
```

Include `` ```suggestion `` blocks with one-click fixes when applicable — **single-line suggestions only** (multi-line suggestions produce broken diffs).

### Phase 5: Submit Review

**See:** [Inline Review Comments Guide](./references/inline-review-comments.md) for the full API spec.

Submit **exactly one** API call:

```bash
gh api "/repos/{owner}/{repo}/pulls/{pull_number}/reviews" \
  --method POST \
  --input "$REVIEW_PAYLOAD"
```

**CRITICAL — do NOT modify the command above:**
- Run it exactly as shown — do NOT pipe the output to `python3`, `jq`, `head`, or any other command
- Do NOT wrap it in a script that parses the response
- If the command exits with code 0, the review was created — you are done
- **NEVER retry or resubmit** — even if the output looks unexpected, even if you're unsure it worked. Each call creates a new review. If you call it twice, every comment appears twice.

**Submission rules:**
- **Use `--input` only** — do NOT use `-f`, `-F`, or `--raw-field` flags
- Do NOT also post comments through other endpoints (`/pulls/{number}/comments` etc.)
- Do NOT add a separate comment to the PR summarizing the review — the review body IS the summary

### Phase 6: Post-Review Summary

Output to the user:
1. Total findings by severity
2. The verdict (APPROVE / COMMENT / REQUEST_CHANGES)
3. List of all inline comments placed
4. Any patterns that were notably well-implemented (positive feedback)

## Review Quality Rules

- **Avoid nitpicking** — focus on significant issues and improvements
- Focus on: bugs, security issues, logic errors, performance problems
- Skip: style preferences, minor formatting, subjective opinions
- Provide actionable feedback with specific suggestions
- Include reference links when golden repo patterns or docs were used
- Report only findings with >80% confidence
- Consolidate similar issues into one comment with examples
- If the PR is too large (>50 files), ask the user which areas to focus on
