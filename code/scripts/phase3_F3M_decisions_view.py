"""Print, for an OCR'd NSB minutes dump, the opening lines and every agenda item that mentions rice
(ধান/হাইব্রিড/rice), showing only its heading and its decision (সিদ্ধান্ত) block. Reading aid for F3M.
Usage: python phase3_F3M_decisions_view.py <stem> [full]"""
import re, sys, pathlib
sys.stdout.reconfigure(encoding="utf-8")
ROOT = pathlib.Path(__file__).resolve().parents[1]
stem = sys.argv[1]; full = len(sys.argv) > 2
L = (ROOT / "03_extracted/text/F3M" / f"{stem}.txt").read_text(encoding="utf-8").splitlines()
page = 0; rows = []
for u in L:
    m = re.match(r"=== page (\d+)", u)
    if m:
        page = int(m.group(1)); continue
    if u.strip():
        rows.append((page, u.rstrip()))
# opening: lines containing a date or 'সভা' in the first 25 lines
for p, u in rows[:25]:
    if re.search(r"তারিখ|সভা|সময়|স্থান|[০-৯]{1,2}[/.-][০-৯]{1,2}[/.-]", u):
        print(f"OPEN p{p}| {u[:200]}")
AG = re.compile(r"^\W{0,3}আলোচ্য\s*সূ?ু?চ[ীি]|^\W{0,3}আলোচ্যসূচী|^\W{0,3}আলোচ্যসুচী|^\W{0,3}আলোচ্য বিষয়")
blocks, cur = [], None
for p, u in rows:
    if AG.match(u):
        if cur: blocks.append(cur)
        cur = [(p, u)]
    elif cur is not None:
        cur.append((p, u))
if cur: blocks.append(cur)
for b in blocks:
    txt = " ".join(u for _, u in b)
    if not re.search(r"ধান|হাইব্রিড|হাইবি|rice|Rice|ব্রি|বিনা", txt):
        print(f"--- p{b[0][0]} [non-rice] {b[0][1][:120]}"); continue
    print(f"=== p{b[0][0]} {b[0][1][:220]}")
    on = full
    for p, u in b[1:]:
        if re.search(r"সমাপ্ত ঘোষণা", u):
            print(f"  p{p}| {u[:230]}"); break
        if re.match(r"^\W{0,3}সিদ্ধান্ত", u): on = True
        if on: print(f"  p{p}| {u[:230]}")
