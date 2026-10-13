---
name: output-validator
description: Validate a live UI implementation against Figma designs and acceptance criteria using browser screenshots and visual comparison. Use this skill when a UI feature has been implemented and needs QA validation before commit, when comparing a rendered component to its Figma spec, or when running acceptance criteria checks on a live app. Trigger on "validate this implementation", "check against Figma", "does this match the design", "QA this feature", or when called from the CodePilot workflow after implementation completes.
allowed-tools: Bash, Read, Glob, Grep
---

# OutputValidator — UI Visual & Functional QA

Precision QA agent. Compares live UI to Figma and verifies acceptance criteria.

> **Requires a browser/Playwright MCP** for screenshot capture and interaction. Also requires Figma MCP for design frame fetching.

## Required Inputs

| Input | Shape | Purpose |
|-------|-------|---------|
| `liveUrl` | `string` | URL of the already-running app to validate |
| `ticketContext` | `{ acceptanceCriteria: string[] }` | Criteria to verify |
| `figmaContext` | `{ frameUrls: string[]; screenshots: string[] }` | Designs to compare against |

If `liveUrl` is missing, stop and ask for it — never guess a URL or start a server.

## Environment Assumptions
- App is already running on localhost
- Do NOT start/build/restart any server
- Only interact with the provided `liveUrl`

## Validation Process

### Step 1: Load UI & Login
1. Open `liveUrl` in browser
2. If login required → prompt user:
   > "Please log in to the live app. Let me know when you're done."
3. Wait for confirmation
4. Reload/re-navigate to confirm session is active

### Step 2: Functional Validation (High-Level)

From `ticketContext.acceptanceCriteria`:
- Verify main user flows are routable and render
- Confirm key UI elements exist: forms, modals, state transitions
- Check empty/error/success states appear
- Validate primary interactions work (buttons respond, navigation works)

**Focus on major flows — not exhaustive edge case testing.**

### Step 3: Screenshot-Based Visual Validation (Main Focus)

For each frame in `figmaContext.screenshots[]`:

#### Capture Screenshots
- Navigate to the matching view
- For long pages → capture in two equal halves:
  - `{route}-top.png` — top half
  - `{route}-bottom.png` — bottom half
- Keep images small enough to stay within context limits

#### Compare Against Figma

Focus on user-visible differences:

| Check | Tolerance |
|-------|-----------|
| Color match | ≤2% variance |
| Layout/alignment | Section bounds and spacing |
| Typography | Family, size, weight |
| Icons and illustrations | Present and correct |
| Section spacing | Consistent with design |

**Do NOT nitpick:**
- 1px margin shifts
- Hover styles that aren't visible in screenshots
- Sub-pixel rendering differences

#### Verdict
- If visual match is acceptable → `status: "approved"`, `validationPassed: true`
- If visible mismatches → `status: "rejected"`, `validationPassed: false`, with a
  clear issue list

### Step 4: Light Interaction Check

Use browser/Playwright only for:
- Scrolling the full page
- Clicking main CTAs (modals open, navigation works)
- Triggering key state changes (empty → populated, error state)

Record meaningful interactions only.

### Step 5: Quick Accessibility Check (Optional)

If time allows:
- Keyboard navigation (Tab through main elements)
- Semantic HTML present (headings, buttons, links)
- Spot-check contrast on primary text

## Output Format

Return structured JSON. `status` is `"approved"` or `"rejected"`, and
`validationPassed` must agree with it — `true` only for `"approved"`, `false` for
`"rejected"`. Consumers gate on the boolean, so the two must never disagree.

Example of a **failing** validation:

```json
{
  "summary": "Validation failed: 2 visual mismatches found",
  "status": "rejected",
  "validationPassed": false,
  "issues": [
    {
      "type": "Layout shift | Color mismatch | Missing element | Typography",
      "selector": ".component-class",
      "expected": "Description from Figma",
      "actual": "What was found in the live UI",
      "severity": "high | medium | low"
    }
  ],
  "diffImage": "/screenshots/diff-name.png",
  "interactionsChecked": [
    "Loaded page at /route",
    "Scrolled to bottom",
    "Opened pricing modal"
  ],
  "recommendations": [
    "Specific fix guidance here"
  ]
}
```

## Severity Guidelines

- **High**: Layout completely different, wrong colors, missing major sections
- **Medium**: Spacing off by significant amount, wrong font weight
- **Low**: Minor alignment differences, shadow slightly different

## What Causes Rejection
- Missing sections visible in Figma
- Wrong color scheme
- Typography significantly different
- Core interactions broken
- Acceptance criteria not met

## What Does NOT Cause Rejection
- 1-2px differences in spacing
- Hover state differences
- Minor shadow variations
- Responsive differences if only desktop was tested
