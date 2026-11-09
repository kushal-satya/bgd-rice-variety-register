"""P2A: split the bijoy-converted MoA cumulative hybrid list (2026 and 2018 editions) into entries;
extract (meeting, date) pairs. Writes 04_working/_P2A_moa_hybrid_entries_<ed>.csv"""
import re, csv, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
BN = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
DATE = re.compile(r"(\d{1,2})\s*[./]\s*(\d{1,2})\s*[./]\s*(\d{2,4})")
MTG = re.compile(r"(\d{2,3})\s*-?\s*(?:তম|তি|সভা)")
def iso(d, m, y):
    y = int(y); y = y + (1900 if y > 50 else 2000) if y < 100 else y
    return f"{y:04d}-{int(m):02d}-{int(d):02d}"
def parse(stem, pdf):
    lines = (ROOT / f"03_extracted/text/P2A/{stem}_unicode.txt").read_text(encoding="utf-8").splitlines()
    ents, cur, page, nxt = [], None, 0, 1
    for l in lines:
        m = re.match(r"=== page (\d+)", l)
        if m: page = int(m.group(1)); continue
        s = l.strip().translate(BN).rstrip(".")
        if s.isdigit() and nxt <= int(s) <= nxt + 2:
            n = int(s); cur = {"serial": n, "page": page, "lines": []}; ents.append(cur); nxt = n + 1; continue
        if cur is not None and l.strip():
            cur["lines"].append(l.strip())
    out = []
    for e in ents:
        txt = " | ".join(e["lines"])
        t = txt.translate(BN)
        dates = [iso(*d) for d in DATE.findall(t)]
        mt = [int(x) for x in MTG.findall(t) if 1 <= int(x) <= 120]
        pairs = list(zip(mt, dates)) if len(mt) == len(dates) else []
        # MoA list writes 'NN তম সভা-DATE' (early) or 'DATE, NNতম সভা' (later); zip on order works for both
        out.append({"source_file": pdf, "page": e["page"], "serial": e["serial"], "row_text": txt,
                    "name_guess": e["lines"][0] if e["lines"] else "", "meetings": ";".join(map(str, mt)),
                    "dates": ";".join(dates), "pairs": ";".join(f"{a}={b}" for a, b in pairs)})
    return out
if __name__ == "__main__":
    for stem, pdf in [("moa_hybrid_list_2026", "02_raw/moa/hybrid_rice_varieties_list_2026-02-05.pdf"),
                      ("moa_hybrid_list_2018", "02_raw/moa_wayback/hybrid_rice_list_2018-08-07.pdf")]:
        rows = parse(stem, pdf)
        with open(ROOT / f"04_working/_P2A_moa_hybrid_entries_{stem[-4:]}.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
        print(stem, len(rows), sum(1 for r in rows if r["pairs"]))
