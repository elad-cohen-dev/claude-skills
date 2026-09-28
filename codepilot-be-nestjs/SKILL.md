---
name: codepilot-be-nestjs
description: Autonomous NestJS backend feature development from a Jira ticket — analyzing the Nest project, designing API architecture, implementing controllers/services/modules/DTOs, writing Jest unit tests, validating, and committing. Use when a backend ticket targets a NestJS/TypeScript codebase. Usually invoked by the codepilot-be router after framework detection, but can be called directly. Trigger on "implement this NestJS ticket" or a backend Jira URL in a Nest repo.
context: fork
agent: general-purpose
allowed-tools: Bash, Read, Edit, Write, Glob, Grep, Skill, mcp__github__search_code, mcp__atlassian__getJiraIssue, mcp__atlassian__editJiraIssue, mcp__atlassian__addCommentToJiraIssue, mcp__atlassian__getTransitionsForJiraIssue, mcp__atlassian__transitionJiraIssue
---

# CodePilot BE (NestJS) — Autonomous Backend Feature Development

Full backend development loop for **NestJS / TypeScript** codebases, from Jira
ticket to PR. Shared orchestration phases (ticket retrieval, branch, commit, CR)
live in `../_shared/references/codepilot-common.md` — run them where noted.

## Required Inputs
- Jira ticket URL
- (Optional) User availability: `available` | `unavailable`

---

### Phase 1: Retrieve & Parse Ticket
Run **Shared Phase A** (`codepilot-common.md`). Backend fields to prioritize:
`apiContracts[]` (Swagger/OpenAPI links), `relatedServices[]`, `databaseChanges[]`.

### Phase 2: Analyze Existing Codebase & API Contracts
Before designing anything, understand the landscape:
- Scan the existing NestJS structure (`apps/`, `libs/`, module boundaries).
- Identify modules, services, and controllers related to the ticket.
- Review existing API contracts (Swagger decorators, DTOs, OpenAPI specs).
- Check for existing database entities/schemas related to the feature.
- Identify shared libraries, utilities, and common patterns already in use.

Store as `existingContext`.

**2b. Golden repos** — search the backend golden repo for canonical NestJS patterns
(guards, interceptors, DTOs, migrations) via `mcp__github__search_code` / `gh search code`
(see `sourcegraph-search.md`). Search shared libraries for reusable utilities.
Store in `existingContext.goldenPatterns`.

**2c. Internal docs** — search Confluence for ADRs and API-design guidelines
(see `documentation-search.md`). Log references.

### Phase 3: Architecture Planning
Switch to architect mode. Produce:
```typescript
{
  modulePath: string;
  module: { name, imports: string[], controllers: string[], providers: string[], exports: string[] };
  controllers: Array<{ name, basePath, endpoints: Array<{
    method: 'GET'|'POST'|'PUT'|'PATCH'|'DELETE'; path; description;
    params?; queryParams?; requestBody?; responseBody?; guards?; interceptors?; pipes?;
  }> }>;
  services: Array<{ name, responsibility, dependencies: string[], methods: string[] }>;
  dtos: Array<{ name, purpose: 'request'|'response'|'internal', validationRules: string[] }>;
  entities: Array<{ name, tableName, fields: string[], relations: string[] }>;
  guards: string[]; interceptors: string[]; pipes: string[]; migrations: string[];
}
```
Write the plan to `architecture.md`. **If a major architectural decision is needed**
(module placement, schema design, sync vs async, REST vs event-driven) → present 2-4
options to the user before proceeding.

### Phase 4: Setup Git Branch
Run **Shared Phase B** (`codepilot-common.md`).

### Phase 5: Implement — build in this order
**5.1 DTOs & Validation** — request/response DTOs with `class-validator` +
`@nestjs/swagger` decorators (`@ApiProperty`, `@IsString`, `@IsNotEmpty`, …).
**5.2 Entities & Migrations** (if needed) — TypeORM/Prisma/Mongoose entities per the
plan; generate and review migrations; **never auto-run migrations**.
**5.3 Service layer** — `@Injectable()` services; keep controllers thin, services fat;
constructor injection; async/await.
**5.4 Controller layer** — `@Controller()` + `@ApiTags`/`@ApiOperation`/`@ApiResponse`;
guards via `@UseGuards()`; delegate to services.
**5.5 Guards / Interceptors / Pipes** (if needed).
**5.6 Module registration** — `@Module({ imports, controllers, providers, exports })`;
register in the parent module. Export deliberately.
**5.7 Build validation** — `npx nx build <project>` or `npm run build`; fix TS errors.

### Phase 6: Unit Tests
Invoke `/unit-testing` for each new service and controller, or write Jest tests with
`@nestjs/testing` `Test.createTestingModule()`. Mock DB/HTTP/queue dependencies; cover
error paths and edge cases. Ensure every service/controller has a `.spec.ts` and
`npx jest --passWithNoTests` passes. **If rejected** → fix and re-run.

### Phase 7: API Validation
Verify: all acceptance criteria met; endpoints match the plan; Swagger decorators on
every endpoint; DTOs have validation decorators; error responses follow project
conventions; no circular deps. Final: `npx nx build <project> && npx nx test <project>`.

### Phase 8: Commit & Push
Run **Shared Phase C** (`codepilot-common.md`).

### Phase 9: CR Review & Fix
Run **Shared Phase D** (`codepilot-common.md`).

---

## NestJS Key Rules
(In addition to the Shared Key Rules in `codepilot-common.md`.)
- Keep controllers thin — business logic belongs in services.
- Always use DTOs for request/response — never expose raw entities.
- `class-validator` on all endpoint inputs; Swagger/OpenAPI decorators on every endpoint.
- Never auto-run database migrations — always require user approval.
- Prefer constructor injection; avoid circular deps (use `forwardRef()` only as a last resort).
- Handle errors with NestJS exception filters, not try/catch in controllers.
- Prefer event-based communication (EventEmitter2, queues) for cross-module side effects.

## NestJS Best Practices (docs.nestjs.com)
- **Config**: `@nestjs/config` `ConfigModule.forRoot()`; validate env vars with a
  `validationSchema` (class-validator/class-transformer).
- **Modular design**: each feature is a self-contained module (controllers, services, DTOs).
- **Separation of concerns**: controllers = HTTP, services = business logic, repositories = data.
- **Guards** for auth/RBAC; **interceptors** for logging/caching/response shaping;
  **pipes** (`ValidationPipe`) for DTO validation; **exception filters** to centralize errors.
- **Testing**: unit-test every service/controller; `supertest` for e2e against real endpoints.
- **Build**: enable `"incremental": true`, exclude test files from prod builds, tree-shake imports.
