"""F5L task 2: OCR page corpus of every official / minutes / gazette / leaflet document.

One row per PDF page (from 04_working/F5L/inventory_pages.csv, re-run phase3_F5L_inventory.py first):
  full_ocr_text      = cached 03_extracted/text/ocr/<stem>/pNNN_psm6.txt, complete and untruncated
  word confidences   = from pNNN_psm6.tsv (level-5 words with conf >= 0 and non-blank text)
  text_layer_text    = the PDF's own text layer when usable: SutonnyMJ / NikoshBAN-free Bijoy spans converted
                       with phase3_F3H_moa_spans.bijoy (bijoy2unicode + 4 repairs); every other font (Times, Arial,
                       Calibri, Cambria, Nirmala, Unicode Nikosh ...) kept raw, so Latin runs are never garbled.
                       Spans whose font has no Unicode map (control characters) are replaced by '[?]'.
                       Glyphless 'Helvetica' layers (junk OCR embedded by a scanner) and AdarshaLipi (non-Bijoy
                       ANSI) are judged unusable -> blank, with the reason in text_layer_note.
Pages that were never OCR'd and have a usable text layer get blank OCR fields (text-layer-only documents).
Writes 05_output/final/bgd_ocr_pages.csv (UTF-8 with BOM so Excel shows Bangla)."""
import csv, glob, os, pathlib, re, statistics, sys
import fitz
ROOT = pathlib.Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT / "scripts"))
from phase3_F3H_moa_spans import bijoy

csv.field_size_limit(10**9)
OCR = ROOT / "03_extracted/text/ocr"
ENGINE = "Tesseract 5.4 ben+eng tessdata_best, psm 6, 300 dpi"
CTRL = re.compile(r"[\x00-\x08\x0b-\x1f]")
JUNK_FONTS = ("Helvetica", "AdarshaLipi")
BIJOY_FONTS = ("SutonnyMJ", "SutonnyOMJ")


def manifest_urls():
    urls = {}
    files = ["02_raw/manifest.csv"] + sorted(glob.glob("02_raw/_manifest_parts/*.csv"))
    for f in files:
        for r in csv.DictReader(open(f, encoding="utf-8")):
            p = (r.get("file_path") or "").replace("\\", "/")
            if p and r.get("source_url") and p not in urls:
                urls[p] = r["source_url"]
    return urls


def classify(f):
    s = f.lower()
    if "nsb_minutes" in s or "tc_minutes" in s:
        return "minutes"
    if "gazette" in s or "moa_extra" in s or "release_notification" in s or "sro" in s or "mofl_gazette" in s:
        return "gazette"
    if "approved_crop_varieties" in s or "registered_hybrid" in s or "approved_varieties_notified" in s \
            or "hybrid_rice_list" in s or "hybrid_rice_varieties_list" in s or "item4_crop" in s:
        return "official_list"
    if "/brri/" in s or "leaflet" in s or "factsheet" in s or "bfri_pub" in s:
        return "leaflet"
    if "sca_laws" in s or "procedure" in s or "guideline" in s or "seed_rules" in s or "declaration" in s:
        return "law_rule_procedure"
    if "dof_notice" in s or "prajnapan" in s:
        return "notice"
    return "other_official"


def text_layer(page):
    """Return (text, note). Bijoy spans converted per run of consecutive Bijoy spans in a line."""
    fonts, out_lines, n_unmapped = set(), [], 0
    d = page.get_text("dict", sort=True)
    for b in d["blocks"]:
        for l in b.get("lines", []):
            runs = []   # (is_bijoy, text)
            for s in l["spans"]:
                t = s["text"]
                if not t:
                    continue
                fonts.add(s["font"])
                if CTRL.search(t):
                    n_unmapped += 1
                    runs.append((False, "[?]"))
                    continue
                isb = s["font"].startswith(BIJOY_FONTS)
                if runs and runs[-1][0] == isb and isb:
                    runs[-1] = (True, runs[-1][1] + t)
                else:
                    runs.append((isb, t))
            parts = []
            for isb, t in runs:
                if isb:
                    try:
                        t = bijoy(t).replace("ÿ", "ক্ষ")   # bijoy2unicode leaves the ক্ষ glyph unmapped
                    except Exception:
                        t = "[bijoy-fail: " + t + "]"
                parts.append(t)
            line = "".join(parts).rstrip()
            if line.strip():
                out_lines.append(line)
    text = "\n".join(out_lines)
    fams = sorted(fonts)
    readable = [f for f in fams if not f.startswith(JUNK_FONTS)]
    if not text.strip():
        return "", "no text layer"
    if not readable:
        return "", f"text layer unusable (fonts: {', '.join(fams)}: glyphless junk OCR / non-Bijoy ANSI font)"
    note = "text layer; Bijoy (SutonnyMJ) spans converted with bijoy2unicode + F3H repairs, other fonts kept raw; fonts: " + ", ".join(fams)
    if n_unmapped:
        note += f"; {n_unmapped} span(s) in fonts without a Unicode map replaced by [?]"
    if any(f.startswith(JUNK_FONTS) for f in fams):
        note += "; Helvetica/AdarshaLipi spans are junk embedded OCR"
    if "hybrid_rice_varieties_list_2026" in page.parent.name or "item4_crop" in page.parent.name:
        note += "; Nikosh Bangla in this list has a broken ToUnicode map (letters garbled, digits/Latin fine; see decisions_F3H)"
    return text, note


