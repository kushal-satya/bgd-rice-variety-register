"""F3H: match variety names printed in other hybrid sources to the MoA 2026 keys.

Signals, strongest first: (1) a manual override in 04_working/_F3H_other_match.csv (source, row_id -> key);
(2) identical normalised full name; (3) identical normalised Latin code; (4) identical normalised name component
(main name or bracketed trade name). Ambiguous or missing matches are returned as None, never guessed.
"""
import csv, re, pathlib, collections

ROOT = pathlib.Path(__file__).resolve().parents[1]
W = ROOT / "04_working"
BN = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
VAR = [("ী", "ি"), ("ূ", "ু"), ("ৃ", "ৃ"), ("য়", "য়"), ("ড়", "ড়"), ("ঈ", "ই"), ("ঊ", "উ"),
       ("চট্রগ্রাম", "চট্টগ্রাম"), ("ব্রাক", "ব্র্যাক"), ("উইনল", "উইনঅল"), ("উইনাল", "উইনঅল"), ("উইন অল", "উইনঅল"),
       ("উইনঅ্ল", "উইনঅল"), ("এ সি আই", "এসিআই"), ("হাইব্রিড", "হাইব্রিড"), ("হাইবিড", "হাইব্রিড"), ("সাইন্স", "সায়েন্স"),
       ("পেট্টোকেম", "পেট্রোকেম"), ("সিনজেন্টা", "সিনজেনটা"), ("ইস্পাহানি", "ইস্পাহানী"), ("সুবর্ণা", "সুবর্ণ"),
       ("লালতীর", "লাল তীর"), ("হীরা", "হিরা"), ("Heera", "Hira")]


def norm(s):
    s = (s or "").translate(BN)
    for a, b in VAR:
        s = s.replace(a, b)
    s = re.sub(r"[\s\-–(),.;:’'“”\"/|®]+", "", s)
    return s.upper()


def latin_codes(s):
    return [norm(m.group(0)) for m in re.finditer(r"[A-Za-z][A-Za-z0-9 .\-]*\d[A-Za-z0-9]*", s or "")]


def components(s):
    return [norm(x) for x in re.split(r"[()]", s or "") if norm(x)]


class Matcher:
    def __init__(self, recs):
        self.full = collections.defaultdict(set)
        self.code = collections.defaultdict(set)
        self.comp = collections.defaultdict(set)
        for r in recs:
            k = r["key"]
            self.full[norm(r["name"])].add(k)
            for c in latin_codes(r["name"]) + ([norm(x) for x in r["code"].split(";")] if r.get("code") else []):
                if len(c) >= 3 and not c.isdigit():
                    self.code[c].add(k)
            for c in components(r["name"]):
                if len(c) >= 3:
                    self.comp[c].add(k)
        self.manual = {}
        p = W / "_F3H_other_match.csv"
        if p.exists():
            for r in csv.DictReader(open(p, encoding="utf-8")):
                self.manual[(r["source_id"], r["row_id"])] = (r["key"], r["notes"])

    def match(self, sid, row_id, name, extra_codes=()):
        if (sid, row_id) in self.manual:
            k, n = self.manual[(sid, row_id)]
            return (k or None), "manual: " + n
        n = norm(name)
        if len(self.full.get(n, ())) == 1:
            return next(iter(self.full[n])), "full name"
        cands = collections.Counter()
        for c in list(latin_codes(name)) + [norm(x) for x in extra_codes if x]:
            for k in self.code.get(c, ()):
                cands[k] += 1
        if len(cands) == 1:
            return next(iter(cands)), "Latin code"
        cc = set()
        for c in components(name):
            cc |= self.comp.get(c, set())
        if len(cc) == 1:
            return next(iter(cc)), "name component"
        return None, f"no unique match (code candidates {sorted(cands)}; component candidates {sorted(cc)})"
