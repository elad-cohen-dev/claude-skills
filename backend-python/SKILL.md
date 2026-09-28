---
name: backend-python
description: |
  House rules for backend Python services in a monorepo (FastAPI apps under `apps/<app>`
  and shared layers under `packages/py-shared/{core,infra,modules}`).
  TRIGGER when the user is writing or modifying Python code in those paths,
  preparing to commit / push / finish a feature, reviewing a backend PR, writing
  pytest tests/fixtures, adding/refactoring a Pydantic model, touching a
  dependency-injector container, or wiring a FastAPI route. Also run as a
  pre-commit / end-of-session checklist on any Python change to those paths.
  Skip for frontend, Helm/chart, or pure infra (Terraform, GitHub Actions) edits.
allowed-tools: Read, Edit, Write, Bash, Grep, Glob
---

# Backend Python — house rules

Operational summary distilled from real PR reviews + CI incidents. Apply it
before saying "done" on any backend Python change.

## 0. Pre-commit / end-of-session checklist (run every time)

Tick these top-to-bottom. Each line is something CI or the reviewer **will**
catch otherwise:

1. **Run tests in every package you touched**, not just the app you ran in your
   editor.
   ```bash
   cd apps/<app> && uv run pytest tests/ -q
   cd packages/py-shared/modules && uv run pytest -q
   cd packages/py-shared/core && uv run pytest -q
   cd packages/py-shared/infra && uv run pytest -q
   ```
   Or, before push, run the same script CI runs:
   ```bash
   ./run_tests.sh
   ```
   `pytest -q` and `pytest tests/` collect tests differently — the CI invocation
   is `pytest tests/`. Reproduce it.
2. **No dead code.** Grep your diff for unused imports, exception classes,
   constants, helpers. If a name has zero references after the refactor, delete
   it — don't leave it "for later" and don't add a `_` prefix.
3. **No duplicate models.** A wire DTO that has the exact same fields and
   constraints as a domain Pydantic model is one class, not two. Type the route
   body as the domain model and pass it through.
4. **Type hints on public DI / handler signatures.** A FastAPI route's `user`
   dep, app-service execute return value, and command/query carriers all need
   real types, not bare `=Depends(...)`.
5. **Re-read the diff against this skill.** Sections 1–8 below are the long
   form of common review hits.

## 1. Validation lives in Pydantic, not in the service

If a service method starts with a sequence of `if field is None: raise` or
"normalize this dict before using it", push that into the Pydantic model the
service receives.

**Bad:**

```python
async def update_by_key(self, *, key, patch_dict, actor_email):
    for field in ("name", "status", "scope"):
        if field in patch_dict and patch_dict[field] is None:
            raise InvalidFlagStatusException(...)
    for field in ("targets", "excludes"):
        if field in patch_dict:
            if patch_dict[field] is None:
                patch_dict[field] = {}
            FeatureFlag.validate_claims_map(patch_dict[field])
            patch_dict[field] = FeatureFlag.normalize_claims_map(patch_dict[field])
    ...
```

**Good:** the same rules on the input model + the canonical `UNSET` sentinel
from `your_pkg.core.domain.value_objects` for the tri-state "not provided / null /
value" distinction. Service becomes 4 lines.

```python
from your_pkg.core.domain.value_objects import UNSET

class FeatureFlagUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(default=UNSET, max_length=NAME_MAX_LENGTH)            # null → 422
    description: str | None = Field(default=UNSET, max_length=DESC_MAX)     # null → clear
    status: FlagStatus = UNSET                                              # null → 422
    targets: ClaimsMap = UNSET                                              # null → 422; {} clears

    @field_validator("targets", "excludes", mode="before")
    @classmethod
    def _validate_and_normalize_claims_map(cls, value):
        if isinstance(value, dict):
            FeatureFlag.validate_claims_map(value)
            return FeatureFlag.normalize_claims_map(value)
        return value
```

