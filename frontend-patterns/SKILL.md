---
name: frontend-patterns
description: Angular frontend development patterns, conventions, and best practices. Use when building Angular components, services, directives, pipes, or routing. Covers standalone components, signals, RxJS patterns, NgRx, forms, and team-specific conventions.
allowed-tools: Read, Edit, Write, Glob, Grep, Bash
---

# Angular Frontend Patterns

Best practices and conventions for Angular development.

## Component Architecture

### Prefer Standalone Components
```typescript
@Component({
  selector: 'app-my-component',
  standalone: true,
  imports: [CommonModule, RouterModule, MyOtherComponent],
  templateUrl: './my-component.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MyComponent {}
```

- Always use `standalone: true` for new components
- Always set `changeDetection: ChangeDetectionStrategy.OnPush`
- Import only what the template needs — no `SharedModule` catch-alls

### Smart vs Dumb Components
- **Smart (container)**: Inject services, manage state, handle side effects
- **Dumb (presentational)**: Accept inputs, emit outputs, no service injection
- Keep dumb components pure — same inputs → same rendered output

### Component File Structure
```
my-feature/
├── my-feature.component.ts
├── my-feature.component.html
├── my-feature.component.scss
├── my-feature.component.spec.ts
└── index.ts   ← public API barrel export
```

---

## Signals (Angular 17+)

Prefer signals over BehaviorSubject for local component state:

```typescript
// ✅ Signals
export class MyComponent {
  count = signal(0);
  doubled = computed(() => this.count() * 2);

  increment() {
    this.count.update(c => c + 1);
  }
}

// ❌ Avoid for simple local state
private count$ = new BehaviorSubject(0);
```

Use `toSignal()` to bridge observables into signals:
```typescript
data = toSignal(this.service.getData$(), { initialValue: [] });
```

---

## RxJS Patterns

### Async Pipe — Always Prefer Over Manual Subscribe
```html
<!-- ✅ -->
<div *ngIf="data$ | async as data">{{ data.name }}</div>

<!-- ❌ Avoid manual subscribe in components -->
```

### Unsubscription
```typescript
// ✅ takeUntilDestroyed (Angular 16+)
this.service.data$.pipe(
  takeUntilDestroyed(this.destroyRef)
).subscribe(data => this.data = data);

// ✅ async pipe (preferred — no manual sub needed)
```

### Error Handling in Streams
```typescript
this.service.load().pipe(
  catchError(err => {
    this.error.set(err.message);
    return EMPTY;
  })
).subscribe();
```

### Common Operators Cheatsheet
| Goal | Operator |
|------|----------|
| Map + flatten one active at a time | `switchMap` |
| Map + flatten all, preserve order | `concatMap` |
| Map + flatten all in parallel | `mergeMap` |
| Ignore new while processing | `exhaustMap` |
| Deduplicate rapid emissions | `debounceTime` |
| Suppress duplicate values | `distinctUntilChanged` |

---

## Services

```typescript
@Injectable({ providedIn: 'root' })
export class MyService {
  private http = inject(HttpClient);

  getData(): Observable<MyData[]> {
    return this.http.get<MyData[]>('/api/data').pipe(
      shareReplay(1)
    );
  }
}
```

- Use `inject()` over constructor injection for cleaner code
- `providedIn: 'root'` for singleton services
- `providedIn: 'any'` only when per-module isolation is needed
- Never hold mutable state in services unless using NgRx or signals

---

## Routing

```typescript
export const routes: Routes = [
  {
    path: 'feature',
    loadComponent: () =>
      import('./feature/feature.component').then(m => m.FeatureComponent),
  },
  {
    path: 'admin',
    loadChildren: () =>
      import('./admin/admin.routes').then(m => m.ADMIN_ROUTES),
    canActivate: [authGuard],
  },
];
```

- Always lazy-load feature routes with `loadComponent` or `loadChildren`
- Use functional guards (`canActivate: [myGuard]`) not class-based guards
- Use `Router.navigate()` for programmatic navigation, never `location.href`

---

## Forms

### Reactive Forms (preferred for complex forms)
```typescript
form = this.fb.group({
  email: ['', [Validators.required, Validators.email]],
  name: ['', Validators.required],
});

// ✅ Typed forms (Angular 14+)
form = new FormGroup({
  email: new FormControl<string>('', { nonNullable: true }),
});
```

### Template-Driven (simple forms only)
Use only for trivial, 1-2 field forms. Reactive forms for everything else.

### Validation Display Pattern
```html
<input formControlName="email" />
<span *ngIf="form.get('email')?.invalid && form.get('email')?.touched">
  Valid email required
</span>
```

---

## NgRx (when needed)

Use NgRx for:
- Shared state across multiple unrelated components
- Complex async flows with loading/error states
- State that needs to survive navigation

Skip NgRx for:
- Component-local state → use signals
- Parent-child state → use @Input/@Output or service with signal

### Pattern: Feature Store with Signals
```typescript
// Prefer NgRx SignalStore for new features
const MyStore = signalStore(
  withState({ items: [] as Item[], loading: false }),
  withMethods((store, service = inject(MyService)) => ({
    loadItems: rxMethod<void>(
      pipe(
        switchMap(() => service.getItems().pipe(
          tapResponse({
            next: items => patchState(store, { items }),
            error: console.error,
          })
        ))
      )
    ),
  }))
);
```

---

## SCSS Conventions

```scss
// ✅ Use design system variables
.my-component {
  color: $color-primary;
  padding: $spacing-md;
  font-size: $font-size-body;
}

// ❌ Never raw hex or magic numbers
.my-component {
  color: #3B82F6;
  padding: 16px;
}
```

- Use `::ng-deep` sparingly and only with a host selector scope
- Prefer BEM naming: `.block__element--modifier`
- Component styles are scoped by default — don't fight the encapsulation

---

## Performance

- **OnPush everywhere** — default for all new components
- **TrackBy on *ngFor** — always, to avoid full list re-renders
  ```html
  <div *ngFor="let item of items; trackBy: trackById">
  ```
- **Lazy load images** — `loading="lazy"` on `<img>` tags
- **Avoid function calls in templates** — they run on every CD cycle; use pipes or computed signals instead
- **Pure pipes** for expensive template transforms

---

## Testing

```typescript
// Component test setup
await TestBed.configureTestingModule({
  imports: [MyComponent, HttpClientTestingModule],
  providers: [{ provide: MyService, useValue: mockService }],
}).compileComponents();
```

- Test behavior, not implementation details
- Mock all services — never hit real HTTP in unit tests
- Use `fixture.detectChanges()` after state changes
- Prefer `By.css('[data-testid="..."]')` selectors over class-based

---

## Naming Conventions

| Type | Convention | Example |
|------|-----------|---------|
| Component | `PascalCase` + `Component` | `UserProfileComponent` |
| Service | `PascalCase` + `Service` | `AuthService` |
| Directive | `PascalCase` + `Directive` | `HighlightDirective` |
| Pipe | `PascalCase` + `Pipe` | `DateFormatPipe` |
| Guard | camelCase + `Guard` | `authGuard` |
| File | `kebab-case` | `user-profile.component.ts` |
| Signal | camelCase noun | `isLoading`, `currentUser` |
| Observable | camelCase + `$` | `users$`, `error$` |
