#!/usr/bin/env python3
"""
Builds christianinterno.com from content.py.

    python3 build.py

Writes index.html, one folder per page, 404.html, sitemap.xml, robots.txt,
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
    ("talks/", "Talks", f"Talks · {ME}", f"Talks and posters by {ME}."),
    ("code/", "Code", f"Code · {ME}", f"Code and datasets by {ME}."),
    ("mentoring/", "Mentoring", f"Mentoring and service · {ME}",
     f"Students {ME} has mentored, reviewing, and volunteering."),
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


def figure_islands():
    arms = [[(46, 32), (120, 32), (120, 90)], [(206, 56), (206, 90), (120, 90)],
            [(192, 152), (120, 152), (120, 90)], [(34, 130), (34, 90), (120, 90)]]
    piers = "".join(_pier(a, 6, 10 + k) for k, a in enumerate(arms))
    clients = "".join(_island(x, y, 8, 20 + k) for k, (x, y) in enumerate(((46, 32), (206, 56), (192, 152), (34, 130))))
    return ('<svg class="tile" viewBox="0 0 240 180" role="img" aria-label="Four small islands joined to a central one by walkways">'
            '<rect class="w" width="240" height="180"/>'
            + _water((20, 48, 76, 106, 138, 168), 6, 234, 7)
            + piers + clients + _island(120, 90, 13, 30)
            + '<rect class="m" x="78" y="28" width="8" height="8" transform="rotate(-4 82 32)"/>'
            + '<rect class="m" x="156" y="148" width="8" height="8" transform="rotate(5 160 152)"/>'
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
    robots = '<meta name="robots" content="noindex">\n' if noindex else ""
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
<link rel="stylesheet" href="/assets/css/site.css">
<script src="/assets/js/lake.js" defer></script>
<noscript><style>.bibbox[hidden]{{display:block}}</style></noscript>
{extra}</head>
"""


def lake(is_home):
    first, last = ME.split(" ", 1)
    name = f"<span>{first}</span> <span>{last}</span>"
    name = f'<h1 class="name">{name}</h1>' if is_home else f'<p class="name"><a href="/">{name}</a></p>'
    links = "\n    ".join(f'<a href="{u}">{l}</a>' for l, u in C.SITE["links"])
    return f"""<aside class="lake" id="lake">
  <svg class="water" id="water" aria-hidden="true"></svg>
  <div class="id">
    {name}
    <p class="who" id="who"><b>{C.SITE["title"]}</b>{C.SITE["interests"]}</p>
  </div>
  <img class="me" id="me" src="/assets/img/me.jpg" width="200" height="200" alt="Portrait of {esc(ME)}">
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
    desc = desc or meta[3]
    is_home = path == ""
    cls = "home" if is_home else "sub"
    return (head(path, title, desc, noindex, extra)
            + f'<body class="{cls}">\n<a class="skip" href="#content">Skip to content</a>\n<div class="frame">\n\n'
            + lake(is_home)
            + '\n\n<main class="shore" id="shore">\n  <svg id="walk-shore" class="walk" aria-hidden="true"></svg>\n  '
            + menu(path if meta else None)
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
    sel = [p for p in C.PAPERS if p.get("selected")]
    groups = "\n  ".join(f'<h3 class="group">{label}</h3>\n  ' + papers([p for p in sel if p["line"] == line])
                         for line, label in C.LINES.items() if any(p["line"] == line for p in sel))
    return f"""  <section class="bio col" aria-label="About">
    <p class="lead">{C.SITE["tagline"]}</p>
    {bio}
  </section>

  <section class="col" id="news" data-rail aria-labelledby="anchor">
  <h2 id="anchor">Recently</h2>
  {news}
  </section>

  <section class="col" aria-labelledby="sel-h">
  <h2 id="sel-h">Selected publications</h2>
  {groups}
  <p class="more"><a href="/publications/">All publications and preprints</a></p>
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


def talks():
    rows = []
    for t in C.TALKS:
        d = "date next" if t.get("next") else "date"
        rows.append(f'    <li class="row"><span class="{d}">{t["date"]}</span><div><p class="t">{t["title"]}</p>'
                    f'<p class="where">{t["kind"]} at {t["where"]}</p></div></li>')
    return f"""  <div class="pagehead tight">
    <h1 class="title" id="anchor">Talks</h1>
  </div>

  <section class="col" data-rail aria-labelledby="anchor">
  <ol class="feed talks">
{chr(10).join(rows)}
  </ol>
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


def mentoring():
    ment = "\n".join(
        f'    <li class="row"><span class="lab">{m["date"]}</span><p><b>{m["who"]}</b>, '
        f'<span class="where">{m["where"]}.</span> {m["what"]}</p></li>' for m in C.MENTORING)
    vol = "\n".join(f'    <li class="row"><span class="lab">{v["date"]}</span><p>{v["text"]}</p></li>'
                    for v in C.VOLUNTEERING)
    return f"""  <div class="pagehead">
    <h1 class="title" id="anchor">Mentoring and service</h1>
  </div>

  <section class="col" aria-labelledby="men-h">
  <h2 id="men-h">Mentoring</h2>
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
    write("talks/index.html", page("talks/", talks()))
    write("code/index.html", page("code/", code()))
    write("mentoring/index.html", page("mentoring/", mentoring()))
    write("404.html", page("404", not_found(), title=f"Not found · {ME}",
                           desc="There’s nothing at this address.", noindex=True))
    urls = "".join(f"  <url><loc>{URL}/{p}</loc><lastmod>{TODAY.isoformat()}</lastmod></url>\n" for p, *_ in PAGES)
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + "</urlset>\n")
    write("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {URL}/sitemap.xml\n")
    write("CNAME", URL.split("://", 1)[1] + "\n")
    write(".nojekyll", "")
    print("Built", len(PAGES), "pages + 404" + (" (with CV)" if HAS_CV else "") + ".")


if __name__ == "__main__":
    main()
