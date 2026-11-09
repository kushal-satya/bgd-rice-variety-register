"""Feature tags derived from the varietal trait text (official lists, NSB minutes, institute records, SPIA flags, TRIVSA codes).

Rules are deliberately strict: a stress tag needs a tolerance word next to the stress term, a resistance tag needs a
resistance word, a clause with a negation (নয়, নহে, not, non-, susceptible) never produces a tag, 'অলবণাক্ত'/'non-saline' is
not salinity, waterlogging is not submergence, 'medium slender' is not fine grain, 'short duration' is dropped when the
stated duration exceeds 145 (boro) / 120 (aman) / 110 (aus) days, and a zinc tag needs official text, a stated zinc content
of at least 19 mg/kg, or the HarvestPlus flag, SPIA flags count only when '=Y', TRIVSA screening codes only when T (tolerant) or R/HR (resistant).
feature_evidence names the column(s) whose text matched, so every tag can be traced to its source text.

Version 1.2 (REV2, 2026-11-10; review A1-01 to A1-04):
* 'অলবনাক্ত' (dental-na spelling) and 'অ-লবনাক্ত' are non-saline too.
* A stress tag (salt, submergence, drought) never rests on a SPIA Table 27 flag alone: when the flag is the only evidence the
  tag is not given and feature_evidence records '<tag>: SPIA only (cgiar_spia_flags), not tagged'.
* A variety that official text places on non-saline tidal land is tagged salt tolerant only if some text states salinity
  tolerance itself (লবণাক্ততা সহনশীল/সহিষ্ণু, 'salinity/salt tolerant', a dS/m threshold); a statement that it suits a saline
  area is then treated as a conflict between sources and recorded in feature_evidence, not tagged (BRRI dhan106).
* TRIVSA screening codes count only when T (tolerant) or R/HR (resistant); MR does not.
* A resistance qualified as moderate or partial (মাঝারীভাবে, আংশিক, কিছুটা, 'moderately', 'partially', 'somewhat') gives no tag.
* A resistance tag is suppressed when any text for the variety says it is susceptible to the same disease
  ('susceptible to (leaf/neck) blast', 'ব্লাস্ট ... সংবেদনশীল'); feature_evidence then records '<tag>: not tagged, source text
  says susceptible (<columns>)'."""
import re
import pandas as pd

FREE_TEXT = ["special_traits_official", "identifying_traits_official", "stress_tolerance", "quality_traits", "key_traits",
             "ecosystem", "recommended_region"]   # product_profile describes a market segment's targets, not the variety
NEAR = r"[^।|;.]{0,40}"
TOL_BN = r"(সহিষ্ণু|সহনশীল|সহ্য|উপযোগী|প্রতিরোধ)"
TOL_EN = r"(toleran|resist|suited|suitable|prone area|adapted)"

