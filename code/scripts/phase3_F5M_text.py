"""F5M: page text for every OCR'd NSB minutes file, with ruled tables read cell by cell.
For each page: Tesseract psm6 lines (from the cached TSV) outside table boxes + table rows from the cell OCR
(phase3_F5M_tables.py), merged top-to-bottom. Two-column tables (the 'আলোচনা | সিদ্ধান্ত' matrix) are written as
'[কলাম ১] ...' / '[কলাম ২] ...' paragraphs; tables with more columns as one line per row, cells joined by " ¦ "..
Writes 03_extracted/text/F5M/<stem>.txt ('=== page N' markers) and <stem>.lines.json (per output line:
page, kind psm6|cell, bbox at 300 dpi, cell png) so any line can be cropped for a visual check.
The unmodified psm6 OCR stays in 03_extracted/text/ocr/<stem>/pNNN_psm6.txt (the 'raw OCR')."""
import sys, json, pathlib, csv, re
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_ocr import OCR, ROOT
G = ROOT / "03_extracted/text/F5M/grid"
CELLS = ROOT / "03_extracted/text/ocr_cells"
OUT = ROOT / "03_extracted/text/F5M"
csv.field_size_limit(10**9)


def tsv_lines(path, dx=0, dy=0):
    """-> list of (top, left, bottom, right, text) per Tesseract line"""
    L = {}
    if not path.exists():
        return []
    with open(path, encoding="utf-8", errors="replace") as f:
        rd = csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
        hdr = next(rd, None)
        for r in rd:
            if len(r) < 12 or r[0] != "5":
                continue
            t = r[11]
            if not t.strip():
                continue
            k = (int(r[2]), int(r[3]), int(r[4]))
            l, tp, w, h = int(r[6]) + dx, int(r[7]) + dy, int(r[8]), int(r[9])
            if k not in L:
                L[k] = [tp, l, tp + h, l + w, []]
            e = L[k]
            e[0] = min(e[0], tp); e[1] = min(e[1], l); e[2] = max(e[2], tp + h); e[3] = max(e[3], l + w)
            e[4].append(t)
    return sorted([(e[0], e[1], e[2], e[3], " ".join(e[4])) for e in L.values()])


SPLITPAGES = []


def tsv_words(path):
    """-> list of (line_key, left, top, right, bottom, text) for every word of a psm6 TSV"""
    out = []
    if not path.exists():
        return out
    with open(path, encoding="utf-8", errors="replace") as f:
        rd = csv.reader(f, delimiter="	", quoting=csv.QUOTE_NONE)
        next(rd, None)
        for r in rd:
            if len(r) < 12 or r[0] != "5" or not r[11].strip():
                continue
            l, t, w, h = int(r[6]), int(r[7]), int(r[8]), int(r[9])
            out.append(((int(r[2]), int(r[3]), int(r[4])), l, t, l + w, t + h, r[11]))
    return out


def cell_from_words(words, box):
    """words of the full-page psm6 OCR whose centre lies in the cell -> lines (top, left, bottom, right, text)"""
    x0, y0, x1, y1 = box
    L = {}
    for k, l, t, r, b, tx in words:
        cx, cy = (l + r) / 2, (t + b) / 2
        if x0 <= cx <= x1 and y0 <= cy <= y1:
            e = L.setdefault(k, [t, l, b, r, []])
            e[0] = min(e[0], t); e[1] = min(e[1], l); e[2] = max(e[2], b); e[3] = max(e[3], r); e[4].append((l, tx))
    return sorted((e[0], e[1], e[2], e[3], " ".join(t for _, t in sorted(e[4]))) for e in L.values())


