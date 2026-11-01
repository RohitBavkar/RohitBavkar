#!/usr/bin/env python3
"""Builds the SVG sections used by the profile README.

GitHub READMEs can't use custom CSS or fonts, so each section is drawn as an
SVG with its fonts subset and embedded. Edit the CONTENT block below, then run:

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

WHOAMI = ("~/rohit", " $ whoami")
NAME = ("Rohit", "Bavkar")
INTRO = ("Backend engineer. Eleven years of shipping Java and Spring Boot "
         "systems, with work across full-stack, mobile and AI/ML.")
LOCATION = "Mumbai, India"
TIMEZONE = "IST · UTC+5:30"

RIGHT_NOW = [
    ("REVISING", "Core Java & DSA",
     "Working through Striver’s A2Z sheet alongside a Core Java refresh."),
    ("STUDYING", "Design patterns & system design",
     "The patterns behind large, maintainable backends."),
    ("BUILDING", "A SaaS product & a YouTube channel",
     "A product of my own on the side, and DEV — my channel."),
]

TOOLKIT = [
    ("core stack", "accent", ["Java", "Spring Boot", "Spring", "Hibernate", "MySQL"], None),
    ("worked across", "plain", ["Backend", "Full-stack", "Mobile", "AI / ML"], None),
    ("off the keyboard", "plain", ["Premiere Pro", "After Effects"],
     "— video editing & motion graphics"),
]

# (title, description, tech label, dot colour); file is work-<n>.svg
WORK = [
    ("[repo-name]", "[One line on what it does and why it’s interesting]",
     "[Java · Spring Boot]", "accent"),
    ("[repo-name]", "[One line on what it does and why it’s interesting]",
     "[Language · Framework]", "blue"),
]

# (label, file name, primary?)
BUTTONS = [
    ("YouTube — DEV", "btn-youtube", True),
    ("LinkedIn", "btn-linkedin", False),
    ("Portfolio & blog", "btn-portfolio", False),
    ("Email", "btn-email", False),
]

# ----------------------------------------------------------------- theme ---

BG = "#0d1117"
DOT = "#1a2129"
CARD = "#121821"
BORDER = "#262e38"
PILL = "#19202a"
PILL_BORDER = "#2b343f"
TEXT = "#eef1f4"
SUB = "#b4bcc6"
MUTED = "#808a96"
ACCENT = "#c8f169"
BLUE = "#79c0ff"
ORANGE = "#ffa657"
COMMENT = "#6e7681"

W = 1000          # design width of full-width panels
X0 = 56           # left gutter
X1 = W - 56       # right gutter

FONT_FILES = {
    ("B", 400): "bricolage-grotesque-latin-400-normal.woff2",
    ("B", 600): "bricolage-grotesque-latin-600-normal.woff2",
    ("B", 700): "bricolage-grotesque-latin-700-normal.woff2",
    ("B", 800): "bricolage-grotesque-latin-800-normal.woff2",
    ("M", 400): "jetbrains-mono-latin-400-normal.woff2",
    ("M", 500): "jetbrains-mono-latin-500-normal.woff2",
    ("M", 700): "jetbrains-mono-latin-700-normal.woff2",
}
_fonts = {}


def font(fam, wt):
    key = (fam, wt)
    if key not in _fonts:
        _fonts[key] = TTFont(os.path.join(FONT_DIR, FONT_FILES[key]))
    return _fonts[key]


def measure(text, fam, wt, size, ls=0.0):
    f = font(fam, wt)
    cmap, hmtx = f.getBestCmap(), f["hmtx"]
    upm = f["head"].unitsPerEm
    w = sum(hmtx[cmap.get(ord(c), cmap[ord("?")])][0] for c in text)
    return w / upm * size + ls * len(text)


def wrap(text, fam, wt, size, maxw):
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if cur and measure(trial, fam, wt, size) > maxw:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    return lines + [cur]


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


# ------------------------------------------------------------ svg builder ---

class Svg:
    def __init__(self, w, h, title):
        self.w, self.h, self.title = w, h, title
        self.defs, self.body, self.used = [], [], {}

    def add(self, s):
        self.body.append(s)

    def text(self, x, y, s, fam="B", wt=400, size=16, fill=TEXT,
             anchor="start", ls=0.0):
        self.used.setdefault((fam, wt), set()).update(s)
        a = f' text-anchor="{anchor}"' if anchor != "start" else ""
        l = f' letter-spacing="{ls}"' if ls else ""
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" class="{fam}{wt}" '
                 f'font-size="{size}" fill="{fill}"{a}{l}>{html.escape(s)}</text>')

    def spans(self, x, y, parts, fam="M", wt=400, size=14):
        """parts: list of (text, colour) rendered on one line."""
        inner = ""
        for s, c in parts:
            s = s.replace(" ", "\u00a0")  # keep indentation: SVG collapses spaces
            self.used.setdefault((fam, wt), set()).update(s)
            inner += f'<tspan fill="{c}">{html.escape(s)}</tspan>'
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" class="{fam}{wt}" '
                 f'font-size="{size}">{inner}</text>')

    def render(self):
        css = ""
        for (fam, wt), chars in sorted(self.used.items()):
            css += (f"@font-face{{font-family:{fam}{wt};src:url(data:font/woff2;"
                    f"base64,{embed(fam, wt, chars)}) format('woff2')}}"
                    f".{fam}{wt}{{font-family:{fam}{wt},"
                    f"{'ui-monospace,monospace' if fam == 'M' else 'system-ui,sans-serif'}}}")
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" '
            f'height="{self.h}" viewBox="0 0 {self.w} {self.h}" '
            f'xml:space="preserve" role="img" aria-label="{html.escape(self.title)}">'
            f"<title>{html.escape(self.title)}</title>"
            f"<style>{css}</style><defs>{''.join(self.defs)}</defs>"
            + "".join(self.body) + "</svg>\n")

    def save(self, name):
        with open(os.path.join(OUT, name + ".svg"), "w") as fh:
            fh.write(self.render())
        print("wrote", name + ".svg")


def panel(h, title):
    """Full-width dark panel with the dotted grid background."""
    s = Svg(W, h, title)
    s.defs.append('<pattern id="dots" width="22" height="22" '
                  'patternUnits="userSpaceOnUse">'
                  f'<circle cx="2" cy="2" r="1" fill="{DOT}"/></pattern>')
    s.add(f'<rect width="{W}" height="{h}" rx="16" fill="{BG}"/>')
    s.add(f'<rect width="{W}" height="{h}" rx="16" fill="url(#dots)"/>')
    return s


def card(s, x, y, w, h, fill=CARD, stroke=BORDER, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    s.add(f'<rect x="{x + .5}" y="{y + .5}" width="{w - 1}" height="{h - 1}" '
          f'rx="12" fill="{fill}" stroke="{stroke}"{d}/>')


def heading(s, y, num, title):
    s.text(X0, y, num, "M", 500, 13, ACCENT)
    s.text(X0 + 32, y + 1, title, "B", 800, 31, TEXT, ls=-0.8)


def arrow(s, x, y, colour, size=9):
    s.add(f'<path d="M{x} {y + size}L{x + size} {y}M{x + 2.5} {y}H{x + size}'
          f'V{y + size - 2.5}" fill="none" stroke="{colour}" stroke-width="1.7" '
          f'stroke-linecap="round" stroke-linejoin="round"/>')


def dot_after(s, x, baseline, r):
    s.add(f'<circle cx="{x + r:.1f}" cy="{baseline - r:.1f}" r="{r}" fill="{ACCENT}"/>')


# --------------------------------------------------------------- sections ---

def hero():
    s = panel(470, f"{NAME[0]} {NAME[1]}. {INTRO}")
    s.text(X0, 88, WHOAMI[0], "M", 500, 14, ACCENT)
    s.spans(X0 + measure(WHOAMI[0], "M", 500, 14), 88,
            [(WHOAMI[1], MUTED)], "M", 400, 14)

    size, ls = 92, -4.2
    s.text(X0 - 4, 190, NAME[0], "B", 800, size, TEXT, ls=ls)
    s.text(X0 - 4, 272, NAME[1], "B", 800, size, TEXT, ls=ls)
    dot_after(s, X0 - 4 + measure(NAME[1], "B", 800, size, ls) + 6, 272, 10)

    y = 328
    for line in wrap(INTRO, "B", 400, 20.5, 430):
        s.text(X0, y, line, "B", 400, 20.5, SUB)
        y += 30

    y += 18
    # map pin
    s.add(f'<g fill="none" stroke="{MUTED}" stroke-width="1.4">'
          f'<path d="M{X0 + 6} {y - 13.5}a4.8 4.8 0 0 1 4.8 4.8c0 3.6-4.8 8.2-4.8 '
          f'8.2s-4.8-4.6-4.8-8.2a4.8 4.8 0 0 1 4.8-4.8z"/>'
          f'<circle cx="{X0 + 6}" cy="{y - 8.7}" r="1.7"/></g>')
    s.text(X0 + 22, y, LOCATION, "M", 400, 13.5, MUTED)
    cx = X0 + 22 + measure(LOCATION, "M", 400, 13.5) + 22
    s.add(f'<g fill="none" stroke="{MUTED}" stroke-width="1.4" stroke-linecap="round">'
          f'<circle cx="{cx + 6}" cy="{y - 5}" r="6.2"/>'
          f'<path d="M{cx + 6} {y - 8.5}V{y - 5}l2.4 1.6"/></g>')
    s.text(cx + 21, y, TIMEZONE, "M", 400, 13.5, MUTED)

    # code card
    x, y0, w, h = 540, 56, 404, 384
    s.add(f'<rect x="{x}" y="{y0 + 6}" width="{w}" height="{h}" rx="14" '
          f'fill="#000" opacity="0.35"/>')
    card(s, x, y0, w, h)
    s.text(x + 20, y0 + 27, "Engineer.java", "M", 500, 12.5, TEXT)
    s.text(x + w - 20, y0 + 27, "Java 21", "M", 400, 12.5, MUTED, anchor="end")
    s.add(f'<line x1="{x + 1}" x2="{x + w - 1}" y1="{y0 + 44}" y2="{y0 + 44}" '
          f'stroke="{BORDER}"/>')
    K, F, Q, C = BLUE, TEXT, ORANGE, COMMENT
    code = [
        [("public record", K), (" Engineer(", F)],
        [("  String name,      ", F), ('// "Rohit Bavkar"', C)],
        [("  ", F), ("int", K), ("    years,     ", F), ("// 11", C)],
        [("  String base,      ", F), ('// "Mumbai, IN"', C)],
        [("  List<String> core ", F), ("// see below", C)],
        [(") {}", F)],
        [],
        [("var", K), (" me = ", F), ("new", K), (" Engineer(", F)],
        [("  ", F), ('"Rohit"', Q), (", ", F), ("11", Q), (", ", F),
         ('"Mumbai"', Q), (",", F)],
        [("  List.of(", F), ('"Java"', Q), (", ", F), ('"Spring Boot"', Q), (",", F)],
        [("          ", F), ('"Hibernate"', Q), (", ", F), ('"MySQL"', Q), (")", F)],
        [(");", F)],
    ]
    cy, step, fs = y0 + 82, 25, 14
    for line in code:
        if line:
            s.spans(x + 21, cy, line, "M", 400, fs)
        cy += step
    cw = measure("x", "M", 400, fs)
    s.add(f'<rect x="{x + 21 + 2 * cw + 2:.1f}" y="{cy - step - 13}" width="{cw:.1f}" '
          f'height="17" fill="{ACCENT}"><animate attributeName="opacity" '
          f'values="1;0" dur="1.1s" calcMode="discrete" repeatCount="indefinite"/>'
          f"</rect>")
    s.save("hero")


def right_now():
    alt = "Right now: " + "; ".join(f"{a.lower()} {b} — {c}" for a, b, c in RIGHT_NOW)
    s = panel(290, alt)
    heading(s, 52, "01", "Right now")
    gap = 17
    cw = (X1 - X0 - 2 * gap) / 3
    for i, (label, title, body) in enumerate(RIGHT_NOW):
        x, y = X0 + i * (cw + gap), 88
        card(s, x, y, cw, 180)
        s.text(x + 24, y + 37, label, "M", 700, 12, ACCENT, ls=1.4)
        ty = y + 70
        for line in wrap(title, "B", 700, 21, cw - 48):
            s.text(x + 24, ty, line, "B", 700, 21, TEXT, ls=-0.3)
            ty += 26
        ty += 8
        for line in wrap(body, "B", 400, 15, cw - 48):
            s.text(x + 24, ty, line, "B", 400, 15, SUB)
            ty += 22
    s.save("right-now")


def toolkit():
    alt = "Toolkit: " + "; ".join(f"{l}: {', '.join(p)}" for l, _, p, _ in TOOLKIT)
    row = 78
    top = 92
    s = panel(top + row * len(TOOLKIT) + 40, alt)
    heading(s, 52, "02", "Toolkit")
    for i, (label, style, pills, note) in enumerate(TOOLKIT):
        y = top + i * row
        s.add(f'<line x1="{X0}" x2="{X1}" y1="{y}" y2="{y}" stroke="{BORDER}"/>')
        mid = y + row / 2
        s.text(X0, mid + 5, label, "M", 400, 13.5, MUTED)
        px = 280
        for p in pills:
            pw = measure(p, "B", 600, 15.5) + 34
            if style == "accent":
                s.add(f'<rect x="{px + .5}" y="{mid - 18 + .5}" width="{pw - 1:.1f}" '
                      f'height="35" rx="17.5" fill="{ACCENT}" fill-opacity="0.06" '
                      f'stroke="{ACCENT}" stroke-opacity="0.9"/>')
                colour = ACCENT
            else:
                s.add(f'<rect x="{px + .5}" y="{mid - 18 + .5}" width="{pw - 1:.1f}" '
                      f'height="35" rx="17.5" fill="{PILL}" stroke="{PILL_BORDER}"/>')
                colour = TEXT
            s.text(px + pw / 2, mid + 5.5, p, "B", 600, 15.5, colour, anchor="middle")
            px += pw + 10
        if note:
            s.text(px + 6, mid + 5.5, note, "B", 400, 15.5, SUB)
    y = top + len(TOOLKIT) * row
    s.add(f'<line x1="{X0}" x2="{X1}" y1="{y}" y2="{y}" stroke="{BORDER}"/>')
    s.save("toolkit")


def section_heading(num, title, name):
    s = panel(84, title)
    heading(s, 56, num, title)
    s.save(name)


def work_cards():
    """Two half-width tiles that line up with the panels' gutters when shown
    side by side at 50% width each."""
    w, h, gap = W // 2, 172, 17
    cw = w - X0 - gap / 2
    for i, (title, desc, tech, dot) in enumerate(WORK, 1):
        s = Svg(w, h, f"{title}: {desc} ({tech})")
        x = X0 if i % 2 else gap / 2
        card(s, x, 0, cw, h)
        s.text(x + 28, 46, title, "M", 700, 15, TEXT)
        arrow(s, x + cw - 36, 32, MUTED)
        y = 84
        for line in wrap(desc, "B", 400, 16, cw - 56):
            s.text(x + 28, y, line, "B", 400, 16, SUB)
            y += 24
        s.add(f'<circle cx="{x + 32}" cy="{h - 38}" r="4.5" '
              f'fill="{ACCENT if dot == "accent" else BLUE}"/>')
        s.text(x + 46, h - 33.5, tech, "M", 400, 12.5, MUTED)
        s.save(f"work-{i}")


def outro():
    s = panel(150, "Let’s build something. Thanks for stopping by.")
    s.add(f'<line x1="{X0}" x2="{X1}" y1="24" y2="24" stroke="{BORDER}"/>')
    title = "Let’s build something"
    s.text(X0, 112, title, "B", 800, 54, TEXT, ls=-2.2)
    dot_after(s, X0 + measure(title, "B", 800, 54, -2.2) + 3, 112, 6.5)
    s.text(X1, 108, "// thanks for stopping by", "M", 400, 13.5, MUTED, anchor="end")
    s.save("outro")


def buttons():
    """Each button carries its own transparent spacing so the row lines up with
    the panels. Prints the width (as % of a panel) to use in the README."""
    for n, (label, name, primary) in enumerate(BUTTONS):
        tw = measure(label, "B", 700, 16)
        bw, h = tw + 62, 52
        left = X0 if n == 0 else 0
        w = left + bw + 12
        s = Svg(round(w), h, label)
        if primary:
            s.add(f'<rect x="{left}" width="{bw:.1f}" height="{h}" rx="11" fill="{ACCENT}"/>')
            fg = BG
        else:
            s.add(f'<rect x="{left + .5}" y=".5" width="{bw - 1:.1f}" height="{h - 1}" '
                  f'rx="11" fill="{CARD}" stroke="{BORDER}"/>')
            fg = TEXT
        s.text(left + 20, 31.5, label, "B", 700, 16, fg)
        arrow(s, left + 20 + tw + 13, 21.5, fg, 8)
        s.save(name)
        print(f"   {name}: width={round(w) / W * 100:.1f}%")


if __name__ == "__main__":
    hero()
    right_now()
    toolkit()
    section_heading("03", "Selected work", "selected-work")
    work_cards()
    section_heading("04", "Activity", "activity")
    outro()
    buttons()
