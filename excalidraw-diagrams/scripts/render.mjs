// Render .excalidraw scenes to PNG with Excalidraw's own exporter, in headless Chromium.
// Usage: node render.mjs <scene.excalidraw>...   (run from a dir whose node_modules has playwright)
import { chromium } from "playwright";
import { readFileSync, writeFileSync } from "node:fs";

const VERSION = "0.18.0";
const html = `<!doctype html><html><head>
<script>window.EXCALIDRAW_ASSET_PATH = "https://unpkg.com/@excalidraw/excalidraw@${VERSION}/dist/prod/";</script>
<script type="importmap">{"imports":{
  "react":"https://esm.sh/react@19.0.0",
  "react/jsx-runtime":"https://esm.sh/react@19.0.0/jsx-runtime",
  "react-dom":"https://esm.sh/react-dom@19.0.0",
  "react-dom/client":"https://esm.sh/react-dom@19.0.0/client",
  "@excalidraw/excalidraw":"https://esm.sh/@excalidraw/excalidraw@${VERSION}?external=react,react-dom"
}}</script>
<script type="module">
  import * as X from "@excalidraw/excalidraw";
  window.render = async (scene, scale) => {
    const elements = X.restoreElements(scene.elements, null, { refreshDimensions: true, repairBindings: true });
    const blob = await X.exportToBlob({
      elements, files: scene.files || {}, mimeType: "image/png", getDimensions: (w, h) => ({ width: w * scale, height: h * scale, scale }),
      appState: { ...scene.appState, exportBackground: true, viewBackgroundColor: "#ffffff", exportWithDarkMode: false },
      exportPadding: 32,
    });
    const buf = new Uint8Array(await blob.arrayBuffer());
    let s = ""; for (const b of buf) s += String.fromCharCode(b);
    return btoa(s);
  };
  window.ready = true;
</script></head><body></body></html>`;

const browser = await chromium.launch();
const page = await browser.newPage();
page.on("console", (m) => m.type() === "error" && console.error("[page]", m.text()));
await page.setContent(html);
await page.waitForFunction(() => window.ready === true, null, { timeout: 90_000 });
for (const file of process.argv.slice(2)) {
  const scene = JSON.parse(readFileSync(file, "utf8"));
  const b64 = await page.evaluate(([s]) => window.render(s, 2), [scene]);
  const out = file.replace(/\.excalidraw$/, ".png");
  writeFileSync(out, Buffer.from(b64, "base64"));
  console.log("wrote", out);
}
await browser.close();