RULES = [  # (tag, free-text pattern, SPIA flag, TRIVSA pattern)
    ("salt tolerant", rf"(লবণ|লবন){NEAR}{TOL_BN}|{TOL_BN}{NEAR}(লবণ|লবন)|(salt|salin|saline){NEAR}{TOL_EN}|{TOL_EN}{NEAR}(salt|salin)",
     "saline_tolerance=Y", r"Salt injury resistance:\s*(T|R)\b"),
    ("submergence tolerant", rf"(জলমগ্ন|আকস্মিক বন্যা){NEAR}{TOL_BN}|{TOL_BN}{NEAR}জলমগ্ন|(submergence|flash.?flood){NEAR}{TOL_EN}|{TOL_EN}{NEAR}submergence|\bSub1\b",
     "sub1=Y", r"Submergence[^:]*:\s*(T|R)\b"),
    ("drought tolerant", rf"খরা{NEAR}{TOL_BN}|{TOL_BN}{NEAR}খরা|drought{NEAR}{TOL_EN}|{TOL_EN}{NEAR}drought|খরা সহিষ্ণু",
     "drought_tolerance=Y", r"Drought[^:]*:\s*(T|R)\b"),
    ("cold tolerant", rf"(?<![ঀ-৿])(ঠান্ডা|ঠাণ্ডা|শীত)(?![ঀ-৿]){NEAR}{TOL_BN}|cold{NEAR}{TOL_EN}", None, r"Cold[^:]*:\s*(T|R)\b"),
    ("heat tolerant", rf"(?<![ঀ-৿])(তাপ|গরম)(?![ঀ-৿]){NEAR}{TOL_BN}|heat{NEAR}{TOL_EN}", None, None),
    ("tidal / deepwater / haor", r"জোয়ার|জোয়ার|tidal|deep ?water|গভীর পানি|হাওর|haor", None, None),
    ("zinc enriched", r"(জিংক|জিঙ্ক)\s*(সমৃদ্ধ|যুক্ত|সমৃদ্ধ)|zinc[- ]?(enrich|rich|biofort|dense)|high[- ]zinc", "harvestplus=Y", None),
    ("high protein", r"উচ্চ প্রোটিন|প্রোটিন সমৃদ্ধ|high protein|protein[- ]rich", None, None),
    ("aromatic", r"সুগন্ধ|aromatic|scented|basmati", None, None),
    ("fine grain", r"(?<!মাঝারি )(?<!মাঝারী )(?<!মাঝারি-)(চিকন|সরু)|(?<!medium )(?<!medium-)\b(slender|fine)\b", None, None),
    ("short duration", r"আগাম|স্বল্প ?মেয়াদ|স্বল্প জীবনকাল|short[- ]duration|early[- ]matur", None, None),
    ("blast resistant", rf"ব্লাস্ট{NEAR}(প্রতিরোধ|সহনশীল|সহিষ্ণু)|(প্রতিরোধ\S*){NEAR}ব্লাস্ট|blast{NEAR}(resist|toleran)|(resist|toleran)\S*{NEAR}blast",
     None, r"Blast[^:]*:\s*(HR|R)\b"),
    ("bacterial blight resistant", rf"(পাতা ?পোড়া|পাতাপোড়া|ঝলসানো){NEAR}(প্রতিরোধ|সহনশীল|সহিষ্ণু)|(প্রতিরোধ\S*){NEAR}(পাতা ?পোড়া|ঝলসানো)|(bacterial (leaf )?blight|BLB){NEAR}(resist|toleran)|(resist|toleran)\S*{NEAR}(bacterial (leaf )?blight|BLB)",
     None, r"(Bacterial blight|BLB)[^:]*:\s*(HR|R)\b"),
    ("lodging resistant", r"হেলে পড়ে না|হেলে পড়া প্রতিরোধ|lodging[- ]resist|non-lodging|does not lodge", None, None),
    ("low glycemic index", r"গ্লাইসেমিক|glycemic index|low GI", None, None),
]
TRIVSA_CODES = re.compile(r"[A-Z][A-Za-z ()/]*?(injury )?resistance[^:]*:\s*[A-Z]{1,2}\b")


NEG = re.compile(r"নয়|নয়|নহে|নাই|নেই|\bnot\b|\bnon[- ]|\bsusceptible\b|সংবেদনশীল")
NON_SALINE = re.compile(r"অলবণাক্ত|অলবনাক্ত|অ-লবণাক্ত|অ-লবনাক্ত|non[- ]?saline", re.I)
STRESS_SPIA = {"salt tolerant", "submergence tolerant", "drought tolerant"}
SALT_ITSELF = re.compile(r"(লবণাক্ততা|লবনাক্ততা)\S*\s*(সহনশীল|সহিষ্ণু|সহ্য)|salinity[- ]toleran|salt[- ]toleran|saline[- ]toleran|dS/m|ডিএস/মিটার", re.I)
MODERATE = re.compile(r"মাঝারী?ভাবে|মাঝারি ভাবে|আংশিক|কিছুটা|moderate|partial|somewhat|\bMR\b", re.I)
SUSCEPT = {"blast resistant": re.compile(r"susceptible[^|;.]{0,30}blast|blast[^|;.]{0,15}susceptib|ব্লাস্ট[^।|;]{0,30}সংবেদনশীল", re.I),
           "bacterial blight resistant": re.compile(r"susceptible[^|;.]{0,30}(bacterial (leaf )?blight|BLB)|(bacterial (leaf )?blight|BLB)[^|;.]{0,15}susceptib"
                                                    r"|(পাতা ?পোড়া|ঝলসানো)[^।|;]{0,30}সংবেদনশীল", re.I)}
CLAUSE = re.compile(r"[।|;.\n]")
ZINC_NUM = re.compile(r"(?:zinc|Zn|জিংক|জিঙ্ক)\D{0,20}?(\d{2}(?:\.\d+)?)\s*(?:ppm|mg|মিগ্রা|পিপিএম)|zinc_mg_kg=(\d{2}(?:\.\d+)?)", re.I)
SHORT_MAX = {"boro": 145, "aman": 120, "aus": 110}     # days; above this a variety is not tagged short duration
OFFICIAL = ("special_traits_official", "identifying_traits_official", "stress_tolerance", "quality_traits")


