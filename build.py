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
# Little views of the lake, drawn in the site's colours so they follow light and dark mode.

def _pier(points, w):
    shifted = " ".join(f"{float(x) + w / 4.5:.1f},{float(y) + w / 4.5:.1f}" for x, y in (p.split(",") for p in points.split()))
    return (f'<polyline class="ps" stroke-width="{w}" points="{shifted}"/>'
            f'<polyline class="p" stroke-width="{w}" points="{points}"/>')


def _ripples(lines):
    return '<g class="r">' + "".join(f'<line x1="{a}" y1="{b}" x2="{c}" y2="{b}"/>' for a, b, c in lines) + "</g>"


def _island(x, y, r):
    return (f'<circle class="sh" cx="{x}" cy="{y}" r="{r * 2}"/><circle class="s" cx="{x}" cy="{y}" r="{r * 1.3:.1f}"/>'
            f'<circle class="i" cx="{x}" cy="{y}" r="{r}"/>')


def figure_straight():
    dots = "".join(f'<circle class="ff" cx="{x}" cy="62" r="3.4"/>' for x in (26, 64, 102, 140, 178, 216))
    gen = [(26, 128), (64, 106), (102, 142), (140, 112), (178, 152), (216, 118)]
    gpts = " ".join(f"{x},{y}" for x, y in gen)
    gdots = "".join(f'<circle class="fsf" cx="{x}" cy="{y}" r="3"/>' for x, y in gen)
    return ('<svg class="tile" viewBox="0 0 240 180" role="img" aria-label="A straight walkway and a zig-zag line">'
            '<rect class="w" width="240" height="180"/>'
            + _ripples([(150, 22, 172), (196, 36, 210), (18, 94, 34), (190, 88, 222), (92, 170, 116), (30, 160, 42)])
            + _pier("20,62 222,62", 9) + dots
            + f'<polyline class="fs" stroke-width="2" stroke-linejoin="round" points="{gpts}"/>' + gdots
            + '<text x="20" y="40">natural</text><text x="20" y="174">generated</text></svg>')


def figure_islands():
    arms = ["46,32 120,32 120,90", "206,56 206,90 120,90", "192,152 120,152 120,90", "34,130 34,90 120,90"]
    piers = "".join(_pier(a, 7) for a in arms)
    clients = "".join(_island(x, y, 7) for x, y in ((46, 32), (206, 56), (192, 152), (34, 130)))
    return ('<svg class="tile" viewBox="0 0 240 180" role="img" aria-label="Four small islands joined to a central one by walkways">'
            '<rect class="w" width="240" height="180"/>'
            + _ripples([(150, 20, 170), (64, 64, 84), (160, 122, 182), (20, 170, 36), (214, 110, 230), (80, 116, 96)])
            + piers + clients + _island(120, 90, 12)
            + '<rect class="ff" x="78" y="28" width="8" height="8"/><rect class="ff" x="156" y="148" width="8" height="8"/></svg>')


