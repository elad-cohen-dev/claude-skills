---
name: hld
description: Write a High-Level Design (Technical Design) end to end, from epic to a reviewed Confluence page with Excalidraw diagrams and linked Jira tickets. Follows the team's Technical Design template section for section and orchestrates the epic-breakdown, excalidraw-diagrams, confluence and ticket-enricher skills. Trigger on "write the HLD for <epic>", "technical design for this epic", "start an HLD", "design doc for <feature>", or when an epic plus PRD/Figma is given and a design is needed before implementation. Skip for a single small ticket that needs no design (use ticket-enricher for a per-ticket HLD comment instead).
argument-hint: "[epic key(s)] [PRD / Figma links]"
---

# HLD: from epic to a reviewed Technical Design

An HLD is a Confluence page that follows the team's **Technical Design template** section for
section, modelled on a **reference HLD** the team considers good. When unsure how a section
should look, read the reference.

## Company settings

Company facts never live in this skill. Read them from a `## HLD` section in the company
`CLAUDE.md` (e.g. `~/dev/<co>/CLAUDE.md`, set up by `/first-day`). If it's missing, ask once
and offer to write it there:

```markdown
## HLD
- Template: <Confluence URL of the Technical Design template>
- Reference HLD: <URL of a good finished HLD>
- Space: <space key>; parent page: <ask each time | page id>
- Roles to cover: <e.g. admin, editor, viewer>
- Request path: <e.g. "SPA → BFF/gateway → service; browsers never call services directly">
- Stores: <SaaS vs on-prem/self-hosted equivalents, if both exist>
- Deploy config repo: <repo that must change before code, if any>
- Logs / events indexes: <where structured logs and usage events land>
- E2E suites: <path and tags>
- Extra design-info rows: <e.g. Epics, HLD ticket, Implementation tickets>
```

This skill is the orchestrator. Four skills do the parts:

| Skill | Used for |
| --- | --- |
| `epic-breakdown` | Child tickets: HLD → Backend → UI-per-surface → Infra, with "Blocks" links |
| `excalidraw-diagrams` | Every diagram, as an Excalidraw PNG embedded inline plus the `.excalidraw` source |
| `confluence` | Creating and updating the page through the REST API |
| `ticket-enricher` | Optional: the per-ticket design slice in each child ticket |