def _days(row):
    nums = [int(x) for x in re.findall(r"(?<!\d)(\d{2,3})(?!\d)", str(row.get("duration_days", "") or "")) if 80 <= int(x) <= 200]
    return max(nums) if nums else None


def _hit(pat, text, resist=False):
    """True when some clause matches the pattern and is not negated ('...সহনশীল নয়', 'not tolerant'); for resistance tags a
    clause that qualifies the resistance as moderate or partial does not count."""
    for cl in CLAUSE.split(text):
        if re.search(pat, cl, re.I) and not NEG.search(cl) and not (resist and MODERATE.search(cl)):
            return True
    return False


def tags_for(row):
    tags, ev = [], []
    spia = row.get("cgiar_spia_flags", "") or ""
    season = str(row.get("season", "") or "").lower()
    days = _days(row)
    for tag, pat, flag, triv in RULES:
        hit = []
        for c in FREE_TEXT:
            v = row.get(c, "")
            if not isinstance(v, str) or not v:
                continue
            if triv and re.search(triv, v, re.I):
                hit.append(c + " (TRIVSA screening)")
                continue
            text = TRIVSA_CODES.sub(" ", v)   # screening codes are judged by their own rule only
            if tag == "salt tolerant":
                text = NON_SALINE.sub(" ", text)
            if tag == "zinc enriched" and c not in OFFICIAL and not ZINC_NUM.search(text):
                continue                      # summary columns need a stated zinc content
            if _hit(pat, text, resist=tag in SUSCEPT):
                hit.append(c)
        if tag == "zinc enriched":
            vals = [float(a or b) for c in FREE_TEXT for a, b in ZINC_NUM.findall(str(row.get(c, "") or ""))]
            if vals and max(vals) >= 19:
                hit.append(f"stated zinc content {max(vals):g} mg/kg")
        if tag == "short duration" and hit and days:
            lim = min([v for k, v in SHORT_MAX.items() if k in season] or [145])
            if days > lim:
                hit = []                      # 'early' relative to a long-duration check, not short duration
        if flag and flag in spia:
            hit.append("cgiar_spia_flags")
        if tag in STRESS_SPIA and hit == ["cgiar_spia_flags"]:
            ev.append(f"{tag}: SPIA only (cgiar_spia_flags), not tagged")
            continue
        if tag == "salt tolerant" and hit:
            official = " ".join(str(row.get(c, "") or "") for c in OFFICIAL + ("recommended_region", "region_scope", "key_traits"))
            itself = any(SALT_ITSELF.search(str(row.get(c, "") or "")) for c in FREE_TEXT)
            if NON_SALINE.search(official) and not itself:
                ev.append(f"{tag}: not tagged, sources conflict (official text says non-saline; "
                          f"{', '.join(dict.fromkeys(hit))} says suited to saline areas)")
                continue
        if tag in SUSCEPT and hit:
            sus = [c for c in FREE_TEXT if SUSCEPT[tag].search(str(row.get(c, "") or ""))]
            if sus:
                ev.append(f"{tag}: not tagged, source text says susceptible ({', '.join(sus)})")
                continue
        if hit:
            tags.append(tag)
            ev.append(f"{tag}: {', '.join(dict.fromkeys(hit))}")
    return " | ".join(tags), " | ".join(ev)


def add(df):
    out = df.apply(lambda r: pd.Series(tags_for(r), index=["feature_tags", "feature_evidence"]), axis=1)
    df = df.copy()
    info = df[[c for c in OFFICIAL + ("key_traits",) if c in df.columns]].apply(lambda r: any(str(v).strip() for v in r), axis=1)
    for c in ("feature_tags", "feature_evidence", "trait_text_available"):
        if c in df.columns:
            df = df.drop(columns=c)
    pos = df.columns.get_loc("key_traits") if "key_traits" in df.columns else len(df.columns)
    df.insert(pos, "feature_tags", out.feature_tags)
    df.insert(pos + 1, "feature_evidence", out.feature_evidence)
    df.insert(pos + 2, "trait_text_available", info.map({True: "yes", False: "no"}))   # no tag + 'no' = no information, not no trait
    return df
