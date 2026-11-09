"""Write 02_raw/CATALOGUE.csv: one row per manifest file, describing what the file is and what it supports.

    python scripts/build_catalogue.py

Inputs (read only): 02_raw/manifest.csv, the files in 02_raw, 05_output/evidence_all.csv, 05_output/final/bgd_sources.csv,
the local_file columns of the other released tables in 05_output/final (never bgd_nsb_attendance.csv),
05_output/final/bgd_cgiar_sources.csv (titles) and 05_output/final/bgd_ocr_pages.csv (language of scanned PDFs).

Columns
  file_path, title, title_basis, issuing_body, document_date, document_type, language, pages, bytes, mime_type, sha256,
  source_url (mailto= removed), archived_url, archive_status, cited_in_register, in_bgd_sources, tables_citing,
  fields_supported, n_evidence_rows, rights_class, rights_basis, duplicate_of, integrity_status, download_date, agent

Rules. Titles come, in order, from the source title recorded in the evidence, the CGIAR source table, the PDF's own
metadata title, the HTML <title>, or the API query in the address; otherwise the title is left blank (title_basis says
which). Issuing body, document type and rights class follow the folder and host rules in scripts/lib_archive.py; the
document date is the date written into the file name, blank if there is none. Language is measured on the text layer
(first three pages), the OCR text, or the page text: bn, en or mixed; Bijoy-encoded text layers count as Bangla.
cited_in_register is Y when the file is a source in bgd_sources.csv, has a row in the evidence, or is the local_file of a
row in any released table. The columns bytes, mime_type, duplicate_of and integrity_status are taken from the manifest when
scripts/repair_manifest.py has added them, and computed here otherwise; archive_status is always recomputed.
"""
import csv
import html
import pathlib
import re
import sys
from collections import Counter, defaultdict

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import lib_archive as LA

ROOT = LA.ROOT
F = ROOT / "05_output/final"
OUT = ROOT / "02_raw/CATALOGUE.csv"
PRIVATE = {"bgd_nsb_attendance.csv"}
# PDF metadata titles are kept only if they look like a real title: three words or more, no file name, scanner or
# template label (e.g. 'BRRI dhan115_22-02-2026.cdr', 'CamScanner 04-08-2026', 'Draft ... Template', '1.Inner')
JUNK_TITLE = re.compile(r"^(untitled|title|document\d*|microsoft word|powerpoint|slide \d|\d+\s*\.|\s*$)|\.[a-z0-9]{2,4}$|"
                        r"camscanner|scanned|template|^[\W\d_]+$", re.I)
COLS = ["file_path", "title", "title_basis", "issuing_body", "document_date", "document_type", "language", "pages", "bytes",
        "mime_type", "sha256", "source_url", "archived_url", "archive_status", "cited_in_register", "in_bgd_sources",
        "tables_citing", "fields_supported", "n_evidence_rows", "rights_class", "rights_basis", "duplicate_of",
        "integrity_status", "download_date", "agent"]


def clean(s):
    return re.sub(r"\s+", " ", html.unescape(s or "")).strip()


def html_text(raw):
    t = re.sub(r"(?is)<(script|style|noscript)\b.*?</\1>", " ", raw)
    return clean(re.sub(r"(?s)<[^>]+>", " ", t))


def html_title(raw):
    m = re.search(r"(?is)<title[^>]*>(.*?)</title>", raw)
    t = clean(m.group(1)) if m else ""
    return "" if not t or re.search(r"just a moment|attention required|404|403|not found|access denied", t, re.I) else t[:300]


def api_title(path, url, issuer):
    q = dict(LA.up.parse_qsl(LA.up.urlsplit(url).query))
    term = q.get("search") or q.get("query") or q.get("query.bibliographic") or q.get("q") or ""
    m = re.search(r"/journals/([\dX\-]+)/works", url)
    if m:
        term = f"works in journal ISSN {m.group(1)}"
    if not term:
        return ""
    pg = re.search(r"_p(\d+)\.json$", path)
    return f"{issuer or 'API'} search response: {term}" + (f" (page {int(pg.group(1)) + 1})" if pg else "")


def pdf_info(fp):
    """(page count, metadata title, text of the first three pages); (0, '', '') if the PDF does not open."""
    try:
        import fitz
        with fitz.open(fp) as d:
            t = clean((d.metadata or {}).get("title", ""))
            text = " ".join(d[i].get_text() for i in range(min(3, d.page_count)))
            return d.page_count, ("" if JUNK_TITLE.search(t) or len(t.split()) < 3 else t[:300]), text
    except Exception:  # noqa
        return 0, "", ""


def xlsx_text(fp, limit=400):
    try:
        import openpyxl
        wb = openpyxl.load_workbook(fp, read_only=True, data_only=True)
        out = []
        for ws in wb.worksheets[:2]:
            for row in ws.iter_rows(max_row=60, values_only=True):
                out += [str(v) for v in row if isinstance(v, str)]
                if len(out) > limit:
                    break
        wb.close()
        return " ".join(out)
    except Exception:  # noqa
        return ""


