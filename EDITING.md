# Bangladesh Rice Variety Register: website

Static site for GitHub Pages. No build tools, frameworks or external requests: plain HTML, CSS and JavaScript.

```
site/
  index.html          page structure (sections, tables, figure slots)
  content/text.md     ALL text on the page: edit this file
  assets/style.css    layout and colours
  assets/app.js       reads the text and the data, draws the figures and tables
  data/               site_data.json (read by the page) and the downloadable CSV, XLSX and data dictionary
  .nojekyll           tells GitHub Pages to serve the files as they are
```

## Editing the text

Open `content/text.md`. Each block begins with a marker line such as `<!-- @methods -->` and runs to the next marker.
Change the words under a marker; do not rename the marker unless you rename the matching `data-text="..."` in `index.html`.

Formatting inside a block: `**bold**`, `*italic*`, `` `code` ``, `[text](https://...)`, lists that start with `- ` or `1. `,
sub-headings that start with `### `. A blank line starts a new paragraph.

To add a new paragraph somewhere on the page: add a block to `text.md` (`<!-- @my-note -->` followed by the text) and an
element `<div class="prose" data-text="my-note"></div>` at the right place in `index.html`. Use `data-inline` on headings.

## Placeholders

Write `{{name}}` anywhere in `text.md` and the page replaces it with the value computed from the data when it loads, so
numbers in the prose stay correct after a rebuild. To add one, add a line to the `STATS` object at the top of `assets/app.js`.

| Placeholder | Value |
|---|---|
| `{{n_rice}}` | approved rice varieties |
| `{{n_inbred}}`, `{{n_hybrid}}` | by seed type |
| `{{n_public}}`, `{{n_private}}` | by developer sector |
| `{{n_brri}}`, `{{n_bina}}` | developed by BRRI, by BINA |
| `{{year_min}}`, `{{year_max}}` | first and last approval year |
| `{{n_dated}}` | varieties with the exact NSB meeting date |
| `{{n_gazette}}` | varieties with a gazette notification date |
| `{{n_cgiar_linked}}` | CGIAR code 1–3 (all varieties) |
| `{{n_cgiar_inbred_linked}}` | CGIAR code 1–3 among inbreds |
| `{{n_cgiar_unknown}}` | CGIAR code 5 |
| `{{n_with_features}}` | varieties with at least one feature tag |
| `{{n_key_papers}}` | varieties with a key paper |
| `{{n_fish}}`, `{{n_fish_events}}`, `{{n_fish_acts}}` | fish strains, germplasm events, government acts |
| `{{n_source_files}}`, `{{n_evidence}}`, `{{n_conflicts}}` | archived sources, evidence rows, disagreeing values |
| `{{n_ocr_pages}}`, `{{ocr_mean_conf}}` | scanned pages read, mean OCR word confidence |
| `{{n_qa_checks}}` | automated integrity checks (all pass) |
| `{{n_pedigree}}` | varieties with a recorded pedigree |
| `{{n_cgiar_known}}` | varieties with a determinate CGIAR link (codes 1 to 4) |
| `{{n_ocr_unconfirmed}}` | OCR readings discarded because neither check confirmed them |
| `{{n_date_conflicts}}` | varieties whose sources disagree on the approval date |
| `{{n_inbred_untagged}}` | inbred varieties with no recorded trait |
| `{{n_fish_ornamental}}` | ornamental fish species in the quarantine schedule |
| `{{built}}`, `{{built_long}}` | build date (2026-10-08 / 8 October 2026) |

## Updating the data

From the project root, `bash scripts/rebuild_all.sh` rebuilds every table and ends with `scripts/build_site.py`, which
refreshes `site/data/` and writes the single-file version `05_output/final/rice_register_standalone.html`
(the same page with text, data and script inlined; it opens from disk with no server).

## Viewing locally

Browsers do not let a page opened from disk read `data/site_data.json`. Serve the folder instead:

```bash
python -m http.server 8765 --directory site
```

then open http://localhost:8765. (Or open the standalone file, which needs no server.)


## Publishing on GitHub Pages

1. Create a repository and copy the contents of `site/` into it (or keep the whole project and publish the `site/` folder).
2. Push to GitHub.
3. Settings → Pages → Build and deployment → Source: "Deploy from a branch"; choose the branch and the folder
   (`/ (root)` if the repository holds only the site; for a whole project, move or copy `site/` to `docs/` and choose `/docs`).
4. The page appears at `https://<user>.github.io/<repository>/` after a minute or two.

Size: the largest file, `bgd_nsb_decisions_full.csv`, is about 18 MB, well under GitHub's 100 MB file limit.
