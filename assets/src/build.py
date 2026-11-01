#!/usr/bin/env python3
"""Builds the SVG rows used by the profile README (bento layout).

GitHub READMEs can't use custom CSS or fonts, so each row is drawn as an SVG
with its fonts subset and embedded. Backgrounds are transparent so the cards
sit on GitHub's own page colour in both light and dark mode.

Edit the CONTENT block below, then run:

    pip install fonttools brotli
    python3 assets/src/build.py
"""
import base64
import glob
import html
import io
import math
import os

from fontTools import subset
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
FONT_DIR = os.path.join(HERE, "fonts")

# ---------------------------------------------------------------- content ---

HANDLE = "rohitbavkar"
TAGS = ["backend", "full-stack", "mobile", "ai/ml"]
STATUS = "Building a SaaS product"
NAME = ("Rohit", "Bavkar")
# (text, bold?) pieces of the intro paragraph
INTRO = [("Backend engineer with ", False), ("11 years", True),
         (" of shipping Java and Spring Boot systems — and work across "
          "full-stack, mobile and AI/ML.", False)]

RIGHT_NOW = [
    ("Revising Core Java & DSA",
     "Working through Striver’s A2Z sheet, one topic at a time."),
    ("Studying design patterns & system design",
     "The ideas behind large, maintainable backends."),
    ("Building a SaaS product & DEV",
     "A product of my own, and my YouTube channel."),
]

CITY = ("Mumbai,", "India")
TIMEZONE = "IST · UTC+05:30"

CORE_STACK = ["Java", "Spring Boot", "Hibernate", "MySQL", "Spring"]  # first is highlighted
WORKED_ACROSS = ["Backend", "Full-stack", "Mobile", "AI / ML"]
OFF_KEYBOARD = "I edit video and build motion graphics."
TOOLS = ["Premiere Pro", "After Effects"]

# (title, description, tech label, dot colour); file is repo-<n>.svg
REPOS = [
    ("[repo-name]", "[One line on what it does and why it’s interesting]",
     "[Java · Spring Boot]", "accent"),
    ("[repo-name]", "[One line on what it does and why it’s interesting]",
     "[Language · Framework]", "blue"),
]

# (label, file name); the first is highlighted
BUTTONS = [
    ("YouTube · DEV", "btn-youtube"),
    ("LinkedIn", "btn-linkedin"),
    ("Portfolio & blog", "btn-portfolio"),
    ("Email", "btn-email"),
]

# ----------------------------------------------------------------- theme ---

CARD = "#11161e"
BORDER = "#252c36"
INSET = "#19202a"
INSET_BORDER = "#2b343f"
TEXT = "#eef1f4"
SUB = "#b4bcc6"
MUTED = "#808a96"
FAINT = "#3b4450"
ACCENT = "#c8f169"
INK = "#0d1117"
BLUE = "#79c0ff"
ORANGE = "#ffa657"
COMMENT = "#6e7681"
LINE = "#2a333e"
EDGE = "#8b949e"    # text outside cards: readable on light and dark pages

W = 1000            # every row is 1000 units wide and shown at width=100%
G = 22              # gap between cards
PAD = 36            # card inner padding
SPLIT = 574         # width of the left card in rows 2 and 3

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
    if (fam, wt) not in _fonts:
        _fonts[(fam, wt)] = TTFont(os.path.join(FONT_DIR, FONT_FILES[(fam, wt)]))
    return _fonts[(fam, wt)]


def measure(text, fam, wt, size, ls=0.0):
    f = font(fam, wt)
    cmap, hmtx = f.getBestCmap(), f["hmtx"]
    w = sum(hmtx[cmap.get(ord(c), cmap[ord("?")])][0] for c in text)
    return w / f["head"].unitsPerEm * size + ls * len(text)


