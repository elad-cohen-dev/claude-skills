---
name: vibe-coder
description: Build beautiful, consistent UI components using an established design system with safety guardrails. Use this skill when the user wants to create, update, or style UI components, pages, or layouts, especially when there's a design system involved. Trigger when the user mentions "vibe coding", building UI, frontend components, design system compliance, or wants help staying within safe editing zones. Also use when validating CSS class usage or checking component safety before making changes.
allowed-tools: Bash, Read, Edit, Write, Glob, Grep
---

# Vibe Coder — Safe UI Development

Creative UI development with design system guardrails. Build beautiful things without breaking existing ones.

## Session Workflow

### 1. Start Safe
Before any code changes, establish context:
- Identify the design system file (e.g., `nb-app-ui-design-system.html` or equivalent)
- Identify safe zones — which files/directories are allowed to edit
- Review existing components before creating new ones

### 2. Explore Before Building
Always check if a component already exists using Grep and Read tools. Reusing > creating. Never invent new styles.

### 3. Code Within Boundaries

**Safe zones** (editable):
- Feature component directories
- Page-level SCSS modules
- Component-specific styles

**Restricted zones** (never edit without explicit confirmation):
- Core design system files
- Global theme/token files
- Shared layout files

### 4. Validate Changes Continuously
After every meaningful edit, check compliance:
- Are all CSS classes from the approved design system?
- Is the file in a safe editing zone?
- Does the component match the design spec?

### 5. Quality Check Before Done
Run linting and type checks:
```bash
ng build --configuration development
tsc --noEmit
npx stylelint "**/*.scss"
```

## Design System Rules

### Colors
- Use only SCSS variables: `$color-primary`, `$nb-blue-500`, etc.
- Never use raw hex values: `color: #3B82F6`
- If a color isn't in the system → define it in `_colors.scss` first

### Components
- Compose from design system building blocks
- Don't create one-off component structures
- If a needed component doesn't exist → flag it for addition to the design system

### Class Naming
- BEM: `.component__element--modifier`
- Match design system naming conventions exactly

## Framing Validation Issues
Present errors as guardrails, not mistakes:
> "This class isn't in the approved set — here's the equivalent design system class that matches what you need."

## Component Patterns

### Safe Component Structure
```typescript
@Component({
  selector: 'app-feature-card',
  standalone: true,
  template: `
    <div class="nb-card nb-card--elevated">
      <div class="nb-card__header">
        <h3 class="nb-heading nb-heading--sm">{{ title }}</h3>
      </div>
      <div class="nb-card__body">
        <ng-content></ng-content>
      </div>
    </div>
  `,
  styleUrls: ['./feature-card.component.scss']
})
```

### SCSS Pattern
```scss
// Correct
@use 'design-system/tokens' as tokens;

.feature-card {
  background: tokens.$surface-primary;
  border-radius: tokens.$radius-md;
  padding: tokens.$spacing-4;
}

// Wrong
.feature-card {
  background: #ffffff;
  border-radius: 8px;
  padding: 16px;
}
```

## Checklist Before Completing
- [ ] All CSS classes are from the design system
- [ ] No raw hex values in SCSS
- [ ] Files edited are within safe zones
- [ ] Build passes with no errors
- [ ] Component is reusable, not one-off
