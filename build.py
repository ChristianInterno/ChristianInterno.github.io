#!/usr/bin/env python3
"""
Builds christianinterno.com from content.py.

    python3 build.py

Writes index.html, one folder per page, a page per blog post (from posts/), the blog feed, 404.html, robots.txt,
CNAME and .nojekyll next to this file. Needs nothing beyond Python 3.
"""
import datetime
import html
import json
import math
import os
import re
import sys

sys.dont_write_bytecode = True
import content as C  # noqa: E402

ROOT = os.path.dirname(os.path.abspath(__file__))
TODAY = datetime.date.today()
UPDATED = TODAY.strftime("%B %Y")
URL = C.SITE["url"].rstrip("/")
ME = C.SITE["name"]
HAS_CV = os.path.exists(os.path.join(ROOT, C.SITE["cv"]))
LISTED = C.SITE.get("listed", True)


def _v(rel):
    """A short fingerprint of a file, so browsers fetch it again whenever it changes."""
    import hashlib
    with open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.sha1(fh.read()).hexdigest()[:8]


V_CSS, V_JS, V_ME = _v("assets/css/site.css"), _v("assets/js/lake.js"), _v("assets/img/me.jpg")

# (folder, menu label, <title>, meta description)
PAGES = [
    ("", "About", ME,
     f"{ME} is a machine learning researcher working on representation learning, world models, "
     "physical reasoning and distributed learning."),
    ("research/", "Research", f"Research · {ME}",
     f"Research by {ME}: the geometry of learned representations, world models and physical reasoning, "
     "and distributed learning."),
    ("publications/", "Publications", f"Publications · {ME}",
     f"Papers and preprints by {ME}, with BibTeX."),
    ("code/", "Code", f"Code · {ME}", f"Code and datasets by {ME}."),
    ("collaborate/", "Collaborate", f"Collaborate · {ME}",
     f"Working with {ME}: how to get in touch, co-authors, students and service."),
    ("blog/", "Blog", f"Blog · {ME}", f"Notes by {ME}."),
]

esc = lambda s: html.escape(s, quote=True)
plain = lambda s: re.sub(r"<[^>]+>", "", s)


# ---------------------------------------------------------------- names

PARTICLES = {"van", "von", "der", "den", "de", "del", "della", "di", "da", "du", "le", "la", "dos", "das", "ter", "ten"}


def split_name(full):
    toks = full.split()
    for i, t in enumerate(toks[1:], 1):
        if t in PARTICLES:
            return toks[:i], toks[i:]
    return toks[:-1], toks[-1:]


def author_html(name):
    star = name.endswith("*")
    name = name.rstrip("*")
    given, last = split_name(name)
    initials = ["-".join(p[0] + "." for p in g.split("-")) for g in given]
    shown = "&nbsp;".join(initials + last)
    if name == ME:
        shown = f"<b>{shown}</b>"
    return shown + ("*" if star else "")


# ---------------------------------------------------------------- BibTeX

ACCENTS = {
    "à": "{\\`a}", "á": "{\\'a}", "â": "{\\^a}", "ä": '{\\"a}', "ã": "{\\~a}", "å": "{\\aa}",
    "è": "{\\`e}", "é": "{\\'e}", "ê": "{\\^e}", "ë": '{\\"e}',
    "ì": "{\\`\\i}", "í": "{\\'\\i}", "î": "{\\^\\i}", "ï": '{\\"\\i}',
    "ò": "{\\`o}", "ó": "{\\'o}", "ô": "{\\^o}", "ö": '{\\"o}', "õ": "{\\~o}", "ø": "{\\o}",
    "ù": "{\\`u}", "ú": "{\\'u}", "û": "{\\^u}", "ü": '{\\"u}',
    "ñ": "{\\~n}", "ç": "{\\c{c}}", "ß": "{\\ss}", "ş": "{\\c{s}}", "ğ": "{\\u{g}}",
    "Ä": '{\\"A}', "Ö": '{\\"O}', "Ü": '{\\"U}', "É": "{\\'E}", "Ç": "{\\c{C}}", "Ş": "{\\c{S}}",
    "’": "'", "‘": "'", "–": "--", "—": "---", "‑": "-", "&": "\\&",
}


def latex(s):
    s = html.unescape(plain(s))
    return "".join(ACCENTS.get(ch, ch) for ch in s)


def protect(title):
    # keep acronyms and CamelCase as written, whatever the bibliography style does
    out = []
    for w in title.split(" "):
        m = re.match(r"^([\W]*)(.*?)([\W]*)$", w)
        lead, core, tail = m.groups()
        if re.search(r"[A-Z]", core[1:]):
            core = "{" + core + "}"
        out.append(lead + core + tail)
    return " ".join(out)


def bib_name(name):
    given, last = split_name(name.rstrip("*"))
    return " ".join(last) + (", " + " ".join(given) if given else "")


def bibtex(p):
    kind = {"conf": "inproceedings", "journal": "article", "arxiv": "article"}[p["bib"]]
    f = [("title", protect(p["title"])), ("author", " and ".join(bib_name(a) for a in p["authors"]))]
    if p["bib"] == "conf":
        f.append(("booktitle", p["booktitle"]))
    elif p["bib"] == "journal":
        f.append(("journal", p["journal"]))
        f += [(k, p[k]) for k in ("volume", "number", "pages") if p.get(k)]
    else:
        f.append(("journal", f"arXiv preprint arXiv:{p['arxiv']}"))
    f.append(("year", str(p["year"])))
    if p.get("doi"):
        f.append(("doi", p["doi"]))
    body = ",\n".join(f"  {k} = {{{latex(v)}}}" for k, v in f)
    return f"@{kind}{{{p['key']},\n{body}\n}}"


# ---------------------------------------------------------------- pictures
# Small pencil drawings in the site's colours (they follow light and dark mode); the walkway is
# coloured in orange, the way Christo coloured the piers into his drawings.

def _rng(seed):
    s = (seed * 7919 + 13) % 2147483647 or 1

    def r():
        nonlocal s
        s = (s * 16807) % 2147483647
        return (s - 1) / 2147483646
    return r


