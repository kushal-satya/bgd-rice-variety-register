"""F3H: render crops of MoA 2026 hybrid rice list rows (serials 103, 162-271)
for visual transcription of Nikosh-garbled Bangla cells."""
import csv
from pathlib import Path
import fitz

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "02_raw/moa/hybrid_rice_varieties_list_2026-02-05.pdf"
CELLS = ROOT / "04_working/_F3H_moa2026_cells.csv"
OUT = ROOT / "04_working/crops/F3H/moa26_nikosh"
GROUP = 6


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader(open(CELLS, encoding="utf-8")))
    want = {103} | set(range(162, 272))
    pieces = {}  # page -> list of (serial, y0, y1)
    for r in rows:
        if not r["serial"].isdigit() or int(r["serial"]) not in want:
            continue
        for b in r["bands"].split(";"):
            p, rng = b.split(":")
            y0, y1 = map(float, rng.split("-"))
            pieces.setdefault(int(p[1:]), []).append((int(r["serial"]), y0, y1))
    doc = fitz.open(PDF)
    index = []
    for p in sorted(pieces):
        lst = sorted(pieces[p], key=lambda t: t[1])
        for i in range(0, len(lst), GROUP):
            g = lst[i:i + GROUP]
            y0, y1 = min(t[1] for t in g), max(t[2] for t in g)
            s0, s1 = g[0][0], g[-1][0]
            name = f"moa26_p{p}_s{s0}" + (f"-{s1}" if s1 != s0 else "") + ".png"
            pix = doc[p - 1].get_pixmap(dpi=220, clip=fitz.Rect(55, y0 - 2, 552, y1 + 2))
            pix.save(OUT / name)
            for t in g:
                index.append((t[0], name))
    with open(OUT / "_crop_index.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["serial", "crop_file"])
        w.writerows(index)
    print(len(index), "pieces")


if __name__ == "__main__":
    main()