def conf_stats(tsv):
    if not tsv.exists():
        return "", "", "", ""
    confs = []
    with open(tsv, encoding="utf-8", errors="replace") as fh:
        for r in csv.DictReader(fh, delimiter="\t", quoting=csv.QUOTE_NONE):
            try:
                c = float(r["conf"])
            except (TypeError, ValueError, KeyError):
                continue
            if r.get("level") == "5" and c >= 0 and (r.get("text") or "").strip():
                confs.append(c)
    if not confs:
        return "", "", "", 0
    return (round(statistics.mean(confs), 2), round(statistics.median(confs), 2),
            round(100 * sum(c < 60 for c in confs) / len(confs), 2), len(confs))


def main():
    urls = manifest_urls()
    inv = list(csv.DictReader(open("04_working/F5L/inventory_pages.csv", encoding="utf-8")))
    rows, docs = [], {}
    for r in inv:
        f, p = r["source_file"], int(r["page"])
        stem = pathlib.Path(f).stem
        txt = OCR / stem / f"p{p:03d}_psm6.txt"
        tsv = OCR / stem / f"p{p:03d}_psm6.tsv"
        if f not in docs:
            docs[f] = fitz.open(f)
        tl, note = text_layer(docs[f][p - 1])
        ocr_text = txt.read_text(encoding="utf-8", errors="replace") if txt.exists() else ""
        if txt.exists() and not ocr_text.strip() and not tl:
            status = "OCR'd: no text recognised (blank or image-only page)"
        elif not ocr_text and not tl:
            status = "not OCR'd, no usable text layer"
        elif ocr_text and tl:
            status = "ocr + text layer"
        elif ocr_text:
            status = "ocr only"
        else:
            status = "text layer only"
        mean, med, pct, n = conf_stats(tsv) if txt.exists() else ("", "", "", "")
        if txt.exists() and not tsv.exists():
            note2 = "OCR text cached; word-level TSV not (yet) available, confidences blank"
        else:
            note2 = ""
        rows.append(dict(source_file=f, page=p, n_pages=r["n_pages"], doc_class=classify(f),
                         source_url=urls.get(f, ""),
                         ocr_engine=ENGINE if txt.exists() else "",
                         full_ocr_text=ocr_text, mean_word_conf=mean, median_word_conf=med,
                         pct_words_conf_below_60=pct, n_words=n,
                         text_layer_text=tl, coverage_status=status,
                         text_layer_note=note, ocr_note=note2,
                         png_path=str((OCR / stem / f"p{p:03d}.png").relative_to(ROOT)).replace("\\", "/") if (OCR / stem / f"p{p:03d}.png").exists() else "",
                         ocr_txt_path=str(txt.relative_to(ROOT)).replace("\\", "/") if txt.exists() else ""))
    # pages whose text layer is mostly unmapped glyphs -> queue for OCR (phase3_F5L_ocr.py reads this list)
    poor = []
    for r in rows:
        t = r["text_layer_text"]
        if t and not r["ocr_txt_path"]:
            q = t.count("[?]")
            good = len(re.findall(r"[ঀ-৿A-Za-z0-9]", t.replace("[?]", "")))
            if q * 5 > good or good < 40:
                poor.append((r["source_file"], r["page"]))
                r["text_layer_note"] += "; text layer mostly unreadable (queued for OCR)"
    with open("04_working/F5L/poor_text_layer_pages.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(["source_file", "page"]); w.writerows(poor)
    out = ROOT / "05_output/final/bgd_ocr_pages.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    cols = ["source_file", "page", "source_url", "ocr_engine", "full_ocr_text", "mean_word_conf", "median_word_conf",
            "pct_words_conf_below_60", "n_words", "text_layer_text", "n_pages", "doc_class", "coverage_status",
            "text_layer_note", "ocr_note", "png_path", "ocr_txt_path"]
    with open(out, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    import collections
    print(len(rows), "pages", len(docs), "documents")
    print(collections.Counter(r["coverage_status"] for r in rows))
    print(collections.Counter(r["doc_class"] for r in rows))
    print("no url:", sorted({r["source_file"] for r in rows if not r["source_url"]}))


if __name__ == "__main__":
    main()
