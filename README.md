# claude-skills

Reusable [Claude Code](https://claude.com/claude-code) skills for Jira/Figma-driven development, code review, and planning.

## Install

```bash
git clone https://github.com/elad-cohen-dev/claude-skills.git
cp -R claude-skills/* ~/.claude/skills/
```

Keep `_shared/` alongside the skills — several reference `../_shared/references/`.

## Skills

- **backend-python** — House rules for FastAPI/Pydantic/dependency-injector backend services and their pytest suites.
- **code-review-default** — Review a GitHub PR with inline comments.
- **codepilot-be-nestjs** — Autonomous NestJS backend feature development from a Jira ticket — analyzing the Nest project, designing API architecture, implementing controllers/services/modules/DTOs, writing Jest unit tests, validating, and committing.
- **codepilot-be-nextjs** — Autonomous Next.
- **codepilot-be-python** — Autonomous Python backend feature development from a Jira ticket — detecting the web framework (FastAPI, Django, or Flask), designing the API architecture, implementing routers/views/services with schema validation, writing pytest tests, validating, and committing.
- **codepilot-be** — Backend feature-development router.
- **codepilot-ui-angular** — Autonomous Angular frontend feature development from a Jira ticket — analyzing Figma designs, planning component architecture, implementing UI via webcode, validating against the design, and committing.
- **codepilot-ui-react** — Autonomous React frontend feature development from a Jira ticket — analyzing Figma designs, planning component/state architecture, implementing accessible components with the repo's styling and state conventions, validating against the design, and committing.
- **codepilot-ui** — Frontend feature-development router.
- **confluence** — Create, update, and search Confluence pages.
- **devloop** — Unified development orchestrator that combines Jira/Figma integration (from codepilot) with iterative quality loops (from trycycle).
- **epic-breakdown** — Break a Jira epic (or a pair of related epics) into a complete, right-sized set of child tickets, or review and refine an epic's existing children.
- **feature-composer** — Transform a PRD document, prototype URL, and empty Jira epic into a fully structured, ticketed implementation plan.
- **frontend-patterns** — Angular frontend development patterns, conventions, and best practices.
- **output-validator** — Validate a live UI implementation against Figma designs and acceptance criteria using browser screenshots and visual comparison.
- **ticket-enricher** — Enrich Jira tickets with High-Level Design (HLD) documents for every ticket in a Jira Epic.
- **unit-testing** — Generate high-quality Jest unit tests for NestJS services and controllers in an Nx monorepo.
- **vibe-coder** — Build beautiful, consistent UI components using an established design system with safety guardrails.
- **webcode** — Implement pixel-perfect Angular UI components from Figma designs with absolute fidelity to the design spec.

## Configuration

- `confluence`: set `CONFLUENCE_BASE_URL`, `CONFLUENCE_EMAIL`, `CONFLUENCE_TOKEN`.
- `backend-python`: replace `your_pkg` / `your_app` imports and `apps/<app>` paths with your own.
- `_shared/references/sourcegraph-search.md`: replace the `your-org/*` golden repos with your own.
