"""F5M: rule-based extraction of structured attributes from the verbatim Bangla/English text of one NSB decision.
Every value is returned with the verbatim sentence(s) it came from; values are candidates that the builder
merges with the hand-read table 04_working/_F5M_manual_fields.tsv (manual entries win)."""
import re

BN2 = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
D = r"[০-৯0-9]"
NUM = rf"{D}+(?:\s?[.,]\s?{D}+)?"


def lat(s):
    return (s or "").translate(BN2)


def num(s):
    s = lat(s).replace(" ", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def fmt(x):
    return ("%g" % x) if x is not None else ""


def sentences(t):
    t = re.sub(r"\s+", " ", t)
    parts = re.split(r"(?<=[।])\s*|\s\|\s(?=\S)|(?<=\S)\|\s", t)
    return [p.strip() for p in parts if p and len(p.strip()) > 2]


def grab(sents, rx):
    r = re.compile(rx, re.I)
    return [s for s in sents if r.search(s)]


COUNTRIES = [("ভারত", "India"), ("ইন্ডিয়া", "India"), ("চীন", "China"), ("চায়না", "China"), ("ফিলিপাইন", "Philippines"),
             ("ভিয়েতনাম", "Vietnam"), ("পাকিস্তান", "Pakistan"), ("ইরান", "Iran"), ("থাইল্যান্ড", "Thailand"),
             ("ইন্দোনেশিয়া", "Indonesia"), ("যুক্তরাষ্ট্র", "USA"), ("আমেরিকা", "USA"), ("কোরিয়া", "Korea"), ("জাপান", "Japan"),
             ("শ্রীলংকা", "Sri Lanka"), ("নেপাল", "Nepal"), ("মিয়ানমার", "Myanmar"), ("বাংলাদেশ", "Bangladesh"),
             ("India", "India"), ("China", "China"), ("Philippines", "Philippines")]

CG = (r"ইরি\b|ইরি[-–, ]|ইরির|ইরি'|IRRI|আন্তর্জাতিক\s*ধান\s*গবেষণা|আর্ন্তজাতিক\s*ধান|International\s+Rice|\bIR\s?-?\d{2,}|"
      r"\b[1lI]R\s?-?\d{4,}|IRBB|IRGC|NERICA|নেরিকা|AfricaRice|WARDA|CIMMYT|সিমিট|PSB\s?Rc|PSBRC|NSIC|HHZ|Huang-?Hua-?Zhan|"
      r"Green\s*Super\s*Rice|GSR|CGIAR|HarvestPlus|হারভেস্ট\s*প্লাস|হারভেস্টপ্লাস|IR\d{2}[A-Z]")

TRAIT_FIELDS = [
    ("special_traits_official", r"বিশেষ\s*বৈশিষ্ট্য|বিশেষ\s*গুণ|প্রধান\s*বৈশিষ্ট্য|বিশেষত্ব|বৈশিষ্ট্য\s*হলো|বৈশিষ্ট্য\s*হচ্ছে"),
    ("identifying_traits_official", r"সনাক্তকারী|শনাক্তকারী|সনাক্তকরণ|শনাক্তকরণ|চেনার\s*উপায়|identif"),
    ("stress_tolerance", r"সহনশীল|সহিষ্ণু|সহিষ্ণুতা|প্রতিরোধী|প্রতিরোধ\s*ক্ষমতা|প্রতিরোধক্ষমতা|tolerant|resistant|লবণাক্ত|লবনাক্ত|"
                         r"জলমগ্ন|খরা|ঠান্ডা|শীত|ব্লাস্ট|পাতা\s*পোড়া|পাতাপোড়া|টুংরো|বাদামী\s*গাছ\s*ফড়িং|রোগ\s*বালাই|রোগবালাই|পোকা"),
    ("tc_recommendation_text", r"কারিগরি\s*কমিটি|কারিগরী\s*কমিটি|Technical\s*Committee|মাঠ\s*মূল্যায়ন\s*দল"),
    ("decision_conditions", r"শর্ত|শতর্|সাময়িক|সাময়িক|বছর\s*মেয়াদ|বছর\s*মেয়াদ|মেয়াদে|মেয়াদে|প্যাকেট|লেবেল|"
                            r"আমদানি\S*\s*(?:করা|যাবে)|আমদানী\S*\s*(?:করা|যাবে)|পর্যন্ত\s*আমদানি"),
    ("cgiar_mentions", CG),
]


def extract(text):
    s = sentences(text)
    out = {}

    def put(k, v, src):
        if v not in (None, "", []):
            out[k] = (v, " ‖ ".join(dict.fromkeys(src)))

    # yield (t/ha): prefer 'গড় ফলন'
    vals = []
    for x in grab(s, r"ফলন|yield"):
        for m in re.finditer(rf"({NUM})(?:\s*(?:-|–|থেকে|হতে)\s*({NUM}))?\s*(?:মে\.?\s*টন|মেট্রিক\s*টন|টন|t/ha)", x):
            a, b = num(m.group(1)), num(m.group(2)) if m.group(2) else None
            if a is not None and 0.5 <= a <= 20:
                pre = x[:m.start()]
                kind = "avg" if re.search(r"গড়|গড়", pre[-60:]) else ("max" if re.search(r"সর্বোচ্চ|সবোর্চ্চ", pre[-60:]) else "")
                vals.append((kind, a, b, x))
    if vals:
        best = [v for v in vals if v[0] == "avg"] or vals
        k, a, b, x = best[0]
        put("yield_t_ha", fmt(a) + ("-" + fmt(b) if b else ""), [x])
        put("yield_statements", " ‖ ".join(dict.fromkeys(v[3] for v in vals)), [v[3] for v in vals])
    # yield advantage %
    adv = []
    for x in s:
        for m in re.finditer(rf"({NUM})\s*(?:%|শতাংশ|ভাগ|percent)\s*(?:এর\s*)?(?:বেশি|বেশী|অধিক|more|higher)", x):
            adv.append((num(m.group(1)), x))
        for m in re.finditer(rf"শতকরা\s*({NUM})\s*ভাগ\s*(?:বেশি|বেশী|অধিক)", x):
            adv.append((num(m.group(1)), x))
    if adv:
        put("yield_advantage_pct", "; ".join(dict.fromkeys(fmt(a) for a, x in adv if a is not None)), [x for a, x in adv])
    # duration
    du = []
    for x in grab(s, r"জীবনকাল|জীবন\s*কাল"):
        for m in re.finditer(rf"(?:জীবনকাল|জীবন\s*কাল)[^।]{{0,40}}?({NUM})(?:\s*(?:-|–|থেকে)\s*({NUM}))?\s*দিন", x):
            a, b = num(m.group(1)), num(m.group(2)) if m.group(2) else None
            if a and 60 <= a <= 220:
                du.append((a, b, x))
    if du:
        a, b, x = du[0]
        put("duration_days", fmt(a) + ("-" + fmt(b) if b else ""), [x])
        put("duration_statements", " ‖ ".join(dict.fromkeys(v[2] for v in du)), [v[2] for v in du])
    # 1000-grain weight
    for x in grab(s, r"১০০০|1000|হাজার"):
        m = re.search(rf"(?:১০০০|1000|হাজার)\s*টি?[^।]{{0,40}}?ওজন[^।]{{0,25}}?({NUM})\s*(?:গ্রাম|গ্রা|g)", x)
        if m:
            put("grain_wt_1000_g", fmt(num(m.group(1))), [x]); break
    # amylose / protein / zinc / iron / LB
    for key, rx, unit in [("amylose_pct", r"অ্যামাইলোজ|এমাইলোজ|এ্যামাইলোজ|অ্যামাইলেজ|এমাইলেজ|amylose", r"%|শতাংশ|ভাগ"),
                          ("protein_pct", r"প্রোটিন|প্রেটিন|আমিষ|protein", r"%|শতাংশ|ভাগ"),
                          ("zinc_mg_kg", r"জিংক|জিঙ্ক|দস্তা|zinc|Zn", r"মি[.:]?\s*গ্রা|মিগ্রা|পিপিএম|ppm|mg|মিলিগ্রাম"),
                          ("iron_mg_kg", r"লৌহ|আয়রন|আয়রন|iron|Fe\b", r"মি[.:]?\s*গ্রা|মিগ্রা|পিপিএম|ppm|mg|মিলিগ্রাম")]:
        for x in grab(s, rx):
            m = re.search(rf"(?:{rx})[^।]{{0,45}}?({NUM})(?:\s*(?:-|–)\s*({NUM}))?\s*(?:{unit})", x, re.I)
            if m:
                a, b = num(m.group(1)), num(m.group(2)) if m.group(2) else None
                put(key, fmt(a) + ("-" + fmt(b) if b else ""), [x]); break
    for x in grab(s, r"দৈর্ঘ্য.{0,10}প্রস্থ|L\s*/\s*B|LB\s*ratio"):
        m = re.search(rf"(?:অনুপাত|ratio|L\s*/\s*B)[^।]{{0,20}}?({NUM})", x, re.I)
        if m:
            put("lb_ratio", fmt(num(m.group(1))), [x]); break
    # grain / rice type
    gt = grab(s, r"চাল\s*(?:সরু|চিকন|মোটা|মাঝারি|লম্বা|খাটো|মাঝারী|লম্বাটে|সাদা)|দানা\s*(?:সরু|চিকন|মোটা|মাঝারি|লম্বা)|সুগন্ধ|aromatic|slender|bold")
    if gt:
        put("grain_quality_statements", " ‖ ".join(gt), gt)
        m = re.search(r"চাল\s*((?:মাঝারি|মাঝারী|লম্বা|খাটো|সরু|চিকন|মোটা|লম্বাটে|ও|এবং|,|\s)+)", " ".join(gt))
        if m and m.group(1).strip(" ,ওএবং"):
            put("grain_type", m.group(1).strip(" ,ওএবং"), gt[:1])
    # check variety
    ck = []
    for x in grab(s, r"চেক\s*জাত|চেকজাত|চেক\s*ভ্যারাইটি|check"):
        for m in re.finditer(r"(?:চেক\s*জাত\S*|চেকজাত\S*|check\s*variet\S*)\s*(?:হিসেবে\s*|হিসাবে\s*)?(?:ব্যবহৃত\s*)?"
                             r"([^\s,।|]+(?:[\s-]*(?:ধান|dhan|হাইব্রিড|hybrid)?[\s-]*[০-৯0-9]+)?(?:\s*\([^)]{0,25}\))?)", x, re.I):
            v = m.group(1).strip()
            if len(v) > 1 and not re.match(r"^(এর|থেকে|হতে|এবং|ও|হিসেবে|হিসাবে|অপেক্ষা|তুলনায়|তুলনায়|সমূহ|গুলো|গুলির|ব্যবহার|[০-৯0-9%])", v):
                ck.append((v, x))
    if ck:
        put("check_variety", "; ".join(dict.fromkeys(v for v, x in ck)), [x for v, x in ck])
    # origin
    org = grab(s, r"উৎস|উৎপত্তি|আমদানি|আমদানী|সংগ্রহ|সংগৃহী|প্রাপ্ত|origin|imported|introduc")
    if org:
        cs = []
        for x in org:
            for bn, en in COUNTRIES:
                if bn in x and en not in cs:
                    cs.append(en)
        put("origin_statements", " ‖ ".join(org), org)
        if cs:
            put("origin_country", "; ".join(cs), org)
    ped = grab(s, r"সংকরায়|সংক্রায়|সংকরায়|সংকরণ|ক্রস|cross|Pedigree|বংশানুক্রম|ব্যাকক্রস|Backcross|পশ্চাৎ\s*সংকর|মিউট্যান্ট|mutant|"
                  r"রশ্মি|গামা|মিউটেশন|বিশুদ্ধ\s*কৌলিক\s*সারি|Pure.?line|সোমা\s*ক্লোনাল|somaclonal|মার্কার|Marker|মাতৃ|পিতৃ|প্যারেন্ট|"
                  r"কৌলিসম্পদ|জার্মপ্লাজম|জামর্প্লাজম|অ্যান্থার|anther|ট্রান্সজেনিক|জিন\s*সংযোজন")
    if ped:
        put("pedigree_statements", " ‖ ".join(ped), ped)
    hp = grab(s, r"A\s*-?\s*line|B\s*-?\s*line|R\s*-?\s*line|সিএমএস|CMS|রেস্টোরার|restorer|maintainer|মেইনটেইনার|প্যারেন্ট\s*লাইন|"
                 r"parent\s*line|মাতৃ\s*সারি|পিতৃ\s*সারি|মাতৃ\s*লাইন|পিতৃ\s*লাইন|\b\d{2,5}A\b|IR\s?58025")
    if hp:
        put("hybrid_parent_statements", " ‖ ".join(hp), hp)
    dus = grab(s, r"ডিইউএস|ডি\s*ইউ\s*এস|\bDUS\b|স্বাতন্ত্র্য|বৈশিষ্ট্যে\s*ভিন্নতা|বৈশিষ্ট্যে\s*পার্থক্য|বৈশিষ্ট্যে\s*ভিন্ন")
    if dus:
        put("dus_statements", " ‖ ".join(dus), dus)
        for x in dus:
            m = re.search(rf"({NUM})\s*(?:\(\S+\)\s*)?টি\s*(?:গুরুত্বপূর্ণ\s*|অত্যাবশ্যকীয়\s*|সুস্পষ্ট\s*)?বৈশিষ্ট্যে", x)
            if m:
                put("dus_distinct_traits_n", fmt(num(m.group(1))), [x]); break
        for x in dus:
            m = re.search(r"(?:চেক\s*জাত\S*|চেকজাত\S*)\s*([^\s,।|]+(?:[\s-]*(?:ধান|dhan)?[\s-]*[০-৯0-9]+)?)\s*(?:থেকে|হতে|এর\s*তুলনায়|অপেক্ষা)[^।]{0,30}বৈশিষ্ট্য", x)
            if m:
                put("dus_check_variety", m.group(1), [x]); break
    vcu = grab(s, r"ভিসিইউ|VCU|মাঠ\s*মূল্যায়|অন-?\s*স্টেশন|অনস্টেশন|অন\s*-?\s*ফার্ম|অনফার্ম|on-?station|on-?farm|টি\s*স্থানে|টি\s*অঞ্চলে|টি\s*অঞ্চলের|ট্রায়াল|ট্রায়াল")
    if vcu:
        put("vcu_statements", " ‖ ".join(vcu), vcu)
        hit = False
        for x in vcu:
            m = re.search(rf"({NUM})\s*(?:\(\S+\)\s*)?টি\s*অঞ্চলের\s*({NUM})\s*(?:\(\S+\)\s*)?টি\s*(?:স্থানে|স্থান|লোকেশন)", x)
            if m:
                put("vcu_regions_n", fmt(num(m.group(1))), [x]); put("vcu_sites_n", fmt(num(m.group(2))), [x]); hit = True; break
        if not hit:
            for x in vcu:
                m = re.search(rf"({NUM})\s*(?:\(\S+\)\s*)?টি\s*(?:স্থানে|লোকেশনে)", x)
                if m:
                    put("vcu_sites_n", fmt(num(m.group(1))), [x]); break
        tt = []
        j = " ".join(vcu)
        if re.search(r"অন-?\s*স্টেশন|অনস্টেশন|on-?station", j, re.I):
            tt.append("on-station")
        if re.search(r"অন\s*-?\s*ফার্ম|অনফার্ম|on-?farm|কৃষকের\s*মাঠ", j, re.I):
            tt.append("on-farm")
        if tt:
            put("vcu_trial_type", "; ".join(tt), vcu)
    for k, rx in TRAIT_FIELDS:
        g = grab(s, rx)
        if g:
            put(k, " ‖ ".join(g), g)
    return out