def wrap(text, fam, wt, size, maxw, ls=0.0):
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if cur and measure(trial, fam, wt, size, ls) > maxw:
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
    sub.populate(text="".join(sorted(chars)) + "  ")
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

    def _use(self, fam, wt, s):
        self.used.setdefault((fam, wt), set()).update(s)

    def text(self, x, y, s, fam="B", wt=400, size=16, fill=TEXT,
             anchor="start", ls=0.0):
        self._use(fam, wt, s)
        a = f' text-anchor="{anchor}"' if anchor != "start" else ""
        l = f' letter-spacing="{ls}"' if ls else ""
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" class="{fam}{wt}" '
                 f'font-size="{size}" fill="{fill}"{a}{l}>{html.escape(s)}</text>')

    def rich(self, x, y, parts, size):
        """parts: (text, colour, family, weight) pieces on one line."""
        inner = ""
        for s, c, fam, wt in parts:
            if fam == "M":
                s = s.replace(" ", " ")  # keep code indentation
            self._use(fam, wt, s)
            inner += (f'<tspan class="{fam}{wt}" fill="{c}">'
                      f"{html.escape(s)}</tspan>")
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


def card(s, x, y, w, h, fill=CARD, stroke=BORDER, r=18):
    s.add(f'<rect x="{x + .5:.1f}" y="{y + .5:.1f}" width="{w - 1:.1f}" '
          f'height="{h - 1:.1f}" rx="{r}" fill="{fill}" stroke="{stroke}"/>')


def label(s, x, y, text):
    s.text(x, y, text.upper(), "M", 500, 13, MUTED, ls=2.2)


def hline(s, x1, x2, y, colour=BORDER):
    s.add(f'<line x1="{x1:.1f}" x2="{x2:.1f}" y1="{y:.1f}" y2="{y:.1f}" stroke="{colour}"/>')


def arrow(s, x, y, colour, size=9, width=1.8):
    s.add(f'<path d="M{x:.1f} {y + size:.1f}L{x + size:.1f} {y:.1f}'
          f'M{x + size * .3:.1f} {y:.1f}H{x + size:.1f}V{y + size * .7:.1f}" '
          f'fill="none" stroke="{colour}" stroke-width="{width}" '
          f'stroke-linecap="round" stroke-linejoin="round"/>')


def pill(s, x, cy, text, size, wt, h, style, padx):
    """style: 'accent' (filled), 'outline' or 'soft'. Returns its width."""
    w = measure(text, "B", wt, size) + 2 * padx
    y = cy - h / 2
    if style == "accent":
        s.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h}" '
              f'rx="{h * .3:.1f}" fill="{ACCENT}"/>')
        fg = INK
    elif style == "outline":
        s.add(f'<rect x="{x + .5:.1f}" y="{y + .5:.1f}" width="{w - 1:.1f}" '
              f'height="{h - 1}" rx="{h * .3:.1f}" fill="none" stroke="{INSET_BORDER}"/>')
        fg = TEXT
    else:
        s.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h}" '
              f'rx="{h / 2:.1f}" fill="{INSET}"/>')
        fg = TEXT
    s.text(x + w / 2, cy + size * .35, text, "B", wt, size, fg, anchor="middle")
    return w


def blink(s, x, y, w, h):
    s.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h}" fill="{ACCENT}">'
          f'<animate attributeName="opacity" values="1;0" dur="1.1s" '
          f'calcMode="discrete" repeatCount="indefinite"/></rect>')


# ------------------------------------------------------------------- rows ---

def topbar():
    s = Svg(W, 56, f"{HANDLE} / README.md")
    s.rich(2, 26, [(f"[{HANDLE}]", EDGE, "M", 500), (" / README.md", EDGE, "M", 400)], 14.5)
    x = W - 2
    for i, tag in enumerate(reversed(TAGS)):
        s.text(x, 26, tag, "M", 400, 14.5, EDGE, anchor="end")
        x -= measure(tag, "M", 400, 14.5)
        if i < len(TAGS) - 1:
            s.text(x - 14, 26, "·", "M", 400, 14.5, EDGE, anchor="middle")
            x -= 28
    hline(s, 0, W, 55, "#8b949e55")
    s.save("topbar")


