"""F5L: inventory of official documents for the OCR page corpus.
For every PDF in the official folders (plus any PDF with an OCR cache dir), per page: text-layer chars,
fonts used, cached OCR files. Writes 04_working/F5L/inventory_pages.csv."""
import csv, glob, os, pathlib, collections
import fitz
ROOT = pathlib.Path(__file__).resolve().parents[1]
os.chdir(ROOT)
OFFICIAL = ["sca", "moa", "moa_wayback", "bgpress", "sca_wayback", "sca_laws"]
OCR = ROOT / "03_extracted/text/ocr"
pdfs = set()
for d in OFFICIAL:
    pdfs |= {p.replace(os.sep, "/") for p in glob.glob(f"02_raw/{d}/**/*.pdf", recursive=True)}
stems = set(os.listdir(OCR))
for p in glob.glob("02_raw/**/*.pdf", recursive=True):
    if pathlib.Path(p).stem in stems:
        pdfs.add(p.replace(os.sep, "/"))
rows = []
for f in sorted(pdfs):
    try:
        doc = fitz.open(f)
    except Exception as e:
        rows.append(dict(source_file=f, page=0, error=str(e))); continue
    stem = pathlib.Path(f).stem
    for i, pg in enumerate(doc):
        fonts = collections.Counter()
        n = 0
        for b in pg.get_text("dict")["blocks"]:
            for l in b.get("lines", []):
                for s in l["spans"]:
                    t = s["text"].strip()
                    if t:
                        fonts[s["font"]] += len(t); n += len(t)
        cd = OCR / stem
        def ex(sfx):
            return (cd / f"p{i+1:03d}{sfx}").exists()
        rows.append(dict(source_file=f, page=i + 1, n_pages=doc.page_count, text_chars=n,
                         fonts=";".join(f"{k}:{v}" for k, v in fonts.most_common(6)),
                         png=int(ex(".png")), psm6_txt=int(ex("_psm6.txt")), psm6_tsv=int(ex("_psm6.tsv")),
                         psm4_txt=int(ex("_psm4.txt")), n_images=len(pg.get_images()), error=""))
with open("04_working/F5L/inventory_pages.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) if rows[0].get("n_pages") else
                       ["source_file","page","n_pages","text_chars","fonts","png","psm6_txt","psm6_tsv","psm4_txt","n_images","error"])
    w.writeheader(); w.writerows(rows)
print(len(pdfs), "pdfs", len(rows), "pages")
