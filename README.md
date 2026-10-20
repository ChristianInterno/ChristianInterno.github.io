# christianinterno.com

The personal site of Christian Internò: plain HTML, CSS and a little JavaScript, served by GitHub Pages.
No framework and no build service. One Python script turns one content file into the pages.

## What's here

```
content.py            everything the site says: bio, news, papers, code, collaborators, students
build.py              turns content.py into the pages:  python3 build.py
index.html            About (generated, like every page below)
publications/  code/  collaborate/  blog/
posts/                the blog posts, one Markdown file each
404.html              "Off the end of the pier"
assets/css/site.css   all the styling; the colours are at the top
assets/js/lake.js     the drawing and the water (linear wave theory), the walkway, the papers filter, BibTeX
assets/img/           me.jpg, og.png (link preview), favicon.svg, apple-touch-icon.png
CNAME                 christianinterno.com
.nojekyll  robots.txt  sitemap.xml
```

Don't edit the generated `.html` files by hand: the next build overwrites them. Change `content.py`
(or `build.py` for structure, `site.css` for looks) and rebuild.

## Changing something

1. Edit `content.py`. New news goes at the top of `NEWS`; a new paper goes into `PAPERS`
   (copy an existing entry). Text can hold simple HTML such as `<a href="…">links</a>` or `<i>italics</i>`.
2. Run `python3 build.py` (Python 3.6 or newer, nothing to install).
3. Commit and push, or upload the changed files on GitHub.

Each paper's BibTeX is generated from its entry, so authors, venue and year only need to be right in one place.
Mark equal contribution with a trailing `*` on the name. The "People I have worked with" list on the Collaborate
page is built from the authors in `PAPERS`, so it grows by itself.

## Writing a blog post

Add a Markdown file to `posts/`, for example `posts/2026-11-02-a-title.md`, starting with:

```
---
title: A title
date: 2026-11-02
summary: One sentence for the list of posts and for link previews.
---
```

Then write the post below it: paragraphs, `## headings`, `- lists`, `*italics*`, `**bold**`, `[links](https://…)`,
`` `code` ``, code blocks between ``` lines, and `![pictures](/assets/img/…)`. A line that starts with `<` is
passed through as HTML (handy for an equation). The address is `/blog/a-title/`. Rebuild, and the post shows up
on the Blog page and in the feed at `/blog/feed.xml`. A file whose name starts with `_` is a draft and is skipped.

## Looking at it before it goes live

Paths start with `/`, so opening `index.html` straight from disk shows an unstyled page. Serve the folder instead:

```
python3 -m http.server 8000
```

and open http://localhost:8000.

## Putting it online

Everything in this folder goes at the root of the `ChristianInterno.github.io` repository (keep `CNAME`).
In the repository's Settings → Pages: deploy from the `main` branch, folder `/ (root)`, custom domain
`christianinterno.com`, then tick "Enforce HTTPS" once GitHub has issued the certificate.

The GeoPhys project page lives in its own repository (`ChristianInterno/GeoPhys`, with Pages switched on)
and shows up at christianinterno.com/GeoPhys/ by itself.

## Small things

- **Search engines**: while `"listed": False` in content.py, every page carries `noindex` and there is no sitemap,
  so search engines leave the site out (anyone with the link can still open it). When it's ready, set it to `True`,
  rebuild and push; then add the site in Google Search Console to have it picked up quickly.

- **CV**: save a PDF as `assets/cv.pdf` and rebuild; a "CV" item appears in the menu.
- **Photo**: `assets/img/me.jpg`, square, 640×640. Replace it with another square photo under the same name.
- **Colours**: black and white, with the walkway as the only colour: `--paper`, `--ink`, `--graphite` (the pencil lines) and `--pier` (the orange). Dark mode swaps paper and ink, like chalk on a blackboard. The name and the caption under the lake are set in Caveat, to read like handwriting on the drawing.
- **The walkway** finds the "Recently" heading on the About page and runs through the dates; on Talks it runs
  through the talk dates. One section per page can carry `data-rail`; its `class="date"` labels become the landings.
- **The water** follows linear wave theory for deep water: every Fourier mode moves with the gravity–capillary
  dispersion relation ω² = gk + (σ/ρ)k³ and fades at γ = γ₀ + 2νk². A light breeze keeps a few wave trains rolling
  across; a tap or a sweep of the pointer drops a disturbance that is stepped exactly in Fourier space (an FFT per
  frame), so the short ripples run out ahead of the long ones. The constants are at the top of the physics section in
  lake.js. The walkway is moored and doesn't move. With reduced motion switched on, the water stays still.
- **Lines of work**: `LINES` in content.py names the two lines; each paper's `line` puts it in one, which drives
  the grouping on the About page and the filter on Publications (`/publications/?line=dist` links straight to it).
