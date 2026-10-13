---
name: codepilot-be
description: Backend feature-development router. Detects the backend framework (NestJS, Next.js, or Python) from the repo and Jira ticket, then dispatches to the matching per-language skill (codepilot-be-nestjs / codepilot-be-nextjs / codepilot-be-python). Falls back to a generic flow for anything else. Use when the user provides a Jira ticket link and wants the full backend development loop handled autonomously. Trigger on "implement this backend ticket", "build this API story", "start on this backend task", or when a Jira URL is pasted with backend/API context.
context: fork
agent: general-purpose
allowed-tools: Bash, Read, Edit, Write, Glob, Grep, Skill, mcp__atlassian__getJiraIssue, mcp__atlassian__editJiraIssue, mcp__atlassian__addCommentToJiraIssue, mcp__atlassian__getTransitionsForJiraIssue, mcp__atlassian__transitionJiraIssue
---

# CodePilot BE — Backend Framework Router

Detects the backend framework, then hands off to the matching per-language skill.
Each language skill owns the framework-specific development loop; the shared
orchestration (ticket, branch, commit, CR) lives in
`../_shared/references/codepilot-common.md`.

## Required Inputs
- Jira ticket URL
- (Optional) User availability: `available` | `unavailable`

## Step 1: Fetch the ticket

Retrieve the ticket (Shared Phase A of `codepilot-common.md`) so its labels and
`relatedServices[]` can feed detection. Do **not** transition it yet — the
dispatched skill will run the full shared flow including the In Progress transition.

## Step 2: Detect the backend framework

Follow `../_shared/references/framework-detection.md`. Inspect the repo first
(package.json, `nest-cli.json`, `next.config.*`, `pyproject.toml` / `requirements.txt`)
and use ticket labels as a tie-breaker. Only ask the user when signals are missing
or conflicting.

Store the result as `beFramework`.

## Step 3: Dispatch

| `beFramework` | Invoke skill |
|---------------|--------------|
| `NestJS` | `codepilot-be-nestjs` |
| `Next.js` | `codepilot-be-nextjs` |
| `Python` | `codepilot-be-python` |
| _anything else / undetected_ | **default** — run `## Default / Generic Flow` in `codepilot-common.md` |

Use the `Skill` tool to invoke the chosen skill, forwarding the ticket URL and all
original arguments. Inform the user which framework was detected and which skill is
taking over, e.g.:
> Detected backend framework: **NestJS** → handing off to `codepilot-be-nestjs`.

For the default path, warn per the generic-flow instructions and proceed — never stop.

## Key Rules
- Always detect before dispatching; inspect the repo, ask only when unclear.
- Forward the ticket URL and arguments unchanged to the dispatched skill.
- Never run two language skills for one ticket — pick one.
- For unsupported/undetected stacks, run the default generic flow with a clear warning; do not stop.