def matrix_split(stem, pn, boxes=()):
    """Two-column 'আলোচনা | সিদ্ধান্ত' pages whose ruling is too broken for the grid detector.
    Find the column rule x by a dark-pixel column projection (x in 55-85 % of width); a psm6 line lies inside the
    table when the rule is dark through >= 50 % of the line's height; its words are then split left/right of the
    rule by word centre. Table rows are split at horizontal rules. Returns list of (lines, metas) or None."""
    import numpy as np
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    a = np.asarray(Image.open(OCR / stem / f"p{pn:03d}.png").convert("L")) < 150
    H, Wd = a.shape
    for b in boxes:                     # blank out tables handled by the grid route
        a[max(0, b[1] - 10):b[3] + 10, max(0, b[0] - 10):b[2] + 10] = False
    lo, hi = int(0.55 * Wd), int(0.85 * Wd)
    colsum = a[:, lo:hi].sum(axis=0)
    x = lo + int(colsum.argmax())
    if colsum.max() < 0.08 * H:
        return None
    band = a[:, max(0, x - 6):x + 7].any(axis=1)
    words = tsv_words(OCR / stem / f"p{pn:03d}_psm6.tsv")
    L = {}
    for k, l, t, r, b, tx in words:
        cx, cy = (l + r) / 2, (t + b) / 2
        if any(bb[0] - 5 <= cx <= bb[2] + 5 and bb[1] - 5 <= cy <= bb[3] + 5 for bb in boxes):
            continue
        L.setdefault(k, []).append((l, t, r, b, tx))
    lines = sorted(L.values(), key=lambda ws: min(w[1] for w in ws))
    # left border of the table = leftmost long vertical dark column left of x
    out = []      # (top, kind, payload)
    for ws in lines:
        t0 = min(w[1] for w in ws); b0 = max(w[3] for w in ws)
        inside = band[t0:b0 + 1].mean() >= 0.35 if b0 > t0 else False
        ws = [w for w in ws if not (w[2] - w[0] < 40 and abs((w[0] + w[2]) / 2 - x) < 30 and re.fullmatch(r"[|।৷!lI1:;\[\]()]+", w[4]))] or ws
        crosses = any(w[0] < x - 4 and w[2] > x + 4 for w in ws)
        if inside and not crosses:
            left = " ".join(w[4] for w in sorted(ws) if (w[0] + w[2]) / 2 < x)
            right = " ".join(w[4] for w in sorted(ws) if (w[0] + w[2]) / 2 >= x)
            out.append((t0, "T", (left, right, [t0, min(w[0] for w in ws), b0, max(w[2] for w in ws)])))
        else:
            out.append((t0, "P", (" ".join(w[4] for w in sorted(ws)), [t0, min(w[0] for w in ws), b0, max(w[2] for w in ws)])))
    # horizontal rules across the table width (row separators)
    rows_dark = a[:, max(0, x - 900):x].mean(axis=1)
    hr = [y for y in range(H) if rows_dark[y] > 0.6]
    def row_id(y):
        return sum(1 for h in hr if h < y)
    res, block = [], None
    def flush():
        if block:
            L1, M1 = [], []
            for c, nm in ((0, "[কলাম 1]"), (1, "[কলাম 2]")):
                part = [(seg[c], seg[2]) for seg in block if seg[c].strip()]
                if part:
                    L1.append(nm); M1.append({"page": pn, "kind": "split", "bbox": None})
                    for tx, bb in part:
                        L1.append(tx); M1.append({"page": pn, "kind": "split", "bbox": bb, "col": c + 1, "x_rule": x})
                    L1.append(""); M1.append(None)
            res.append((block[0][2][0], L1, M1))
    cur_row = None
    for t0, kind, pl in out:
        if kind == "T":
            rid = row_id(t0)
            if block is not None and rid != cur_row:
                flush(); block = None
            if block is None:
                block = []
            cur_row = rid
            block.append(pl)
        else:
            flush(); block = None
            res.append((t0, [pl[0]], [{"page": pn, "kind": "psm6", "bbox": pl[1]}]))
    flush()
    return res


