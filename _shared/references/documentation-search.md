# Internal Documentation Search Guide

Reference document for searching Confluence and internal docs before making design decisions.
Any skill can reference this guide to ensure implementations align with documented standards.

## When to Search

Search internal documentation when:
- Learning about team-specific standards or patterns
- Answering "how to" questions about implementations
- Uncertain about team best practices for a specific case
- Need authoritative guidance on architectural decisions
- References to internal processes or workflows
- Questions about team conventions or policies

## When to Skip

Skip searching when:
- Answering general programming questions (use your knowledge)
- Information is already visible in current context
- Simple clarifications that don't require standards
- External technology documentation is more appropriate
- Time-sensitive trivial questions

## How to Search Confluence

Use the `mcp__atlassian__searchConfluenceUsingCql` tool with CQL (Confluence Query Language).

### Basic CQL Queries

**Full-text search:**
```
text ~ "search term"
```

**Search within a specific space:**
```
space = "ENGINEERING" AND text ~ "search term"
```

**Search by title:**
```
title ~ "API design"
```

**Search recently updated content:**
```
text ~ "search term" AND lastModified > now("-30d")
```

**Combine conditions:**
```
space = "ENGINEERING" AND text ~ "NestJS guard" AND type = "page"
```

### Query Best Practices

#### 1. Use Short, Focused Keywords

**Good:**
- "NestJS dependency injection"
- "Angular component testing"
- "GitHub Actions deployment"
- "API authentication patterns"

**Avoid:**
- "How do we handle dependency injection in NestJS services?" (too verbose)
- "best practices" (too generic)
- "guidelines" (too vague)
- Long sentences or questions

#### 2. One Aspect Per Query

For complex topics, make **2-3 separate focused queries** rather than one complex query.

Instead of: `"REST API endpoint authentication validation error handling"`

Use separate queries:
1. `"REST API authentication"`
2. `"request validation patterns"`
3. `"API error handling"`

#### 3. Include Technology Names

Always include the specific technology or framework:

**Good:** "NestJS middleware patterns", "Angular routing guards"
**Avoid:** "middleware patterns", "routing" (too generic)

#### 4. Focus on What, Not Why

**Good:** "database connection pooling", "JWT token validation"
**Avoid:** "why use connection pooling", "benefits of JWT"

### Common Search Scenarios

| Scenario | CQL Query |
|----------|-----------|
| Find ADRs | `title ~ "ADR" AND space = "ENGINEERING"` |
| Find API guidelines | `text ~ "API design" OR text ~ "API guidelines"` |
| Find service docs | `title ~ "<service-name>"` |
| Find runbooks | `text ~ "runbook" AND text ~ "<topic>"` |
| Find HLD docs | `title ~ "HLD" AND text ~ "<feature-name>"` |
| Find conventions | `text ~ "convention" OR text ~ "style guide"` |

## Search Strategy for Different Tasks

### Answering Questions
1. Identify the core technology/pattern being asked about
2. Extract 2-3 key terms from the question
3. Search once with focused keywords
4. Evaluate results — do they answer the question?
5. If not found — rely on general knowledge or code examples

### Code Review
1. Identify technologies introduced in the PR
2. Search for each technology separately (if multiple)
3. Look for integration patterns if connecting systems
4. Stop after 2-3 searches — don't over-search

### Implementation
1. Before starting — search for relevant patterns
2. One query per major technology/pattern
3. Search for integration patterns if connecting multiple systems
4. Treat results as source of truth for standards

## Interpreting Results

### When Results Are Found
- **Treat as authoritative** — internal docs are the source of truth
- **Follow patterns exactly** — don't deviate without good reason
- **Reference in your response** — provide links when available
- **Extract key points** — summarize relevant sections

### When Results Are Sparse
- **Don't force it** — lack of results is meaningful
- **Check golden repos** — code examples may exist there
- **Don't fabricate** — don't claim standards exist if not found
- **Fall back to general knowledge** — use standard practices

### When Results Are Contradictory
- **Prefer newer documentation** — check dates if available
- **Use context** — repository or team-specific may vary
- **Note the contradiction** — mention to user if significant
- **Ask for clarification** — when in doubt