def _hand(seed, amp=1.0):
    """A hand is never ruler-straight: a slow, seeded wobble."""
    r = _rng(seed)
    p0, p1, p2 = r() * 6.283, r() * 6.283, r() * 6.283
    return lambda x: amp * (0.55 * math.sin(x / 61 + p0) + 0.32 * math.sin(x / 27 + p1) + 0.16 * math.sin(x / 11.5 + p2))


def _pts(seq):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in seq)


def _dense(points, step=5):
    out = []
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        m = max(1, math.ceil((abs(x1 - x0) + abs(y1 - y0)) / step))
        out += [(x0 + (x1 - x0) * t / m, y0 + (y1 - y0) * t / m) for t in range(m)]
    return out + [points[-1]]


def _wobble(d, h, off=0.0):
    out = []
    for i, (x, y) in enumerate(d):
        j = i + 1 if i < len(d) - 1 else i - 1
        steep = abs(d[j][1] - y) > abs(d[j][0] - x)
        w = h(x + y)
        out.append((x + off + (w if steep else 0), y + off + (0 if steep else w)))
    return out


def _pencil(points, cls, seed, amp=0.6, ghost=True, extra=""):
    """A line drawn by hand, then gone over a second time, lighter."""
    d = _dense(points)
    out = f'<polyline class="{cls}"{extra} points="{_pts(_wobble(d, _hand(seed, amp)))}"/>'
    if ghost:
        out += f'<polyline class="{cls}"{extra} opacity=".4" points="{_pts(_wobble(d, _hand(seed + 1, amp * 1.3), 0.7))}"/>'
    return out


def _pier(points, w, seed=1):
    """The walkway, coloured in: three strokes side by side, each with its own wobble."""
    d, out = _dense(points), []
    for k, (o, ww, op) in enumerate(((-0.3, 0.42, .9), (0.0, 0.46, 1), (0.3, 0.42, .85))):
        line = _wobble(d, _hand(seed * 10 + k, 0.45), o * w)
        out.append(f'<polyline class="p" stroke-width="{ww * w:.1f}" opacity="{op}" points="{_pts(line)}"/>')
    return "".join(out)


def _water(ys, x0, x1, seed=3):
    # still water: pencil strokes broken by short lifts, a different rhythm on every line
    out = []
    for n, y in enumerate(ys):
        r, dash, total = _rng(seed * 31 + n), [], 0
        while total < (x1 - x0) + 60:
            on, off = 18 + r() * 70, 3 + r() * 7
            dash += [f"{on:.0f}", f"{off:.0f}"]
            total += on + off
        end = x1 - r() * (x1 - x0) * 0.12
        out.append(_pencil([(x0, y), (end, y)], "r", seed * 50 + n, 0.5, ghost=False, extra=f' stroke-dasharray="{" ".join(dash)}"'))
    return "<g>" + "".join(out) + "</g>"


def _loop(cx, cy, r, seed, cls="i"):
    """A circle in one movement of the pencil: it never quite closes on itself."""
    h, a = _hand(seed, 0.9), []
    t = 0.0
    while t <= 6.283 * 1.06:
        rr = r + h(t * 40) * 0.6 + t * 0.12
        a.append((cx + rr * math.cos(t - 1.9), cy + rr * math.sin(t - 1.9)))
        t += 0.12
    return f'<polyline class="{cls}" points="{_pts(a)}"/>'


def _island(x, y, r, seed=1):
    return f'<circle class="s" cx="{x}" cy="{y}" r="{r * 1.9:.1f}"/>' + _loop(x, y, r, seed)


def _frame(w, h, seed):
    """The edge of the little sheet, drawn freehand."""
    return _pencil([(1.4, 2.0), (w - 1.6, 1.2), (w - 1.0, h - 1.8), (1.8, h - 1.2), (1.2, 2.6)], "edge", seed, 0.35, ghost=False)


def _bounce(x0, top, ground, r, n0, e, frames, every, vx):
    """A ball dropped from rest at height `top`, bouncing on `ground` with restitution `e`.
    Sampled every `every` frames; with n0 = 8 and e = 0.75 the contacts fall exactly on frames 8 and 20."""
    contact = ground - r
    g = 2 * (contact - top) / n0 ** 2                 # so that the fall takes n0 frames
    starts, v, t = [(0.0, 0.0, True)], e * g * n0, float(n0)
    while t <= frames:
        starts.append((t, v, False))
        t += 2 * v / g
        v *= e
    out, shown = [], list(range(0, frames + 1, every))
    for idx, f in enumerate(shown):
        t0, v0, drop = [s for s in starts if s[0] <= f][-1]
        tau = f - t0
        y = top + 0.5 * g * f * f if drop else contact - v0 * tau + 0.5 * g * tau * tau
        last = idx == len(shown) - 1
        op = 1 if last else round(0.3 + 0.7 * (idx / (len(shown) - 1)) ** 1.3, 2)
        out.append(f'<circle class="{"ball" if last else "frame"}" cx="{x0 + vx * f:.1f}" cy="{y:.1f}" r="{r}" opacity="{op}"/>')
    return "".join(out)


def figure_bounce():
    return ('<svg class="tile" viewBox="0 0 240 180" role="img" aria-label="A ball bouncing along the walkway, drawn once per frame">'
            '<rect class="w" width="240" height="180"/>'
            + _water((124, 133, 144, 157, 172), 6, 234)
            + _pier([(3, 112), (237, 112)], 7, 4)
            + _bounce(18, 22, 108.5, 5.2, 8, 0.75, 28, 2, 7.6) + _frame(240, 180, 5) + "</svg>")


def _plank(a, b, w, seed):
    """A straight walkway at any angle, coloured in with three strokes laid side by side across it."""
    (x0, y0), (x1, y1) = a, b
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    nx, ny = -uy, ux
    n, out = max(2, math.ceil(L / 5)), []
    for k, (o, ww, op) in enumerate(((-0.3, 0.42, .9), (0.0, 0.46, 1), (0.3, 0.42, .85))):
        h = _hand(seed * 10 + k, 0.45)
        line = [(x0 + ux * L * i / n + nx * (o * w + h(L * i / n)), y0 + uy * L * i / n + ny * (o * w + h(L * i / n)))
                for i in range(n + 1)]
        out.append(f'<polyline class="p" stroke-width="{ww * w:.1f}" opacity="{op}" points="{_pts(line)}"/>')
    return "".join(out)


