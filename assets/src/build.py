#!/usr/bin/env python3
"""Builds the SVG sections used by the profile README.

GitHub READMEs can't use custom CSS or fonts, so each section is drawn as an
SVG with its fonts subset and embedded. Card rows have transparent
backgrounds so they sit on GitHub's own page colour in light and dark mode.
The contribution snake is generated separately by .github/workflows/snake.yml.

Edit the CONTENT block below, then run:

    pip install fonttools brotli
    python3 assets/src/build.py
"""
import base64
import hashlib
import html
import io
import os
import re

from fontTools import subset
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
FONT_DIR = os.path.join(HERE, "fonts")
ICON_DIR = os.path.join(HERE, "icons")   # logos from Devicon (MIT) and Simple Icons (CC0)

# ---------------------------------------------------------------- content ---

HANDLE = "rohitbavkar"
ROLE = "Software Engineer · Mumbai, India"
NAME = "Rohit Bavkar"
# intro lines as (text, bold?) pieces
INTRO = [
    [("11 years building backend systems with ", False), ("Java & Spring Boot", True), (" —", False)],
    [("across full-stack, mobile and AI/ML.", False)],
]
# (label, dot colour) for the scrolling strip under the intro
MARQUEE = [("Java", "#f97316"), ("Spring Boot", "#6ad04b"), ("Spring", "#86d64a"),
           ("Hibernate", "#c9b56a"), ("MySQL", "#4f9cf0")]

# (label, logo file in assets/src/icons, fill for single-colour logos or None)
TECH = [
    ("Java", "java", None),
    ("Spring Boot", "springboot", "#6db33f"),
    ("Spring", "spring", "#6db33f"),
    ("Hibernate", "hibernate", None),
    ("MySQL", "mysql", None),
]

# (icon, title, subtitle)
RIGHT_NOW = [
    ("briefcase", "Working at Cognizant", "as a Senior Software Engineer"),
    ("leaf", "Building a SaaS product", "my own, from idea to launch"),
    ("spark", "Running my own AI agent", "Hermes on Oracle Cloud"),
    ("chat", "Open to collaborations", "backend, AI or SaaS ideas"),
]

CHANNEL = ("YOUTUBE · LAUNCHING SOON", "DEV — my channel")

SIDE_PROJECT = {
    "flow": [("chat", "Discord", "I chat"), ("spark", "Hermes Agent", "thinks & acts"),
             ("server", "Oracle Cloud", "free-tier VM")],
    "text": [[("My own AI agent — Nous Research’s ", False), ("Hermes", True),
              (", self-hosted on", False)],
             [("Oracle Cloud and talking to me over Discord.", False)]],
    "tags": ["Dokploy", "MySQL HeatWave", "Self-hosted"],
}

CTA = ("Let’s build", "something great", "Backend, AI, or a SaaS idea — say hi.")

BUTTONS = [("YouTube · DEV", "btn-youtube"), ("LinkedIn", "btn-linkedin"),
           ("Portfolio & blog", "btn-portfolio"), ("Email", "btn-email")]

# ----------------------------------------------------------------- theme ---

PAGE = "#0c0c0e"
CARD = "#131316"
BORDER = "#26262c"
INSET = "#1a1a1e"
INSET_BORDER = "#2d2d34"
TEXT = "#f4f4f5"
SUB = "#a1a1aa"
MUTED = "#71717a"
ORANGE = "#f97316"
ORANGE_SOFT = "#fdba74"
ORANGE_DEEP = "#7c2d12"
GREEN = "#4ade80"
EDGE = "#8b949e"     # text drawn outside cards: readable on light and dark pages

W = 1000
G = 20
PAD = 32

FONT_FILES = {
    ("B", 400): "bricolage-grotesque-latin-400-normal.woff2",
    ("B", 600): "bricolage-grotesque-latin-600-normal.woff2",
    ("B", 700): "bricolage-grotesque-latin-700-normal.woff2",
    ("B", 800): "bricolage-grotesque-latin-800-normal.woff2",
    ("M", 400): "jetbrains-mono-latin-400-normal.woff2",
    ("M", 500): "jetbrains-mono-latin-500-normal.woff2",
}
_fonts = {}