def hero():
    intro = "".join(t for t, _ in INTRO)
    s = Svg(W, 515, f"Hi, I’m {NAME[0]} {NAME[1]}. {intro}")
    hw = 516
    card(s, 0, 0, hw, 515)

    # status pill
    pw = measure(STATUS, "M", 500, 13.5) + 58
    s.add(f'<rect x="{PAD + 4}.5" y="41.5" width="{pw:.1f}" height="33" rx="16.5" '
          f'fill="{INSET}" stroke="{INSET_BORDER}"/>')
    s.add(f'<circle cx="{PAD + 26}" cy="58" r="4.5" fill="{ACCENT}"/>')
    s.text(PAD + 42, 62.5, STATUS, "M", 500, 13.5, TEXT)

    s.text(PAD + 4, 122, "Hi, I’m", "M", 400, 15, MUTED)

    size = 118
    ls = -size * .055
    s.text(PAD, 236, NAME[0], "B", 800, size, TEXT, ls=ls)
    s.text(PAD, 336, NAME[1], "B", 800, size, TEXT, ls=ls)
    r = 11
    s.add(f'<circle cx="{PAD + measure(NAME[1], "B", 800, size, ls) + r + 4:.1f}" '
          f'cy="{336 - r}" r="{r}" fill="{ACCENT}"/>')

    # intro paragraph with a bold run, wrapped by hand across the pieces
    size, maxw, y = 20.5, hw - 2 * PAD - 8, 400
    words = []
    for text, bold in INTRO:
        for i, wd in enumerate(text.split(" ")):
            if wd:
                words.append((wd, bold, i == 0 and not text.startswith(" ")))
    line, width = [], 0.0
    lines = []
    for wd, bold, glued in words:
        wt = 700 if bold else 400
        ww = measure(wd + " ", "B", wt, size)
        if line and width + ww > maxw:
            lines.append(line)
            line, width = [], 0.0
        line.append((wd, bold))
        width += ww
    lines.append(line)
    for ln in lines:
        parts = []
        for i, (wd, bold) in enumerate(ln):
            sep = "" if i == len(ln) - 1 else " "
            parts.append((wd + sep, TEXT if bold else SUB, "B", 700 if bold else 400))
        s.rich(PAD + 4, y, parts, size)
        y += 31

    # code card
    cx, cw = hw + G, W - hw - G
    card(s, cx, 0, cw, 515)
    s.add(f'<path d="M{cx + 1} 47V18a17 17 0 0 1 17-17H{cx + 158}V47z" fill="{INSET}"/>')
    hline(s, cx + 1, cx + cw - 1, 47.5)
    s.add(f'<line x1="{cx + 158.5}" x2="{cx + 158.5}" y1="1" y2="47" stroke="{BORDER}"/>')
    s.add(f'<rect x="{cx + 1}" y="45" width="157" height="2.5" fill="{ACCENT}"/>')
    s.text(cx + 20, 29, "Engineer.java", "M", 500, 13.5, TEXT)
    s.text(cx + 178, 29, "Now.java", "M", 400, 13.5, MUTED)

    K, F, Q, C, A = BLUE, TEXT, ORANGE, COMMENT, ACCENT
    code = [
        [("public record ", K), ("Engineer", A), ("(", F)],
        [("    String name,", F)],
        [("    ", F), ("int", K), (" yearsShipping,", F)],
        [("    String basedIn,", F)],
        [("    List<String> coreStack", F)],
        [(") {}", F)],
        [],
        [("var", K), (" rohit = ", F), ("new ", K), ("Engineer", A), ("(", F)],
        [("    ", F), ('"Rohit Bavkar"', Q), (", ", F), ("11", Q), (", ", F),
         ('"Mumbai, IN"', Q), (",", F)],
        [("    List.of(", F), ('"Java"', Q), (", ", F), ('"Spring Boot"', Q), (",", F)],
        [("            ", F), ('"Hibernate"', Q), (", ", F), ('"MySQL"', Q), ("));", F)],
        [],
        [("// always learning", C)],
    ]
    fs, step, y = 14.2, 26.6, 90
    for n, line in enumerate(code, 1):
        s.text(cx + 34, y, str(n), "M", 400, 12.5, FAINT, anchor="end")
        if line:
            s.rich(cx + 54, y, [(t, c, "M", 400) for t, c in line], fs)
        y += step
    chw = measure("x", "M", 400, fs)
    blink(s, cx + 54 + chw * (len("// always learning") + .4), y - step - 13.5, chw * .9, 18)
    s.save("hero")