def figure_islands():
    """Five islands, each with its own data, joined to a larger one by straight walkways at irregular angles.
    The data (dots) stay on their islands; only the models (squares) go out on the walkways, to be merged
    on the island in the middle."""
    hx, hy, hr = 130, 96, 15
    isles = [(44, 42, 9), (198, 34, 8), (214, 128, 9), (122, 160, 8), (36, 138, 7.5)]
    masks = "".join(f'<circle class="s" cx="{x}" cy="{y}" r="{r + 3:.1f}"/>' for x, y, r in isles)
    masks += f'<circle class="s" cx="{hx}" cy="{hy}" r="{hr + 3}"/>'
    piers, land, dots, models = "", "", "", ""
    for k, (x, y, r) in enumerate(isles):
        L = math.hypot(hx - x, hy - y)
        ux, uy = (hx - x) / L, (hy - y) / L
        piers += _plank((x + ux * (r + 1), y + uy * (r + 1)), (hx - ux * (hr + 1), hy - uy * (hr + 1)), 5.5, 10 + k)
        land += _loop(x, y, r, 20 + k)
        rr = _rng(70 + k)
        for _ in range(3):
            a, d = rr() * 6.283, r * (0.2 + 0.4 * rr())
            dots += f'<circle class="ball" cx="{x + d * math.cos(a):.1f}" cy="{y + d * math.sin(a):.1f}" r="1.3"/>'
        if k in (0, 2, 3):
            t = (r + 1 + (L - r - hr - 2) * (0.5 if k != 2 else 0.42)) / L
            mx, my = x + (hx - x) * t, y + (hy - y) * t
            ang = math.degrees(math.atan2(uy, ux))
            models += f'<rect class="m" x="{mx - 4:.1f}" y="{my - 4:.1f}" width="8" height="8" transform="rotate({ang:.0f} {mx:.1f} {my:.1f})"/>'
    hub = _loop(hx, hy, hr, 30) + f'<rect class="m" x="{hx - 5}" y="{hy - 5}" width="10" height="10" transform="rotate(-6 {hx} {hy})"/>'
    return ('<svg class="tile" viewBox="0 0 240 180" role="img" '
            'aria-label="Five small islands, each holding its own data, joined by straight walkways to a larger island; '
            'the models travel along the walkways and are merged in the middle">'
            '<rect class="w" width="240" height="180"/>'
            + _water((18, 46, 74, 104, 132, 164), 6, 234, 7)
            + masks + piers + land + hub + dots + models
            + _frame(240, 180, 6) + "</svg>")


def _ellipse(cx, cy, rx, ry, seed):
    h, a, t = _hand(seed, 0.8), [], 0.0
    while t <= 6.283 * 1.04:
        k = 1 + h(t * 30) * 0.03
        a.append((cx + rx * k * math.cos(t), cy + ry * k * math.sin(t)))
        t += 0.15
    return f'<polyline class="fs" stroke-width="1.1" points="{_pts(a)}"/>'


GLYPHS = {
    "bounce": _water((80, 88, 96), 6, 94, 11) + _pier([(3, 71), (97, 71)], 6, 12) + _bounce(10, 14, 68, 3.4, 8, 0.75, 28, 4, 2.9),
    "straight": _water((66, 76, 88), 6, 94, 13) + _pier([(8, 56), (92, 56)], 6, 14)
                + "".join(f'<circle class="ff" cx="{x}" cy="56" r="1.9"/>' for x in (18, 39, 60, 81)),
    "frames": _pencil([(34, 18), (82, 18), (82, 52), (34, 52), (34, 18)], "f", 15, 0.35, extra=' stroke-width="1.2"')
              + _pencil([(26, 30), (74, 30), (74, 64), (26, 64), (26, 30)], "f", 17, 0.35, extra=' stroke-width="1.2"')
              + '<polygon class="pf" points="18.6,42.8 42,41.6 66.4,42.4 65.6,59 66.8,76.2 42,75.4 17.6,76.6 18.4,60"/>'
              + "".join(f'<circle class="ff" cx="{x}" cy="{y}" r="1.7"/>' for x in (28, 38, 48, 58) for y in (52, 66)),
    "kinked": _water((80, 90), 6, 94, 19) + _pier([(10, 62), (28, 40), (46, 66), (64, 36), (90, 56)], 5, 20),
    "prune": '<g stroke-width="1.1" stroke-dasharray="2 3" class="fs">'
             '<line x1="20" y1="26" x2="50" y2="74"/><line x1="20" y1="74" x2="50" y2="26"/>'
             '<line x1="50" y1="50" x2="80" y2="62"/><line x1="50" y1="74" x2="80" y2="38"/></g>'
             + "".join(_pier([a, b], 3.2, 30 + k) for k, (a, b) in enumerate((((20, 26), (50, 26)), ((20, 50), (50, 50)), ((20, 74), (50, 74)),
                                                                             ((50, 26), (80, 38)), ((50, 50), (80, 38)), ((50, 74), (80, 62)))))
             + "".join(f'<circle class="n" cx="{x}" cy="{y}" r="3.8"/>'
                       for x, y in ((20, 26), (20, 50), (20, 74), (50, 26), (50, 50), (50, 74), (80, 38), (80, 62))),
    "landscape": _ellipse(60, 58, 36, 28, 41) + _ellipse(60, 58, 24, 18, 42) + _ellipse(60, 58, 11, 8, 43)
                 + _pier([(8, 16), (34, 16), (34, 58), (60, 58)], 5, 44) + '<circle class="ball" cx="60" cy="58" r="3.2"/>',
    "signal": _pencil([(8, 42), (26, 42), (26, 26), (50, 26), (50, 36), (60, 36), (60, 22), (78, 22), (78, 42), (92, 42)], "f", 51, 0.4,
                      extra=' stroke-width="1.5"')
              + _pier([(8, 72), (26, 72), (26, 60), (50, 60), (50, 72), (92, 72)], 5, 52)
              + _pencil([(8, 88), (60, 88), (60, 80), (78, 80), (78, 88), (92, 88)], "fs", 53, 0.4, ghost=False, extra=' stroke-width="1.4"'),
}


