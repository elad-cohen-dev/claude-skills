# React Review Checklist

Framework-specific review checklist for React code (Vite-based apps, React 18/19).
Apply this checklist when reviewing PRs that contain React components, hooks, or routes.

## Checklist

For each item, report **PASS**, **FAIL**, or **N/A**. Explain every FAIL and provide a corrected snippet.

### TypeScript
- [ ] No `any` types without justification
- [ ] Props and hook return values are explicitly typed where inference is not obvious
- [ ] Discriminated unions used for state that has mutually exclusive shapes (e.g. loading/error/success)

### Components
- [ ] Function components only — no class components
- [ ] Components stay focused; large components are split by responsibility
- [ ] No business logic embedded in JSX — extracted to hooks or plain functions
- [ ] Keys on list items are stable IDs, never array index (unless the list is static and never reorders)

### Hooks
- [ ] `useEffect`/`useMemo`/`useCallback` dependency arrays are complete and correct (no suppressed `eslint-disable-line react-hooks/exhaustive-deps` without justification)
- [ ] No `useEffect` used to derive state from props/other state that could be computed inline during render
- [ ] Custom hooks follow `use*` naming and don't call hooks conditionally
- [ ] Cleanup functions are returned from effects that subscribe/set timers/open connections

### Server State (TanStack Query)
- [ ] Server data fetched via `useQuery`/`useMutation` — not ad-hoc `useEffect` + `fetch`/`axios`
- [ ] Query keys are structured and include all variables the query depends on
- [ ] Mutations invalidate or update the relevant query cache on success
- [ ] Loading/error states from the query are surfaced in the UI (no silent failures)

### Routing (TanStack Router)
- [ ] Route params/search params are validated (e.g. via a `zod` schema in `validateSearch`), not read as raw untyped strings
- [ ] Data dependencies for a route are loaded via the route's `loader`, not fetched imperatively after mount when avoidable

### Forms (react-hook-form + zod)
- [ ] Validation schema defined with `zod` and wired through `zodResolver` — not hand-rolled validation
- [ ] Server-side/API validation errors are mapped back onto the relevant form field
- [ ] Uncontrolled inputs (`register`) preferred over manual `useState` per field

### Styling (Tailwind)
- [ ] Utility classes used directly; no new CSS files/CSS-in-JS introduced without reason
- [ ] Conditional class composition uses `tailwind-merge` / `clsx`-style helpers, not string concatenation that can produce conflicting utility classes
- [ ] No inline `style={{ ... }}` for values that could be a Tailwind utility

### Performance
- [ ] No new inline object/array/function literals passed as props to memoized children on every render without `useMemo`/`useCallback`
- [ ] Expensive derived values are memoized, not recomputed every render
- [ ] Large route bundles are code-split (`React.lazy` + `Suspense`) when not needed on first paint

### Accessibility
- [ ] Interactive elements are real `<button>`/`<a>`, not `<div onClick>`
- [ ] Images have meaningful `alt` text (or `alt=""` if decorative)
- [ ] Form inputs have associated `<label>`s

### Testing
- [ ] New components/hooks have tests using `@testing-library/react` + `vitest`
- [ ] Tests query by role/label text (`getByRole`, `getByLabelText`), not by CSS class or test-id when an accessible query exists
- [ ] No implementation-detail assertions (e.g. asserting internal state instead of rendered output)

## Correct Component Example

```tsx
const searchSchema = z.object({ userId: z.string().uuid() });

function useUser(userId: string) {
  return useQuery({
    queryKey: ['user', userId],
    queryFn: () => fetchUser(userId),
  });
}

export function UserCard({ userId }: { userId: string }) {
  const { data: user, isLoading, error } = useUser(userId);

  if (isLoading) return <Spinner />;
  if (error) return <ErrorMessage error={error} />;

  return (
    <div className={twMerge('rounded-lg border p-4', user.isActive && 'border-green-500')}>
      <h2 className="text-lg font-semibold">{user.name}</h2>
    </div>
  );
}
```