def main():
    man = LA.read_manifest()
    ev = pd.read_csv(ROOT / "05_output/evidence_all.csv", dtype=str, keep_default_na=False,
                     usecols=["field", "source_title", "local_file"])
    ev["local_file"] = ev.local_file.str.replace("\\", "/", regex=False)
    src = pd.read_csv(F / "bgd_sources.csv", dtype=str, keep_default_na=False)
    in_src = set(src.local_file.str.replace("\\", "/", regex=False))
    titles = {}
    for lf, g in ev[ev.source_title.str.strip() != ""].groupby("local_file"):
        titles[lf] = g.source_title.value_counts().index[0]
    for r in src.itertuples():
        if r.source_title.strip():
            titles.setdefault(r.local_file, r.source_title)
    cg = pd.read_csv(F / "bgd_cgiar_sources.csv", dtype=str, keep_default_na=False)
    cg_titles = {r.local_file: r.source_title for r in cg.itertuples() if r.source_title.strip() and r.local_file}
    fields = ev.groupby("local_file").field.agg(lambda s: " | ".join(sorted(set(s))))
    n_ev = ev.groupby("local_file").size()
    tables = defaultdict(set)
    for fp in sorted(F.glob("bgd_*.csv")):
        if fp.name in PRIVATE:
            continue
        with open(fp, encoding="utf-8-sig", newline="") as fh:
            header = next(csv.reader(fh))
        lcols = [c for c in header if c == "local_file" or c.endswith("local_file")]
        if not lcols:
            continue
        d = pd.read_csv(fp, dtype=str, keep_default_na=False, usecols=lcols)
        for c in lcols:
            for v in set(d[c]):
                for part in re.split(r"\s*[|;]\s*", v):
                    if part.startswith("02_raw/"):
                        tables[part.replace("\\", "/")].add(fp.name)
    ocr = pd.read_csv(F / "bgd_ocr_pages.csv", dtype=str, keep_default_na=False,
                      usecols=["source_file", "page", "full_ocr_text", "text_layer_text"])
    ocr["p"] = pd.to_numeric(ocr.page, errors="coerce").fillna(999)
    ocr_text = ocr[ocr.p <= 3].groupby("source_file").apply(
        lambda g: " ".join(g.full_ocr_text) + " " + " ".join(g.text_layer_text), include_groups=False).to_dict()

    first_sha = {}
    for r in man:
        first_sha.setdefault(r["sha256"], r["file_path"])
    rows = []
    for r in man:
        path, url = r["file_path"], r.get("source_url", "")
        fp = ROOT / path
        ext = fp.suffix.lower()
        exists = fp.exists()
        head = fp.open("rb").read(2_000_000) if exists and ext in (".json", ".xml", ".html", ".htm", ".txt", ".csv") else b""
        pages, meta_title, text = ("", "", "")
        if ext == ".pdf" and exists:
            pages, meta_title, text = pdf_info(fp)
            if not LA.language(text):
                text = ocr_text.get(path, text)
        elif ext in (".html", ".htm") and exists:
            raw = head.decode("utf-8", "replace")
            text = html_text(raw)[:30000]
        elif ext in (".json", ".xml", ".txt", ".csv"):
            text = head.decode("utf-8", "replace")[:30000]
        elif ext == ".xlsx" and exists:
            text = xlsx_text(fp)
        doc_type = LA.document_type(path, url)
        issuer = LA.issuing_body(path, url, doc_type)
        title, basis = titles.get(path, ""), "register source title"
        if not title and cg_titles.get(path):
            title, basis = cg_titles[path], "CGIAR source table"
        if not title and meta_title:
            title, basis = meta_title, "PDF metadata"
        if not title and ext in (".html", ".htm") and exists:
            t = html_title(head.decode("utf-8", "replace"))
            if t:
                title, basis = t, "HTML title"
        if not title and doc_type == "API response":
            t = api_title(path, url, issuer)
            if t:
                title, basis = t, "API query in address"
        if not title:
            basis = ""
        rc, rb = LA.rights_class(path, url, head)
        cited = path in in_src or path in fields.index or path in tables
        rows.append(dict(
            file_path=path, title=title, title_basis=basis, issuing_body=issuer, document_date=LA.document_date(path),
            document_type=doc_type, language=LA.language(text), pages=pages,
            bytes=r.get("bytes") or (fp.stat().st_size if exists else ""),
            mime_type=r.get("mime_type") or LA.mime_type(path), sha256=r["sha256"], source_url=LA.strip_mailto(url),
            archived_url=r.get("archived_url", ""), archive_status=LA.archive_status(r),   # recomputed: archive_wayback.py may have filled archived_url since repair
            cited_in_register="Y" if cited else "N", in_bgd_sources="Y" if path in in_src else "N",
            tables_citing=" | ".join(sorted(tables.get(path, ()))), fields_supported=fields.get(path, ""),
            n_evidence_rows=int(n_ev.get(path, 0)), rights_class=rc, rights_basis=rb,
            duplicate_of=r.get("duplicate_of", "") if "duplicate_of" in r else ("" if first_sha[r["sha256"]] == path else first_sha[r["sha256"]]),
            integrity_status=r.get("integrity_status") or ("missing" if not exists else ("truncated" if ext == ".pdf" and pages == 0 else "ok")),
            download_date=r.get("download_date", ""), agent=r.get("agent", "")))
    cat = pd.DataFrame(rows, columns=COLS)
    cat.to_csv(OUT, index=False, encoding="utf-8-sig")
    c = cat[cat.cited_in_register == "Y"]
    print(f"wrote {OUT.relative_to(ROOT)}: {len(cat)} files, {len(c)} cited ({(c.in_bgd_sources == 'Y').sum()} in bgd_sources.csv)")
    print("titles:", dict(Counter(cat.title_basis.replace("", "(blank)"))))
    print("cited files without title:", int((c.title == "").sum()))
    print("document_type:", dict(Counter(cat.document_type)))
    print("language:", dict(Counter(cat.language.replace("", "(blank)"))))
    print("rights_class (cited):", dict(Counter(c.rights_class)))
    print("archive_status (cited):", dict(Counter(c.archive_status)))
    print("integrity_status:", dict(Counter(cat.integrity_status)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