def glyph(name):
    return (f'<svg class="tile" viewBox="0 0 100 100" aria-hidden="true"><rect class="w" width="100" height="100"/>'
            f'{GLYPHS[name]}{_frame(100, 100, 60 + sum(map(ord, name)))}</svg>')


FIGURES = {"bounce": figure_bounce, "islands": figure_islands}


# ---------------------------------------------------------------- shared pieces

def head(path, title, desc, noindex=False, extra=""):
    url = URL + "/" + path
    robots = '<meta name="robots" content="noindex, nofollow">\n' if noindex or not LISTED else ""
    canon = "" if noindex else f'<link rel="canonical" href="{url}">\n'
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
{robots}{canon}<meta property="og:type" content="website">
<meta property="og:site_name" content="{esc(ME)}">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:image" content="{URL}/assets/img/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#FFFFFF" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#000000" media="(prefers-color-scheme: dark)">
<link rel="icon" href="/assets/img/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/assets/img/apple-touch-icon.png">
<script>document.documentElement.classList.add("js");setTimeout(function(){{var l=document.getElementById("lake");if(l)l.classList.add("ready")}},2500)</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:ital,wdth,wght@0,62..125,400..800;1,62..125,400..800&amp;family=Caveat:wght@400;600&amp;display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/css/site.css?v={V_CSS}">
<script src="/assets/js/lake.js?v={V_JS}" defer></script>
<noscript><style>.bibbox[hidden]{{display:block}}</style></noscript>
{extra}</head>
"""


# profile logos (Simple Icons, CC0), drawn in the text colour
ICONS = {
    "googlescholar": "M5.242 13.769L0 9.5 12 0l12 9.5-5.242 4.269C17.548 11.249 14.978 9.5 12 9.5c-2.977 0-5.548 1.748-6.758 4.269zM12 10a7 7 0 1 0 0 14 7 7 0 0 0 0-14z",
    "github": "M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12",
    "huggingface": "M1.4446 11.5059c0 1.1021.1673 2.1585.4847 3.1563-.0378-.0028-.0691-.0058-.1058-.0058-.4209 0-.8015.16-1.0704.4512-.3454.3737-.4984.8335-.4316 1.293a1.576 1.576 0 0 0 .2148.5978c-.2319.1864-.4018.4456-.4844.7578-.0646.2448-.131.7543.2149 1.2794a1.4552 1.4552 0 0 0-.0625.1055c-.208.3923-.2207.8372-.0371 1.25.2783.6258.9696 1.1175 2.3126 1.6467.8356.3292 1.5988.5411 1.6056.543 1.1046.2847 2.104.4277 2.969.4277 1.4173 0 2.4754-.3849 3.1525-1.1446 1.538.2651 2.791.1403 3.592.006.6773.7555 1.7332 1.1387 3.1467 1.1387.8649 0 1.8643-.143 2.969-.4278.0068-.0019.77-.2138 1.6056-.543 1.343-.5292 2.0343-1.0208 2.3126-1.6466.1836-.4129.171-.8577-.037-1.25a1.4685 1.4685 0 0 0-.0626-.1056c.346-.525.2795-1.0346.2149-1.2793-.0826-.3122-.2525-.5714-.4844-.7579.11-.1816.1831-.3788.2148-.5977.0669-.4595-.0862-.9193-.4316-1.293-.2688-.2913-.6495-.4513-1.0704-.4513-.0209 0-.0376.0008-.0588.0018.3162-.9966.4846-2.0518.4846-3.1523 0-5.807-4.7362-10.5144-10.5789-10.5144-5.8426 0-10.5788 4.7073-10.5788 10.5144Zm10.5788-9.4831c5.2727 0 9.5476 4.246 9.5476 9.483a9.4201 9.4201 0 0 1-.2696 2.2365c-.0039-.0047-.0079-.011-.0117-.0156-.274-.3255-.6679-.5059-1.1075-.5059-.352 0-.714.1155-1.0763.3438-.2403.1517-.5058.422-.7793.7598-.2534-.3492-.608-.5832-1.0137-.6465a1.5174 1.5174 0 0 0-.2344-.0176c-.9263 0-1.4828.7993-1.6935 1.5177-.1046.2426-.6065 1.3482-1.3614 2.0978-1.1681 1.1601-1.4458 2.3534-.8396 3.6382-.843.1029-1.5836.0927-2.365-.006.5906-1.212.3626-2.4388-.8426-3.6322-.755-.7496-1.2568-1.8552-1.3614-2.0978-.2107-.7184-.7673-1.5177-1.6935-1.5177-.078 0-.1568.0054-.2344.0176-.4057.0633-.7604.2973-1.0137.6465-.2735-.3379-.539-.6081-.7794-.7598-.3622-.2283-.7243-.3438-1.0762-.3438-.4266 0-.8094.171-1.0821.4786a9.4208 9.4208 0 0 1-.2598-2.1936c0-5.237 4.2749-9.483 9.5475-9.483zM8.6443 7.0036c-.4838.0043-.9503.2667-1.1934.7227-.3536.6633-.1006 1.4873.5645 1.84.351.1862.4883-.5261.836-.6485.3107-.1095.841.399 1.0078.086.3536-.6634.1025-1.4874-.5625-1.84a1.3659 1.3659 0 0 0-.6524-.1602Zm6.8403 0c-.2199-.002-.4426.05-.6504.1602-.665.3526-.9181 1.1766-.5645 1.84.1669.313.6971-.1955 1.0079-.086.3476.1224.4867.8347.838.6485.6649-.3527.916-1.1767.5624-1.84-.243-.456-.7096-.7184-1.1934-.7227Zm-9.7565 1.418a.8768.8768 0 0 0-.877.877c0 .4846.3925.877.877.877a.8768.8768 0 0 0 .877-.877.8768.8768 0 0 0-.877-.877zm12.6434 0c-.4845 0-.879.3925-.879.877 0 .4846.3945.877.879.877a.8768.8768 0 0 0 .877-.877.8768.8768 0 0 0-.877-.877zM8.7927 11.459c-.179-.003-.2793.1107-.2793.416 0 .8097.3874 2.125 1.4279 2.924.207-.7123 1.3453-1.2832 1.5079-1.2012.2315.1167.2191.4417.6074.7266.3884-.285.374-.6098.6056-.7266.1627-.082 1.3009.4889 1.5079 1.2012 1.0404-.799 1.4278-2.1144 1.4278-2.924 0-1.2212-1.583.6402-3.5413.6485-1.4686-.0061-2.7266-1.0558-3.2639-1.0645zM4.312 14.4768c.5792.365 1.6964 2.2751 2.1056 3.0177.1371.2488.371.3536.582.3536.4188 0 .7465-.4138.0391-.9395-1.0636-.791-.6914-2.0846-.1836-2.1642a.4302.4302 0 0 1 .0664-.004c.4616 0 .666.7892.666.7892s.5959 1.4898 1.6213 2.508c.942.9356 1.062 1.703.4961 2.6661-.0164-.004-.0159.0236-.1484.2149-.1853.2673-.4322.4688-.7188.6152-.5062.2269-1.1397.2696-1.7833.2696-1.037 0-2.1017-.1824-2.6975-.336-.0293-.0075-3.6505-.9567-3.1916-1.8224.0771-.1454.2033-.2031.3633-.2031.6463 0 1.823.9551 2.3283.9551.113 0 .196-.0865.2285-.2031.2249-.8045-3.2787-1.0522-2.9846-2.1642.0519-.1967.193-.2757.3907-.2754.854 0 2.7704 1.4923 3.172 1.4923.0307 0 .0525-.0085.0645-.0274.2012-.3227.1096-.5865-1.3087-1.4395-1.4182-.8533-2.4315-1.329-1.8653-1.9416.0651-.0707.1574-.1015.2695-.1015.8611.0002 2.8948 1.84 2.8948 1.84s.5487.5683.8809.5683c.0762 0 .1416-.0315.1855-.1054.2355-.3946-2.1858-2.2183-2.3224-2.971-.0926-.51.0641-.7676.3555-.7676-.0006.008.1701-.0285.4942.1759zm16.2257.5918c-.1366.7526-2.5579 2.5764-2.3224 2.9709.044.074.1092.1055.1855.1055.3321 0 .881-.5684.881-.5684s2.0336-1.8397 2.8947-1.84c.1121 0 .2044.0308.2695.1016.5662.6125-.447 1.0882-1.8653 1.9415-1.4183.853-1.51 1.1168-1.3087 1.4396.012.0188.0337.0273.0644.0273.4016 0 2.3181-1.4923 3.1721-1.4923.1977-.0002.3388.0787.3907.2754.294 1.112-3.2095 1.3597-2.9846 2.1642.0325.1166.1156.2032.2285.2032.5054 0 1.682-.9552 2.3283-.9552.16 0 .2862.0577.3633.2032.459.8656-3.1623 1.8149-3.1916 1.8224-.5958.1535-1.6605.336-2.6975.336-.6351 0-1.261-.0409-1.7638-.2599-.2949-.1472-.5488-.3516-.7383-.625-.0411-.0682-.1026-.1476-.1426-.205-.5726-.9679-.455-1.7371.4903-2.676 1.0254-1.0182 1.6212-2.508 1.6212-2.508s.2044-.7891.666-.7891a.4318.4318 0 0 1 .0665.0039c.5078.0796.88 1.3732-.1836 2.1642-.7074.5257-.3797.9395.039.9395.211 0 .445-.1047.5821-.3535.4092-.7426 1.5264-2.6527 2.1056-3.0178.5588-.3524.99-.1816.8497.5918z",
    "linkedin": "M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z",
    "x": "M18.901 1.153h3.68l-8.04 9.19L24 22.846h-7.406l-5.8-7.584-6.638 7.584H.474l8.6-9.83L0 1.154h7.594l5.243 6.932ZM17.61 20.644h2.039L6.486 3.24H4.298Z",
}
ICON_FOR = {"Scholar": "googlescholar", "GitHub": "github", "Hugging Face": "huggingface", "LinkedIn": "linkedin", "X": "x"}
MAIL = ('<svg class="ico line" viewBox="0 0 24 24" aria-hidden="true"><path d="M3.5 6.2h17v11.6h-17z"/>'
        '<path d="M3.8 6.6l8.2 6.6 8.2-6.6"/></svg>')


def icon(label):
    if label == "Email":
        return MAIL
    key = ICON_FOR.get(label)
    return f'<svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><path d="{ICONS[key]}"/></svg>' if key else ""


def lake(is_home):
    first, last = ME.split(" ", 1)
    name = f"<span>{first}</span> <span>{last}</span>"
    name = f'<h1 class="name">{name}</h1>' if is_home else f'<p class="name"><a href="/">{name}</a></p>'
    links = "\n    ".join(f'<a href="{u}">{icon(l)}<span>{l}</span></a>' for l, u in C.SITE["links"])
    return f"""<aside class="lake" id="lake">
  <svg class="water" id="water" aria-hidden="true"></svg>
  <div class="id">
    {name}
    <p class="who" id="who"><b>{C.SITE["title"]}</b>{C.SITE["interests"]}</p>
  </div>
  <img class="me" id="me" src="/assets/img/me.jpg?v={V_ME}" width="640" height="640" alt="Portrait of {esc(ME)}">
  <p class="map" id="lbl-lake" aria-hidden="true">Lago d’Iseo, simulated</p>
  <nav class="links" id="links" aria-label="Contact and profiles">
    {links}
  </nav>