GLYPHS = {
    "straight": _ripples([(14, 22, 30), (60, 30, 76), (40, 84, 56)]) + _pier("8,56 92,56", 8)
                + "".join(f'<circle class="ff" cx="{x}" cy="56" r="2.8"/>' for x in (18, 39, 60, 81)),
    "frames": '<rect class="fs" stroke-width="2" x="34" y="18" width="48" height="34"/>'
              '<rect class="fs" stroke-width="2" x="26" y="30" width="48" height="34"/>'
              '<rect class="psf" x="21" y="45" width="48" height="34"/><rect class="pf" x="18" y="42" width="48" height="34"/>'
              + "".join(f'<circle class="w" cx="{x}" cy="{y}" r="2"/>' for x in (28, 38, 48, 58) for y in (52, 66)),
    "kinked": _ripples([(60, 20, 78), (12, 84, 26)]) + _pier("10,64 28,40 46,68 64,36 90,58", 7),
    "prune": '<g stroke-width="1.4" stroke-dasharray="2 3" class="fs">'
             '<line x1="20" y1="26" x2="50" y2="74"/><line x1="20" y1="74" x2="50" y2="26"/>'
             '<line x1="50" y1="50" x2="80" y2="62"/><line x1="50" y1="74" x2="80" y2="38"/></g>'
             '<g stroke-width="3" class="p"><line x1="20" y1="26" x2="50" y2="26"/><line x1="20" y1="50" x2="50" y2="50"/>'
             '<line x1="20" y1="74" x2="50" y2="74"/><line x1="50" y1="26" x2="80" y2="38"/><line x1="50" y1="50" x2="80" y2="38"/>'
             '<line x1="50" y1="74" x2="80" y2="62"/></g>'
             + "".join(f'<circle class="ff" cx="{x}" cy="{y}" r="4.2"/>'
                       for x, y in ((20, 26), (20, 50), (20, 74), (50, 26), (50, 50), (50, 74), (80, 38), (80, 62))),
    "landscape": '<g class="fs" stroke-width="1.5"><ellipse cx="60" cy="58" rx="36" ry="28"/>'
                 '<ellipse cx="60" cy="58" rx="24" ry="18"/><ellipse cx="60" cy="58" rx="11" ry="8"/></g>'
                 + _pier("8,16 34,16 34,58 60,58", 7) + '<circle class="ff" cx="60" cy="58" r="3.4"/>',
    "signal": '<polyline class="f" stroke-width="2" stroke-linejoin="round" points="8,42 26,42 26,26 50,26 50,36 60,36 60,22 78,22 78,42 92,42"/>'
              + _pier("8,74 26,74 26,62 50,62 50,74 92,74", 6)
              + '<polyline class="fs" stroke-width="2" points="8,90 60,90 60,80 78,80 78,90 92,90"/>',
}


def glyph(name):
    return (f'<svg class="tile" viewBox="0 0 100 100" aria-hidden="true"><rect class="w" width="100" height="100"/>'
            f'{GLYPHS[name]}</svg>')


FIGURES = {"straight": figure_straight, "islands": figure_islands}


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
<meta name="theme-color" content="#1A555C" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0E3439" media="(prefers-color-scheme: dark)">
<link rel="icon" href="/assets/img/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/assets/img/apple-touch-icon.png">
<script>document.documentElement.classList.add("js");setTimeout(function(){{var l=document.getElementById("lake");if(l)l.classList.add("ready")}},2500)</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:ital,wdth,wght@0,62..125,400..800;1,62..125,400..800&amp;display=swap" rel="stylesheet">
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
  <svg class="ripples" id="ripples" aria-hidden="true"></svg>
  <svg class="walk" id="walk-lake" aria-hidden="true"></svg>
  <div class="id">
    {name}
    <p class="who" id="who"><b>{C.SITE["title"]}</b>{C.SITE["interests"]}</p>
  </div>
  <img class="isle me" id="me" src="/assets/img/me.jpg" width="200" height="200" alt="Portrait of {esc(ME)}">
  <span class="isle islet" id="islet" aria-hidden="true"></span>
  <p class="map" id="lbl-isle" aria-hidden="true">San Paolo</p>
  <p class="map" id="lbl-lake" aria-hidden="true">Lago d’Iseo</p>
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
    out = [f'    <li class="row" id="{p["key"]}"><span class="{badge}">{p["badge"]}</span><div>',
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
  {papers(sel)}
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
    return f"""  <div class="pagehead">
    <h1 class="title" id="anchor">Publications</h1>
    <p>Newest first. * marks equal contribution. Citations are on <a href="{SCHOLAR}">Google Scholar</a>
    and the record is on <a href="{C.SITE["dblp"]}">dblp</a>.</p>
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
                    f'<p class="where">{t["kind"]} · {t["where"]}</p></div></li>')
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
      <p class="t">{c["name"]}<span class="venue">{c["venue"]}</span></p>
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
        "image": URL + "/assets/img/me.jpg", "jobTitle": "PhD candidate in machine learning",
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