Then the service iterates fields and skips UNSET:

```python
patch_dict = {
    f: getattr(patch, f)
    for f in FeatureFlagUpdate.model_fields
    if getattr(patch, f) is not UNSET
}
```

Why:

- Validators run at FastAPI body-validation time → 422 with detail.
  Imperative checks mid-service produce uglier errors and run after work.
- `UNSET` as the default makes "field not provided" type-level explicit and
  separates it from "field explicitly null" (which only nullable fields
  accept). No reliance on Pydantic's internal `model_fields_set`.
- `extra="forbid"` catches typo'd field names at the boundary.
- The shared `Sentinel` class already wires a custom Pydantic schema, so
  `name: str = UNSET` validates `null` against `str` (rejects) without you
  writing a `_reject_null` validator.

## 2. Domain helpers go _on_ the entity

No free `_helper_foo(entity, ...)` functions for domain rules. They live on
the model as `@staticmethod` / `@classmethod`. Inline generic Python ops
where they appear once.

**Bad:**

```python
def _dedup_preserving_order(values: list[str]) -> list[str]:
    seen = set(); out = []
    for v in values:
        if v not in seen: seen.add(v); out.append(v)
    return out
```

**Good:** `list(dict.fromkeys(values))` at the call site.

## 3. Partial-update pattern: `model_copy` + `update_fields`

For PATCH-style updates, never dump-and-rebuild the whole entity. The
canonical pattern is:

```python
patch_dict = patch.model_dump(exclude_unset=True)
updated = existing.model_copy(
    update={**patch_dict, "updated_at": now, "updated_by": actor_email},
)
update_fields = set(patch_dict) | {"updated_at", "updated_by"}
await self._repository.update(updated, upsert=False, update_fields=update_fields)
```

- `exclude_unset=True` gives you exactly the fields the caller touched.
- `update_fields` becomes the Mongo `$set` mask — fields the caller didn't
  touch keep their stored value.

No `_MUTABLE_FIELDS` allowlist; no `or k == "description"` carve-outs; no
re-validating-via-rebuild.

## 4. Async repo patterns

**First-or-none lookup:**

```python
return await anext(self._dao.find(query={"key": key}, limit=1), None)
```

Not `async for item in find(...): return item`. One line, no sentinel, no
trailing `return None`.

**AsyncGenerator from a service:** consume at the last mile, not in the
middle of the pipeline. See `[[guideline_vertical_filters]]` if you exist
in a future where that memory is reachable.

## 5. Role checks: use `require_role`, not bespoke decorators

We have `your_pkg.core.infra.fast_api.iam.require_role(role)` and the
`ADMIN_ROLE` constant. Use them. Do not invent `@require_admin` /
`is_admin_caller` shims for new modules — every consumer of `user.roles`
should agree on the source of truth.

The decorator wrapper requires `request: Request` in the handler signature.
That's expected; ignore the basedpyright "request is not accessed" warning
on otherwise-clean handlers.

## 6. Response shaping: classmethods on the response model

The router constructs response DTOs through a `from_entity` classmethod on
the DTO, not a free helper:

```python
class FeatureFlagResponse(_FeatureFlagBaseDTO):
    created_at: datetime
    ...

    @classmethod
    def from_entity(cls, flag: FeatureFlag) -> "FeatureFlagResponse":
        return cls.model_validate(flag, from_attributes=True)
```

Use `model_validate(entity, from_attributes=True)` rather than
`cls(**entity.model_dump())` — fewer round-trips, preserves types.

## 7. JWT claim access has fallbacks

Never `request.state.user.claims["email"]` — JWTs without an `email` claim
raise `KeyError` → 500. Use the `preferred_username` fallback (it's
email-shaped in our realm):

```python
def _actor_email(request: Request) -> str:
    claims = getattr(request.state.user, "claims", {}) or {}
    return claims.get("email") or claims.get("preferred_username") or ""
```

