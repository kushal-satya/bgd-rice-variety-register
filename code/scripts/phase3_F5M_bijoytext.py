"""F5M: font-aware text of the SutonnyMJ minutes bundle (NSB 58-75, 02_raw/sca/nsb_minutes_058-075.pdf).
SutonnyMJ spans -> bijoy2unicode after pre-fixes (reph moved before its consonant, PDF glyph quirks
Í->ত, ø->ল-ফলা, ÿ->ক্ষ); Latin-font spans (Times, Arial) are kept as typed (codes, names, IR lines).
Lines are rebuilt from span baselines; cells far apart on one baseline are joined with ' ¦ '.
Output: 03_extracted/text/F5M/nsb_minutes_058-075.txt with '=== page N' markers."""
import re, pathlib, fitz, unicodedata
from bijoy2unicode import converter
ROOT = pathlib.Path(__file__).resolve().parents[1]
C = converter.Unicode()
CONS = set("KLMNOPQRSTUVWXYZ_`abcdefghijklmnopqrstu")
PRE = set("w‡†ˆ‰")
HALF = set("¯š®˜™›ó")
POSTV = set("vxyz„…~¨ªÖ")


def move_reph(s):
    out = list(s)
    i = 0
    while i < len(out):
        if out[i] == "©":
            j = i - 1
            while j >= 0 and out[j] in POSTV:
                j -= 1
            if j >= 0 and (out[j] in CONS or (ord(out[j]) > 127 and out[j] not in PRE and out[j] not in POSTV)):
                j -= 1
                while j >= 0 and (out[j] in HALF or out[j] == "&"):
                    if out[j] == "&":
                        j -= 1
                    j -= 1
                while j >= 0 and out[j] in PRE:
                    j -= 1
                ins = j + 1
                del out[i]
                out[ins:ins] = ["i", "&"]
                i += 2
        i += 1
    return "".join(out)


def bconv(s):
    s = s.replace("Í", "Z").replace("ø", "­").replace("ÿ", "¶")
    s = move_reph(s)
    try:
        u = C.convertBijoyToUnicode(s + "  ").rstrip()
    except Exception:
        u = C.convertBijoyToUnicode(s.replace("&", "") + "  ").rstrip()
    u = u.replace("্‌", "্").replace("­", "")
    return unicodedata.normalize("NFC", u)


def page_lines(page):
    items = []
    for b in page.get_text("dict")["blocks"]:
        for ln in b.get("lines", []):
            spans = ln["spans"]
            if not spans:
                continue
            # merge consecutive spans of the same font class
            runs = []
            for sp in spans:
                cls = "B" if "Sutonny" in sp["font"] else "L"
                if runs and runs[-1][0] == cls and sp["bbox"][0] - runs[-1][2] < 6:
                    runs[-1][1] += sp["text"]; runs[-1][2] = sp["bbox"][2]
                else:
                    runs.append([cls, sp["text"], sp["bbox"][2], sp["bbox"][0]])
            txt = ""
            rawt = "".join(sp["text"] for sp in spans)
            for cls, t, x1, x0 in runs:
                if cls == "B":
                    lead = " " if t[:1] == " " else ""
                    tail = " " if t[-1:] == " " else ""
                    t = lead + bconv(t.strip()) + tail
                txt += t
            y = round((ln["bbox"][1] + ln["bbox"][3]) / 2, 1)
            items.append((y, ln["bbox"][0], ln["bbox"][2], txt, rawt))
    items.sort()
    rows = []
    for y, x0, x1, t, rt in items:
        if rows and abs(rows[-1][0] - y) <= 3.0:
            rows[-1][1].append((x0, x1, t, rt))
        else:
            rows.append([y, [(x0, x1, t, rt)]])
    lines, raws = [], []
    prev_y = None
    for y, cells in rows:
        if prev_y is not None and y - prev_y > 24:
            lines.append(""); raws.append("")          # paragraph / table-row gap
        prev_y = y
        cells.sort()
        s, r, last = "", "", None
        for x0, x1, t, rt in cells:
            if last is not None:
                sep = " ¦ " if x0 - last > 18 else " "
                s += sep; r += sep
            s += t.strip(); r += rt.strip()
            last = x1
        lines.append(re.sub(r"[ 	]+", " ", s).strip()); raws.append(re.sub(r"[ 	]+", " ", r).strip())
    return lines, raws


if __name__ == "__main__":
    pdf = ROOT / "02_raw/sca/nsb_minutes_058-075.pdf"
    d = fitz.open(pdf)
    out = ROOT / "03_extracted/text/F5M"; out.mkdir(parents=True, exist_ok=True)
    buf, rbuf = [], []
    for i, pg in enumerate(d):
        buf.append(f"=== page {i+1}"); rbuf.append(f"=== page {i+1}")
        a, b = page_lines(pg)
        buf.extend(a); rbuf.extend(b)
    (out / "nsb_minutes_058-075.txt").write_text("\n".join(buf) + "\n", encoding="utf-8")
    # same line structure, original SutonnyMJ-encoded text layer = the 'raw' text of this file
    (out / "nsb_minutes_058-075.raw.txt").write_text("\n".join(rbuf) + "\n", encoding="utf-8")
    print("pages", d.page_count)
