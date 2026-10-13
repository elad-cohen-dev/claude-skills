# Golden Repos Search Guide

Reference document for searching known-good repositories before implementing or reviewing code.
Any skill can reference this guide to ensure implementations follow established patterns.

## Why Search First?

Before writing new code or reviewing a PR, search the team's golden repositories to find:
- Established patterns for similar features
- Naming conventions and code organization
- Error handling approaches
- Testing patterns
- Configuration and dependency injection patterns

## Golden Repositories

Choose ONE most relevant repo, search it, stop if found, try next if needed.

| Repo | Domain | When to Use |
|------|--------|-------------|
| `your-org/backend-golden` | Backend APIs | Services, controllers, guards, interceptors |
| `your-org/frontend-golden` | Frontend apps | Components, services, directives, SCSS patterns |
| `your-org/shared-libs` | Shared libraries | Reusable utilities, core functions |

> **Note:** Replace the repos above with your team's canonical repositories.

## How to Search

### Option 1: GitHub MCP Tool (Preferred)

Use the `mcp__github__search_code` deferred tool. Load it first via ToolSearch, then search:

```
Query format: "<search-term> repo:<org>/<repo>"
```

**Examples:**
- NestJS guard patterns: `"@UseGuards repo:your-org/backend-golden"`
- Angular signal usage: `"signal( repo:your-org/frontend-golden"`
- Shared utility patterns: `"export function repo:your-org/shared-libs"`

**Multi-repo search** (omit repo filter):
- `"ValidationPipe org:your-org"`
- `"HttpExceptionFilter org:your-org"`

### Option 2: GitHub CLI Fallback

If the MCP tool is unavailable, use `gh search code`:

```bash
gh search code "<search-term>" --repo your-org/backend-golden --limit 10
gh search code "<search-term>" --repo your-org/frontend-golden --limit 10
```

To see full file content after finding a match:
```bash
gh api repos/your-org/backend-golden/contents/<file-path> --jq '.content' | base64 -d
```

## When to Search

### Before Implementing (Proactive — Golden Repos)
1. Search BEFORE writing any code OR reviewing PR changes OR answering questions
2. Choose the ONE most relevant golden repo based on task type
3. Search only that repo first
4. If found, use patterns with links to files and line numbers
5. If not found, try next most relevant repo
6. If nothing useful found, proceed with your knowledge without mentioning the search
7. NEVER fabricate code snippets or references

### Before Code Review
1. Identify the patterns used in the PR (e.g., new service, new component, new pipe)
2. Search golden repos for how the same pattern is implemented there
3. Flag deviations from golden repo patterns as review findings

### Search Strategy
- Start broad: search for the class/decorator/pattern name
- Narrow down: add file extension or path qualifiers
- Check tests: search for `*.spec.ts` files alongside implementation files
- Check imports: understand what shared modules/utilities are available

## Other Repos (Search Only When Explicitly Asked)

Only search non-golden repos when the user specifically mentions another repository:
- "How did we implement X in the auth-service repo?"
- "Check the payment-processor repo for the retry pattern"

Do NOT search other repos for general PR reviews or implementation questions.

## Interpreting Results

- **Follow the pattern** if it aligns with current best practices
- **Note deviations** if the golden repo pattern is outdated and explain why
- **Log what you found** in your architecture plan or review notes so the human can verify
- **Never fabricate** code snippets or references — if nothing is found, say so
