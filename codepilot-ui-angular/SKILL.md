---
name: codepilot-ui-angular
description: Autonomous Angular frontend feature development from a Jira ticket — analyzing Figma designs, planning component architecture, implementing UI via webcode, validating against the design, and committing. Use when a UI ticket targets an Angular codebase. Usually invoked by the codepilot-ui router after framework detection, but can be called directly.
context: fork
agent: general-purpose
allowed-tools: Bash, Read, Edit, Write, Glob, Grep, Skill, mcp__github__search_code, mcp__atlassian__getJiraIssue, mcp__atlassian__editJiraIssue, mcp__atlassian__addCommentToJiraIssue, mcp__atlassian__getTransitionsForJiraIssue, mcp__atlassian__transitionJiraIssue
---

# CodePilot UI (Angular) — Autonomous Frontend Feature Development

Full frontend loop for **Angular** codebases, from Jira ticket to PR. Shared
orchestration phases (ticket, branch, commit, CR) live in
`../_shared/references/codepilot-common.md`.

## Required Inputs
- Jira ticket URL
- (Optional) User availability: `available` | `unavailable`

---

### Phase 1: Retrieve & Parse Ticket
Run **Shared Phase A**. Prioritize `figmaLinks[]` and `relatedComponents[]`.

### Phase 2: Pull Figma Designs
For each URL in `ticket.figmaLinks[]`: fetch full-page screenshots and capture
developer frame links. Only fetch main frame views here. Store as
`figmaContext: { frameUrls: string[]; screenshots: string[] }` — `frameUrls` holds
the developer frame links, `screenshots` the captured images. Downstream skills
(`/webcode`, `/output-validator`) read those exact keys.

### Phase 2.5: Search Golden Repos for Patterns
Before planning, search the frontend golden repo for canonical Angular patterns
(component structure, signal/state management, SCSS organization, module boundaries)
via `mcp__github__search_code` / `gh search code` (see `sourcegraph-search.md`).
Search shared libraries for existing components/utilities. Log findings to inform Phase 3.

### Phase 3: Architecture Planning
```typescript
{
  componentPath: string;
  components: Array<{ name; responsibility; inputs?: string[]; outputs?: string[] }>;
  state: { signals: string[]; services: string[]; communication: string[] };
  events: string[];
  sharedModules: string[];
}
```
Write to `architecture.md`. **If a major architectural decision is needed** (feature
placement, reuse vs extend, competing strategies) → present 2-4 options to the user.

### Phase 4: Setup Git Branch
Run **Shared Phase B**.

### Phase 5: Delegate UI Implementation
Invoke `/webcode` with `{ ticketContext, figmaContext, architecturePlan }`.
WebCode must:
- Re-fetch each Figma frame before starting.
- Implement with 100% design fidelity.
- Use standalone Angular components + signals and modular SCSS.
- Follow `architecturePlan` strictly.
- Validate with `ng build` (or `npx nx build <project>`).

You may also consult `/frontend-patterns` for team Angular conventions and
`/vibe-coder` when working within an established design system.

### Phase 6: Output Validation
Invoke `/output-validator` with `{ ticketContext, figmaContext, liveUrl: "http://localhost:PORT/feature-route" }`.
Validator checks visual match against Figma, all `acceptanceCriteria`, and accessibility
basics. Returns `{ status, issues[], recommendations[] }`. **If rejected** → return to
Phase 5, fix, re-validate. **Never start the dev server — the app is already running.**

### Phase 7: Commit & Push
Run **Shared Phase C**.

### Phase 8: CR Review & Fix
Run **Shared Phase D**.

---

## Angular Key Rules
(In addition to the Shared Key Rules in `codepilot-common.md`.)
- Never skip subcomponents defined in the architecture plan.
- Never start the dev server (the app is already running).
- Prefer standalone components, signals, and modular SCSS; follow team conventions from `/frontend-patterns`.

## Dependency Injection Note
Before injecting core services (LeadService, ApiService, etc.) into feature components:
- Analyze the dependency graph first.
- Only inject services truly needed for core functionality.
- Prefer event emission to parent components over direct service injection.
- Avoid circular dependency chains between feature modules and core services.