</aside>"""


def menu(current):
    items = [(p, label) for p, label, _, _ in PAGES]
    if HAS_CV:
        items.append((C.SITE["cv"], "CV"))
    out = []
    for p, label in items:
        cur = ' aria-current="page"' if p == current else ""
        out.append(f'<a href="/{p}"{cur}>{label}</a>')
    return '<nav class="menu" aria-label="Pages">' + "".join(out) + "</nav>"


FOOT = f"""<footer class="foot">
    <div class="jetty" aria-hidden="true"></div>
    <p>{C.FOOTNOTE}</p>
    <p>Last updated {UPDATED}.</p>
  </footer>"""


def page(path, body, title=None, desc=None, noindex=False, extra=""):
    meta = next((p for p in PAGES if p[0] == path), None)
    title = title or meta[2]
    desc = desc or (meta[3] if meta else C.SITE["interests"])
    is_home = path == ""
    cls = "home" if is_home else "sub"
    section = meta[0] if meta else next((p for p, *_ in PAGES if p and path.startswith(p)), None)
    return (head(path, title, desc, noindex, extra)
            + f'<body class="{cls}">\n<a class="skip" href="#content">Skip to content</a>\n<div class="frame">\n\n'
            + lake(is_home)
            + '\n\n<main class="shore" id="shore">\n  <svg id="walk-shore" class="walk" aria-hidden="true"></svg>\n  '
            + menu(section)
            + '\n  <div id="content">\n'
            + body
            + "\n  </div>\n  " + FOOT + "\n</main>\n\n</div>\n</body>\n</html>\n")


def feed(items, cls="feed"):
    rows = []
    for n in items:
        d = "date next" if n.get("next") else "date"
        rows.append(f'    <li class="row"><span class="{d}">{n["date"]}</span><p>{n["text"]}</p></li>')
    return f'<ol class="{cls}">\n' + "\n".join(rows) + "\n  </ol>"


def paper(p, bib=False):
    badge = "badge pre" if p["kind"] == "pre" else "badge"
    authors = ", ".join(author_html(a) for a in p["authors"])
    meta = []
    if p.get("venue"):
        meta.append(f'<span class="venue">{p["venue"]}</span>')
    meta += [f'<a href="{u}">{l}</a>' for l, u in p["links"]]
    if bib:
        meta.append(f'<button class="bibtoggle" type="button" aria-expanded="false" aria-controls="bib-{p["key"]}">BibTeX</button>')
    out = [f'    <li class="row" id="{p["key"]}" data-line="{p["line"]}"><span class="{badge}">{p["badge"]}</span><div>',
           f'      <p class="t">{p["title"]}</p>',
           f'      <p class="au">{authors}</p>']
    if meta:
        out.append('      <div class="meta">' + "".join(meta) + "</div>")
    if bib:
        out.append(f'      <div class="bibbox" id="bib-{p["key"]}" hidden><button class="copy" type="button">Copy</button>'
                   f'<pre>{esc(bibtex(p))}</pre></div>')
    out += [f'      <p class="flag">{f}</p>' for f in p.get("flags", [])]
    out.append("    </div></li>")
    return "\n".join(out)


def papers(items, bib=False):
    return '<ol class="pubs">\n' + "\n".join(paper(p, bib) for p in items) + "\n  </ol>"


BY_KEY = {p["key"]: p for p in C.PAPERS}
SCHOLAR = C.SITE["scholar"]


# ---------------------------------------------------------------- pages

def home():
    bio = "\n    ".join(f"<p>{p}</p>" for p in C.BIO)
    shown, earlier = C.NEWS[:C.NEWS_SHOWN], C.NEWS[C.NEWS_SHOWN:]
    news = feed(shown)
    if earlier:
        news += '\n  <details class="earlier"><summary>Earlier news</summary>\n  ' + feed(earlier) + "\n  </details>"
    cards = "\n".join(f"""    <article class="card">
      <figure>{FIGURES[t["figure"]]()}</figure>
      <h3><a href="/research/#{t["id"]}">{t["title"]}</a></h3>
      <p>{t["text"]}</p>
      <p class="more"><a href="/publications/?line={t["line"]}">The papers</a></p>
    </article>""" for t in C.THEMES)
    return f"""  <section class="bio col" aria-label="About">
    <p class="lead">{C.SITE["tagline"]}</p>
    {bio}
  </section>

  <section class="col" id="news" data-rail aria-labelledby="anchor">
  <h2 id="anchor">Recently</h2>
  {news}
  </section>

  <section class="col" aria-labelledby="lines-h">
  <h2 id="lines-h">Research</h2>
  <div class="cards">
{cards}
  </div>
  </section>"""


def research():
    blocks = []
    for t in C.THEMES:
        qs = "\n".join(
            f'        <li>{q} <a href="/publications/#{k}">{BY_KEY[k]["short"]}</a></li>' for q, k in t["questions"])
        blocks.append(f"""  <section class="theme" id="{t["id"]}" aria-labelledby="{t["id"]}-h">
    <figure>{FIGURES[t["figure"]]()}<figcaption>{t["caption"]}</figcaption></figure>
    <div>
      <h2 id="{t["id"]}-h">{t["title"]}</h2>
      <p class="text">{t["text"]}</p>
      <ul class="qs">
{qs}
      </ul>
      <p class="more"><a href="/publications/?line={t["line"]}">All papers on {C.LINES[t["line"]][0].lower() + C.LINES[t["line"]][1:]}</a></p>
    </div>
  </section>""")
    return f"""  <div class="pagehead">
    <h1 class="title" id="anchor">Research</h1>
    <p>{C.RESEARCH_INTRO}</p>
  </div>

