# Python Review Checklist

Framework-specific review checklist for Python services (FastAPI + Pydantic).
Apply this checklist when reviewing PRs that contain FastAPI routers, Pydantic models, or service/repository code.

## Checklist

For each item, report **PASS**, **FAIL**, or **N/A**. Explain every FAIL and provide a corrected snippet.

### Routing & Endpoints
- [ ] Endpoints live on an `APIRouter` with a `prefix` and `tags`, not registered ad-hoc on the app
- [ ] Request bodies and query/path params are typed with Pydantic models or explicit primitive types — no untyped `dict`/`Any` payloads
- [ ] Every endpoint declares a `response_model` (or explicit return type) so the response shape is enforced, not implicit
- [ ] Appropriate `status_code` set on the route decorator (e.g. `202` for accepted-async-work, `201` for creation) rather than defaulting to `200` everywhere

### Pydantic Models
- [ ] Models validate meaningfully (constrained types, `Field` constraints) rather than accepting anything and relying on downstream checks
- [ ] No mutable default arguments/fields (`= []`, `= {}`) — uses `Field(default_factory=...)`
- [ ] Models used at the API boundary are distinct from internal/domain models where the shapes diverge (no leaking internal-only fields into responses)

### Dependency Injection
- [ ] Dependencies (config, clients, loggers, repositories) are obtained via `Depends(...)` / the DI container — not constructed inline in the handler or imported as global singletons
- [ ] Shared resources (DB connections, HTTP clients) are injected, not instantiated per-request

### Async & Concurrency
- [ ] Handlers that do I/O (DB, HTTP, queue) are `async def` and `await` their calls — no blocking calls (`requests`, sync DB drivers) inside an async handler
- [ ] Background/fire-and-forget work uses the app's task/buffer mechanism rather than un-awaited coroutines

### Error Handling
- [ ] Expected failure cases raise `HTTPException` (or the app's standard exception type) with an appropriate status code — not a bare `Exception`/`assert`
- [ ] Exceptions from downstream calls (HTTP, DB) are caught and translated, not left to bubble up as raw 500s with internal details exposed
- [ ] No silent `except Exception: pass` swallowing errors

### Logging
- [ ] Uses the injected structured logger — not `print()`
- [ ] Log calls pass structured context via `extra={...}` rather than string-interpolating values into the message
- [ ] No PII, tokens, or full request/response bodies logged

### Security
- [ ] Trust boundaries are explicit — if an endpoint intentionally trusts an upstream-authenticated header (e.g. a user-id header from an internal gateway), that trust assumption is documented in a comment, not assumed implicitly
- [ ] No secrets/credentials hardcoded or read from anywhere but config/env
- [ ] Inputs used in external calls (queries, file paths, shell commands) are validated/escaped

### Testing
- [ ] New endpoints/services have `pytest` tests (async tests using `pytest-asyncio`)
- [ ] External calls are mocked (e.g. `aioresponses` for HTTP) rather than hitting real services in tests
- [ ] Tests cover the error path, not just the happy path

### Style & Tooling
- [ ] Code is `ruff`-clean (lint + format) — no obvious violations a pre-commit run would catch
- [ ] Type hints present on function signatures (params and return type)

## Correct Endpoint Example

```python
router = APIRouter(prefix="/events", tags=["Events"])


@router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=IngestEventResponse)
@inject
async def ingest_event(
    body: ClientEvent,
    buffer: AsyncEventBuffer = Depends(Provide[Container.events.buffer]),
    logger: Logger = Depends(Provide[Container.logger]),
) -> IngestEventResponse:
    try:
        await buffer.add(build_event(body))
    except BufferFullError as exc:
        raise HTTPException(status_code=503, detail="Event buffer full") from exc

    logger.debug("Accepted analytics event", extra={"event_type": body.event_type})
    return IngestEventResponse(accepted=True)
```