def font(fam, wt):
    if (fam, wt) not in _fonts:
        _fonts[(fam, wt)] = TTFont(os.path.join(FONT_DIR, FONT_FILES[(fam, wt)]))
    return _fonts[(fam, wt)]


def measure(text, fam, wt, size, ls=0.0):
    f = font(fam, wt)
    cmap, hmtx = f.getBestCmap(), f["hmtx"]
    w = sum(hmtx[cmap.get(ord(c), cmap[ord("?")])][0] for c in text)
    return w / f["head"].unitsPerEm * size + ls * len(text)


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

    def text(self, x, y, s, fam="B", wt=400, size=16, fill=TEXT, anchor="start",
             ls=0.0, extra=""):
        self.used.setdefault((fam, wt), set()).update(s)
        a = f' text-anchor="{anchor}"' if anchor != "start" else ""
        l = f' letter-spacing="{ls}"' if ls else ""
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" class="{fam}{wt}" font-size="{size}" '
                 f'fill="{fill}"{a}{l}{extra}>{html.escape(s)}</text>')

    def rich(self, x, y, parts, size, anchor="start"):
        """parts: (text, colour, family, weight)."""
        inner = ""
        for s, c, fam, wt in parts:
            self.used.setdefault((fam, wt), set()).update(s)
            inner += f'<tspan class="{fam}{wt}" fill="{c}">{html.escape(s)}</tspan>'
        a = f' text-anchor="{anchor}"' if anchor != "start" else ""
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}"{a}>{inner}</text>')

    def render(self):
        css = "text{white-space:pre}"
        for (fam, wt), chars in sorted(self.used.items()):
            fallback = "ui-monospace,monospace" if fam == "M" else "system-ui,sans-serif"
            css += (f"@font-face{{font-family:{fam}{wt};src:url(data:font/woff2;"
                    f"base64,{embed(fam, wt, chars)}) format('woff2')}}"
                    f".{fam}{wt}{{font-family:{fam}{wt},{fallback}}}")
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" '
                f'height="{self.h}" viewBox="0 0 {self.w} {self.h}" role="img" '
                f'aria-label="{html.escape(self.title)}">'
                f"<title>{html.escape(self.title)}</title>"
                f"<style>{css}</style><defs>{''.join(self.defs)}</defs>"
                + "".join(self.body) + "</svg>\n")

    def save(self, name):
        with open(os.path.join(OUT, name + ".svg"), "w") as fh:
            fh.write(self.render())
        print("wrote", name + ".svg")


