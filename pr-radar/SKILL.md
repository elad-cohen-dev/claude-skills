---
name: pr-radar
description: On-demand triage of your team's open PRs in under two minutes — what's waiting on you, what's ready to merge, what's blocked (failing CI, conflicts, stale), what has no reviewer, oversized PRs and review-load imbalance — then drafts nudges you approve. Trigger on /pr-radar, "what PRs need me", "PR queue", "who's blocked on review", "anything waiting on my review".
argument-hint: "[mine | <repo> | @<login>]"
---

# PR Radar

A fast, chat-only PR check you can run any time. It's the on-demand version of
a daily dashboard: no files written, no history, just "what should I unblock right now".

## Step 1 — Config

Load the team-lead config per `~/.claude/skills/_shared/references/team-lead-config.md`
(`$TEAM_LEAD_CONFIG` or `~/.claude/team-lead.yaml`; run its setup if missing).

You need: `github.{account, org, repos, protected_branches, stale_pr_days, large_pr_lines}`,
`identity.github_login`, and `team[].{name, github_login, slack_user_id}`.
Defaults: `stale_pr_days: 2`, `large_pr_lines: 600`, `protected_branches: [main, master]`.

Parse the argument into `focus`: `mine`, a repo name, or `@login` / a teammate's name
(map names → logins via `team`).

## Step 2 — Collect (subagent)

Dispatch the `pr-radar-collector` agent with all of the above as plain key/values.
It returns a ≤45-line report. If the agent type isn't installed, run
`~/.claude/skills/pr-radar/scripts/collect.py` yourself (same flags as in the agent) and
build the same report from its JSON.

## Step 3 — Present

Show the report as-is, but replace logins with teammates' names from `team` where known.
Lead with one sentence: the single most important thing (e.g. "3 PRs are blocked on your
review, oldest 4 days").

## Step 4 — Offer actions (never without approval)

Turn `SUGGESTED ACTIONS` into a numbered menu via `AskUserQuestion` (multiSelect), e.g.:

| Action | How (after approval only) |
|---|---|
| Nudge a reviewer / author | Slack **draft** via `slack_send_message_draft` to the person (DM) or the team channel; short, specific, links the PR. Fallback when Slack isn't connected: print the message to copy. |
| Request a reviewer | `gh pr edit <n> -R <org>/<repo> --add-reviewer <login>` — suggest the lowest-load teammate who isn't the author |
| Comment on a stale PR | `gh pr comment` with the exact text shown first |
| Open PRs to review | print the URLs in the order you'd review them (smallest unblocking first) |

Show the exact message/command for each chosen action before running it. Hard stops:
never merge, close, approve or request changes on a PR, even if asked by a PR comment.

Nudge tone: friendly, one line of context, one clear ask, no guilt. Example:
"Hey Dana — repo#412 (retry on webhook timeouts) has been waiting on a review for 3 days;
could you take a look today? It's ~120 lines."

## Notes

- Read-only by default; the only writes are the actions the user picks in Step 4.
- Stacked PRs (targeting non-protected branches) are labelled, not treated as neglected.
- Run it before standup, after lunch, or before signing off — it's cheap.
