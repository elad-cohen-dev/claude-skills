"""excal_lib — build full-schema .excalidraw scenes from a compact Python spec.

Every labeled shape gets a real bound text element (containerId + boundElements), so the
scene renders identically in excalidraw.com, the Excalidraw exporter, and the MCP viewer.
"""
import json
import random
import sys
from pathlib import Path

OUT = Path.cwd()  # scenes are written to the current directory
FONT = 5  # Excalifont (hand-drawn), excalidraw >= 0.18
LH = 1.25

BLUE, PURPLE, GREEN, ORANGE, TEAL, YELLOW, RED = (
    "#a5d8ff", "#d0bfff", "#b2f2bb", "#ffd8a8", "#c3fae8", "#fff3bf", "#ffc9c9")
S_BLUE, S_PURPLE, S_GREEN, S_ORANGE, S_TEAL, S_GREY = (
    "#1971c2", "#6741d9", "#2f9e44", "#e8590c", "#0c8599", "#868e96")


class Scene:
    def __init__(self):
        self.els = []
        self.rng = random.Random(42)

    def _base(self, typ, id_, x, y, w, h, **kw):
        el = {
            "id": id_, "type": typ, "x": x, "y": y, "width": w, "height": h, "angle": 0,
            "strokeColor": kw.get("stroke", "#1e1e1e"),
            "backgroundColor": kw.get("bg", "transparent"),
            "fillStyle": "solid", "strokeWidth": kw.get("sw", 2),
            "strokeStyle": kw.get("style", "solid"), "roughness": kw.get("rough", 1),
            "opacity": kw.get("opacity", 100), "groupIds": [], "frameId": None,
            "roundness": kw.get("roundness"), "seed": self.rng.randint(1, 2**31),
            "version": 1, "versionNonce": self.rng.randint(1, 2**31), "isDeleted": False,
            "boundElements": [], "updated": 1, "link": None, "locked": False,
        }
        self.els.append(el)
        return el

    @staticmethod
    def _text_size(text, size):
        lines = text.split("\n")
        return max(len(line) for line in lines) * size * 0.55, len(lines) * size * LH

    def text(self, id_, x, y, text, size=16, color="#1e1e1e", align="left", container=None, w=None):
        tw, th = self._text_size(text, size)
        el = self._base("text", id_, x, y, w or tw, th, stroke=color)
        el.update({
            "text": text, "originalText": text, "fontSize": size, "fontFamily": FONT,
            "textAlign": align, "verticalAlign": "middle" if container else "top",
            "containerId": container, "autoResize": True, "lineHeight": LH,
        })
        return el

    def box(self, id_, x, y, w, h, label, bg=BLUE, stroke="#1e1e1e", size=16, shape="rectangle",
            style="solid", sw=2, opacity=100, color="#1e1e1e"):
        el = self._base(shape, id_, x, y, w, h, bg=bg, stroke=stroke, style=style, sw=sw,
                        opacity=opacity, roundness={"type": 3} if shape == "rectangle" else {"type": 2})
        if label:
            tw, th = self._text_size(label, size)
            t = self.text(f"{id_}_t", x + (w - tw) / 2, y + (h - th) / 2, label, size,
                          color=color, align="center", container=id_, w=tw)
            el["boundElements"].append({"id": t["id"], "type": "text"})
        return el

    def zone(self, id_, x, y, w, h, title, bg, stroke, title_color):
        self._base("rectangle", id_, x, y, w, h, bg=bg, stroke=stroke, sw=1, opacity=35,
                   roundness={"type": 3})
        self.text(f"{id_}_title", x + 16, y + 10, title, 20, color=title_color)

    def arrow(self, id_, pts, start=None, end=None, stroke="#1e1e1e", style="solid",
              label=None, label_at=None, size=14, head="arrow", sw=2, label_color=None):
        x0, y0 = pts[0]
        rel = [[px - x0, py - y0] for px, py in pts]
        xs, ys = [p[0] for p in rel], [p[1] for p in rel]
        el = self._base("arrow", id_, x0, y0, max(xs) - min(xs), max(ys) - min(ys),
                        stroke=stroke, style=style, sw=sw, roundness=None)
        el.update({
            "points": rel, "lastCommittedPoint": None, "startArrowhead": None,
            "endArrowhead": head, "elbowed": False,
            "startBinding": None, "endBinding": None,
        })
        for key, target in (("startBinding", start), ("endBinding", end)):
            if target:
                el[key] = {"elementId": target, "focus": 0, "gap": 4}
                self.by_id(target)["boundElements"].append({"id": id_, "type": "arrow"})
        if label:
            tw, th = self._text_size(label, size)
            lx, ly = label_at or ((pts[0][0] + pts[-1][0]) / 2, (pts[0][1] + pts[-1][1]) / 2 - th - 6)
            self.text(f"{id_}_l", lx - tw / 2, ly, label, size, color=label_color or stroke)
        return el

    def by_id(self, id_):
        return next(e for e in self.els if e["id"] == id_)

    def save(self, name):
        doc = {"type": "excalidraw", "version": 2, "source": "https://excalidraw.com",
               "elements": self.els,
               "appState": {"viewBackgroundColor": "#ffffff", "gridSize": None},
               "files": {}}
        (OUT / f"{name}.excalidraw").write_text(json.dumps(doc, indent=1))




# ---------------------------------------------------------------- sequence-diagram helpers
def lifelines(s, actors, top, bottom):
    """actors: [(id, x_center, label, fill, stroke), ...] -> header boxes + dashed lifelines."""
    for id_, x, label, bg, stroke in actors:
        s.box(id_, x - 90, top, 180, 56, label, bg, stroke=stroke)
        s.arrow(f"{id_}_ll", [(x, top + 56), (x, bottom)], stroke="#adb5bd", style="dashed", head=None, sw=1)


def msg(s, id_, x1, x2, y, label, stroke="#1e1e1e", style="solid"):
    """Message arrow between lifelines at height y (x1 == x2 draws a self-call loop)."""
    if x1 == x2:
        s.arrow(id_, [(x1, y), (x1 + 60, y), (x1 + 60, y + 26), (x1 + 4, y + 26)], stroke=stroke, style=style)
        s.text(f"{id_}_l", x1 + 70, y - 2, label, 14, color=stroke)
        return
    s.arrow(id_, [(x1, y), (x2, y)], stroke=stroke, style=style, label=label)