def build(stem):
    grid = json.loads((G / f"{stem}.json").read_text()) if (G / f"{stem}.json").exists() else {}
    pngs = sorted((OCR / stem).glob("p[0-9][0-9][0-9].png"))
    text, meta = [], []
    SPLITPAGES.clear()
    for png in pngs:
        pn = int(png.stem[1:])
        text.append(f"=== page {pn}"); meta.append(None)
        tabs = grid.get(png.name, [])
        raw = OCR / stem / f"p{pn:03d}_psm6.txt"
        MS = None
        if re.match(r"nsb_minutes_(09[3-9]|1\d\d)$", stem):
            MS = matrix_split(stem, pn, [t["box"] for t in tabs])
            if MS and any(m and m.get("kind") == "split" for y, L1, M1 in MS for m in M1):
                SPLITPAGES.append(pn)
            else:
                MS = None
        if MS is not None and not tabs:
            for y, L1, M1 in MS:
                text.extend(L1); meta.extend(M1)
            continue
        if not tabs:
            # no ruled table: psm6 text as-is (line boxes from the TSV where they can be paired)
            tl = tsv_lines(OCR / stem / f"p{pn:03d}_psm6.tsv")
            tlx = {re.sub(r"\s+", " ", t[4]).strip(): t for t in tl}
            rt = raw.read_text(encoding="utf-8", errors="replace") if raw.exists() else ""
            if not rt.strip():   # empty .txt beside a filled .tsv: rebuild the lines from the TSV
                rt = chr(10).join(t[4] for t in tl)
            for line in rt.splitlines():
                text.append(line)
                b = tlx.get(re.sub(r"\s+", " ", line).strip())
                meta.append({"page": pn, "kind": "psm6", "bbox": list(b[:4]) if b else None})
            continue
        items = []   # (y, order, [lines], [meta])
        boxes = [t["box"] for t in tabs]
        if MS is not None:
            for y, L1, M1 in MS:
                items.append((y, 0, L1, M1))
        for tp, l, bt, rt, t in ([] if MS is not None else tsv_lines(OCR / stem / f"p{pn:03d}_psm6.tsv")):
            cy = (tp + bt) / 2; cx = (l + rt) / 2
            if any(b[1] - 5 <= cy <= b[3] + 5 and b[0] - 5 <= cx <= b[2] + 5 for b in boxes):
                continue
            items.append((tp, 0, [t], [{"page": pn, "kind": "psm6", "bbox": [tp, l, bt, rt]}]))
        words = tsv_words(OCR / stem / f"p{pn:03d}_psm6.tsv")
        for k, tb in enumerate(tabs):
            xs, ys = tb["x"], tb["y"]
            ncol = len(xs) - 1
            for r in range(len(ys) - 1):
                cells = []
                for c in range(ncol):
                    base = CELLS / stem / f"p{pn:03d}_t{k}_r{r:02d}_c{c}"
                    if base.with_suffix(".tsv").exists():
                        ls = tsv_lines(base.with_suffix(".tsv"), xs[c] + 7, ys[r] + 6)     # cell re-OCR
                    else:   # words of the full-page psm6 OCR, re-assigned to this cell by position
                        ls = cell_from_words(words, (xs[c], ys[r], xs[c + 1], ys[r + 1]))
                    cells.append((ls, str(base.with_suffix(".png").relative_to(ROOT)), [xs[c], ys[r], xs[c + 1], ys[r + 1]]))
                if not any(c[0] for c in cells):
                    continue
                lines, mm = [], []
                if ncol == 2:
                    for c, (ls, cp, cb) in enumerate(cells):
                        if not ls:
                            continue
                        lines.append(f"[কলাম {c+1}]"); mm.append({"page": pn, "kind": "cell", "bbox": cb, "cell": cp})
                        for tp, l, bt, rt, t in ls:
                            lines.append(t); mm.append({"page": pn, "kind": "cell", "bbox": [tp, l, bt, rt], "cell": cp})
                        lines.append(""); mm.append(None)
                else:
                    row = " ¦ ".join(" ".join(t[4] for t in ls) for ls, cp, cb in cells)
                    lines.append(row); mm.append({"page": pn, "kind": "cell_row", "bbox": [ys[r], xs[0], ys[r + 1], xs[-1]],
                                                  "cells": [cp for ls, cp, cb in cells]})
                items.append((ys[r], 1, lines, mm))
        items.sort(key=lambda x: (x[0], x[1]))
        for y, o, ls, mm in items:
            text.extend(ls); meta.extend(mm)
    (OUT / f"{stem}.splitpages.json").write_text(json.dumps(SPLITPAGES))
    (OUT / f"{stem}.txt").write_text("\n".join(text) + "\n", encoding="utf-8")
    (OUT / f"{stem}.lines.json").write_text(json.dumps(meta), encoding="utf-8")
    return len(pngs)


if __name__ == "__main__":
    for s in sys.argv[1:]:
        print(s, build(s))
