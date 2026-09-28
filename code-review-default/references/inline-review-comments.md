# Inline PR Review Comments via GitHub API

Technical reference for submitting pull request reviews with inline (line-level) comments
via the GitHub Enterprise / GitHub.com REST API.

## API Endpoint

```
POST /repos/{owner}/{repo}/pulls/{pull_number}/reviews
```

## Request Body Structure

```json
{
  "body": "Review summary text (appears at the top of the review)",
  "event": "APPROVE | COMMENT | REQUEST_CHANGES",
  "comments": [
    {
      "path": "relative/path/to/file.ts",
      "line": 42,
      "side": "RIGHT",
      "body": "Comment text in markdown"
    }
  ]
}
```

## Field Reference

### Top-level fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `body` | string | Yes | Summary text shown at the top of the review |
| `event` | string | Yes | One of: `APPROVE`, `COMMENT`, `REQUEST_CHANGES` |
| `comments` | array | No | Array of inline comment objects |
| `commit_id` | string | No | SHA of the commit to review (defaults to HEAD of PR) |

### Comment object fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `path` | string | Yes | Relative file path from repo root |
| `line` | number | Yes* | Line number in the diff to comment on |
| `side` | string | No | `RIGHT` (new code) or `LEFT` (deleted code). Default: `RIGHT` |
| `body` | string | Yes | Comment text (supports markdown) |
| `start_line` | number | No | For multi-line comments: first line of range |
| `start_side` | string | No | Side for start_line: `RIGHT` or `LEFT` |

*Either `line` or both `start_line` + `line` must be provided.

**Important:** Do NOT include `subject_type` — it is not supported on GitHub Enterprise.

### Multi-line comment example

To comment on lines 10-15 of a file:
```json
{
  "path": "src/service.ts",
  "start_line": 10,
  "line": 15,
  "side": "RIGHT",
  "start_side": "RIGHT",
  "body": "This block should be extracted into a helper method."
}
```

## Using with `gh` CLI

### Submit a review with inline comments

Write the payload to a temp file and use `--input`:

```bash
REVIEW_PAYLOAD=$(mktemp)
cat > "$REVIEW_PAYLOAD" <<'EOF'
{
  "body": "Review summary",
  "event": "REQUEST_CHANGES",
  "comments": [
    {
      "path": "src/auth/auth.guard.ts",
      "line": 15,
      "side": "RIGHT",
      "body": "**CRITICAL**: This guard does not validate the JWT signature."
    }
  ]
}
EOF

gh api repos/{owner}/{repo}/pulls/{pull_number}/reviews \
  --method POST \
  --input "$REVIEW_PAYLOAD"
```

### For GitHub Enterprise (GHE)

Add `--hostname <ghe-hostname>`:
```bash
gh api repos/{owner}/{repo}/pulls/{pull_number}/reviews \
  --method POST \
  --hostname your-ghe-instance.com \
  --input "$REVIEW_PAYLOAD"
```

## Line Number Mapping

The `line` field refers to:
- For `side: "RIGHT"`: the line number in the **new version** of the file
- For `side: "LEFT"`: the line number in the **old version** of the file

To find the correct line number:
1. Get the diff from `gh pr diff <number>` or the PR files API
2. Parse the `@@ -old,count +new,count @@` hunk headers
3. Use the new-file line number for commenting on additions (`side: "RIGHT"`)
4. Use the old-file line number for commenting on deletions (`side: "LEFT"`)
5. You can only comment on lines that appear in the diff — lines outside diff hunks will cause a 422 error

## Comment Formatting

```markdown
**SEVERITY**: Brief title of the issue

Explanation of why this is a problem.

Suggested fix:
\`\`\`suggestion
corrected code here
\`\`\`

_Pattern reference: [golden-repo/file.ts](link)_
```

**Note:** Use `` ```suggestion `` blocks for one-click fixes. Only use **single-line suggestions** — multi-line suggestions produce broken diffs on GHE.

## Error Handling

| Status | Meaning | Action |
|--------|---------|--------|
| 200 | Review submitted successfully | Done — do NOT resubmit |
| 422 | Validation error | Check line numbers against diff; verify file paths |
| 404 | PR or repo not found | Verify owner/repo/PR number |
| 403 | Permission denied | User may not have write access |

### Common 422 causes
- Line number is outside the diff hunk (can only comment on changed lines)
- File path does not match any file in the PR
- `commit_id` points to a commit not in the PR

## Fetching Existing Reviews

```bash
# List all reviews on a PR
gh api repos/{owner}/{repo}/pulls/{pull_number}/reviews

# List inline comments on a PR
gh api repos/{owner}/{repo}/pulls/{pull_number}/comments
```
