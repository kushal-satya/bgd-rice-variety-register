"""F3H: span/char-level parse of the MoA cumulative hybrid-rice lists (2026 and 2018 editions).

Why not line-level conversion (P2A): the PDFs mix fonts. SutonnyMJ text is Bijoy-encoded (convert
with bijoy2unicode); Times New Roman / Vrinda / Shonar Bangla / Nirmala text is already Unicode or
Latin (keep raw; converting it garbles it); Nikosh text has a broken ToUnicode map, so its Bangla
letters come out garbled (digits and Latin survive) -> those cells are flagged for visual reading.

Cells are assigned with the table geometry: column x-borders and the horizontal rules drawn on each
page; characters (rawdict) are split at column borders, because one text span sometimes runs
across two cells. Rows without a serial at the top of a page continue the previous entry.

Writes 04_working/_F3H_moa<ed>_cells.csv (one row per serial).
"""
import csv, pathlib, re
import fitz
from bijoy2unicode import converter

ROOT = pathlib.Path(__file__).resolve().parents[1]
CONV = converter.Unicode()
BN = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
COLS = [("serial", 0, 85), ("name", 85, 184), ("origin", 184, 256), ("developer", 256, 350),
        ("region", 350, 458), ("date", 458, 10000)]
BANGLA = re.compile("[ঀ-৿]")
MARK = ""
CONS = "[ক-হড়ঢ়য়ৎ]"
VS = "[া-ৄেৈোৌ]"
HAS = "্"


def bijoy(raw):
    """bijoy2unicode plus four repairs for errors it makes on this list (checked against page images):
    reph (U+00A9) left after its cluster; U+00F8 (lower la) emitted as 'স্ন'; U+00AA U+00A8 (ra-phala +
    ya-phala) losing the first hasant; U+00CD (lower ta) emitted as 'ত্ম'."""
    t = raw.replace("Í", "Z").replace("©", MARK)
    u = CONV.convertBijoyToUnicode(t + "  ").rstrip()
    u = re.sub("(" + CONS + "(?:" + HAS + CONS + ")*" + VS + "*)" + MARK, lambda m: "র" + HAS + m.group(1), u)
    u = u.replace(MARK, "র" + HAS)
    if "ø" in raw:
        def _la(m):
            v = m.group(2) or ""
            if v == "ে" and m.group(3):
                v, tail = "ো", ""
            else:
                tail = m.group(3) or ""
            return m.group(1) + HAS + "ল" + v + tail
        u = re.sub("(" + CONS + ")([িে])?স" + HAS + "ন(া)?", _la, u)
    if "ª¨" in raw:
        u = re.sub("(" + CONS + ")র" + HAS + "য", lambda m: m.group(1) + HAS + "র" + HAS + "য", u)
    return u


def convert(text, font):
    if font.startswith("SutonnyMJ"):
        try:
            return bijoy(text), "bijoy"
        except Exception:
            return text, "bijoy_fail"
    if font.startswith("Nikosh") and BANGLA.search(text):
        return text, "nikosh"
    return text, "raw"


def colof(x, cols=COLS):
    return next(c for c, a, z in cols if a <= x < z)


def page_cols(page):
    """Column borders from the vertical rules on the page (the 2018 edition has different widths)."""
    import collections
    xs = collections.Counter()
    for g in page.get_drawings():
        for it in g["items"]:
            if it[0] == "l" and abs(it[1].x - it[2].x) < 1 and abs(it[1].y - it[2].y) > 5:
                xs[round(it[1].x)] += 1
            if it[0] == "re" and it[1].width < 2 and it[1].height > 5:
                xs[round(it[1].x0)] += 1
    v = sorted(x for x, c in xs.items() if c > 3)
    if len(v) != 7:
        return COLS
    names = [c for c, _, _ in COLS]
    edges = [0] + v[1:6] + [10000]
    return [(names[i], edges[i], edges[i + 1]) for i in range(6)]


def hrules(page):
    ys = []
    for g in page.get_drawings():
        for it in g["items"]:
            if it[0] == "l":
                a, b = it[1], it[2]
                if abs(a.y - b.y) < 1 and min(a.x, b.x) < 100 and max(a.x, b.x) > 150:
                    ys.append(a.y)
            elif it[0] == "re":
                r = it[1]
                if r.x0 < 100 and r.x1 > 150:
                    ys += [r.y0] if r.height < 2 else [r.y0, r.y1]
    out = []
    for y in sorted(ys):
        if not out or y - out[-1] > 2:
            out.append(y)
    return out


