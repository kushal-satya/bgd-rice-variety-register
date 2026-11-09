"""P2B: parse SPIA Bangladesh Study 2025, Appendix B Table 27 (PDF pp.106-114) with pdfplumber word positions.
Columns come from the table's ruling-line x positions (identical on every page). Rows have no separators,
so each row is anchored on its 4-digit year in the Year column; every word below an anchor (and above the next)
belongs to that row (cells are top-aligned; checked on page renders). Names that wrap ("BRRI" / "dhan36") are
re-joined. Output: 03_extracted/tables/spia2025_table27.csv"""
import pdfplumber, csv, pathlib, re, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
PDF = ROOT / "02_raw/spia_cgspace/SPIA_Bangladesh_Study_2025.pdf"
X = [47, 107, 160, 227, 292, 354, 416, 462, 524, 587, 633, 700, 795]
COLS = ["variety", "year", "irri_direct", "indirect_ir_parent", "inger_entry", "in_reference_library",
        "sub1", "saline_tolerance", "drought_tolerance", "harvestplus", "irri_inger_listed_released_directly",
        "irri_inger_entry_used_as_parents"]


def col(w):
    xm = w["x0"] + 1  # left edge decides (cells are left-aligned)
    for k in range(len(X) - 1):
        if X[k] - 1 <= xm < X[k + 1]:
            return COLS[k]
    return None


def join(ws):
    ws = sorted(ws, key=lambda w: (round(w["top"]), w["x0"]))
    lines = []
    for w in ws:
        if lines and abs(w["top"] - lines[-1][0]["top"]) < 3:
            lines[-1].append(w)
        else:
            lines.append([w])
    parts = [" ".join(x["text"] for x in sorted(l, key=lambda w: w["x0"])) for l in lines]
    s = ""
    for p in parts:
        if not s:
            s = p
        elif s.endswith(("-", "/")):
            s += p  # line broke inside a code or after a slash
        else:
            s += " " + p
    return s, len(parts)


def main():
    pdf = pdfplumber.open(PDF)
    rows, stray = [], []
    for pn in range(105, 114):
        p = pdf.pages[pn]
        hdr_bottom = max(r["bottom"] for r in p.rects)  # shaded header cells
        foot = [l["top"] for l in p.lines if abs(l["top"] - l["bottom"]) < 1 and l["top"] > hdr_bottom + 1]
        bottom = min(foot) if foot else p.height
        words = [w for w in p.extract_words() if hdr_bottom < w["top"] < bottom]
        anchors = sorted(w["top"] for w in words if col(w) == "year" and re.fullmatch(r"(19|20)\d\d", w["text"]))
        for i, a in enumerate(anchors):
            nxt = anchors[i + 1] if i + 1 < len(anchors) else bottom
            rw = [w for w in words if a - 2 <= w["top"] < nxt - 2]
            cells = {c: [] for c in COLS}
            for w in rw:
                c = col(w)
                if c: cells[c].append(w)
            r = {}
            for c in COLS:
                r[c], n = join(cells[c])
            r["variety"] = re.sub(r"\s+", " ", r["variety"]).strip()
            r["n_lines"] = max(1, len({round(w["top"]) for w in rw}))
            r["pdf_page"] = pn + 1; r["printed_page"] = pn + 1 - 12; r["row_top_pt"] = round(a, 1)
            rows.append(r)
        if anchors:
            stray += [(pn + 1, w["text"]) for w in words if w["top"] < anchors[0] - 2]
    bad = [r for r in rows if any(r[c] not in ("Y", "N") for c in COLS[2:10])]
    out = ROOT / "03_extracted/tables/spia2025_table27.csv"
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["row_no"] + COLS + ["n_lines", "pdf_page", "printed_page", "row_top_pt"])
        w.writeheader()
        for i, r in enumerate(rows, 1):
            w.writerow({"row_no": i, **r})
    print(len(rows), "rows; flag cells not Y/N:", len(bad), "; stray words above first anchor:", stray, file=sys.stderr)
    for r in bad:
        print("BAD", r, file=sys.stderr)


if __name__ == "__main__":
    main()
