---
name: webcode
description: Implement pixel-perfect Angular UI components from Figma designs with absolute fidelity to the design spec. Use this skill when implementing frontend components, building Angular UI from Figma frames, or when precise design-to-code translation is required. Trigger on "implement this Figma design", "build this component", "create this Angular component", "match this design exactly", or when receiving a Figma URL alongside implementation instructions. Always fetch every Figma frame before writing any code.
allowed-tools: Bash, Read, Edit, Write, Glob, Grep
---

# WebCode — Pixel-Perfect Angular Implementation

Elite frontend implementation from Figma to Angular. Zero guessing. 100% fidelity.

> **Requires Figma MCP** to fetch frame designs. All Figma frame fetching uses the Figma MCP tools.

## Required Inputs

| Input | Shape | Purpose |
|-------|-------|---------|
| `figmaContext` | `{ frameUrls: string[]; screenshots?: string[] }` | Every frame to implement |
| `architecturePlan` | see calling skill | Component boundaries to follow exactly |
| `ticketContext` | `{ acceptanceCriteria: string[] }` | What the UI must satisfy |

If `figmaContext.frameUrls[]` is absent or empty, stop and ask for the frames —
implementing without them violates the Zero Guess Policy below.

## Zero Guess Policy
- Never approximate or estimate design details
- Never skip a Figma frame
- Never use raw hex values in SCSS
- Fetch and analyze EVERY frame in `figmaContext.frameUrls[]`
- Inspect Figma layer panel and Dev Mode — not just appearance

## Implementation Flow

### 1. Fetch All Figma Frames

For each URL in `figmaContext.frameUrls[]`:
- Fetch the frame (do not skip any)
- Extract from each:
  - Layout flow: row/column, flex direction
  - Padding, margin, gap, alignment
  - Sizes: width, height (exact values)
  - Visual hierarchy: parent-child grouping
  - Font styles, weights, sizes
  - Corner radius, shadows, z-index
  - Component boundary zones

**Use Figma's layer panel and Dev Mode — not just visual appearance.**

### 2. Color Integration

Before writing any style:
1. Extract hex values for ALL colors (backgrounds, text, borders, accents, icons)
2. Check if color exists in repo's SCSS variables
3. If **exists** → use the variable: `$color-name`
4. If **doesn't exist** → define in `_colors.scss`:
   ```scss
   $meaningful-color-name: #ABCDEF;
   ```
5. Import and use — never raw hex in component files

### 3. Component Structure

For each component in `architecturePlan.components[]`:

```
<componentPath>/<component-name>/
├── <component-name>.component.ts
├── <component-name>.component.html
├── <component-name>.component.scss
└── (optional) /models, /interfaces, /constants
```

**Angular 17 standalone component:**
```typescript
@Component({
  selector: 'app-component-name',
  standalone: true,
  imports: [CommonModule, ...],
  templateUrl: './component-name.component.html',
  styleUrls: ['./component-name.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
```

**SCSS — BEM naming:**
```scss
.component-name {
  &__element { }
  &__element--modifier { }
}
```

### 4. Build Validation

After implementing each component:

```bash
ng build --configuration development
tsc --noEmit
```

**If either fails:**
- Stop immediately
- Do NOT continue
- Read terminal output carefully
- Fix ALL errors before proceeding

**Both must pass cleanly (zero errors) before continuing.**

Then visually verify in browser:
- Layout structure and spacing
- Alignment (no visual shifts)
- Shadows, borders, backgrounds
- Typography (font, weight, size)
- Hover/focus states

### 5. Pixel Match Verification

Compare rendered component against Figma side-by-side:
- Layout structure matches?
- Spacing: padding, margin, gap identical?
- Colors match SCSS variables?
- Typography: family, weight, size correct?
- Responsive behavior for all breakpoints?

**If any mismatch → fix before proceeding. No exceptions.**

## Dependency Injection Rules

Before injecting services into feature components:
- Analyze dependency graph
- Only inject services truly needed for this component's core function
- Prefer event emission (`@Output`) to parent components over direct service injection
- Avoids circular dependencies between feature modules and core services

## Code Quality

Every component must be:
- **Simple** — readable, minimal logic, no over-engineering
- **Single responsibility** — one job, easily testable
- **Reusable** — ask: "Can this be reused elsewhere without modification?"

Constants, enums, and interfaces → extract to:
- `./constants/`
- `./models/`
- `./interfaces/`

## Units & Values
- Use relative units: `rem`, `em`, `%`
- Use `px` only when Figma explicitly defines pixel values
- Match Figma spacing values exactly

## Final Checklist Before Completing

- [ ] All frames in `figmaContext.frameUrls[]` were fetched and analyzed
- [ ] Components match `architecturePlan` structure exactly
- [ ] New colors added to `_colors.scss` before use
- [ ] Zero raw hex values in component SCSS
- [ ] Layout flow, flex direction, sizes, alignment match Figma
- [ ] `ng build --configuration development` passes (zero errors)
- [ ] `tsc --noEmit` passes (zero errors)
- [ ] Rendered UI visually matches Figma design
- [ ] Props, constants, enums, interfaces properly extracted

## Clarification Required

If any design is:
- Overlapping in ways that seem unintentional
- Ambiguous (multiple possible interpretations)
- Flattened without clear layer structure
- Impossible to implement exactly as shown

→ **Do NOT guess. Halt and raise a clarification question.**
