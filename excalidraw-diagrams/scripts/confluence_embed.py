#!/usr/bin/env python3
"""Upload diagram attachments to a Confluence page and embed them inline.

    confluence_embed.py PAGE_ID \
        --map "flowchart LR=architecture.png" \
        --map "sequenceDiagram=field-change.png" \
        [--source-suffix .excalidraw] [--width 1200] [--dry-run]

Each --map is "<marker>=<png path>". The script:
  1. uploads the PNG, and its sibling .excalidraw source if it exists, as page attachments.
     An existing attachment with the same name gets a new version instead of a duplicate.
  2. re-reads the page storage XML (fresh, right before editing), finds code macros
     (ac:name="code") whose body contains <marker> and replaces the FIRST unused match per
     --map entry with an inline <ac:image> plus a small "edit source" link to the .excalidraw.
  3. PUTs the page with version + 1, touching nothing else.

Auth: basic auth with $CONFLUENCE_EMAIL and $CONFLUENCE_TOKEN against $CONFLUENCE_BASE_URL.
The token must be a Confluence-enabled Atlassian API token. On 401/403 the script stops and says so.
"""
import argparse
import html
import json
import os
import re
import subprocess
import sys
from pathlib import Path

BASE = os.environ.get("CONFLUENCE_BASE_URL", "")  # e.g. https://<site>.atlassian.net/wiki
USER = os.environ.get("CONFLUENCE_EMAIL", "")


def curl(*args, data=None):
    token = os.environ.get("CONFLUENCE_TOKEN")
    if not (token and BASE and USER):
        sys.exit("set CONFLUENCE_BASE_URL, CONFLUENCE_EMAIL and CONFLUENCE_TOKEN (source ~/.zshrc)")
    cmd = ["curl", "-s", "-w", "\n%{http_code}", "-u", f"{USER}:{token}", *args]
    out = subprocess.run(cmd, input=data, capture_output=True, text=True, check=True).stdout
    body, _, code = out.rpartition("\n")
    if code in ("401", "403"):
        sys.exit(f"Confluence auth failed (HTTP {code}): {body[:200]}\n"
                 "-> the API token is expired/revoked or lacks Confluence access. Create a new one at "
                 "https://id.atlassian.com/manage-profile/security/api-tokens and update CONFLUENCE_TOKEN.")
    if not code.startswith("2"):
        sys.exit(f"HTTP {code}: {body[:500]}")
    return json.loads(body) if body.strip() else {}


def upload(page_id, path):
    existing = curl(f"{BASE}/rest/api/content/{page_id}/child/attachment?filename={path.name}")
    results = existing.get("results", [])
    url = (f"{BASE}/rest/api/content/{page_id}/child/attachment/{results[0]['id']}/data" if results
           else f"{BASE}/rest/api/content/{page_id}/child/attachment")
    curl("-X", "POST", "-H", "X-Atlassian-Token: no-check",
         "-F", f"file=@{path}", "-F", "minorEdit=true", url)
    print(("updated" if results else "uploaded"), path.name)


CODE_MACRO = re.compile(r'<ac:structured-macro[^>]*ac:name="code".*?</ac:structured-macro>', re.S)


def image_block(png, source, width):
    img = (f'<ac:image ac:align="center" ac:width="{width}">'
           f'<ri:attachment ri:filename="{html.escape(png)}" /></ac:image>')
    if source:
        img += (f'<p style="text-align: center;"><sub>Source: <ac:link><ri:attachment ri:filename="'
                f'{html.escape(source)}" /><ac:plain-text-link-body><![CDATA[{source}]]>'
                f'</ac:plain-text-link-body></ac:link> (open in excalidraw.com to edit)</sub></p>')
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("page_id")
    ap.add_argument("--map", action="append", required=True, help='"<marker in code block>=<png>"')
    ap.add_argument("--source-suffix", default=".excalidraw")
    ap.add_argument("--width", type=int, default=1200)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    pairs = []
    for m in a.map:
        marker, _, png = m.rpartition("=")
        png = Path(png).expanduser()
        if not png.exists():
            sys.exit(f"missing {png}")
        src = png.with_suffix(a.source_suffix)
        pairs.append((marker, png, src if src.exists() else None))

    page = curl(f"{BASE}/rest/api/content/{a.page_id}?expand=version,body.storage")
    body, version, title = page["body"]["storage"]["value"], page["version"]["number"], page["title"]
    macros = CODE_MACRO.findall(body)
    used = set()
    for marker, png, src in pairs:
        idx = next((i for i, mac in enumerate(macros) if i not in used and marker in mac), None)
        if idx is None:
            sys.exit(f"no unused code block contains marker {marker!r}")
        used.add(idx)
        body = body.replace(macros[idx], image_block(png.name, src.name if src else None, a.width), 1)
        print(f"block {idx} ({marker!r}) -> {png.name}")

    if a.dry_run:
        print("dry run: nothing uploaded or saved")
        return
    for _, png, src in pairs:
        upload(a.page_id, png)
        if src:
            upload(a.page_id, src)
    payload = json.dumps({"type": "page", "title": title, "version": {"number": version + 1,
                          "message": "Diagrams: Excalidraw PNGs inline"},
                          "body": {"storage": {"value": body, "representation": "storage"}}})
    curl("-X", "PUT", "-H", "Content-Type: application/json", "--data-binary", "@-",
         f"{BASE}/rest/api/content/{a.page_id}", data=payload)
    print(f"page {a.page_id} saved as version {version + 1}")


if __name__ == "__main__":
    main()