def page_cells(page, rules, cols):
    top, bot = rules[0], rules[-1]
    cells = {}
    for b in page.get_text("rawdict")["blocks"]:
        for l in b.get("lines", []):
            for s in l["spans"]:
                chars = s["chars"]
                if not chars:
                    continue
                y = (s["bbox"][1] + s["bbox"][3]) / 2
                if y < top or y > bot:
                    continue
                band = max(i for i, r in enumerate(rules) if r <= y)
                # split the span at column borders (by character centre)
                pieces = []
                for ch in chars:
                    col = colof((ch["bbox"][0] + ch["bbox"][2]) / 2, cols)
                    if pieces and pieces[-1][0] == col:
                        pieces[-1][1].append(ch)
                    else:
                        pieces.append((col, [ch]))
                for col, chs in pieces:
                    raw = "".join(ch["c"] for ch in chs)
                    if not raw.strip():
                        continue
                    t, kind = convert(raw, s["font"])
                    cells.setdefault(band, {}).setdefault(col, []).append(
                        (s["bbox"][1], chs[0]["bbox"][0], t, kind))
    return cells


def parse(pdf, ed):
    doc = fitz.open(ROOT / pdf)
    entries, cur = [], None
    for pn in range(doc.page_count):
        page = doc[pn]
        rules = hrules(page)
        if len(rules) < 2:
            continue
        cells = page_cells(page, rules, page_cols(page))
        for band in sorted(cells):
            c = cells[band]
            ser = re.sub(r"[^0-9]", "", "".join(t for _, _, t, _ in sorted(c.get("serial", []))).translate(BN))
            blank = (not ser and cur is not None and band != min(cells) and c.get("name") and c.get("date"))
            if blank:  # full row with an empty serial cell (2026 list: BADC hybrid dhan-2 after 124)
                ser = str(cur["serial"] + 1)
            if ser:
                cur = {"serial": int(ser), "pages": [pn + 1], "bands": [], "kinds": set(),
                       "serial_note": "serial cell blank on the page; serial inferred" if blank else "",
                       **{k: [] for k, _, _ in COLS[1:]}}
                entries.append(cur)
            elif cur is None:
                continue  # header band
            elif pn + 1 not in cur["pages"]:
                cur["pages"].append(pn + 1)
            nxt = rules[band + 1] if band + 1 < len(rules) else None
            cur["bands"].append((pn + 1, round(rules[band], 1), round(nxt, 1) if nxt else None))
            for col, _, _ in COLS[1:]:
                clusters = []  # visual lines: cluster pieces whose top y differs by < 5 pt, then order by x
                for y, x, t, k in sorted(c.get(col, [])):
                    if clusters and abs(y - clusters[-1][0]) < 5:
                        clusters[-1][1].append((x, t))
                    else:
                        clusters.append((y, [(x, t)]))
                    if k != "raw":
                        cur["kinds"].add((col, k))
                lines = ["".join(t for _, t in sorted(pcs)) for _, pcs in clusters]
                cur[col] += [re.sub(r"\s+", " ", ln).strip() for ln in lines if ln.strip()]
    rows = []
    for e in entries:
        r = {"edition": ed, "source_file": pdf, "serial": e["serial"], "pages": ";".join(map(str, e["pages"])),
             "serial_note": e["serial_note"], "bands": ";".join(f"p{p}:{a}-{b}" for p, a, b in e["bands"])}
        for col, _, _ in COLS[1:]:
            r[col] = " | ".join(e[col])
        if e["serial_note"]:  # 2018 edition: serials 100-107 printed left-shifted into the name cell
            m = re.match(r"^([০-৯]+)\s+", r["name"])
            if m and int(m.group(1).translate(BN)) == e["serial"]:
                r["name"] = r["name"][m.end():]
                r["serial_note"] = "serial printed inside the name cell (shifted left); taken from there"
        r["nikosh_cols"] = ";".join(sorted({c for c, k in e["kinds"] if k == "nikosh"}))
        r["bijoy_fail"] = ";".join(sorted({c for c, k in e["kinds"] if k == "bijoy_fail"}))
        rows.append(r)
    return rows


if __name__ == "__main__":
    for pdf, ed in [("02_raw/moa/hybrid_rice_varieties_list_2026-02-05.pdf", "2026"),
                    ("02_raw/moa_wayback/hybrid_rice_list_2018-08-07.pdf", "2018")]:
        rows = parse(pdf, ed)
        with open(ROOT / f"04_working/_F3H_moa{ed}_cells.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        sers = [r["serial"] for r in rows]
        print(ed, len(rows), "max serial", max(sers), "missing", [s for s in range(1, max(sers) + 1) if s not in sers],
              "dups", sorted({s for s in sers if sers.count(s) > 1}),
              "nikosh rows", sum(1 for r in rows if r["nikosh_cols"]),
              "bijoy_fail rows", sum(1 for r in rows if r["bijoy_fail"]))
