"""P2B: parse BRRI Adhunik Dhaner Chash 2025 Table 1 (PDF pp.9-12 = printed pp.7-10).
Rows come from the horizontal rule rects; columns from the vertical rule rects that cross each row
(page 12 has a different column grid for the hybrid block). SutonnyMJ words are converted with
bijoy2unicode; Times New Roman words are kept as is. Code-like Bangla strings (আইআর৫৩২-১-১৭৬) are
transliterated to Latin by an explicit token table (TOK); anything left in Bangla is flagged.
Output: 03_extracted/tables/adc2025_table1.csv"""
import pdfplumber, csv, pathlib, re, sys, unicodedata
from bijoy2unicode import converter
ROOT = pathlib.Path(__file__).resolve().parents[1]
PDF = ROOT / "02_raw/brri/brri_adhunik_dhaner_chash_2025_adc2025.pdf"
C = converter.Unicode()
COLS = ["variety", "station_no", "breeding_line", "parentage", "year"]
BN = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")

# longest first; Bangla spelling of Latin codes -> Latin
TOK = [("ব্রি হাইব্রিড ধান", "BRRI hybrid dhan"), ("ব্রি ধান", "BRRI dhan"), ("আইআরআরআই", "IRRI"),
       ("বিআরআরআই", "BRRI"), ("বিআরআর", "BRR"), ("আইআরবিবি", "IRBB"), ("এনএসআইসি আরসি", "NSIC Rc"),
       ("পিএসবিআরসি", "PSBRc"), ("বিআরএইচ", "BRH"), ("বিআরসি", "BRC"), ("এইচআরবি", "HRB"),
       ("আইআর", "IR"), ("আইইটি", "IET"), ("বিআর", "BR"), ("এইচআর", "HR"), ("এইচ আর", "HR"), ("এআরসি", "ARC"),
       ("সিআর", "CR"), ("টিকেএম", "TKM"), ("টিসিসিপি", "TCCP"), ("এসএটিবি", "SATB"), ("সিপি-এসএলও", "CP-SLO"),
       ("সিগাডিস", "Sigadis"), ("কেএন", "KN"), ("বিজি", "BG"), ("ডিএ", "DA"), ("পিআই", "PI"), ("ওএম", "OM"),
       ("এফএল", "FL"), ("এসসি", "SC"), ("এসি", "AC"), ("বিসি", "BC"), ("পিএল", "PL"), ("আরএএন", "RAN"),
       ("আরডবিস্নউবিসি", "RWBC"), ("বিডাবিস্নউ", "BW"), ("এমআর", "MR"), ("টিআর", "TR"), ("বায়ো", "Bio"),
       ("বিই", "BE"), ("এসএফ", "SF"), ("আরএস", "RS"), ("এইচ", "H"),
       # landrace / variety names and words that occur in the parentage column
       ("লতিশাইল", "Latisail"), ("বাদশাহভোগ", "Badshabhog"), ("জেরাক", "Zerak"), ("পেলিটা", "Pelita"),
       ("নাইজারশাইল", "Nizersail"), ("পাজাম", "Pajam"), ("পূবার্চী", "Purbachi"), ("খাসকানি", "Khaskani"),
       ("বাসমতি", "Basmati"), ("স্বণর্লতা", "Swarnalata"), ("রনজিত স্বণার্", "Ranjit Swarna"), ("স্বণার্", "Swarna"),
       ("জিরাকাটারি", "Jirakatari"), ("আমল", "Amol"), ("নেরিকা", "NERICA"), ("নিয়ামত", "Niamat"),
       ("তিলোক-কাচারি", "Tilok-kachari"), ("বারিশাইল", "Barisail"), ("লতাবালাম", "Latabalam"),
       ("চাইনিজ ইনব্রেড", "Chinese inbred"), ("ধান/গম", "rice/wheat"),
       ("সোমাক্লোনাল লাইন অব", "somaclonal line of"), ("বিশুদ্ধ সারি বাছাইকরণ প্রক্রিয়া", "pure line selection"),
       ("বিশুদ্ধ সারি বাছাইকরণ", "pure line selection"), ("-এর বিশুদ্ধ সারি", " pure line"),
       ("-থেকে নিবার্চন", " selection"), (" এবং ", " and "), (" ধান", " rice"), ("নিল", "NIL")]
NFC = lambda x: unicodedata.normalize("NFC", x)
TOK = sorted(((NFC(a), b) for a, b in TOK), key=lambda ab: len(ab[0]), reverse=True)
SYL = {"বি": "B", "আর": "R", "এ": "A", "জে": "J", "পি": "P", "ডি": "D", "সি": "C", "ই": "E",
       "এস": "S", "এন": "N", "এম": "M", "টি": "T", "জি": "G", "কে": "K", "ও": "O"}
SYLRE = re.compile("(?:" + "|".join(sorted(map(re.escape, SYL), key=len, reverse=True)) + ")+")


