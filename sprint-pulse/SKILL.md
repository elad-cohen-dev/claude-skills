---
name: sprint-pulse
description: On-demand sprint health check for a team lead — progress vs. time, risky tickets (stale, no PR, PR merged but ticket open, blocked, unassigned, high priority not started, carried over, scope creep), per-person status and WIP — in a one-screen report, with a short standup mode. Trigger on /sprint-pulse, "how's the sprint", "sprint health", "prep me for standup", "what's at risk this sprint".
argument-hint: "[standup | full | @<teammate>]"
---

# Sprint Pulse

A quick Jira + GitHub read of the current sprint — the answer to "are we going to make
it, and what do I need to poke?". Chat-only; nothing is written unless you approve it.

## Step 1 — Config

Load the team-lead config per `~/.claude/skills/_shared/references/team-lead-config.md`.
You need the `jira` block (cloud_id or site, project_keys, scope, sprint_field,
sprint_mode, stale_days, high_priorities), `github.{account, org, repos}` and `team`.
Defaults: `stale_days: 3`, `sprint_field: customfield_10020`, `sprint_mode: scrum`,
`high_priorities: [Highest, High]`.

If `scope` is missing or `project`-wide on a large project, warn once that shared sprints
can return hundreds of issues, and offer to set up team scoping (see the config setup).

Argument → `mode`: `standup` (short) or `full` (default); `@name` → `focus`.

## Step 2 — Collect (subagent)

Dispatch the `sprint-pulse-collector` agent with the config values, `mode` and `focus`.
If the agent type isn't installed, follow its steps yourself
(`~/.claude/agents/sprint-pulse-collector.md`, or `agents/` in the skills repo), keeping raw
Jira payloads out of your reply.

## Step 3 — Present

Show the report. Map account ids / logins to the names in `team`. Put the verdict first.
For `standup`, stop after the report and a single line: "Want nudges drafted for any of these?"

## Step 4 — Offer actions (approval required, one menu)

`AskUserQuestion` (multiSelect) built from `SUGGESTED ACTIONS`, e.g.:

| Action | How (after approval only) |
|---|---|
| Nudge an owner | Slack **draft** (`slack_send_message_draft`) — DM the assignee or post in the team channel; fallback: print the text |
| Ask for a status update on a ticket | Jira comment via `addCommentToJiraIssue`, text shown first |
| Fix hygiene (PR merged, ticket open) | list the keys and their PR links for the owner to move — **do not transition** tickets yourself |
| Rebalance | propose who could pick up an unassigned / overloaded item; `editJiraIssue` assignee only on explicit approval per ticket |
| Share the digest | Slack draft of the standup version to the team channel |

Hard stops: never transition, close or delete issues; never change sprint membership,
estimates or priority.

## Notes

- "Scope creep" uses `created` after sprint start — an approximation (issues moved in from
  the backlog aren't caught). Say so if asked.
- Custom workflows are fine: logic uses status **category**, not status names.
- Good moments: 10 minutes before standup, mid-sprint check, day before sprint end.
