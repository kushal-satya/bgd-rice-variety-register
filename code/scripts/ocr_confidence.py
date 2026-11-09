"""OCR confidence audit: for every (file, page) that supplied an OCR'd evidence value, compute Tesseract's
word-level confidence (0-100) from the TSV output (re-running tesseract in TSV mode on the cached 300-dpi render
if the TSV is missing). Writes 05_output/final/bgd_ocr_audit.csv (one row per page) and adds ocr_page_conf to
the evidence rows (05_output/evidence_all.csv is not modified; see bgd_ocr_audit.csv joined by file+page)."""
import pathlib, subprocess, csv, io, statistics, sys
import pandas as pd
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from lib_ocr import render, TESS, TD, OCR
ev = pd.read_csv(ROOT / "05_output/evidence_all.csv", dtype=str).fillna("")
o = ev[(ev.method == "ocr") & ev.page.str.fullmatch(r"\d+")]
pages = o.groupby(["local_file", "page"]).agg(n_values=("value", "size"),
        n_key_check=("validation", lambda s: (s == "key_check").sum()),
        n_visual_check=("validation", lambda s: (s == "visual_check").sum()),
        n_unvalidated=("validation", lambda s: (s == "unvalidated").sum())).reset_index()
# 1) make sure every needed TSV exists (3 tesseract processes in parallel, cached/resumable)
from concurrent.futures import ThreadPoolExecutor
todo = []
for r in pages.itertuples():
    f = ROOT / r.local_file
    if f.exists() and f.suffix.lower() == ".pdf":
        try:
            png = render(r.local_file, int(r.page) - 1)
        except Exception:  # noqa
            continue
        tsv = png.with_name(f"p{int(r.page):03d}_psm6.tsv")
        if not tsv.exists():
            todo.append((png, tsv))
print(len(todo), "pages need TSV", flush=True)
def run(a):
    png, tsv = a
    subprocess.run([TESS, str(png), str(tsv.with_suffix("")), "--tessdata-dir", TD, "-l", "ben+eng", "--psm", "6", "tsv"], capture_output=True)
with ThreadPoolExecutor(3) as ex:
    for i, _ in enumerate(ex.map(run, todo)):
        if i % 25 == 0: print("tsv", i, flush=True)
rows = []
for r in pages.itertuples():
    f = ROOT / r.local_file
    if not f.exists() or f.suffix.lower() != ".pdf":
        continue
    p0 = int(r.page) - 1
    try:
        png = render(r.local_file, p0)
    except Exception as e:  # noqa
        continue
    tsv = png.with_name(f"p{p0+1:03d}_psm6.tsv")
    if not tsv.exists():
        subprocess.run([TESS, str(png), str(tsv.with_suffix("")), "--tessdata-dir", TD, "-l", "ben+eng", "--psm", "6", "tsv"],
                       capture_output=True)
    if not tsv.exists():
        continue
    confs = []
    with open(tsv, encoding="utf-8", errors="replace") as fh:
        for w in csv.DictReader(fh, delimiter="\t", quoting=csv.QUOTE_NONE):
            try:
                c = float(w.get("conf", -1))
            except ValueError:
                continue
            if c >= 0 and (w.get("text") or "").strip():
                confs.append(c)
    if not confs:
        continue
    rows.append(dict(local_file=r.local_file, page=r.page, n_words=len(confs),
                     mean_word_conf=round(statistics.mean(confs), 1), median_word_conf=round(statistics.median(confs), 1),
                     pct_words_conf_below_60=round(100 * sum(c < 60 for c in confs) / len(confs), 1),
                     n_values=r.n_values, n_key_check=r.n_key_check, n_visual_check=r.n_visual_check,
                     n_unvalidated=r.n_unvalidated))
out = pd.DataFrame(rows).sort_values("mean_word_conf")
(ROOT / "05_output/final").mkdir(exist_ok=True)
out.to_csv(ROOT / "05_output/final/bgd_ocr_audit.csv", index=False, encoding="utf-8-sig")
print(len(pages), "OCR pages with evidence;", len(out), "scored")
print(out.describe().round(1).to_string())