Required: the Atlassian connector (Jira + Confluence) and the `CONFLUENCE_*` env vars the
`confluence` skill uses (the connector can't upload attachments, so diagrams need the REST API).
The Figma connector is needed when designs exist.

## Phase 1: Gather context (read only)

1. **Jira**: fetch the epic(s) and every child ticket: description, AC, status, assignee. Note whether an HLD ticket exists.
2. **Product inputs**: the PRD, Figma frames (fetch the real frames and record node ids for linking), and any Slack threads the user points to.
   Treat the PM's written decisions as requirements, and date them.
3. **Codebase**: for each layer the feature touches, find what already exists (a code-graph tool such as `graphify` first if the repo has one, then Grep).
   Look for modules to reuse, the pattern to copy (cite the file), and the exact place each change goes.
   Read the relevant `CLAUDE.md` sections; they record the traps.
4. **Gaps**: list requirement ambiguities and ask the user **before** writing, in one batch. Never invent a product decision.

## Phase 2: Ticket structure

Run `epic-breakdown` if the epic has no children or they are vague. Keep the coarse split, never mini-tasks.
The HLD's *Milestones* map 1:1 to these tickets, so settle them first.

## Phase 3: Write the page

Draft in Markdown in the scratchpad (`hld/body_v1.md`), keeping the template's headings and order **exactly**.
Write in plain, short sentences; prefer bullets and tables to paragraphs.

### Design information
The template table, plus the company's extra rows (typically **Epics**, **HLD ticket**, **Implementation tickets** with a one-word scope each).
Reviewers are real `@mentions`; ask the user who reviews.

### Goals
The **why** and the **what**, strategic, one or two paragraphs. Name the customer or meeting that asked for it.

### Functional Requirements
- Group by epic or capability, with the ticket key in the group heading (`**Notes (PROJ-12)**`).
- One behaviour per bullet, phrased "The system will …" or "Users will be able to …", testable as yes/no.
- Always cover: **permissions per role** (the company's role list), **feature-flag gating**
  (what is hidden, and that the backend rejects too), **export** (does a new field get an export column?), and **filters/stats**.
- A requirement that changed carries its decision date: `(decided 2026-10-15)`.

### Technical Requirements
Measurable constraints: latency budgets (p95, *where* it is measured), atomicity, consistency rules, identity, limits.
Always state:
- **Every deployment flavour** (e.g. SaaS and self-hosted): which existing stores it uses, and that no new infra is needed, or what is.
- **Server-side enforcement** of flags and roles.
- **Request path**, per the company setting (e.g. clients only reach services through the gateway).

### Out Of Scope
Explicit bullets, each with a pointer to *Open issues* when there is a path to doing it later.

### Consumers / Customers + Access Pattern
The template table (consumer, Online/Stream/Batch, frequency/volume), then how each consumer queries the data
(by key, by page of ids, filtered, aggregated). Use it to justify indexes and collection shape.

### Detail Design
- **Overview**: one paragraph covering the problem, the approach, and where the code lives.
- **Flow Diagram**: use `excalidraw-diagrams`, **never Mermaid, Miro or ASCII**.
  Normally there are three diagrams: one architecture diagram (client → gateway → service → stores), plus one sequence per main write path.
  Keep each diagram's Python source in the scratchpad (`excal/<name>.py`); scope changes mean re-render and re-upload.
- **Interfaces/ API**: the template table. Before it, state the path conventions once: which service owns the routes,
  any proxy layer, and abbreviations like `…/items/{id}/…`. Give status codes (`404`, `409`, `422`) and what each means.
- **Entities definition**: one table per collection/table (field, type, constraints, comments), plus indexes.
- **Business Logic/Transformations**: one `###` per hard rule (identity merges, validation, limits/policies, backfill).
- **Deployment Plan**: numbered, in dependency order (shared packages → services → gateway → frontend → infra).
  For each step: what ships, config keys, and whether it affects existing services. Call out anything needed in the
  **deploy-config repo** (new URLs, env vars), which must land **before** the code, plus DevOps tickets (buckets, CORS, IAM),
  feature-flag creation, and differences between deployment flavours.
- **Monitoring**: structured logs (name the index), error-rate alerts, latency vs. the TR budget,
  capacity warnings (growth, list sizes), and usage events.
- **Testing**: by layer. Unit, API route tests, frontend, and E2E (name the suite and its tags). List the concrete cases, not "add tests".

### Milestones
One per implementation ticket, with the key, its scope, and an estimate in days. Say whether they ship together behind the flag.

### Open issues
Only real, unresolved items, each with an owner or a ticket. Remove an item once it is decided, and move the decision into the body with its date.

### Rejected Alternatives (after Open issues, even if the template lacks it)
A table: alternative | reason rejected. Add a row whenever a reviewer proposes something that is not taken; this ends repeat debates.

## Phase 4: Publish

1. Show the user the Markdown draft and get approval.
2. Create the page with `confluence` in the configured space (ask for the parent page). Title: `<Feature> HLD`.
3. Render and embed the diagrams with `excalidraw-diagrams` (`confluence_embed.py`).
4. **From now on, never republish the Markdown.** The page has attachments, and the user and reviewers edit it by hand.
   Every later change is: re-fetch the storage body → make text-anchored edits to the affected section → PUT with version + 1.

## Phase 5: Tickets and review

1. Link the HLD from the epic(s) and every child ticket. Optionally run `ticket-enricher` to put each ticket's slice
   (files, API, AC) in its description. Write Jira bodies in Markdown with `[text](url)` links.
2. Post the page to the reviewers (Slack thread or DM) and ask which threads to watch.
3. For each review decision: update the HLD section (dated), add to *Rejected Alternatives* if a proposal was declined,
   update the affected tickets, and reply in the thread. Re-fetch the page and the ticket **right before every edit**:
   people edit them by hand, and a stale full overwrite deletes their changes.

## Checklist before calling it done

- [ ] Every template section is present, in order (optional ones marked N/A rather than deleted)
- [ ] Every functional requirement maps to exactly one ticket and one milestone
- [ ] Roles, flag gating, export, filters, every deployment flavour, and deploy-config changes are all addressed
- [ ] Diagrams are Excalidraw PNGs with their `.excalidraw` sources attached
- [ ] Decisions are dated; Open issues has only open items
- [ ] HLD linked from the epic(s) and all children; reviewers @mentioned
