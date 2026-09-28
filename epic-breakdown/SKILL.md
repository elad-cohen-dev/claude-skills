---
name: epic-breakdown
description: Break a Jira epic (or a pair of related epics) into a complete, right-sized set of child tickets, or review and refine an epic's existing children. It finds requirement gaps, fixes vague titles, writes Context/Scope/AC/Dependencies descriptions, creates only the missing tickets, and wires "Blocks" links. Follows a coarse HLD → Backend → UI-per-surface → Infra split, never mini-tasks. Trigger on "break this epic into tickets", "review the epic's child tickets", "are we missing tickets for PROJ-…", "refine the children of this epic", "split this epic". Skip for PRD-to-epic creation from scratch (use feature-composer) or per-ticket HLD documents (use ticket-enricher).
---

# Epic Breakdown: review and complete an epic's child tickets

Take one or more Jira epics and leave them with a **complete, coarse-grained** set of child tickets. Every epic requirement should have exactly one owning ticket, every ticket should have a real description, and the dependency order should be visible as links.

The user's preference is **high-level splits**. One ticket per real deliverable, never a checklist of mini-tasks. When in doubt, fold a small item into the nearest existing ticket rather than creating a new one.

## Inputs

- One or more epic keys or URLs (e.g. `PROJ-9811`, `PROJ-9812`). Related epics that ship together should be reviewed together.
- Optional: an HLD/design page, Figma links, and a note on which items are already built.

## Phase 1: Gather (read everything before judging)

1. **Epic(s):** `getJiraIssue` with `responseContentFormat: markdown`. Extract the in-scope list, feature descriptions, acceptance criteria (AC), Figma links, and any "Design:" link.
2. **Children:** `searchJiraIssuesUsingJql` with `parent in (EPIC-1, EPIC-2) ORDER BY key` and fields `summary, description, status, assignee, issuelinks, customfield_10001` (team), `customfield_10024` (story points), `customfield_11360` (QA to verify) and `comment`.
3. **Design:**
   - If an HLD exists (Confluence), read it. It is the source of truth for the technical split: services, storage, infra, rollout.
   - If there is none, stop and suggest writing one first; the breakdown will be guesswork without it.
4. **Figma** (when linked): screenshot every frame with `get_screenshot`. Links often point to overlay or empty frames (e.g. an "Action Area" scrim). Note those; don't trust the link text.
5. **Code state:** check whether parts are already built, for example UI on mock data behind a hook, or an existing flag constant. The git log for the epic's ticket keys usually shows this. A "Done" UI ticket on mock data means the follow-up is a *wire-to-real-data* ticket, not a *build* ticket.

## Phase 2: Gap analysis

Build a coverage matrix: **every epic AC and scope item → the child ticket that owns it**. Then look for these gaps:

- **Unowned requirements.** Entry points are the usual miss: row icons, table columns, filters, empty states, permission gating, feature-flag gating.
- **Cross-team work with no ticket.** Infra/DevOps (buckets, lifecycle rules, CORS, IAM, provisioning), design follow-ups, data migrations. Work owned by another team always gets its **own** ticket, with that team set.
- **Missing dependency links.** UI tickets not blocked by their backend; a second epic's backend not blocked by the shared foundation from the first.
- **Titles that lie**, e.g. "X UI - Backend". Also titles that are too vague to scope, or that don't mention a sub-scope such as filters.
- **Empty descriptions** on any non-Done ticket.
- **Contradictions** between the epic, the HLD, the Figma and what is built. Report these; don't silently resolve them.

Don't create tickets for:

- Tests (unit/integration/E2E). They go in each ticket's acceptance criteria.
- Feature-flag creation. It goes in the backend ticket.
- Docs or code review.
- Anything that is under a day of work and fits naturally in an existing ticket.

## Phase 3: Target split (the convention)

Title pattern: `<Feature> <Layer> - <what, in user terms>`. Layers:

| Layer | Typical count per epic | Owns |
| --- | --- | --- |
| `HLD` | 1 (can be shared across related epics) | The design doc |
| `Backend` | 1 per epic | Storage, service, API routes, BFF/proxy, server-side flag and role gates, flag creation, backend tests plus an E2E API spec |
| `UI` | 1 per user-facing **surface** (e.g. overview-table columns, drawer tab, edit/delete flow) | Wiring to the API, states, gating, frontend tests |
| `Infra` | 0–1, only when another team is needed | Cloud/on-prem provisioning |