def translit(s):
    t = NFC(s)
    for a, b in TOK:
        t = t.replace(a, b)
    t = t.translate(BN)

    def rep(m):
        a, b = m.start(), m.end()
        left = t[a - 1] if a > 0 else " "
        right = t[b] if b < len(t) else " "
        if re.match(r"[0-9A-Za-z\-*/(]", left) or re.match(r"[0-9A-Za-z\-*)]", right):
            out, x = "", m.group(0)
            while x:
                for k in sorted(SYL, key=len, reverse=True):
                    if x.startswith(k):
                        out += SYL[k]; x = x[len(k):]; break
            return out
        return m.group(0)
    t = SYLRE.sub(rep, t)
    t = re.sub(r"\s+", " ", t).strip()
    return t, bool(re.search(r"[ঀ-৿]", t))


def lines(words):
    """cluster words into visual lines (tolerance 4 pt), left to right"""
    ws = sorted(words, key=lambda w: w["top"])
    L = []
    for w in ws:
        if L and abs(w["top"] - L[-1][0]["top"]) < 4:
            L[-1].append(w)
        else:
            L.append([w])
    return [sorted(l, key=lambda w: w["x0"]) for l in L]


def conv(words):
    out = []
    for l in lines(words):
        for w in l:
            t = w["text"]
            if "Sutonny" in w["fontname"]:
                t = C.convertBijoyToUnicode(t + "  ").strip()
            out.append(t)
    s = " ".join(out)
    s = re.sub(r"(\S)- (\S)", r"\1-\2", s)  # rejoin hyphen line breaks inside codes
    return s


def raw(words):
    return " ".join(w["text"] for l in lines(words) for w in l)


def merge(xs, tol):
    o = []
    for x in sorted(xs):
        if not o or x - o[-1] > tol:
            o.append(x)
    return o


def parse_page(p, pn):
    hr = [r for r in p.rects if r["height"] < 1.5 and r["width"] > 20]
    vr = [r for r in p.rects if r["width"] < 1.5 and r["height"] > 3]
    H = merge([r["top"] for r in hr], 2)
    words = p.extract_words(extra_attrs=["fontname"])
    rows = []
    for a, b in zip(H, H[1:]):
        mid = (a + b) / 2
        V = merge([r["x0"] for r in vr if r["top"] - 1 <= mid <= r["bottom"] + 1], 3)
        band = [w for w in words if a - 1 < (w["top"] + w["bottom"]) / 2 < b + 1]
        if not band or len(V) != 6:
            continue
        cells = {}
        for k, (x0, x1) in enumerate(zip(V, V[1:])):
            cw = [w for w in band if x0 - 2 <= (w["x0"] + w["x1"]) / 2 < x1]
            cells[COLS[k]] = (raw(cw), conv(cw))
        rows.append((pn + 1, a, cells))
    return rows


def main():
    pdf = pdfplumber.open(PDF)
    out = []
    block = "inbred"
    for pn in range(8, 12):
        for page, top, c in parse_page(pdf.pages[pn], pn):
            v_bn = c["variety"][1]
            if "হাইব্রিড" in v_bn + c["breeding_line"][1] + c["parentage"][1] and not c["year"][1]:
                block = "hybrid"; continue
            if not re.search(r"[০-৯]", c["year"][1]) or "অবমুক্তির" in c["year"][1]:
                continue
            m = re.match(r"^(.*?)\s*\((.+)\)\s*$", v_bn)
            name_bn, pop_bn = (m.group(1), m.group(2)) if m else (v_bn, "")
            name_bn = re.sub(r"ধান\s+([০-৯])", r"ধান\1", name_bn)
            name_en, _ = translit(name_bn)
            name_en = re.sub(r"dhan\s+", "dhan", name_en)
            bl_clean, bl_flag = translit(c["breeding_line"][1])
            pa_clean, pa_flag = translit(c["parentage"][1])
            st_clean, _ = translit(c["station_no"][1])
            if name_en.startswith("BRRI hybrid"):
                block = "hybrid"
            out.append({"block": block, "variety_bn": name_bn, "variety_en": name_en,
                        "popular_name_bn": pop_bn, "station_no_raw": c["station_no"][1], "station_no": st_clean,
                        "breeding_line_raw": c["breeding_line"][1], "breeding_line_clean": bl_clean,
                        "parentage_raw": c["parentage"][1], "parentage_clean": pa_clean,
                        "release_year": c["year"][1].translate(BN).strip(),
                        "residual_bangla_flag": "Y" if (bl_flag or pa_flag) else "",
                        "bijoy_ascii_row": " | ".join(c[k][0] for k in COLS),
                        "pdf_page": page, "printed_page": page - 2, "row_top_pt": round(top, 1)})
    f = ROOT / "03_extracted/tables/adc2025_table1.csv"
    with open(f, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader(); w.writerows(out)
    print(len(out), "rows;", sum(r["block"] == "inbred" for r in out), "inbred", file=sys.stderr)


if __name__ == "__main__":
    main()