def now_and_place():
    alt = "Right now: " + "; ".join(f"{t} — {d}" for t, d in RIGHT_NOW)
    alt += f". Based in {' '.join(CITY)}, {TIMEZONE}."
    h = 410
    s = Svg(W, h, alt)
    card(s, 0, 0, SPLIT, h)
    label(s, PAD, 46, "Right now")
    y = 70
    hline(s, PAD, SPLIT - PAD, y)
    for i, (title, desc) in enumerate(RIGHT_NOW, 1):
        y += 41
        s.text(PAD, y, f"{i:02d}", "M", 500, 14, ACCENT)
        for ln in wrap(title, "B", 700, 21, SPLIT - PAD - 92, -0.3):
            s.text(92, y, ln, "B", 700, 21, TEXT, ls=-0.3)
            y += 27
        s.text(92, y + 2, desc, "B", 400, 16, SUB)
        y += 38
        if i < len(RIGHT_NOW):
            hline(s, PAD, SPLIT - PAD, y)

    # based-in card with a wireframe globe
    x0, w = SPLIT + G, W - SPLIT - G
    card(s, x0, 0, w, h)
    s.defs.append(f'<clipPath id="c"><rect x="{x0 + 1}" y="1" width="{w - 2}" '
                  f'height="{h - 2}" rx="17"/></clipPath>')
    gx, gy, r = x0 + 300, 150, 125
    g = [f'<circle cx="{gx}" cy="{gy}" r="{r}"/>']
    for deg in (25, 55, 80):
        g.append(f'<ellipse cx="{gx}" cy="{gy}" rx="{r * math.cos(math.radians(deg)):.1f}" ry="{r}"/>')
    for lat in (-50, -22, 0, 22, 50):
        rr = r * math.cos(math.radians(lat))
        g.append(f'<ellipse cx="{gx}" cy="{gy - r * math.sin(math.radians(lat)):.1f}" '
                 f'rx="{rr:.1f}" ry="{rr * .2:.1f}"/>')
    s.add(f'<g clip-path="url(#c)" fill="none" stroke="{LINE}" stroke-width="1.3">'
          + "".join(g) + "</g>")
    mx, my = gx + 45, gy - 22
    s.add(f'<circle cx="{mx}" cy="{my}" r="9" fill="none" stroke="{ACCENT}" stroke-opacity=".6">'
          '<animate attributeName="r" values="9;22" dur="2.2s" repeatCount="indefinite"/>'
          '<animate attributeName="stroke-opacity" values=".6;0" dur="2.2s" '
          'repeatCount="indefinite"/></circle>')
    s.add(f'<circle cx="{mx}" cy="{my}" r="12" fill="{ACCENT}" fill-opacity=".18"/>')
    s.add(f'<circle cx="{mx}" cy="{my}" r="6" fill="{ACCENT}"/>')
    label(s, x0 + PAD, 46, "Based in")
    s.text(x0 + PAD, 298, CITY[0], "B", 800, 40, TEXT, ls=-1.2)
    s.text(x0 + PAD, 340, CITY[1], "B", 800, 40, TEXT, ls=-1.2)
    s.text(x0 + PAD, 376, TIMEZONE, "M", 400, 14, MUTED)
    s.save("now")


def stack_and_craft():
    alt = (f"Core stack: {', '.join(CORE_STACK)}. Worked across: {', '.join(WORKED_ACROSS)}. "
           f"Off the keyboard: {OFF_KEYBOARD} {' and '.join(TOOLS)}.")
    h = 350
    s = Svg(W, h, alt)
    card(s, 0, 0, SPLIT, h)
    label(s, PAD, 46, "Core stack")
    x, cy = PAD, 106
    for i, p in enumerate(CORE_STACK):
        pw = measure(p, "B", 700, 23) + 44
        if x + pw > SPLIT - PAD:
            x, cy = PAD, cy + 69
        pill(s, x, cy, p, 23, 700, 57, "accent" if i == 0 else "outline", 22)
        x += pw + 12
    hline(s, PAD, SPLIT - PAD, cy + 54)
    label(s, PAD, cy + 92, "Worked across")
    x = PAD
    for p in WORKED_ACROSS:
        x += pill(s, x, cy + 130, p, 16.5, 600, 34, "soft", 16) + 10

    x0, w = SPLIT + G, W - SPLIT - G
    card(s, x0, 0, w, h)
    label(s, x0 + PAD, 46, "Off the keyboard")
    # timeline: three tracks, keyframes and a playhead
    tx, tw = x0 + PAD - 6, w - 2 * PAD + 6
    keys = [([.12, .48], "#e6edf3"), ([.27, .52, .72], ORANGE), ([.05, .30], BLUE)]
    for i, (pos, colour) in enumerate(keys):
        ty = 100 + i * 28
        s.add(f'<rect x="{tx}" y="{ty - 6}" width="{tw}" height="12" rx="3" fill="{INSET}"/>')
        for p in pos:
            kx = tx + 18 + p * (tw - 36)
            s.add(f'<rect x="{kx - 4.5:.1f}" y="{ty - 4.5}" width="9" height="9" '
                  f'fill="{colour}" transform="rotate(45 {kx:.1f} {ty})"/>')
    px = tx + .44 * tw
    s.add(f'<rect x="{px - 6:.1f}" y="74" width="12" height="9" rx="2" fill="{ACCENT}"/>')
    s.add(f'<line x1="{px:.1f}" x2="{px:.1f}" y1="80" y2="178" stroke="{ACCENT}" stroke-width="2"/>')
    y = 228
    for ln in wrap(OFF_KEYBOARD, "B", 700, 23, w - 2 * PAD, -0.4):
        s.text(x0 + PAD, y, ln, "B", 700, 23, TEXT, ls=-0.4)
        y += 30
    x = x0 + PAD
    for p in TOOLS:
        x += pill(s, x, cy + 130, p, 16.5, 600, 34, "soft", 16) + 10
    s.save("stack")


