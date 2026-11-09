"""F5L: fill OCR gaps for the page corpus (cache-aware, resumable, 3 tesseract processes).
Job classes, in priority order:
  full  : page has no cached pNNN_psm6.txt and no usable text layer -> render 300 dpi (lib_ocr.render), tesseract txt+tsv
  full  : also any page already rendered to PNG but never OCR'd (even if it has a text layer)
  tsv   : page has cached pNNN_psm6.txt but no .tsv -> tesseract tsv only (same PNG, same params: the cached
          txt is NOT touched; the tsv is needed only for word-confidence statistics)
Usable text layer = any span font other than glyphless Helvetica (embedded junk OCR) / AdarshaLipi.
Excluded: bfri_annual_report_2021-22_part1 pages never OCR'd (an annual report, not an official list; 75 cached pages kept).
Log: logs/ocr_F5L.log"""
import csv, os, pathlib, subprocess, sys, time
os.environ["OMP_THREAD_LIMIT"] = "1"   # 3 single-threaded tesseracts; multithreaded ones thrashed the CPU
from concurrent.futures import ThreadPoolExecutor
ROOT = pathlib.Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT / "scripts"))
from lib_ocr import TESS, TD, OCR, render

UNUSABLE = ("Helvetica", "AdarshaLipi")
SKIP_FULL = {"02_raw/bfri/bfri_annual_report_2021-22_part1.pdf"}


def usable(fonts):
    fams = [x.split(":")[0] for x in fonts.split(";") if x]
    return any(not f.startswith(UNUSABLE) for f in fams)


def jobs():
    inv = list(csv.DictReader(open("04_working/F5L/inventory_pages.csv", encoding="utf-8")))
    full, tsv = [], []
    for r in inv:
        f, p = r["source_file"], int(r["page"])
        if r["psm6_txt"] == "1":
            if r["psm6_tsv"] != "1":
                tsv.append((f, p))
        elif r["png"] == "1" and f not in SKIP_FULL:
            full.append((f, p))   # rendered earlier but never OCR'd (e.g. NSB report no.5): brief says run it
        elif f not in SKIP_FULL and not (int(r["text_chars"]) >= 30 and usable(r["fonts"])):
            full.append((f, p))
    pf = pathlib.Path("04_working/F5L/poor_text_layer_pages.csv")
    if pf.exists():   # text layer mostly unmapped glyphs (written by phase3_F5L_corpus.py)
        for r in csv.DictReader(open(pf, encoding="utf-8")):
            j = (r["source_file"], int(r["page"]))
            if j not in full and not (OCR / pathlib.Path(j[0]).stem / f"p{j[1]:03d}_psm6.txt").exists():
                full.append(j)
    return sorted(full, key=prio), sorted(tsv, key=prio)


PRIORITY = ["approved_varieties_notified", "gazette_variety_registration", "hybrid_rice_list_1998", "gazette_nsb93",
            "brri/", "nsb_minutes_058", "approved_crop_varieties", "registered_hybrid", "moa_wayback/", "moa/",
            "bgpress/", "sca_wayback/", "nsb_minutes", "sca_laws/", "bfri/"]


def prio(j):
    f, p = j
    return (next((i for i, k in enumerate(PRIORITY) if k in f), 99), f, p)


def run(job):
    kind, f, p = job
    t0 = time.time()
    png = render(f, p - 1)
    base = png.with_name(f"p{p:03d}_psm6")
    outs = ["txt", "tsv"] if kind == "full" else ["tsv"]
    if all(base.with_suffix("." + o).exists() for o in outs):
        return f"{kind} {f} p{p} cached"
    subprocess.run([TESS, str(png), str(base), "--tessdata-dir", TD, "-l", "ben+eng", "--psm", "6"] + outs,
                   capture_output=True, check=False)
    return f"{kind} {f} p{p} {time.time()-t0:.1f}s"


if __name__ == "__main__":
    full, tsv = jobs()
    only = sys.argv[1] if len(sys.argv) > 1 else "all"
    todo = ([("full", *j) for j in full] if only in ("all", "full") else []) + \
           ([("tsv", *j) for j in tsv] if only in ("all", "tsv") else [])
    log = open("logs/ocr_F5L.log", "a", encoding="utf-8")
    log.write(f"=== start {time.ctime()} full={len(full)} tsv={len(tsv)} running={len(todo)}\n"); log.flush()
    with ThreadPoolExecutor(3) as ex:
        for i, msg in enumerate(ex.map(run, todo), 1):
            log.write(f"[{i}/{len(todo)}] {msg}\n"); log.flush()
    log.write(f"=== done {time.ctime()}\n")