If the resulting value is empty, downstream `EmailStr` validation produces
a 422 — strictly better than a 500.

## 8. Constants > duplicated literals

If a `max_length`, regex, or role name appears in both a DTO and the
domain entity, extract a module constant in the domain module (`NAME_MAX_LENGTH`,
`KEY_PATTERN`, `ADMIN_ROLE`) and import it. The next change that bumps the
limit then has one place to edit.

---

# Tests — house rules

## T1. Fixtures live in the closest applicable `conftest.py`

Look at the directory tree first. If a fixture is used by app-level _and_
api-level tests, it goes in the root `tests/conftest.py`. If only app
tests need it, `tests/app/conftest.py`. Never copy-paste the same fixture
into two `conftest.py`s — pytest's hierarchical discovery is for this.

When in doubt: try moving the fixture _up_ one level and see if any tests
break. If they don't, leave it up.

## T2. One expected object, one assertion

Reviewers expect:

```python
expected = [{"key": "x", "name": "X"}, ...]
actual = response.json()
assert actual == expected
```

Not:

```python
assert response.status_code == 200
assert len(body) == 2
assert body[0]["key"] == "x"
assert "id" not in body[0]
```

When you genuinely need to assert two independent things, tuple them:

```python
assert (response.status_code, response.json()) == (200, expected)
```

(Side-effect assertions like `mock.execute.assert_called_once_with(...)`
are exempt — they're checking interaction, not return value.)

## T3. Parametrize copy-paste

If two tests differ only in input or expected status, that's a
`@pytest.mark.parametrize` (with `pytest.param(..., id="...")` for
readable failure ids), not two functions.

## T4. No section dividers, no narrative comments

`# ----- evaluation algorithm -----` style separators don't survive
reviews. Group tests by file or by class instead.

## T5. Validation tests belong at the validation layer

If you push a check into Pydantic, the test that exercises the check
moves to the Pydantic layer too:

- "service rejects unknown claim key" → test the DTO directly
  (`pytest.raises(ValidationError): CreateFeatureFlagRequest(...)`) or the
  router (`response = client.post(...); assert response.status_code == 422`).
- Don't keep a service-level `pytest.raises(MyException)` after the check
  has moved upstream — it's testing yesterday's code path.

## T6. End-to-end smoke through the real DI container

Keep at least one integration test per route that runs against the real
service + mongomock (no `applications.X.override(...)`). It catches DI
wiring mistakes and DAO/projection drift that mocked tests miss.

---

# Container / dependency-injector gotchas

## D1. Recursion limit _before_ the Container import

Class-definition of an `apps/<app>/.../config/container.py` `Container`
triggers a deepcopy walk through every nested `DependenciesContainer`
wired into the shared `ModulesContainer`. On Linux runners this exceeds
Python's default 1000-deep stack.

If your `tests/conftest.py` imports `Container`, set the limit on the
very first executable line — before the project imports:

```python
# ruff: noqa: E402
import sys
sys.setrecursionlimit(10000)

# ... project imports below ...
from your_app.config.container import Container
```

A `sys.setrecursionlimit` call _after_ the import is too late. CI on
PR #301 burned an iteration on exactly this.

## D2. Don't introduce new shims that wrap shared providers

`ApplicationContainer` already knows how to wire `feature_flags=modules.feature_flags`.
A new module should add one provider to the shared `ModulesContainer`
plus one app-service `Factory` in `ApplicationContainer`. Don't invent a
new intermediate container if the pattern is "shared service →
application service → route".

---

# What this skill is _not_

- It does not replace a senior reviewer. New design choices still need a
  human conversation; this captures the post-review cleanups so you don't
  spend a review cycle on them.
- It does not cover frontend, Helm, or Terraform — different repos,
  different conventions.
- It is not a style guide for Python in general — assume `ruff` /
  `ruff-format` (configured in repo) are the formatter. Focus on
  patterns the formatter can't enforce.