def repos():
    """Two half-width tiles; shown side by side at 50% each they line up
    with the full-width rows."""
    w, h = W // 2, 229
    cw = w - G / 2
    for i, (title, desc, tech, dot) in enumerate(REPOS, 1):
        s = Svg(w, h, f"Featured repo {title}: {desc} ({tech})")
        x = 0 if i % 2 else G / 2
        card(s, x, 0, cw, h)
        label(s, x + PAD, 54, "Featured repo")
        s.add(f'<circle cx="{x + cw - 50}" cy="50" r="18" fill="none" stroke="{INSET_BORDER}"/>')
        arrow(s, x + cw - 54, 46, TEXT, 8, 1.7)
        s.text(x + PAD, 114, title, "B", 800, 27, TEXT, ls=-0.6)
        y = 156
        for ln in wrap(desc, "B", 400, 16.5, cw - 2 * PAD):
            s.text(x + PAD, y, ln, "B", 400, 16.5, SUB)
            y += 24
        s.add(f'<circle cx="{x + PAD + 4}" cy="{h - 37}" r="4.5" '
              f'fill="{ACCENT if dot == "accent" else BLUE}"/>')
        s.text(x + PAD + 18, h - 32.5, tech, "M", 400, 13, MUTED)
        s.save(f"repo-{i}")


def outro():
    h = 240
    s = Svg(W, h, "Let’s build something. Thanks for stopping by.")
    card(s, 0, 0, W, h)
    size, ls = 64, -2.6
    s.text(46, 112, "Let’s build", "B", 800, size, TEXT, ls=ls)
    s.text(46, 178, "something", "B", 800, size, TEXT, ls=ls)
    r = 7.5
    s.add(f'<circle cx="{46 + measure("something", "B", 800, size, ls) + r + 3:.1f}" '
          f'cy="{178 - r}" r="{r}" fill="{ACCENT}"/>')
    s.text(W - 46, 172, "// thanks for stopping by", "M", 400, 14, MUTED, anchor="end")
    s.save("outro")


def buttons():
    """Four equal tiles at 25% width each; the transparent offsets inside
    each tile make the gaps between buttons match the card gaps."""
    n = len(BUTTONS)
    tile = W / n
    bw, h = (W - (n - 1) * G) / n, 62
    for i, (text, name) in enumerate(BUTTONS):
        s = Svg(round(tile), h, text)
        x = i * (bw + G) - i * tile
        if i == 0:
            s.add(f'<rect x="{x:.1f}" width="{bw:.1f}" height="{h}" rx="12" fill="{ACCENT}"/>')
            fg = INK
        else:
            s.add(f'<rect x="{x + .5:.1f}" y=".5" width="{bw - 1:.1f}" height="{h - 1}" '
                  f'rx="12" fill="{CARD}" stroke="{INSET_BORDER}"/>')
            fg = TEXT
        s.text(x + 22, 37, text, "B", 700, 17.5, fg)
        arrow(s, x + bw - 34, 27, fg, 8)
        s.save(name)


if __name__ == "__main__":
    for old in glob.glob(os.path.join(OUT, "*.svg")):
        os.remove(old)
    topbar()
    hero()
    now_and_place()
    stack_and_craft()
    repos()
    outro()
    buttons()
