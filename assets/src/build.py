#!/usr/bin/env python3
"""Builds the custom SVGs used by the profile README:

    assets/monitor.svg    illustration beside the About me code block
    assets/currently.svg  the 2x2 "Currently" cards

Everything else on the profile comes from live widgets (see README.md).
Colours follow the Tokyo Night theme used by the stats cards. Fonts are
subset and embedded because GitHub serves SVGs as images.

Edit the CONTENT block below, then run:

    pip install fonttools brotli
    python3 assets/src/build.py
"""
import base64
import html
import io
import os

from fontTools import subset
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
FONT_DIR = os.path.join(HERE, "fonts")

# ---------------------------------------------------------------- content ---

# Each item: (icon, [(text, bold?), ...])
CURRENTLY = [
    ("book", [("Revising ", False), ("Core Java & DSA", True), (" — Striver’s A2Z", False)]),
    ("layers", [("Studying ", False), ("design patterns & system design", True)]),
    ("leaf", [("Building ", False), ("a SaaS product", True), (" of my own", False)]),
    ("play", [("Launching ", False), ("DEV", True), (", my YouTube channel", False)]),
]

# ----------------------------------------------------------------- theme ---

CARD = "#1a1b27"
BORDER = "#2a2d40"
TEXT = "#a9b1d6"
BRIGHT = "#e6e9f5"
PURPLE = "#bb9af7"
BLUE = "#7aa2f7"
TEAL = "#2ac3de"
GREEN = "#9ece6a"
RED = "#f7768e"
YELLOW = "#e0af68"
GREY = "#414868"
ICON_COLOURS = {"book": BLUE, "layers": PURPLE, "leaf": GREEN, "play": RED}

FONT_FILES = {
    ("B", 400): "bricolage-grotesque-latin-400-normal.woff2",
    ("B", 700): "bricolage-grotesque-latin-700-normal.woff2",
    ("M", 500): "jetbrains-mono-latin-500-normal.woff2",
}
_fonts = {}


def font(fam, wt):
    if (fam, wt) not in _fonts:
        _fonts[(fam, wt)] = TTFont(os.path.join(FONT_DIR, FONT_FILES[(fam, wt)]))
    return _fonts[(fam, wt)]


def measure(text, fam, wt, size):
    f = font(fam, wt)
    cmap, hmtx = f.getBestCmap(), f["hmtx"]
    w = sum(hmtx[cmap.get(ord(c), cmap[ord("?")])][0] for c in text)
    return w / f["head"].unitsPerEm * size


def embed(fam, wt, chars):
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["kern"]
    opts.name_IDs = []
    f = TTFont(os.path.join(FONT_DIR, FONT_FILES[(fam, wt)]))
    sub = subset.Subsetter(opts)
    sub.populate(text="".join(sorted(chars)) + " ")
    sub.subset(f)
    buf = io.BytesIO()
    f.flavor = "woff2"
    f.save(buf)
    return base64.b64encode(buf.getvalue()).decode()


class Svg:
    def __init__(self, w, h, title):
        self.w, self.h, self.title = w, h, title
        self.defs, self.body, self.used = [], [], {}

    def add(self, s):
        self.body.append(s)

    def rich(self, x, y, parts, size):
        """parts: (text, colour, family, weight) pieces on one line."""
        inner = ""
        for s, c, fam, wt in parts:
            self.used.setdefault((fam, wt), set()).update(s)
            inner += f'<tspan class="{fam}{wt}" fill="{c}">{html.escape(s)}</tspan>'
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}">{inner}</text>')

    def render(self):
        css = "text{white-space:pre}"
        for (fam, wt), chars in sorted(self.used.items()):
            fallback = "ui-monospace,monospace" if fam == "M" else "system-ui,sans-serif"
            css += (f"@font-face{{font-family:{fam}{wt};src:url(data:font/woff2;"
                    f"base64,{embed(fam, wt, chars)}) format('woff2')}}"
                    f".{fam}{wt}{{font-family:{fam}{wt},{fallback}}}")
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" '
            f'height="{self.h}" viewBox="0 0 {self.w} {self.h}" role="img" '
            f'aria-label="{html.escape(self.title)}">'
            f"<title>{html.escape(self.title)}</title>"
            f"<style>{css}</style><defs>{''.join(self.defs)}</defs>"
            + "".join(self.body) + "</svg>\n")

    def save(self, name):
        with open(os.path.join(OUT, name + ".svg"), "w") as fh:
            fh.write(self.render())
        print("wrote", name + ".svg")


# ------------------------------------------------------------------ icons ---

