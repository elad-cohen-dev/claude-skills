---
name: confluence
description: Create, update, and search Confluence pages. Use when the user wants to publish documents, design docs, or any content to Confluence.
argument-hint: "[create|update|search] [title or query]"
---

# Confluence Page Management

Create, update, and search pages in your Confluence instance.

## Configuration

- **Base URL:** `$CONFLUENCE_BASE_URL`
- **Auth:** Basic auth with `$CONFLUENCE_EMAIL` and `$CONFLUENCE_TOKEN` env vars (`$CONFLUENCE_BASE_URL` e.g. `https://<your-site>.atlassian.net/wiki`) (source `~/.zshrc` first)
- **Default Space:** `DEV`

## Authentication

Always source the token before API calls:
```bash
source ~/.zshrc 2>/dev/null
```

All API calls use:
```bash
-u "$CONFLUENCE_EMAIL:$CONFLUENCE_TOKEN"
```

## Commands

### Create a Page

Arguments: `create <title>` — followed by the content the user wants to publish.

1. Ask the user (if not specified):
   - **Space key** (default: `DEV`)
   - **Parent page ID** (optional — can look up by title)
2. Convert the content to **Confluence storage format** (XHTML with Confluence macros)
3. Create the page via REST API:

```bash
curl -s -X POST "$CONFLUENCE_BASE_URL/rest/api/content" \
  -u "$CONFLUENCE_EMAIL:$CONFLUENCE_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "type": "page",
    "title": "<TITLE>",
    "space": {"key": "<SPACE_KEY>"},
    "ancestors": [{"id": <PARENT_PAGE_ID>}],
    "body": {
      "storage": {
        "value": "<CONFLUENCE_STORAGE_FORMAT_HTML>",
        "representation": "storage"
      }
    }
  }'
```

4. Return the page URL: `$CONFLUENCE_BASE_URL/spaces/<SPACE>/pages/<ID>`

### Update a Page

Arguments: `update <page-id or title>` — followed by updated content.

1. Fetch the current page version:
```bash
curl -s "$CONFLUENCE_BASE_URL/rest/api/content/<PAGE_ID>?expand=version,body.storage" \
  -u "$CONFLUENCE_EMAIL:$CONFLUENCE_TOKEN"
```

2. Increment the version number and PUT the update:
```bash
curl -s -X PUT "$CONFLUENCE_BASE_URL/rest/api/content/<PAGE_ID>" \
  -u "$CONFLUENCE_EMAIL:$CONFLUENCE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "page",
    "title": "<TITLE>",
    "version": {"number": <CURRENT_VERSION + 1>},
    "body": {
      "storage": {
        "value": "<UPDATED_HTML>",
        "representation": "storage"
      }
    }
  }'
```

### Search Pages

Arguments: `search <query>`

```bash
curl -s "$CONFLUENCE_BASE_URL/rest/api/content/search?cql=text~\"<QUERY>\"+and+space=<SPACE>" \
  -u "$CONFLUENCE_EMAIL:$CONFLUENCE_TOKEN" \
  -H "Accept: application/json"
```

### Find Page by Title

```bash
curl -s "$CONFLUENCE_BASE_URL/rest/api/content?title=<URL_ENCODED_TITLE>&spaceKey=<SPACE>&expand=version" \
  -u "$CONFLUENCE_EMAIL:$CONFLUENCE_TOKEN"
```

### List Child Pages

```bash
curl -s "$CONFLUENCE_BASE_URL/rest/api/content/<PARENT_ID>/child/page" \
  -u "$CONFLUENCE_EMAIL:$CONFLUENCE_TOKEN"
```

## Confluence Storage Format Guide

Convert markdown to Confluence XHTML storage format. Key mappings:

| Markdown | Confluence Storage Format |
|----------|--------------------------|
| `# H1` | `<h1>H1</h1>` |
| `## H2` | `<h2>H2</h2>` |
| `**bold**` | `<strong>bold</strong>` |
| `*italic*` | `<em>italic</em>` |
| `- item` | `<ul><li>item</li></ul>` |
| `1. item` | `<ol><li>item</li></ol>` |
| `` `code` `` | `<code>code</code>` |
| Code block | `<ac:structured-macro ac:name="code"><ac:parameter ac:name="language">lang</ac:parameter><ac:plain-text-body><![CDATA[code]]></ac:plain-text-body></ac:structured-macro>` |
| Table | Standard `<table><thead><tbody>` with `<tr><th><td>` |
| `> quote` | `<blockquote><p>quote</p></blockquote>` |

### Confluence Macros

**Table of Contents:**
```xml
<ac:structured-macro ac:name="toc">
  <ac:parameter ac:name="printable">true</ac:parameter>
  <ac:parameter ac:name="style">disc</ac:parameter>
  <ac:parameter ac:name="maxLevel">3</ac:parameter>
</ac:structured-macro>
```

**Info Panel:**
```xml
<ac:structured-macro ac:name="info">
  <ac:rich-text-body><p>Info text here</p></ac:rich-text-body>
</ac:structured-macro>
```

**Warning Panel:**
```xml
<ac:structured-macro ac:name="warning">
  <ac:rich-text-body><p>Warning text here</p></ac:rich-text-body>
</ac:structured-macro>
```

**Note Panel:**
```xml
<ac:structured-macro ac:name="note">
  <ac:rich-text-body><p>Note text here</p></ac:rich-text-body>
</ac:structured-macro>
```

**Status Badge:**
```xml
<ac:structured-macro ac:name="status">
  <ac:parameter ac:name="colour">Red</ac:parameter>
  <ac:parameter ac:name="title">HIGH</ac:parameter>
</ac:structured-macro>
```
Colours: `Red`, `Yellow`, `Green`, `Blue`, `Grey`

**Expand (collapsible section):**
```xml
<ac:structured-macro ac:name="expand">
  <ac:parameter ac:name="title">Click to expand</ac:parameter>
  <ac:rich-text-body><p>Hidden content</p></ac:rich-text-body>
</ac:structured-macro>
```

## Attachments and inline images

The Atlassian MCP connector can't upload files, so use REST for anything that involves an attachment.

- **Upload** (new file): `curl -X POST -H "X-Atlassian-Token: no-check" -F "file=@x.png" -F "minorEdit=true" .../rest/api/content/<PAGE_ID>/child/attachment`
- **Replace** an existing file: POST to `.../child/attachment/<ATTACHMENT_ID>/data`. First look the id up with `GET .../child/attachment?filename=x.png`.
- **Embed inline:** `<ac:image ac:align="center" ac:width="1200"><ri:attachment ri:filename="x.png" /></ac:image>`
- **Diagrams in HLDs and design docs:** always use the `excalidraw-diagrams` skill. It draws Excalidraw scenes, renders PNGs, and uploads and embeds them with `scripts/confluence_embed.py`. Don't use Mermaid code blocks or excalidraw.com share links: smart cards strip their `#json` fragment.
- **Once a page has attachment images**, edit it via the storage API or the MCP with `contentFormat: "html"`, after a fresh fetch. A markdown re-publish can drop the images.

## Auth troubleshooting

HTTP 401 (Jira) or 403 "Current user not permitted to use Confluence" means the token is expired or revoked. Ask the user to create a new API token at https://id.atlassian.com/manage-profile/security/api-tokens and update `CONFLUENCE_TOKEN` in `~/.zshrc`. They should do it themselves; never ask for the token in chat.

## Important Notes

- Always escape `&` as `&amp;`, `<` as `&lt;`, `>` as `&gt;` in text content (NOT in XML tags)
- Use `<![CDATA[...]]>` inside code blocks to avoid escaping issues
- The JSON payload must be valid — use heredocs or temp files for large content
- Always return the created/updated page URL to the user
- For large documents, consider writing the JSON to a temp file and using `curl -d @/tmp/confluence-payload.json`