""" + "\n\n".join(blocks)


def publications():
    pubs = [p for p in C.PAPERS if p["kind"] == "pub"]
    pre = [p for p in C.PAPERS if p["kind"] == "pre"]
    filters = "".join(f'<button type="button" data-line="{k}" aria-pressed="false">{v}</button>' for k, v in C.LINES.items())
    return f"""  <div class="pagehead">
    <h1 class="title" id="anchor">Publications</h1>
    <p>Newest first. * marks equal contribution. Citations are on <a href="{SCHOLAR}">Google Scholar</a>
    and the record is on <a href="{C.SITE["dblp"]}">dblp</a>.</p>
    <div class="filter" role="group" aria-label="Show papers on">
      <button type="button" data-line="" aria-pressed="true">All</button>{filters}
    </div>
  </div>

  <section class="col" aria-labelledby="pub-h">
  <h2 id="pub-h">Papers</h2>
  {papers(pubs, bib=True)}
  </section>

  <section class="col" aria-labelledby="pre-h">
  <h2 id="pre-h">Preprints</h2>
  {papers(pre, bib=True)}
  </section>

  <section class="col" aria-labelledby="pat-h">
  <h2 id="pat-h">Patents</h2>
  <p class="prose">{C.PATENTS}</p>
  </section>"""


def code():
    rows = []
    for c in C.CODE:
        links = "".join(f'<a href="{u}">{l}</a>' for l, u in c["links"])
        rows.append(f"""    <li>{glyph(c["glyph"])}<div>
      <p class="t">{c["name"]} <span class="venue">{c["venue"]}</span></p>
      <p class="d">{c["text"]}</p>
      <div class="meta">{links}</div>
    </div></li>""")
    return f"""  <div class="pagehead">
    <h1 class="title" id="anchor">Code</h1>
    <p>Code and data that go with the papers. Everything else is on <a href="https://github.com/ChristianInterno">GitHub</a>
    and <a href="https://huggingface.co/CInterno">Hugging Face</a>.</p>
  </div>

  <section class="col" aria-label="Repositories">
  <ul class="codes">
{chr(10).join(rows)}
  </ul>
  </section>"""


def surname_key(name):
    import unicodedata
    given, last = split_name(name)
    flat = lambda t: unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    return (flat(last[-1]), flat(" ".join(given)))


def collaborate():
    me = ME.replace("*", "")
    people = sorted({a.rstrip("*") for p in C.PAPERS for a in p["authors"]} - {me}, key=surname_key)
    names = ", ".join(f"<span>{esc(n)}</span>" for n in people)
    ment = "\n".join(
        f'    <li class="row"><span class="lab">{m["date"]}</span><p><b>{m["who"]}</b>, '
        f'<span class="where">{m["where"]}.</span> {m["what"]}</p></li>' for m in C.MENTORING)
    vol = "\n".join(f'    <li class="row"><span class="lab">{v["date"]}</span><p>{v["text"]}</p></li>'
                    for v in C.VOLUNTEERING)
    return f"""  <div class="pagehead">
    <h1 class="title" id="anchor">Collaborate</h1>
    {"".join(f"<p>{p}</p>" for p in C.COLLABORATE)}
  </div>

  <section class="col" aria-labelledby="ppl-h">
  <h2 id="ppl-h">People I have worked with</h2>
  <p class="names">{names}.</p>
  </section>

  <section class="col" aria-labelledby="men-h">
  <h2 id="men-h">Students</h2>
  <ul class="plain">
{ment}
  </ul>
  </section>

  <section class="col" aria-labelledby="rev-h">
  <h2 id="rev-h">Reviewing</h2>
  <p class="prose">{C.SERVICE}</p>
  </section>

  <section class="col" aria-labelledby="vol-h">
  <h2 id="vol-h">Volunteering</h2>
  <ul class="plain">
{vol}
  </ul>
  </section>"""


# ---------------------------------------------------------------- blog
# Posts are Markdown files in posts/, each starting with a few lines of front matter:
#     ---
#     title: The lake on this page
#     date: 2026-10-20
#     summary: One sentence for the list of posts and for link previews.
#     ---
# The Markdown understood here is the everyday part: paragraphs, ## headings, - and 1. lists, > quotes,
# ``` code blocks, *italics*, **bold**, `code`, [links](…) and ![pictures](…). Lines that start with "<"
# are passed through as HTML. A file whose name starts with "_" is a draft and is not published.

POSTS_DIR = os.path.join(ROOT, "posts")


def md_inline(t):
    out = []
    for part in re.split(r"(`[^`]+`)", t):
        if len(part) > 1 and part[0] == part[-1] == "`":
            out.append("<code>" + esc(part[1:-1]) + "</code>")
            continue
        part = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)", r'<img src="\2" alt="\1" loading="lazy">', part)
        part = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', part)
        part = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", part)
        part = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", part)
        out.append(part)
    return "".join(out)


def markdown(text):
    html_out, para, items, kind, quote, code = [], [], [], None, [], None

    def flush():
        nonlocal para, items, kind, quote
        if para:
            html_out.append("<p>" + md_inline(" ".join(para)) + "</p>")
        if items:
            html_out.append(f"<{kind}>" + "".join(f"<li>{md_inline(i)}</li>" for i in items) + f"</{kind}>")
        if quote:
            html_out.append("<blockquote><p>" + md_inline(" ".join(quote)) + "</p></blockquote>")
        para, items, kind, quote = [], [], None, []

    for line in text.splitlines():
        if code is not None:
            if line.strip().startswith("```"):
                html_out.append("<pre><code>" + esc("\n".join(code)) + "</code></pre>")
                code = None
            else:
                code.append(line)
            continue
        st = line.strip()
        if st.startswith("```"):
            flush(); code = []
        elif not st:
            flush()
        elif re.match(r"#{2,4} ", st):
            flush()
            n = len(st) - len(st.lstrip("#"))
            html_out.append(f"<h{n}>{md_inline(st[n:].strip())}</h{n}>")
        elif re.match(r"[-*] ", st):
            if kind != "ul":
                flush(); kind = "ul"
            items.append(st[2:])
        elif re.match(r"\d+\. ", st):
            if kind != "ol":
                flush(); kind = "ol"
            items.append(st.split(" ", 1)[1])
        elif st.startswith(">"):
            if para or items:
                flush()
            quote.append(st[1:].strip())
        elif st.startswith("<"):
            flush(); html_out.append(st)
        elif items and line.startswith("  "):
            items[-1] += " " + st
        else:
            if items or quote:
                flush()
            para.append(st)
    flush()
    return "\n".join(html_out)


def load_posts():
    posts = []
    if not os.path.isdir(POSTS_DIR):
        return posts
    for fn in sorted(os.listdir(POSTS_DIR)):
        if not fn.endswith(".md") or fn.startswith("_"):
            continue
        with open(os.path.join(POSTS_DIR, fn), encoding="utf-8") as fh:
            raw = fh.read()
        meta, body = {}, raw
        m = re.match(r"---\s*\n(.*?)\n---\s*\n", raw, re.S)
        if m:
            for ln in m.group(1).splitlines():
                if ":" in ln:
                    k, v = ln.split(":", 1)
                    meta[k.strip()] = v.strip()
            body = raw[m.end():]
        slug = meta.get("slug") or re.sub(r"^\d{4}-\d{2}-\d{2}-", "", fn[:-3])
        date = datetime.date.fromisoformat(meta["date"])
        posts.append({"slug": slug, "title": meta["title"], "date": date, "summary": meta.get("summary", ""),
                      "html": markdown(body)})
    return sorted(posts, key=lambda p: p["date"], reverse=True)


POSTS = load_posts()
FEED_LINK = f'<link rel="alternate" type="application/atom+xml" title="{esc(ME)}: blog" href="/blog/feed.xml">\n'


def nice_date(d):
    return f"{d.day} {d.strftime('%B %Y')}"


def blog():
    if POSTS:
        rows = "\n".join(
            f'    <li class="row"><span class="date">{p["date"].strftime("%b %Y")}</span><div>'
            f'<p class="t"><a href="/blog/{p["slug"]}/">{p["title"]}</a></p><p class="d">{p["summary"]}</p></div></li>'
            for p in POSTS)
        listing = f'<ol class="feed posts">\n{rows}\n  </ol>'
    else:
        listing = '<p class="prose">Nothing here yet.</p>'
    return f"""  <div class="pagehead">
    <h1 class="title">Blog</h1>
    <p id="anchor">{C.BLOG_INTRO} There is a <a href="/blog/feed.xml">feed</a> for readers.</p>
  </div>

  <section class="col" data-rail aria-label="Posts">
  {listing}
  </section>"""


def post(p):
    return f"""  <article class="post" aria-labelledby="anchor">
    <header class="pagehead tight">
      <p class="kicker"><time datetime="{p["date"].isoformat()}">{nice_date(p["date"])}</time></p>
      <h1 class="title" id="anchor">{p["title"]}</h1>
    </header>
    <div class="body">
{p["html"]}
    </div>
    <p class="more back"><a href="/blog/">All posts</a></p>
  </article>"""


def atom():
    updated = (POSTS[0]["date"] if POSTS else TODAY).isoformat() + "T00:00:00Z"
    entries = "".join(f"""  <entry>
    <title>{esc(plain(p["title"]))}</title>
    <link href="{URL}/blog/{p["slug"]}/"/>
    <id>{URL}/blog/{p["slug"]}/</id>
    <updated>{p["date"].isoformat()}T00:00:00Z</updated>
    <summary>{esc(plain(p["summary"]))}</summary>
    <content type="html">{esc(p["html"])}</content>
  </entry>
