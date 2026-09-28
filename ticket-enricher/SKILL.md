---
name: ticket-enricher
description: Enrich Jira tickets with High-Level Design (HLD) documents for every ticket in a Jira Epic. Use this skill when the user wants to add architectural documentation to Jira tickets, generate HLD documents for an epic, or prepare tickets for implementation with technical blueprints. Trigger on "enrich tickets", "add HLD to epic", "create architecture docs for tickets", "prepare tickets for development", or when a Jira epic key is provided and the user wants technical planning added to each child ticket.
context: fork
agent: general-purpose
allowed-tools: Bash, Read, Glob, Grep, mcp__atlassian__getJiraIssue, mcp__atlassian__editJiraIssue, mcp__atlassian__searchJiraIssuesUsingJql, mcp__atlassian__addCommentToJiraIssue, mcp__atlassian__getAccessibleAtlassianResources
---

# Ticket Enricher — HLD Generation for Jira Epics

Adds High-Level Design (HLD) documents to every Jira ticket in an Epic, backed by architectural analysis of the existing codebase.

## Required Inputs
- Jira Epic URL or list of ticket keys
- Optional: Git repo context or file tree

## Workflow

### Step 1: Retrieve Tickets

Use Jira MCP to fetch all child tickets from the epic:
- Retrieve only: ticket key, title, description
- Skip tickets marked: "Duplicate", "Cancelled", "Blocked"
- Skip tickets that already have an HLD link (unless `forceRewrite=true`)

Store as `ticketList[]`.

### Step 2: Process Each Ticket

For each `ticketKey` in `ticketList`:

#### A. Architectural Analysis

Investigate the codebase using Read, Glob, and Grep tools:
- Existing feature dependencies in the codebase
- Component/module hierarchy relevant to this ticket
- Whether functionality already exists or must be created
- Where in the codebase this should be implemented

Plan using Angular 17 best practices:
- Generic, modular, secure architecture
- Performance optimizations
- Code reuse strategies
- Minimal new dependencies

#### B. HLD Structure to Generate

Produce a document with these sections:

```
Summary
[What this task achieves and why it matters]

Relevant Modules, Components & Services
[Existing and new code involved]

Data Flow & Interactions
[How data moves through the system for this feature]

Security & Validation Notes
[Auth checks, input validation, sensitive data handling]

Performance & UX Concerns
[Loading states, lazy loading, optimistic updates, caching]

Testing Entry Points
[Key scenarios to unit/integration test]

Code Structure
[Exact file paths and what changes go where]
```

#### C. Update Jira Ticket

Add HLD content directly to the Jira ticket description or as a comment via Jira MCP.

### Step 3: Wrap Up

Report:
```
Processed: X tickets
Skipped: Y tickets (reason)

Ticket links:
- PROJ-123: HLD added
- PROJ-124: HLD added
...

All tickets in Epic {epicKey} now enriched with architectural HLDs.
```

## Architecture Principles to Apply

### Angular 17 Best Practices
- Standalone components where appropriate
- Signal-based state management
- Lazy-loaded feature modules
- OnPush change detection strategy
- Smart/dumb component pattern

### Code Quality Guidelines
- Single responsibility per component/service
- Interface-driven development
- Shared module extraction for reusable logic
- No circular dependencies

### Security Patterns
- Input sanitization
- Role-based access guards
- HTTP interceptors for auth headers
- Environment variable usage (never hardcode secrets)

## Skip Conditions
Do not generate HLD for:
- Tickets with status: Duplicate, Cancelled, Blocked
- Tickets already containing "HLD Document:" in description (unless `forceRewrite=true`)
- Sub-tasks (create HLD on parent story instead)
