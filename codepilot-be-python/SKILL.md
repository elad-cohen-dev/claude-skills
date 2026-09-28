---
name: codepilot-be-python
description: Autonomous Python backend feature development from a Jira ticket — detecting the web framework (FastAPI, Django, or Flask), designing the API architecture, implementing routers/views/services with schema validation, writing pytest tests, validating, and committing. Use when a backend ticket targets a Python codebase. Usually invoked by the codepilot-be router after framework detection, but can be called directly.
context: fork
agent: general-purpose
allowed-tools: Bash, Read, Edit, Write, Glob, Grep, Skill, mcp__github__search_code, mcp__atlassian__getJiraIssue, mcp__atlassian__editJiraIssue, mcp__atlassian__addCommentToJiraIssue, mcp__atlassian__getTransitionsForJiraIssue, mcp__atlassian__transitionJiraIssue
---

# CodePilot BE (Python) — Autonomous Backend Feature Development

Full backend loop for **Python** web services. Auto-detects the framework
(FastAPI / Django / Flask) and adapts idioms accordingly. Shared orchestration
phases live in `../_shared/references/codepilot-common.md`.

## Required Inputs
- Jira ticket URL
- (Optional) User availability: `available` | `unavailable`

---

### Phase 1: Retrieve & Parse Ticket
Run **Shared Phase A**. Prioritize `apiContracts[]`, `relatedServices[]`, `databaseChanges[]`.

### Phase 2: Analyze Existing Codebase
- **Detect the web framework**: `fastapi` / `django` / `flask` in `pyproject.toml` /
  `requirements.txt`, or `manage.py` (Django), `app = FastAPI()` / `Flask(__name__)`.
- **Detect tooling**: dependency manager (Poetry / uv / pip-tools), test runner
  (pytest), linter/formatter (ruff / black / flake8), type checker (mypy / pyright),
  ORM (SQLAlchemy / Django ORM / Tortoise), migrations (Alembic / Django migrations).
- Map existing routers/views, schemas/serializers, services, and settings/env handling.
- **Golden repos & docs**: search for canonical patterns and internal ADRs
  (`sourcegraph-search.md`, `documentation-search.md`). Log findings.

### Phase 3: Architecture Planning
```python
{
  "framework": "fastapi | django | flask",
  "routers": [ { "path": "...", "methods": ["GET","POST"], "request_schema": "...",
                 "response_schema": "...", "auth": "..." } ],
  "schemas": [ { "name": "...", "kind": "request|response", "validation": ["..."] } ],
  "services": [ { "name": "...", "responsibility": "...", "deps": ["..."] } ],
  "models": [ { "name": "...", "table": "...", "fields": ["..."], "relations": ["..."] } ],
  "migrations": ["..."],
  "settings": ["env vars / config keys"]
}
```
Write to `architecture.md`. Present 2-4 options for major decisions (sync vs async,
ORM choice, schema/serializer strategy, background tasks vs queue).

### Phase 4: Setup Git Branch
Run **Shared Phase B**.

### Phase 5: Implement (framework-appropriate)
**5.1 Schemas / validation**
- *FastAPI*: Pydantic models for request/response; declare them as endpoint params.
- *Django (REST)*: DRF serializers with field-level validation.
- *Flask*: Pydantic or marshmallow schemas; validate before touching services.
**5.2 Models & migrations** (if needed) — SQLAlchemy/Django models; generate Alembic /
`makemigrations` files; **never auto-run migrations**.
**5.3 Service layer** — pure, framework-agnostic functions/classes so they unit-test
without the web stack; keep views/routers thin.
**5.4 Routers / views**:
```python
# FastAPI example
from fastapi import APIRouter, Depends, HTTPException
router = APIRouter(prefix="/orders", tags=["orders"])

@router.post("", response_model=OrderOut, status_code=201)
async def create_order(payload: OrderCreate, svc: OrderService = Depends(get_order_service)):
    return await svc.create(payload)
```
- Use dependency injection (`Depends` / Django DI patterns) for services and auth.
- Raise framework-native errors (`HTTPException` / DRF exceptions), not bare returns.
**5.5 Auth / middleware** (if needed) — dependencies, decorators, or middleware.
**5.6 Static checks** — run the repo's linter/formatter/type checker
(`ruff check . && mypy .` or equivalent); fix issues.

### Phase 6: Tests
Write `pytest` tests: unit-test the service layer with mocked deps; test endpoints via
the framework's test client (`TestClient` for FastAPI, Django/DRF `APIClient`, Flask
`test_client`). Cover validation errors and edge cases. Run `pytest -q`.

### Phase 7: Validation
Verify: acceptance criteria met; every endpoint validates input and returns typed
responses with correct status codes; auth enforced; type checks and lint pass; tests green.

### Phase 8: Commit & Push
Run **Shared Phase C**.

### Phase 9: CR Review & Fix
Run **Shared Phase D**.

---

## Python Key Rules
(In addition to the Shared Key Rules in `codepilot-common.md`.)
- Validate every request boundary with Pydantic / DRF serializers / marshmallow.
- Keep business logic in a framework-agnostic service layer; keep views/routers thin.
- Match the repo's existing style, dependency manager, and type-checking strictness.
- Use type hints everywhere; keep `mypy`/`pyright` clean.
- Raise framework-native HTTP errors with correct status codes; don't swallow exceptions.
- Manage config via settings/env objects — never hardcode secrets.
- Never auto-run database migrations — require user approval.
- Respect sync vs async boundaries (don't block the event loop in async FastAPI code).
