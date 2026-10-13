---
name: codepilot-ui
description: Frontend feature-development router. Detects the UI framework (Angular or React) from the repo and Jira ticket, then dispatches to the matching per-language skill (codepilot-ui-angular / codepilot-ui-react). Falls back to a generic flow for anything else. Use when the user provides a Jira ticket link and wants the full frontend development loop handled autonomously. Trigger on "implement this UI ticket", "build this frontend story", "start on this UI task", or when a Jira URL is pasted with frontend/UI context.
context: fork
agent: general-purpose
allowed-tools: Bash, Read, Edit, Write, Glob, Grep, Skill, mcp__atlassian__getJiraIssue, mcp__atlassian__editJiraIssue, mcp__atlassian__addCommentToJiraIssue, mcp__atlassian__getTransitionsForJiraIssue, mcp__atlassian__transitionJiraIssue
---

# CodePilot UI — Frontend Framework Router

Detects the UI framework, then hands off to the matching per-language skill.
Each language skill owns the framework-specific development loop; the shared
orchestration (ticket, branch, commit, CR) lives in
`../_shared/references/codepilot-common.md`.

## Required Inputs
- Jira ticket URL
- (Optional) User availability: `available` | `unavailable`

## Step 1: Fetch the ticket

Retrieve the ticket (Shared Phase A of `codepilot-common.md`) so its labels and
`relatedComponents[]` can feed detection. Do **not** transition it yet — the
dispatched skill will run the full shared flow including the In Progress transition.

## Step 2: Detect the UI framework

Follow `../_shared/references/framework-detection.md`. Inspect the repo first
(package.json, `angular.json`, `*.tsx`/`*.jsx`, `vite` config) and use ticket labels
as a tie-breaker. A repo with `next` present is Next.js (backend) — route those via
`codepilot-be`. Only ask the user when signals are missing or conflicting.

Store the result as `uiFramework`.

## Step 3: Dispatch

| `uiFramework` | Invoke skill |
|---------------|--------------|
| `Angular` | `codepilot-ui-angular` |
| `React` | `codepilot-ui-react` |
| _anything else / undetected_ | **default** — run `## Default / Generic Flow` in `codepilot-common.md` |

Use the `Skill` tool to invoke the chosen skill, forwarding the ticket URL and all
original arguments. Inform the user which framework was detected and which skill is
taking over, e.g.:
> Detected UI framework: **Angular** → handing off to `codepilot-ui-angular`.

For the default path, warn per the generic-flow instructions and proceed — never stop.

## Key Rules
- Always detect before dispatching; inspect the repo, ask only when unclear.
- Forward the ticket URL and arguments unchanged to the dispatched skill.
- Never run two language skills for one ticket — pick one.
- For unsupported/undetected stacks, run the default generic flow with a clear warning; do not stop.