""" for p in POSTS)
    return f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>{esc(ME)}</title>
  <link href="{URL}/blog/"/>
  <link rel="self" href="{URL}/blog/feed.xml"/>
  <id>{URL}/blog/</id>
  <updated>{updated}</updated>
  <author><name>{esc(ME)}</name></author>
{entries}</feed>
"""


def not_found():
    return """  <div class="pagehead">
    <h1 class="title" id="anchor">Off the end of the pier</h1>
    <p>There’s nothing at this address, only water. Head <a href="/">back to the shore</a>,
    or try the <a href="/publications/">publications</a>.</p>
  </div>"""


def person_ld():
    data = {
        "@context": "https://schema.org", "@type": "Person", "name": ME, "url": URL + "/",
        "image": URL + "/assets/img/me.jpg", "jobTitle": "Machine learning researcher",
        "email": "mailto:" + C.SITE["email"],
        "knowsAbout": ["Representation learning", "World models", "Physical reasoning", "Distributed learning"],
        "affiliation": [
            {"@type": "CollegeOrUniversity", "name": "Bielefeld University"},
            {"@type": "Organization", "name": "Honda Research Institute Europe"},
            {"@type": "CollegeOrUniversity", "name": "University of Oxford"},
        ],
        "sameAs": [u for l, u in C.SITE["links"] if u.startswith("http")] + [C.SITE["dblp"]],
    }
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False) + "</script>\n"


