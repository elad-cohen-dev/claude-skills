---
name: excalidraw-diagrams
description: Draw architecture, flow and sequence diagrams for HLDs and design docs as Excalidraw scenes, render them to PNG with Excalidraw's own exporter, and embed them inline in a Confluence page (PNG plus the editable .excalidraw source attached). Use whenever an HLD, design doc or Confluence page needs a diagram, or when asked to replace Mermaid/ASCII diagrams with Excalidraw ones. Trigger on "draw the flow diagram", "add an architecture diagram to the HLD", "replace the mermaid with excalidraw", "export the excalidraw as an image into Confluence".
---

# Excalidraw diagrams → inline PNG in Confluence

The user's HLD standard is **hand-drawn Excalidraw diagrams embedded inline as images**. That means no Mermaid code blocks and no share links. Every diagram ships as two page attachments:

- `<name>.png`, the inline image;
- `<name>.excalidraw`, the editable source, linked under the image so anyone can reopen it in excalidraw.com.

## Why this pipeline, and not the Excalidraw MCP export

- The MCP `create_view` shorthand (`label: {text}`) looks fine in its viewer. It is **not** real Excalidraw JSON, though: exported to excalidraw.com, every label comes out empty.
  - `scripts/excal_lib.py` writes the full schema instead: bound text with `containerId`, and `boundElements` on the container.
- Confluence smart cards strip the `#json=` fragment from excalidraw.com share links, so a link is useless. Embed the image instead.
- The Atlassian MCP connector **cannot upload attachments**. The REST API with `$CONFLUENCE_TOKEN` can.

## Steps

1. **Design the diagrams from the doc**, not from memory. Re-read the section the diagram replaces, and keep every component and arrow that section describes.
   - One architecture view (zones per app/service, stores on the right).
   - One sequence diagram per important flow.
   - Keep text at 14px or larger. Use the palette in `excal_lib.py`: blue = frontend, purple = BFF, green = backend, teal = data stores, orange = object storage or external systems.
2. **Write a small generator** next to your scratch files, using the library. See `example.py` for a worked example: an architecture view with zones and routed arrows, plus a sequence diagram with an alt block.

```python
import sys; sys.path.insert(0, str(Path.home() / ".claude/skills/excalidraw-diagrams/scripts"))
from excal_lib import Scene, lifelines, msg, BLUE, PURPLE, GREEN, TEAL, ORANGE, S_BLUE, S_PURPLE, S_GREEN, S_TEAL
s = Scene()
s.zone("zfe", 20, 60, 340, 560, "apps/platform", "#dbe4ff", S_BLUE, S_BLUE)
s.box("ov", 45, 130, 290, 110, "Overview table\nstatus column", BLUE)
s.box("api", 445, 130, 290, 110, "platform-api", GREEN)
s.arrow("a1", [(335, 185), (445, 185)], "ov", "api", label="PATCH field")
s.save("architecture")          # -> ./architecture.excalidraw
```

   - `box`: a labeled rectangle with bound text.
   - `zone`: a translucent group background with a title.
   - `arrow(points, start_id, end_id, label=…, style="dashed")`: route around boxes with multi-point polylines, which render with sharp corners.
   - `lifelines`, `msg`: sequence diagrams. `msg` with the same x on both ends draws a self-call.
3. **Render to PNG**. Run it from a directory whose `node_modules` has `playwright`; e.g. a repo with Playwright installed. It loads `@excalidraw/excalidraw@0.18` from esm.sh, and exports at 2× with 32px padding.

```bash
cp ~/.claude/skills/excalidraw-diagrams/scripts/render.mjs ./.render-excal.mjs
node ./.render-excal.mjs /path/architecture.excalidraw /path/flow.excalidraw   # writes .png next to each
rm ./.render-excal.mjs
```

4. **Look at every PNG** with the Read tool before publishing. Check for:
   - labels overlapping arrows or boxes;
   - arrows cutting through boxes;
   - text overflowing a short arrow.

   Fix the coordinates, then re-render. Expect one or two passes.
5. **Embed in Confluence**. The script re-reads the page itself, so manual edits made since your last read are kept.

```bash
source ~/.zshrc
python3 ~/.claude/skills/excalidraw-diagrams/scripts/confluence_embed.py <PAGE_ID> \
  --map "flowchart LR=/path/architecture.png" \
  --map "participant PA=/path/flow.png" --dry-run      # drop --dry-run to apply
```

   - Each `--map` replaces the first unused code block that contains the marker. Pick a marker unique to that Mermaid block.
   - To add a diagram where there is no code block, insert `<ac:image ac:align="center" ac:width="1200"><ri:attachment ri:filename="x.png" /></ac:image>` into the storage XML, using the same upload helper.
6. **Keep the page editable through the MCP afterwards.** Treat the markdown `updateConfluencePage` path as unsafe for pages with attachment images: it is not guaranteed to round-trip `ac:image`, so a markdown re-publish can drop them. After diagrams are embedded, make later text edits either:
   - with `contentFormat: "html"`, after re-fetching the page as HTML, or
   - through the REST storage API.

   Never re-publish a cached markdown body.

## Auth failures

- HTTP 401 on Jira, or 403 "Current user not permitted to use Confluence", means `$CONFLUENCE_TOKEN` is expired or revoked.
- Ask the user to create a new token at https://id.atlassian.com/manage-profile/security/api-tokens and update `CONFLUENCE_TOKEN` in `~/.zshrc` themselves. Never ask them to paste the token into chat.
- Meanwhile, finish and verify the PNGs so only the upload step is left.
