---
name: codepilot-be-nextjs
description: Autonomous Next.js backend feature development from a Jira ticket — analyzing the Next app, designing the server/API architecture (route handlers, server actions, middleware), implementing with typed validation, writing tests, validating, and committing. Use when a backend ticket targets a Next.js codebase. Usually invoked by the codepilot-be router after framework detection, but can be called directly.
context: fork
agent: general-purpose
allowed-tools: Bash, Read, Edit, Write, Glob, Grep, Skill, mcp__github__search_code, mcp__atlassian__getJiraIssue, mcp__atlassian__editJiraIssue, mcp__atlassian__addCommentToJiraIssue, mcp__atlassian__getTransitionsForJiraIssue, mcp__atlassian__transitionJiraIssue
---

# CodePilot BE (Next.js) — Autonomous Server-Side Feature Development

Full backend loop for **Next.js** server code (App Router route handlers, server
actions, middleware, and the data/service layer behind them). Shared orchestration
phases live in `../_shared/references/codepilot-common.md`.

## Required Inputs
- Jira ticket URL
- (Optional) User availability: `available` | `unavailable`

---

### Phase 1: Retrieve & Parse Ticket
Run **Shared Phase A**. Prioritize `apiContracts[]`, `relatedServices[]`, `databaseChanges[]`.

### Phase 2: Analyze Existing Codebase
- Determine the router style: **App Router** (`app/`, route handlers, server actions,
  `"use server"`) vs **Pages Router** (`pages/api/*`). Match whatever the repo uses.
- Map existing route handlers (`app/**/route.ts`), server actions, `middleware.ts`,
  and the data/service layer (`lib/`, `server/`, ORM clients — Prisma/Drizzle).
- Note runtime targets (`edge` vs `nodejs`), auth (NextAuth/Clerk/custom), and the
  validation library in use (usually `zod`).
- Identify shared utilities and env-var handling.
- **Golden repos & docs**: search for canonical Next.js server patterns and internal
  ADRs (`sourcegraph-search.md`, `documentation-search.md`). Log findings.

### Phase 3: Architecture Planning
```typescript
{
  routerStyle: 'app' | 'pages';
  routes: Array<{
    path: string;                     // e.g. app/api/orders/route.ts
    methods: ('GET'|'POST'|'PUT'|'PATCH'|'DELETE')[];
    runtime?: 'nodejs' | 'edge';
    inputSchema?: string;             // zod schema name
    responseType?: string;
    auth?: string;                    // guard/middleware/session check
  }>;
  serverActions?: Array<{ name, file, inputSchema, revalidates?: string[] }>;
  middleware?: { matcher: string[]; responsibility: string };
  services: Array<{ name, responsibility, dependencies: string[] }>;
  data?: { orm: string; models: string[]; migrations: string[] };
}
```
Write to `architecture.md`. Present 2-4 options for major decisions (route handler vs
server action, edge vs node runtime, caching/revalidation strategy).

### Phase 4: Setup Git Branch
Run **Shared Phase B**.

### Phase 5: Implement — build in this order
**5.1 Validation schemas** — define `zod` schemas for every request body / search param.
**5.2 Data & migrations** (if needed) — Prisma/Drizzle models + migration files;
**never auto-run migrations**.
**5.3 Service / data-access layer** — pure functions or classes in `lib/`/`server/`,
free of framework globals so they stay unit-testable.
**5.4 Route handlers / server actions**:
```ts
// app/api/orders/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { createOrderSchema } from '@/lib/schemas';

export async function POST(req: NextRequest) {
  const parsed = createOrderSchema.safeParse(await req.json());
  if (!parsed.success) {
    return NextResponse.json({ error: parsed.error.flatten() }, { status: 400 });
  }
  const order = await orderService.create(parsed.data);
  return NextResponse.json(order, { status: 201 });
}
```
- Always validate input at the boundary; return typed JSON with correct status codes.
- Server actions: mark `"use server"`, validate input, `revalidatePath`/`revalidateTag` as needed.
**5.5 Middleware / auth** (if needed) — `middleware.ts` with a correct `matcher`.
**5.6 Build validation** — `npm run build` (or `pnpm build`); fix type/lint errors.

### Phase 6: Tests
Use the repo's runner (Vitest or Jest). Unit-test the service/data layer with mocked
deps; test route handlers by invoking the exported `GET`/`POST` with a mock `Request`
and asserting status + body. Cover validation-failure and error paths.

### Phase 7: Validation
Verify: acceptance criteria met; every route validates input and returns typed
responses with correct status codes; auth enforced where required; no secrets leaked to
the client bundle (server-only code stays server-only); build passes.

### Phase 8: Commit & Push
Run **Shared Phase C**.

### Phase 9: CR Review & Fix
Run **Shared Phase D**.

---

## Next.js Key Rules
(In addition to the Shared Key Rules in `codepilot-common.md`.)
- Validate every request boundary (zod `safeParse`) — never trust client input.
- Keep business/data logic in a framework-agnostic service layer, not inside route handlers.
- Never leak secrets or server-only imports into client components; respect `"use server"`/`"use client"`.
- Return proper HTTP status codes and typed JSON; handle errors explicitly.
- Choose the runtime deliberately (`edge` only when the code is edge-safe).
- Revalidate caches (`revalidatePath`/`revalidateTag`) after mutations.
- Never auto-run database migrations — require user approval.