Examples of good titles:

- `Case Management Backend - Audit Status, Assigned Auditor and activity history APIs (incl. overview columns and filters)`
- `Case Notes UI - Notes tab on real data with attachments, and overview-row notes icon`
- `Case Notes Infra - Object storage for note attachments (S3 SaaS / MinIO on-prem)`

When a shared foundation (module, flag gate, controller) is built in epic A's backend ticket, epic B's backend ticket is **blocked by** it. Don't duplicate the foundation.

## Phase 4: Propose, then apply

1. Show the user a short plan before any write, as one table with the columns: key (or NEW), current title → proposed title, what changes, and links to add. Also list the contradictions found.
   - If the user already said "go ahead / fix what's needed", apply without waiting. Otherwise wait for a yes.
2. **Re-fetch each ticket right before editing it.** Someone may have changed it since you read it. Patch it; never overwrite blindly.
3. Write each description in **Markdown** (`contentFormat: markdown`). Wrap every URL as `[text](url)`, because bare URLs render as plain text. Use this template:

```markdown
## Context
<1–3 lines: why this ticket exists, and what is already built.>

Design: [HLD](<url>). See *<relevant HLD sections>*.
Figma: [<frame name>](<url>) ...   (UI tickets)

## Scope
**<Area>**
* <concrete deliverable: endpoints, files/paths, components, config>

## Acceptance criteria
* <observable, testable outcomes, incl. permissions, flag-off behaviour, tests>

## Notes            (optional: coordination, out-of-scope reminders)

## Dependencies
* Blocked by [KEY](url) (<why>).
* Blocks [KEY](url).
```

4. **New tickets:** `createJiraIssue` with `issueTypeName: Task` and `parent: <epic>`. Set both required custom fields in `additional_fields`, or the create fails:
   - Team, `customfield_10001`, as a **plain string** id. The ids are:
     - Platform `bab1ddec-6991-4697-b524-91a0db0d3a39`
     - Impala `8bc58574-4c7c-4671-9590-87e35f0b0056`
     - DevOps `2a614fbc-e89d-49f2-ab0c-c2de71318d8c`
     - Crypto Team `2d826e0c-332c-483c-a084-898d0029f248`
     - Applications `737548dc-0eb9-4a44-8484-12d8cdf60570`
     - Origins `e2db9fdb-a4b7-4c57-bb7f-3c65b78235c9`
     - Foundations `2c6b68c3-d9c9-46dd-a968-db967648bfb1`
   - QA to verify, `customfield_11360`, as `{"value": "Yes"}` or `{"value": "No"}`. Match what sibling tickets use.
   - Don't put `&amp;` in summaries; write "and".
5. **Links:** use `createIssueLink` with `type: "Blocks"`, **`inwardIssue` = the blocker** and `outwardIssue` = the blocked ticket. Create the first link, `getJiraIssue fields=["issuelinks"]` on the blocked ticket, and confirm it shows the blocker as `inwardIssue` before creating the rest.
6. After a new ticket gets its key, go back and replace placeholder mentions ("the infra ticket") in the other descriptions with the real link.

## Guardrails

- **Don't edit Done tickets.** Reference them as "already built" instead.
- **Don't change assignees or priority.**
- **Story points** (`customfield_10024`, a plain number; the convention is 1 SP = 1 day of work):
  - By default, recommend estimates in the summary, e.g. flag 1 SP for a change that touches every vertical.
  - When the user asks for estimates, set them on every non-Done ticket. Size from the scope: count the endpoints, the surfaces × verticals touched, the tests, and the SaaS + on-prem variants. Read them back with a JQL query, because the edit response doesn't show custom fields.
  - Report the before and after values, the remaining total, and the critical path.
- **Don't invent product decisions.** If the epic, HLD and Figma disagree, ask. Only encode what the user or the HLD already decided.
- Epics written by someone else (e.g. the PM) may be edited when the user asks, but say in the summary that the author may want to review.
- Keep scope to the epics named. A bug found along the way (e.g. a security gap) gets its own ticket outside the epic, and only with the user's OK.

## Final report

End with:

1. A table of every child ticket, with key, final title, status and what changed (renamed / described / new / linked).
2. The dependency chain in one line, e.g. `HLD → Backend A → {UI 1, UI 2}; Backend A + Infra → Backend B → {UI 3, UI 4}`.
3. Recommendations you did *not* apply: estimates, design follow-ups, open contradictions.
