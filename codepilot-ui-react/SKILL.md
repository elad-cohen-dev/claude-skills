---
name: codepilot-ui-react
description: Autonomous React frontend feature development from a Jira ticket — analyzing Figma designs, planning component/state architecture, implementing accessible components with the repo's styling and state conventions, validating against the design, and committing. Use when a UI ticket targets a React codebase (Vite/CRA, not Next.js). Usually invoked by the codepilot-ui router after framework detection, but can be called directly.
context: fork
agent: general-purpose
allowed-tools: Bash, Read, Edit, Write, Glob, Grep, Skill, mcp__github__search_code, mcp__atlassian__getJiraIssue, mcp__atlassian__editJiraIssue, mcp__atlassian__addCommentToJiraIssue, mcp__atlassian__getTransitionsForJiraIssue, mcp__atlassian__transitionJiraIssue
---

# CodePilot UI (React) — Autonomous Frontend Feature Development

Full frontend loop for **React** codebases (Vite / CRA / plain React — for Next.js
use `codepilot-be-nextjs` for server code and this skill's patterns for client
components). Shared orchestration phases live in
`../_shared/references/codepilot-common.md`.

## Required Inputs
- Jira ticket URL
- (Optional) User availability: `available` | `unavailable`

---

### Phase 1: Retrieve & Parse Ticket
Run **Shared Phase A**. Prioritize `figmaLinks[]` and `relatedComponents[]`.

### Phase 2: Pull Figma Designs
For each URL in `ticket.figmaLinks[]`: fetch full-page screenshots and capture
developer frame links. Store as
`figmaContext: { frameUrls: string[]; screenshots: string[] }` — the keys
`/output-validator` reads.

### Phase 2.5: Analyze Repo Conventions & Golden Repos
Detect and mirror the repo's established React conventions:
- **Styling**: CSS Modules / Tailwind / styled-components / vanilla-extract — match it.
- **State**: local `useState`/`useReducer`, Context, Redux Toolkit, Zustand, or Jotai.
- **Data fetching**: TanStack Query, SWR, RTK Query, or fetch in effects.
- **Component library / design system**: MUI, shadcn/ui, Radix, Chakra, or in-house.
- **Routing**: React Router (version) if applicable.
Search the golden repo / shared libraries for existing components and utilities
(`sourcegraph-search.md`); search internal docs (`documentation-search.md`). Log findings.

### Phase 3: Architecture Planning
```typescript
{
  componentPath: string;
  components: Array<{ name; responsibility; props?: string[]; children?: string[] }>;
  state: {
    local: string[];                    // useState/useReducer
    shared: string[];                    // context/store slices
    server: string[];                    // query keys / hooks
  };
  hooks: string[];                        // custom hooks to extract
  styling: string;                        // approach used
  sharedComponents: string[];             // reused from design system / shared libs
}
```
Write to `architecture.md`. Present 2-4 options for major decisions (state location,
data-fetching strategy, controlled vs uncontrolled, composition boundaries).

### Phase 4: Setup Git Branch
Run **Shared Phase B**.

### Phase 5: Implement
- Build small, composable **function components** with typed props (TS `interface`/`type`).
- Lift state only as far as needed; extract reusable logic into **custom hooks**.
- Use the repo's styling approach; match Figma to high fidelity (spacing, tokens, states:
  hover/focus/disabled/loading/empty/error).
- Fetch data with the repo's chosen library; handle loading/error/empty states explicitly.
- **Accessibility**: semantic elements, labels, `aria-*` where needed, keyboard operability,
  visible focus.
- Memoize deliberately (`useMemo`/`useCallback`/`React.memo`) only where it measurably helps.
- Validate with `npm run build` and `npm run lint`; fix type/lint errors.

### Phase 6: Tests
Use the repo's runner (Vitest or Jest) with **React Testing Library**: test behavior via
roles/text, not implementation details; cover interactions and error/empty states. Run the
test command; if the repo has Storybook, add/update a story for the new component.

### Phase 7: Output Validation
Invoke `/output-validator` with `{ ticketContext, figmaContext, liveUrl: "http://localhost:PORT/feature-route" }`
to check visual match, acceptance criteria, and accessibility basics. Returns
`{ status, issues[], recommendations[] }`. **If rejected** → return to Phase 5, fix,
re-validate. **Never start the dev server — the app is already running.**

### Phase 8: Commit & Push
Run **Shared Phase C**.

### Phase 9: CR Review & Fix
Run **Shared Phase D**.

---

## React Key Rules
(In addition to the Shared Key Rules in `codepilot-common.md`.)
- Mirror the repo's existing styling, state, and data-fetching conventions — don't introduce a new one.
- Typed props everywhere; no `any` on component boundaries.
- Handle loading / error / empty states for every async view.
- Follow the Rules of Hooks; keep components pure and side-effects in effects/handlers.
- Accessibility is a requirement, not a nice-to-have.
- Never skip subcomponents defined in the architecture plan.
- Never start the dev server (the app is already running).