def card(s, x, y, w, h, fill=CARD, stroke=BORDER, r=20, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    s.add(f'<rect x="{x + .5:.1f}" y="{y + .5:.1f}" width="{w - 1:.1f}" height="{h - 1:.1f}" '
          f'rx="{r}" fill="{fill}" stroke="{stroke}"{d}/>')


def glow(s, gid, cx, cy, r, colour=ORANGE, opacity=0.5):
    s.defs.append(f'<radialGradient id="{gid}" cx="{cx}" cy="{cy}" r="{r}" '
                  f'gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="{colour}" '
                  f'stop-opacity="{opacity}"/><stop offset="1" stop-color="{colour}" '
                  f'stop-opacity="0"/></radialGradient>')


def arrow(s, x, y, colour, size=8, width=1.7):
    s.add(f'<path d="M{x:.1f} {y + size:.1f}L{x + size:.1f} {y:.1f}'
          f'M{x + size * .3:.1f} {y:.1f}H{x + size:.1f}V{y + size * .7:.1f}" fill="none" '
          f'stroke="{colour}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/>')


def soft_pill(s, x, cy, text, size=15, h=34, wt=600, dot=None, fill=INSET, stroke=INSET_BORDER,
              fg=TEXT, mono=False):
    fam = "M" if mono else "B"
    pad = 16
    lead = 18 if dot else 0
    w = measure(text, fam, wt, size) + 2 * pad + lead
    s.add(f'<rect x="{x + .5:.1f}" y="{cy - h / 2 + .5:.1f}" width="{w - 1:.1f}" '
          f'height="{h - 1}" rx="{h / 2}" fill="{fill}" stroke="{stroke}"/>')
    if dot:
        s.add(f'<circle cx="{x + pad + 3.5:.1f}" cy="{cy}" r="3.5" fill="{dot}"/>')
    s.text(x + pad + lead, cy + size * .35, text, fam, wt, size, fg)
    return w


def icon(kind, x, y, colour, size=18):
    """Line icons drawn in an 18x18 box with top-left (x, y), scaled to size."""
    k = size / 18
    a = (f'fill="none" stroke="{colour}" stroke-width="{1.7 / k:.2f}" '
         f'stroke-linecap="round" stroke-linejoin="round"')
    paths = {
        "book": f'<path {a} d="M4 2h10v15l-5-3.5-5 3.5z"/>',
        "briefcase": (f'<rect {a} x="1.5" y="5" width="15" height="11" rx="2"/>'
                      f'<path {a} d="M6 5V3.5A1.5 1.5 0 0 1 7.5 2h3A1.5 1.5 0 0 1 12 3.5V5M1.5 10h15"/>'),
        "layers": f'<path {a} d="M9 2l8 4.5-8 4.5-8-4.5zM1 10.5l8 4.5 8-4.5"/>',
        "leaf": f'<path {a} d="M3 16c0-8 5-13 13-14 0 8-4 13-12 13M3 16l6-6"/>',
        "play": (f'<rect {a} x="1" y="3" width="16" height="12" rx="3"/>'
                 f'<path fill="{colour}" d="M7.5 6.5v5l4.2-2.5z"/>'),
        "chat": f'<path {a} d="M3 9a6 6 0 1 1 3 5.2L2.5 15.5 3.6 12A6 6 0 0 1 3 9z"/>',
        "spark": (f'<path fill="{colour}" d="M9 1.5l1.6 4.9L15.5 8l-4.9 1.6L9 14.5 7.4 9.6 2.5 8l4.9-1.6z"/>'
                  f'<path fill="{colour}" d="M14.5 12l.7 1.8 1.8.7-1.8.7-.7 1.8-.7-1.8-1.8-.7 1.8-.7z"/>'),
        "server": (f'<rect {a} x="2" y="2.5" width="14" height="5.5" rx="1.5"/>'
                   f'<rect {a} x="2" y="10" width="14" height="5.5" rx="1.5"/>'),
    }
    return f'<g transform="translate({x:.1f} {y:.1f}) scale({k:.3f})">{paths[kind]}</g>'


def logo(name, x, y, size, fill=None):
    """Inline a logo SVG from ICON_DIR into a size x size box at (x, y)."""
    with open(os.path.join(ICON_DIR, name + ".svg")) as fh:
        src = fh.read()
    view = re.search(r'viewBox="([^"]+)"', src).group(1)
    inner = re.sub(r"(?s)^.*?<svg[^>]*>|</svg>\s*$", "", src)
    inner = re.sub(r"(?s)<title>.*?</title>", "", inner)
    f = f' fill="{fill}"' if fill else ""
    return (f'<svg x="{x:.1f}" y="{y:.1f}" width="{size}" height="{size}" '
            f'viewBox="{view}"><g{f}>{inner}</g></svg>')


# --------------------------------------------------------------- sections ---

def hero():
    h = 500
    intro = " ".join("".join(t for t, _ in line) for line in INTRO)
    s = Svg(W, h, f"{NAME}. {ROLE}. {intro}")
    s.defs.append(f'<clipPath id="panel"><rect width="{W}" height="{h}" rx="24"/></clipPath>')
    glow(s, "g1", W / 2, -40, 560, "#ea580c", .55)
    glow(s, "fade", W / 2, 120, 520, "#ffffff", 1)
    s.defs.append('<mask id="gridmask"><rect width="100%" height="100%" fill="url(#fade)"/></mask>')
    s.defs.append('<pattern id="grid" width="44" height="44" patternUnits="userSpaceOnUse">'
                  '<path d="M44 0H0V44" fill="none" stroke="#ffffff" stroke-opacity=".06"/></pattern>')
    s.add('<g clip-path="url(#panel)">')
    s.add(f'<rect width="{W}" height="{h}" fill="{PAGE}"/>')
    s.add(f'<rect width="{W}" height="{h}" fill="url(#g1)"/>')
    s.add(f'<rect width="{W}" height="{h}" fill="url(#grid)" mask="url(#gridmask)"/>')

    # role pill
    pw = measure(ROLE, "B", 600, 15) + 66
    s.add(f'<rect x="{(W - pw) / 2:.1f}" y="62.5" width="{pw:.1f}" height="38" rx="19" '
          f'fill="#1c120c" fill-opacity=".85" stroke="#5a2a10"/>')
    s.add(f'<circle cx="{(W - pw) / 2 + 26:.1f}" cy="81.5" r="7" fill="{ORANGE}" fill-opacity=".25"/>')
    s.add(f'<circle cx="{(W - pw) / 2 + 26:.1f}" cy="81.5" r="3.6" fill="{ORANGE}"/>')
    s.text((W - pw) / 2 + 44, 86.8, ROLE, "B", 600, 15, "#f4e9e1")

    # name with a metallic gradient
    s.defs.append('<linearGradient id="metal" x1="0" y1="0" x2="0" y2="1">'
                  '<stop offset=".15" stop-color="#ffffff"/><stop offset="1" stop-color="#8f8f98"/>'
                  '</linearGradient>')
    size = 150
    ls = -size * .055
    nw = measure(NAME, "B", 800, size, ls)
    s.text((W - nw + ls) / 2, 268, NAME, "B", 800, size, "url(#metal)", ls=ls)  # no spacing after last letter

    y = 340
    for line in INTRO:
        s.rich(W / 2, y, [(t, TEXT if b else SUB, "B", 700 if b else 400) for t, b in line],
               21, anchor="middle")
        y += 32

    # scrolling strip, faded at both edges
    s.defs.append('<linearGradient id="edge" x1="0" x2="1">'
                  '<stop offset="0" stop-color="#fff" stop-opacity="0"/>'
                  '<stop offset=".18" stop-color="#fff"/><stop offset=".82" stop-color="#fff"/>'
                  '<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>')
    s.defs.append(f'<mask id="edgemask"><rect width="{W}" height="{h}" fill="url(#edge)"/></mask>')
    widths = [measure(t, "B", 600, 16) + 32 + 18 + 12 for t, _ in MARQUEE]
    span = sum(widths)
    s.add(f'<g mask="url(#edgemask)"><g>'
          f'<animateTransform attributeName="transform" type="translate" from="0 0" '
          f'to="{-span:.1f} 0" dur="28s" repeatCount="indefinite"/>')
    x = 20
    for _ in range(3):
        for (t, dot), wd in zip(MARQUEE, widths):
            soft_pill(s, x, 448, t, 16, 42, 600, dot, fill="#141416", stroke="#2a2a30")
            x += wd
    s.add("</g></g></g>")
    s.save("hero")


def stack_and_now():
    h = 340
    lw = 640
    alt = (f"Tech stack: {', '.join(t[0] for t in TECH)}. Right now: "
           + "; ".join(f"{t} ({d})" for _, t, d in RIGHT_NOW) + ".")
    s = Svg(W, h, alt)
    card(s, 0, 0, lw, h)
    s.text(PAD, 50, "Tech stack", "B", 700, 22.5, TEXT, ls=-0.3)
    s.text(lw - PAD, 48, "core", "M", 400, 13, MUTED, anchor="end")
    cols, gap = 3, 12
    tiles = TECH + [None]
    rows = -(-len(tiles) // cols)
    tw = (lw - 2 * PAD - (cols - 1) * gap) / cols
    th = min(96, (h - 82 - PAD - (rows - 1) * gap) / rows)  # fill the card height
    for i, t in enumerate(tiles):
        x = PAD + (i % cols) * (tw + gap)
        y = 82 + (i // cols) * (th + gap)
        if t is None:
            card(s, x, y, tw, th, fill="none", stroke=INSET_BORDER, r=12, dash="4 4")
            s.text(x + 16, y + th / 2 - 3, "+ always", "M", 400, 12.5, MUTED)
            s.text(x + 16, y + th / 2 + 15, "learning", "M", 400, 12.5, MUTED)
            continue
        label, name, fill = t
        card(s, x, y, tw, th, fill=INSET, stroke=INSET_BORDER, r=12)
        isz = 46
        ix, iy = x + 14, y + (th - isz) / 2
        s.add(f'<rect x="{ix}" y="{iy}" width="{isz}" height="{isz}" rx="12" fill="#f6f6f7"/>')
        s.add(logo(name, ix + 8, iy + 8, isz - 16, fill))
        room = tw - (isz + 14 + 12) - 6
        fs = 17
        words = label.split()
        fits = measure(label, "B", 700, fs) <= room
        lines = [label] if fits or len(words) == 1 else [" ".join(words[:-1]), words[-1]]
        while max(measure(l, "B", 700, fs) for l in lines) > room and fs > 12:
            fs -= .5
        ly = y + th / 2 + fs * .35 - (len(lines) - 1) * fs * .6
        for l in lines:
            s.text(ix + isz + 12, ly, l, "B", 700, fs, TEXT, ls=-0.2)
            ly += fs * 1.2

    x0, rw = lw + G, W - lw - G
    card(s, x0, 0, rw, h)
    s.text(x0 + PAD, 50, "Right now", "B", 700, 22.5, TEXT, ls=-0.3)
    y = 82
    for kind, title, sub in RIGHT_NOW:
        s.add(f'<rect x="{x0 + PAD + .5}" y="{y + .5}" width="41" height="41" rx="10" '
              f'fill="#1c130d" stroke="{ORANGE_DEEP}"/>')
        s.add(icon(kind, x0 + PAD + 12, y + 12, ORANGE, 18))
        s.text(x0 + PAD + 58, y + 18, title, "B", 700, 17, TEXT, ls=-0.2)
        s.text(x0 + PAD + 58, y + 37, sub, "B", 400, 14.5, SUB)
        y += 62
    s.save("stack")


def channel():
    w, h = 405, 330
    s = Svg(w + G, h, f"{CHANNEL[1]} — {CHANNEL[0].lower()}")  # gap baked in on the right
    s.defs.append(f'<clipPath id="cc"><rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="19"/></clipPath>')
    glow(s, "cg", w * .55, h * .55, 330, "#ea580c", .55)
    s.add(f'<g clip-path="url(#cc)"><rect width="{w}" height="{h}" fill="#140d09"/>'
          f'<rect width="{w}" height="{h}" fill="url(#cg)"/>')
    s.text(48, 168, "DEV", "B", 800, 190, "#ffffff", ls=-8, extra=' fill-opacity=".07"')
    s.add("</g>")
    card(s, 0, 0, w, h, fill="none", stroke="#6b2a0e")
    cx, cy = w / 2, 128
    s.add(f'<circle cx="{cx}" cy="{cy}" r="52" fill="#ffffff" fill-opacity=".08">'
          f'<animate attributeName="r" values="40;56" dur="2.4s" repeatCount="indefinite"/>'
          f'<animate attributeName="fill-opacity" values=".18;0" dur="2.4s" repeatCount="indefinite"/>'
          f'</circle>')
    s.add(f'<circle cx="{cx}" cy="{cy}" r="40" fill="#ffffff"/>')
    s.add(f'<path d="M{cx - 7} {cy - 11}v22l18-11z" fill="#111"/>')
    s.text(PAD, 254, CHANNEL[0], "M", 500, 13, ORANGE_SOFT, ls=1.6)
    s.text(PAD, 290, CHANNEL[1], "B", 800, 26, TEXT, ls=-0.6)
    s.save("channel")


def side_project():
    w, h = 575, 330
    sp = SIDE_PROJECT
    alt = ("Side project: " + " ".join("".join(t for t, _ in l) for l in sp["text"])
           + " Built with " + ", ".join(sp["tags"]) + ".")
    s = Svg(w, h, alt)
    card(s, 0, 0, w, h)
    s.text(PAD, 50, "Side project", "B", 700, 22.5, TEXT, ls=-0.3)
    tag = "self-hosted"
    tw = measure(tag, "M", 500, 13) + 40
    s.add(f'<rect x="{w - PAD - tw + .5:.1f}" y="27.5" width="{tw - 1:.1f}" height="29" rx="14.5" '
          f'fill="#0c2416" stroke="#1f6b3c"/>')
    s.add(f'<circle cx="{w - PAD - tw + 15:.1f}" cy="42" r="3" fill="{GREEN}"/>')
    s.text(w - PAD - tw + 25, 46.5, tag, "M", 500, 13, GREEN)

    boxes = [140, 168, 160]
    gap = (w - 2 * PAD - sum(boxes)) / 2
    x, y, bh = PAD, 80, 98
    for i, ((kind, title, sub), bw) in enumerate(zip(sp["flow"], boxes)):
        hot = i == 1
        card(s, x, y, bw, bh, fill="#24150b" if hot else INSET,
             stroke="#b4470f" if hot else INSET_BORDER, r=12)
        if hot:
            s.add(f'<rect x="{x + 14}" y="{y + bh / 2 - 18}" width="36" height="36" rx="9" fill="{ORANGE}"/>')
            s.add(icon(kind, x + 22, y + bh / 2 - 10, "#ffffff", 20))
        else:
            bg = "#1f2240" if kind == "chat" else "#2a1717"
            col = "#a5b4fc" if kind == "chat" else "#fca5a5"
            s.add(f'<rect x="{x + 14}" y="{y + bh / 2 - 18}" width="36" height="36" rx="9" fill="{bg}"/>')
            s.add(icon(kind, x + 23, y + bh / 2 - 9, col, 18))
        tx = x + 60
        words = title.split()
        lines = [title] if measure(title, "B", 700, 16) < bw - 70 else [" ".join(words[:-1]), words[-1]]
        ty = y + bh / 2 - 2 - (len(lines) - 1) * 9
        for l in lines:
            s.text(tx, ty, l, "B", 700, 16, TEXT, ls=-0.2)
            ty += 18
        s.text(tx, ty + 1, sub, "M", 400, 12, SUB)
        if i < 2:
            dx = x + bw + gap / 2
            s.add(f'<circle cx="{dx:.1f}" cy="{y + bh / 2}" r="3.2" fill="{ORANGE}">'
                  f'<animate attributeName="opacity" values="1;.3;1" dur="1.6s" begin="{i * .8}s" '
                  f'repeatCount="indefinite"/></circle>')
        x += bw + gap

    y = 222
    for line in sp["text"]:
        s.rich(PAD, y, [(t, TEXT if b else SUB, "B", 700 if b else 400) for t, b in line], 17)
        y += 26
    x = PAD
    for t in sp["tags"]:
        x += soft_pill(s, x, 296, t, 14, 32, 600) + 8
    s.save("side-project")


def activity_header():
    h = 74
    s = Svg(W, h, "Contribution activity")
    card(s, 0, 0, W, h)
    s.text(PAD, 46, "Contribution activity", "B", 700, 22.5, TEXT, ls=-0.3)
    s.text(W - PAD, 44, f"live on github.com/{HANDLE}", "M", 400, 13, MUTED, anchor="end")
    s.save("activity")


def cta():
    h = 230
    s = Svg(W, h, f"{CTA[0]} {CTA[1]}. {CTA[2]}")
    s.defs.append(f'<clipPath id="k"><rect x="1" y="1" width="{W - 2}" height="{h - 2}" rx="23"/></clipPath>')
    glow(s, "kg", W * .78, 20, 420, "#ea580c", .42)
    s.add(f'<g clip-path="url(#k)"><rect width="{W}" height="{h}" fill="{CARD}"/>'
          f'<rect width="{W}" height="{h}" fill="url(#kg)"/></g>')
    card(s, 0, 0, W, h, fill="none", r=24)
    size, ls = 48, -1.6
    s.text(46, 92, CTA[0], "B", 800, size, TEXT, ls=ls)
    s.text(46, 146, CTA[1], "B", 800, size, TEXT, ls=ls)
    sq = 10
    s.add(f'<rect x="{46 + measure(CTA[1], "B", 800, size, ls) + 3:.1f}" y="{146 - sq}" '
          f'width="{sq}" height="{sq}" fill="{ORANGE}"/>')
    s.text(46, 186, CTA[2], "B", 400, 17.5, SUB)
    s.save("cta")


def buttons():
    """Four equal tiles shown at 25% width each; offsets inside each tile
    make the gaps between buttons match the card gaps."""
    n = len(BUTTONS)
    tile, h = W / n, 58
    bw = (W - (n - 1) * G) / n
    for i, (label, name) in enumerate(BUTTONS):
        s = Svg(round(tile), h, label)
        x = i * (bw + G) - i * tile
        if i == 0:
            s.add(f'<rect x="{x:.1f}" width="{bw:.1f}" height="{h}" rx="12" fill="{ORANGE}"/>')
            fg = "#1a0d05"
        else:
            s.add(f'<rect x="{x + .5:.1f}" y=".5" width="{bw - 1:.1f}" height="{h - 1}" rx="12" '
                  f'fill="{CARD}" stroke="{INSET_BORDER}"/>')
            fg = TEXT
        s.text(x + 20, 35, label, "B", 700, 17, fg)
        arrow(s, x + bw - 32, 25, fg)
        s.save(name)


def footer():
    h = 60
    s = Svg(W, h, f"github.com/{HANDLE} — Made in Mumbai, IST")
    s.add(f'<line x1="0" x2="{W}" y1="8.5" y2="8.5" stroke="{EDGE}" stroke-opacity=".35"/>')
    s.text(0, 44, f"github.com/{HANDLE}", "M", 400, 14, EDGE)
    s.text(W, 44, "Made in Mumbai · IST", "M", 400, 14, EDGE, anchor="end")
    s.save("footer")


def stamp_readme():
    """Add ?v=<content hash> to every assets/*.svg link in README.md so
    browsers and GitHub's image cache fetch the new version after a change."""
    path = os.path.join(os.path.dirname(OUT), "README.md")
    with open(path) as fh:
        text = fh.read()

    def repl(m):
        with open(os.path.join(OUT, m.group(1) + ".svg"), "rb") as fh:
            digest = hashlib.sha1(fh.read()).hexdigest()[:8]
        return f"assets/{m.group(1)}.svg?v={digest}"

    text = re.sub(r"assets/([\w-]+)\.svg(?:\?v=[0-9a-f]+)?", repl, text)
    with open(path, "w") as fh:
        fh.write(text)
    print("stamped README.md")


if __name__ == "__main__":
    for old in os.listdir(OUT):
        if old.endswith(".svg"):
            os.remove(os.path.join(OUT, old))
    hero()
    stack_and_now()
    channel()
    side_project()
    activity_header()
    cta()
    buttons()
    footer()
    stamp_readme()
