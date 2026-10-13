# Framework Detection

Canonical logic for detecting which concrete framework a ticket/repo targets.
Consumed by `codepilot-be`, `codepilot-ui`, and `devloop`. Keep this the
single source of truth — don't duplicate detection heuristics elsewhere.

- **UI** → `Angular` | `React`
- **Backend** → `NestJS` | `Next.js` | `Python`
- **Neither matches** → `default` (generic, language-appropriate flow)

## Strategy: inspect the repo first, ask only if unclear

Prefer autodetection from the repository. Only prompt the user when signals are
missing or conflicting.

```bash
# Framework fingerprints (run from repo root; harmless if files are absent)
PKG=$(test -f package.json && cat package.json || echo '{}')

# --- UI ---
echo "$PKG" | grep -q '"@angular/core"' && echo "ui:angular"
test -f angular.json && echo "ui:angular"
echo "$PKG" | grep -Eq '"react"|"react-dom"' && echo "ui:react"

# --- Backend ---
echo "$PKG" | grep -q '"@nestjs/core"' && echo "be:nestjs"
test -f nest-cli.json && echo "be:nestjs"
echo "$PKG" | grep -q '"next"' && echo "be:nextjs"
test -f next.config.js -o -f next.config.ts -o -f next.config.mjs && echo "be:nextjs"
test -f pyproject.toml -o -f requirements.txt -o -f Pipfile -o -f setup.py && echo "be:python"
```

## Secondary signals

- **Angular**: `*.component.ts` / `*.component.html`, `@nx/angular` in `nx.json`, standalone components, signals.
- **React**: `*.tsx` / `*.jsx` with `react` imports, `vite` / `react-scripts`, hooks (`useState`, `useEffect`). (Note: a repo with `next` present is **Next.js**, not plain React.)
- **NestJS**: `@nestjs/*` decorators (`@Controller`, `@Injectable`, `@Module`), `*.module.ts`, `nest-cli.json`.
- **Next.js**: `app/` or `pages/` route dirs, `next` in scripts, route handlers / server actions.
- **Python**: `*.py` plus a web framework hint — FastAPI, Django, or Flask in deps.
- Ticket `labels[]` can tie-break (`react`, `nextjs`, `python`, `fastapi`, `django`, `angular`, `nestjs`).

## Decision logic

1. **Single consistent signal** → auto-select and inform the user (e.g. *"Detected backend framework: NestJS"*).
2. **Multiple frameworks present** (monorepo) → narrow to the one that owns the paths/components/services named in the ticket. If still ambiguous, ask the user to pick.
3. **No signal at all** → ask the user which framework this ticket targets. If the user is unavailable or the answer is still unclear → fall back to `default`.

Store the result as `uiFramework` (`Angular` | `React` | `default`) or
`beFramework` (`NestJS` | `Next.js` | `Python` | `default`).

## Skill routing

| Detected | Route to |
|----------|----------|
| Angular | `codepilot-ui-angular` |
| React | `codepilot-ui-react` |
| NestJS | `codepilot-be-nestjs` |
| Next.js | `codepilot-be-nextjs` |
| Python | `codepilot-be-python` |
| _anything else / undetected_ | **default** — run the generic flow in `codepilot-common.md` (`## Default / Generic Flow`) |