def icon(kind, x, y, colour):
    """18x18 line icons, top-left at (x, y)."""
    a = (f'fill="none" stroke="{colour}" stroke-width="1.8" '
         f'stroke-linecap="round" stroke-linejoin="round"')
    if kind == "book":
        return f'<path {a} d="M{x + 4} {y + 2}h10v15l-5-3.5-5 3.5z"/>'
    if kind == "layers":
        return (f'<path {a} d="M{x + 9} {y + 2}l8 4.5-8 4.5-8-4.5z'
                f'M{x + 1} {y + 10.5}l8 4.5 8-4.5"/>')
    if kind == "leaf":
        return (f'<path {a} d="M{x + 3} {y + 16}c0-8 5-13 13-14 0 8-4 13-12 13'
                f'M{x + 3} {y + 16}l6-6"/>')
    if kind == "play":
        return (f'<rect {a} x="{x + 1}" y="{y + 3}" width="16" height="12" rx="3"/>'
                f'<path fill="{colour}" d="M{x + 7.5} {y + 6.5}v5l4.2-2.5z"/>')
    raise ValueError(kind)


# --------------------------------------------------------------- graphics ---

def currently():
    w, gap, ch, rg = 1000, 22, 76, 16
    cw = (w - gap) / 2
    rows = (len(CURRENTLY) + 1) // 2
    h = rows * ch + (rows - 1) * rg
    alt = "Currently: " + "; ".join("".join(t for t, _ in parts) for _, parts in CURRENTLY)
    s = Svg(w, h, alt)
    for i, (kind, parts) in enumerate(CURRENTLY):
        x, y = (i % 2) * (cw + gap), (i // 2) * (ch + rg)
        s.add(f'<rect x="{x + .5:.1f}" y="{y + .5}" width="{cw - 1:.1f}" height="{ch - 1}" '
              f'rx="10" fill="{CARD}" stroke="{BORDER}"/>')
        s.add(icon(kind, x + 28, y + ch / 2 - 9, ICON_COLOURS[kind]))
        s.rich(x + 68, y + ch / 2 + 6.5,
               [(t, BRIGHT if b else TEXT, "B", 700 if b else 400) for t, b in parts], 17.5)
    s.save("currently")


def monitor():
    w, h = 320, 230
    s = Svg(w, h, "Illustration of a monitor showing code")
    s.defs.append('<filter id="glow" x="-40%" y="-40%" width="180%" height="180%">'
                  '<feGaussianBlur stdDeviation="14"/></filter>')
    sx, sy, sw, sh = 40, 18, 240, 150
    # glow, stand, screen
    s.add(f'<rect x="{sx + 10}" y="{sy + 30}" width="{sw - 20}" height="{sh - 20}" '
          f'rx="12" fill="{PURPLE}" opacity=".45" filter="url(#glow)"/>')
    s.add(f'<path d="M{w / 2 - 14} {sy + sh}h28l4 26h-36z" fill="{GREY}"/>')
    s.add(f'<rect x="{w / 2 - 50}" y="{sy + sh + 24}" width="100" height="6" rx="3" fill="{GREY}"/>')
    s.add(f'<rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" rx="12" fill="{CARD}" '
          f'stroke="{GREY}" stroke-width="2.5"/>')
    for i, c in enumerate((RED, YELLOW, GREEN)):
        s.add(f'<circle cx="{sx + 18 + i * 11}" cy="{sy + 17}" r="3.4" fill="{c}"/>')
    # code lines that gently "type" in a loop
    lines = [(0, 112, PURPLE), (14, 146, BLUE), (14, 96, TEAL), (28, 128, GREY),
             (0, 108, BLUE), (0, 56, PURPLE)]
    for i, (indent, lw, c) in enumerate(lines):
        x, y = sx + 18 + indent, sy + 34 + i * 17
        begin = f"{i * .35:.2f}s"
        s.add(f'<rect x="{x}" y="{y}" width="{lw}" height="6" rx="3" fill="{c}">'
              f'<animate attributeName="width" values="0;{lw};{lw};{lw}" '
              f'keyTimes="0;.18;.9;1" dur="6s" begin="{begin}" repeatCount="indefinite"/>'
              f'</rect>')
    # floating tags
    for x, y, label, d in ((6, 70, "</>", 0), (w - 54, 130, "{ }", 1.5)):
        tw = measure(label, "M", 500, 12) + 18
        s.add(f'<g><animateTransform attributeName="transform" type="translate" '
              f'values="0 0;0 -5;0 0" dur="4s" begin="{d}s" repeatCount="indefinite"/>'
              f'<rect x="{x}" y="{y}" width="{tw:.1f}" height="24" rx="6" fill="{CARD}" '
              f'stroke="{GREY}" stroke-width="1.5"/>')
        s.rich(x + 9, y + 16, [(label, BLUE, "M", 500)], 12)
        s.add("</g>")
    s.save("monitor")


if __name__ == "__main__":
    for old in os.listdir(OUT):
        if old.endswith(".svg"):
            os.remove(os.path.join(OUT, old))
    currently()
    monitor()
