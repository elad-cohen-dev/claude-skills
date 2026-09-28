---
name: unit-testing
description: Generate high-quality Jest unit tests for NestJS services and controllers in an Nx monorepo. Use this skill whenever the user asks to write, generate, add, or improve unit tests for NestJS code, mentions spec files, test coverage, or wants to test services/controllers. Also trigger when the user says "test this", "add tests", "write specs", or mentions coverage gaps. Always use this skill for any NestJS testing task, even if the user just says "make tests for this file."
allowed-tools: Bash, Read, Edit, Write, Glob, Grep
---

# NestJS Jest Unit Testing (Nx Monorepo)

## Goal
- All tests pass via `nx run {project}:test`
- ≥90% branch coverage
- NestJS testing best practices throughout

## Quick Start

```bash
nx run {project}:test
nx run {project}:test --coverage
```

## Architecture

### Module Setup
Always use `Test.createTestingModule()`:

```typescript
let service: MyService;
let mockDep: jest.Mocked<DepService>;

beforeEach(async () => {
  const module: TestingModule = await Test.createTestingModule({
    providers: [
      MyService,
      { provide: DepService, useValue: mockDepService },
    ],
  }).compile();

  service = module.get<MyService>(MyService);
});
```

### Mocking Rules
- **NEVER** use `jest.mock()` for services — use `.overrideProvider()` and `useValue`
- Mock repositories with `jest.fn()` returning controlled values
- Use `jest.Mocked<T>` for type-safe mocks

```typescript
const mockDepService = {
  findOne: jest.fn(),
  save: jest.fn(),
  delete: jest.fn(),
};
```

### Coverage Requirements
Every test file must cover:
- Happy path
- All `if`/`else` branches
- All `switch` cases
- All `catch` blocks
- Loop iterations (0, 1, many)
- Null/undefined edge cases
- Async rejection paths

## Controller Tests

```typescript
describe('MyController', () => {
  let controller: MyController;
  let service: jest.Mocked<MyService>;

  beforeEach(async () => {
    const module = await Test.createTestingModule({
      controllers: [MyController],
      providers: [{ provide: MyService, useValue: mockMyService }],
    }).compile();

    controller = module.get<MyController>(MyController);
    service = module.get(MyService);
  });

  describe('findOne', () => {
    it('should return entity when found', async () => {
      const entity = { id: 1, name: 'test' };
      service.findOne.mockResolvedValue(entity);
      expect(await controller.findOne('1')).toEqual(entity);
    });

    it('should throw NotFoundException when not found', async () => {
      service.findOne.mockResolvedValue(null);
      await expect(controller.findOne('999')).rejects.toThrow(NotFoundException);
    });
  });
});
```

## Service Tests

```typescript
describe('MyService', () => {
  let service: MyService;
  let repo: jest.Mocked<Repository<MyEntity>>;

  beforeEach(async () => {
    const module = await Test.createTestingModule({
      providers: [
        MyService,
        {
          provide: getRepositoryToken(MyEntity),
          useValue: { findOne: jest.fn(), save: jest.fn() },
        },
      ],
    }).compile();

    service = module.get<MyService>(MyService);
    repo = module.get(getRepositoryToken(MyEntity));
  });

  it('should throw on DB error', async () => {
    repo.findOne.mockRejectedValue(new Error('DB error'));
    await expect(service.findById(1)).rejects.toThrow('DB error');
  });
});
```

## Nx Monorepo Rules
- Place `.spec.ts` files next to source files: `apps/{project}/src/**/*.spec.ts` or `libs/{project}/src/lib/**/*.spec.ts`
- Respect Nx module boundaries — no cross-project imports unless allowed by `tags`
- Run only the relevant project: `nx run {project}:test`

## Formatting
- Use `describe` + `it` naming (not `test`)
- No comments in code unless edge case logic truly needs explanation
- Format with Prettier (matches project config)
- Meaningful test names: `it('should throw when user not found')`

## Self-Validation Checklist
1. Run `nx run {project}:test` — all pass?
2. Run with `--coverage` — ≥90% branches?
3. If <90%: find uncovered branches in coverage report, add tests, repeat
4. Output only `.spec.ts` files
