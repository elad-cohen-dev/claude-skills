# claude-skills

Reusable [Claude Code](https://claude.com/claude-code) skills for Jira/Figma-driven development, code review, and planning.

## Install

```bash
git clone https://github.com/elad-cohen-dev/claude-skills.git && cd claude-skills
mkdir -p ~/.claude/skills ~/.claude/agents
for d in */; do [ "$d" != agents/ ] && ln -sfn "$PWD/${d%/}" ~/.claude/skills/; done
ln -sf "$PWD"/agents/*.md ~/.claude/agents/
```

Symlinks keep `~/.claude` in sync with `git pull`. Keep `_shared/` alongside the skills — several reference it.

## Team-lead toolkit

Day-to-day skills for a hands-on team lead. They share one local config,
`~/.claude/team-lead.yaml` (start from [`team-lead.example.yaml`](team-lead.example.yaml);
details in [`_shared/references/team-lead-config.md`](_shared/references/team-lead-config.md)).
All three are read-only by default; every write (Slack draft, PR/Jira comment, reviewer,
new ticket) is shown first and needs your approval.

| Command | What it gives you | Uses |
|---|---|---|
| `/pr-radar [mine\|repo\|@who]` | What's waiting on you, ready to merge, blocked (CI, conflicts, stale), needs a reviewer, oversized; review-load balance; drafted nudges | gh CLI, Slack (optional) · agent `pr-radar-collector` |
| `/sprint-pulse [standup\|full\|@who]` | Sprint progress vs. time with a verdict, risky tickets, PR↔ticket gaps, per-person status and WIP | Jira (Atlassian MCP), gh CLI · agent `sprint-pulse-collector` |
| `/bug-triage <thread\|error\|key>` | Duplicate check, code location, suspect PRs, owner, severity, ready-to-file Jira bug + Slack reply draft | Jira, Slack, gh/git |

## Skills

- **backend-python** — House rules for FastAPI/Pydantic/dependency-injector backend services and their pytest suites.
- **bug-triage** — Triage a bug report end-to-end into a ready-to-file Jira bug with suspects, owner and severity.
- **code-review-default** — Review a GitHub PR with inline comments.
- **codepilot-be** — Backend feature-development router.
- **codepilot-be-nestjs** — Autonomous NestJS backend feature development from a Jira ticket — analyzing the Nest project, designing API architecture, implementing controllers/services/modules/DTOs, writing Jest unit tests, validating, and committing.
- **codepilot-be-nextjs** — Autonomous Next.js backend feature development from a Jira ticket.
- **codepilot-be-python** — Autonomous Python backend feature development from a Jira ticket — detecting the web framework (FastAPI, Django, or Flask), designing the API architecture, implementing routers/views/services with schema validation, writing pytest tests, validating, and committing.
- **codepilot-ui** — Frontend feature-development router.
- **codepilot-ui-angular** — Autonomous Angular frontend feature development from a Jira ticket — analyzing Figma designs, planning component architecture, implementing UI via webcode, validating against the design, and committing.
- **codepilot-ui-react** — Autonomous React frontend feature development from a Jira ticket — analyzing Figma designs, planning component/state architecture, implementing accessible components with the repo's styling and state conventions, validating against the design, and committing.
- **confluence** — Create, update, and search Confluence pages.
- **devloop** — Unified development orchestrator that combines Jira/Figma integration (from codepilot) with iterative quality loops (from trycycle).
- **excalidraw-diagrams** — Draw architecture/sequence diagrams as Excalidraw scenes, render them to PNG with Excalidraw's own exporter (Playwright), and embed them inline in Confluence with the editable `.excalidraw` source attached.
- **epic-breakdown** — Break a Jira epic (or a pair of related epics) into a complete, right-sized set of child tickets, or review and refine an epic's existing children.
- **feature-composer** — Transform a PRD document, prototype URL, and empty Jira epic into a fully structured, ticketed implementation plan.
- **frontend-patterns** — Angular frontend development patterns, conventions, and best practices.
- **output-validator** — Validate a live UI implementation against Figma designs and acceptance criteria using browser screenshots and visual comparison.
- **pr-radar** — On-demand triage of your team's open PRs, with drafted nudges.
- **sprint-pulse** — On-demand sprint health check with a short standup mode.
- **ticket-enricher** — Enrich Jira tickets with High-Level Design (HLD) documents for every ticket in a Jira Epic.
- **unit-testing** — Generate high-quality Jest unit tests for NestJS services and controllers in an Nx monorepo.
- **vibe-coder** — Build beautiful, consistent UI components using an established design system with safety guardrails.
- **webcode** — Implement pixel-perfect Angular UI components from Figma designs with absolute fidelity to the design spec.

## Configuration

- `confluence`, `excalidraw-diagrams`: set `CONFLUENCE_BASE_URL`, `CONFLUENCE_EMAIL`, `CONFLUENCE_TOKEN`.
- `excalidraw-diagrams`: rendering needs Node + `playwright` (with Chromium) in the directory you run `render.mjs` from, and network access to esm.sh/unpkg.
- `epic-breakdown`: Jira custom-field ids (Team, QA to verify, story points) are site-specific; adjust them to your instance.
- `backend-python`: replace `your_pkg` / `your_app` imports and `apps/<app>` paths with your own.
- `_shared/references/sourcegraph-search.md`: replace the `your-org/*` golden repos with your own.
