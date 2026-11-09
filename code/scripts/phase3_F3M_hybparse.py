"""Parse hybrid-rice registration items out of NSB minutes text.
Items look like: '(ক) <company> এর <name> (<code>) হাইব্রিড জাতটি <regions> অঞ্চলে ... নিবন্ধন... (১ম ও ২য় বর্ষে ... এইচ-xxx ও এইচ-yyy)'.
Input: list of (page, text_line, latin_tokens). Output rows (dicts). Used by phase3_F3M_build.py; run directly to print.
Usage: python phase3_F3M_hybparse.py r5 <p_from> <p_to>   |   python phase3_F3M_hybparse.py ocr <stem> [p_from p_to]"""
import re, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
BN = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
ITEM = re.compile(r"^\s*(\(?[০-৯0-9]{1,2}\)|\([ক-হ]\)|[ক-হ]\))\s*")
LAT = re.compile(r"\(([^()]*[0-9][^()]*)\)|\b([A-Z][A-Za-z]*[ .-]?[A-Za-z]*[ .-]?\d+[A-Za-z0-9.-]*)")
REG = ["ঢাকা", "ময়মনসিংহ", "কুমিল্লা", "কুমিলস্না", "চট্টগ্রাম", "চট্রগ্রাম", "যশোর", "ষশোর", "রাজশাহী", "রংপুর",
       "বরিশাল", "খুলনা", "সিলেট", "দিনাজপুর", "বগুড়া", "ফরিদপুর", "কুষ্টিয়া"]
REG_EN = {"ঢাকা": "Dhaka", "ময়মনসিংহ": "Mymensingh", "কুমিল্লা": "Comilla", "কুমিলস্না": "Comilla", "চট্টগ্রাম": "Chattogram",
          "চট্রগ্রাম": "Chattogram", "যশোর": "Jessore", "ষশোর": "Jessore", "রাজশাহী": "Rajshahi", "রংপুর": "Rangpur",
          "বরিশাল": "Barisal", "খুলনা": "Khulna", "সিলেট": "Sylhet", "দিনাজপুর": "Dinajpur", "বগুড়া": "Bogura",
          "ফরিদপুর": "Faridpur", "কুষ্টিয়া": "Kushtia"}


def r5_lines(a, b):
    R = ROOT / "03_extracted/text/P2A"
    uni = (R / "nsb_058-075_unicode.txt").read_text(encoding="utf-8").splitlines()
    raw = (R / "nsb_058-075_raw.txt").read_text(encoding="utf-8", errors="replace").splitlines()
    page, out = 0, []
    for u, r in zip(uni, raw):
        m = re.match(r"=== page (\d+)", u)
        if m:
            page = int(m.group(1)); continue
        if a <= page <= b:
            out.append((page, u.strip(), [x[0] or x[1] for x in LAT.findall(r)]))
    return out


def ocr_lines(stem, a=1, b=999):
    t = (ROOT / "03_extracted/text/F3M" / f"{stem}.txt").read_text(encoding="utf-8").splitlines()
    page, out = 0, []
    for u in t:
        m = re.match(r"=== page (\d+)", u)
        if m:
            page = int(m.group(1)); continue
        if a <= page <= b:
            out.append((page, u.strip(), [x[0] or x[1] for x in LAT.findall(u)]))
    return out


def items(lines):
    cur = None
    for page, u, lat in lines:
        if ITEM.match(u) or re.match(r"^আলোচ্য|^সিদ্ধান্ত", u):
            if cur:
                yield cur
            cur = {"page": page, "text": u, "lat": list(lat)} if ITEM.match(u) else None
        elif cur is not None:
            cur["text"] += " " + u; cur["lat"] += lat
    if cur:
        yield cur


def parse(it):
    t = it["text"]
    if "হাইব্রিড" not in t or "জাত" not in t or not re.search(r"নিবন্ধ|ছাড়করণ|সুপারিশ", t):
        return None
    m = re.search(r"^\s*\S+\s+(.*?)\s+এর\s+(.*?)\s*(?:হাইব্রিড\s+)?(?:ধানের\s+)?জাতটি(?:কে)?\s+(.*)$", t)
    if not m:
        return None
    comp, name, rest = m.groups()
    reg_txt = rest.split("অঞ্চল")[0]
    regs = [REG_EN[r] for r in REG if r in reg_txt]
    regs = list(dict.fromkeys(regs))
    codes = re.findall(r"এইচ\s*-?\s*([০-৯0-9]{2,4})", rest)
    code_name = re.search(r"\(([^()]*)\)", name)
    return {"page": it["page"], "company": comp.strip(), "name_bn": name.strip(), "code_bn": code_name.group(1) if code_name else "",
            "regions": ", ".join(regs), "h_codes": "/".join("H-" + c.translate(BN) for c in codes),
            "retrial": "পুনঃ" in t or "পূনঃ" in t or "পুণঃ" in t, "latin": " ; ".join(dict.fromkeys(it["lat"])), "text": t}


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if sys.argv[1] == "r5":
        L = r5_lines(int(sys.argv[2]), int(sys.argv[3]))
    else:
        L = ocr_lines(sys.argv[2], *(int(x) for x in sys.argv[3:5]))
    for it in items(L):
        r = parse(it)
        if r:
            print(f"p{r['page']}\t{r['company']}\t{r['name_bn']}\t{r['regions']}\t{r['h_codes']}\t{'RT' if r['retrial'] else ''}\t{r['latin']}")