# ---------------------------------------------------------------- write

def write(rel, text):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def main():
    write("index.html", page("", home(), extra=person_ld()))
    write("research/index.html", page("research/", research()))
    write("publications/index.html", page("publications/", publications()))
    write("code/index.html", page("code/", code()))
    write("collaborate/index.html", page("collaborate/", collaborate()))
    write("blog/index.html", page("blog/", blog(), extra=FEED_LINK))
    for p in POSTS:
        write(f"blog/{p['slug']}/index.html",
              page(f"blog/{p['slug']}/", post(p), title=f"{plain(p['title'])} · {ME}", desc=plain(p["summary"]) or None,
                   extra=FEED_LINK))
    write("blog/feed.xml", atom())
    write("404.html", page("404", not_found(), title=f"Not found · {ME}",
                           desc="There’s nothing at this address.", noindex=True))
    if LISTED:
        urls = "".join(f"  <url><loc>{URL}/{p}</loc><lastmod>{TODAY.isoformat()}</lastmod></url>\n" for p, *_ in PAGES)
        urls += "".join(f"  <url><loc>{URL}/blog/{p['slug']}/</loc><lastmod>{p['date'].isoformat()}</lastmod></url>\n" for p in POSTS)
        write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n'
              '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + "</urlset>\n")
        write("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {URL}/sitemap.xml\n")
    else:
        # crawlers may still visit, so they can read the "noindex" on every page; there is no sitemap to offer
        if os.path.exists(os.path.join(ROOT, "sitemap.xml")):
            os.remove(os.path.join(ROOT, "sitemap.xml"))
        write("robots.txt", "User-agent: *\nAllow: /\n")
    write("CNAME", URL.split("://", 1)[1] + "\n")
    write(".nojekyll", "")
    print("Built", len(PAGES), "pages,", len(POSTS), "posts + 404" + (" (with CV)" if HAS_CV else "") + ("" if LISTED else ", hidden from search engines") + ".")


if __name__ == "__main__":
    main()
