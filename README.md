# christianinterno.com

The personal site of Christian Internò: plain HTML, CSS and a little JavaScript, served by GitHub Pages.
No framework and no build service. One Python script turns one content file into the pages.

## What's here

```
content.py            everything the site says: bio, news, papers, talks, code, mentoring
build.py              turns content.py into the pages:  python3 build.py
index.html            About (generated, like every page below)
research/  publications/  talks/  code/  mentoring/
404.html              "Off the end of the pier"
assets/css/site.css   all the styling; the colours are at the top
assets/js/lake.js     the water (a small wave-equation solver), the walkway, the papers filter, BibTeX
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
Mark equal contribution with a trailing `*` on the name. `"selected": True` puts a paper on the About page.

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

- **CV**: save a PDF as `assets/cv.pdf` and rebuild; a "CV" item appears in the menu.
- **Photo**: `assets/img/me.jpg` is 200×200. A square photo of 600×600 or more, under the same name, looks sharper.
- **Colours**: `--lake` is the water, `--pier` the walkway, `--shore` the page, `--ink` the text. Dark mode has its own set just below.
- **The walkway** finds the "Recently" heading on the About page and runs through the dates; on Talks it runs
  through the talk dates. One section per page can carry `data-rail`; its `class="date"` labels become the landings.
- **The water** is simulated with the 2D wave equation. Moving the pointer over it, or tapping it, makes ripples
  that reflect off the portrait and fade; the walkway rides them, moored at its ends. With reduced motion switched
  on in the system settings, the water stays still.
- **Lines of work**: `LINES` in content.py names the two lines; each paper's `line` puts it in one, which drives
  the grouping on the About page and the filter on Publications (`/publications/?line=dist` links straight to it).
