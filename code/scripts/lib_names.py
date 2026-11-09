"""Uniform display names (variety_name) from canonical keys, so 'BRRI dhan 33', 'BRRI dhan-31',
'Bri Dhan BR-29' all become one form. Official spellings stay in official_name_en / _bn."""
import re

CO = {"ACI": "ACI", "ACIAGROLINK": "ACI Agrolink", "ACIFORMULATION": "ACI Formulations", "AFTAB": "Aftab",
      "AMERICANADVANCEDAGRO": "American Advanced Agro", "AMIN": "Amin", "AUSBANGLA": "Aus-Bangla", "AUTOCROP": "Autocrop",
      "AYESHAABED": "Ayesha Abed", "BABYLON": "Babylon", "BADC": "BADC", "BAGRO": "B-Agro", "BAYER": "Bayer",
      "BLESSING": "Blessing", "BRAC": "BRAC", "DUPONT": "DuPont", "EXPLORE": "Explore", "FARMERS": "Farmers",
      "GBK": "GBK", "GETCO": "Getco", "GETCOAGRITECHNOLOGIES": "Getco Agri Technologies", "GETCOAGROVISION": "Getco Agro Vision",
      "GIANTAGROPROCESSING": "Giant Agro Processing", "ISPAHANI": "Ispahani", "KBP": "KBP", "KRISHIBID": "Krishibid",
      "KRISHIBIDSEED": "Krishibid Seed", "LALTEER": "Lal Teer", "MAHYCO": "Mahyco", "MALLIKA": "Mallika", "MASUD": "Masud",
      "MCDONALD": "McDonald", "METALAGRO": "Metal Agro", "MITALI": "Mitali", "MITALIAGRO": "Mitali Agro", "NAFCO": "Nafco",
      "NATIONALAGRICARE": "National Agricare", "NILSAGAR": "Nilsagar", "NORTHSOUTH": "North South", "PARTEX": "Partex",
      "PETROCHEM": "Petrochem", "QUALITYSEED": "Quality Seed", "RICECO": "Rice Co", "RISINGSUN": "Rising Sun",
      "SABUJBANGLA": "Sabuj Bangla", "SUPREME": "Supreme", "SUPREMESEED": "Supreme Seed", "SURAVI": "Suravi",
      "SYNGENTA": "Syngenta", "THREES": "Three S", "THREESAGRO": "Three S Agro", "TINPATA": "Tinpata",
      "TINPATASUPER": "Tinpata Super", "VISIONAGRO": "Vision Agro", "VNR": "VNR", "WINALL": "Winall", "WINALLHITECH": "Winall Hi-Tech"}
FIXED = {"OLD_PAJAM": "Pajam", "OLD_PURBACHI": "Purbachi", "OLD_BRISHAIL": "BRRI-shail", "OLD_BAU63": "BAU-63 (Bharosa)",
         "OLD_JIRASHAIL": "Jirashail", "BINASHAIL": "Binashail", "PVT_RABI_DHAN1": "RU dhan1 (Rabi dhan1)",
         "PVT_SUPREME_DHAN1": "Supreme dhan1", "HYB_TINPATASUPER": "Tinpata Super", "HYB_ARIZETEJ": "Arize Tej",
         "HYB_SL8H": "SL-8H", "HYB_IAHS100001": "IAHS-100-001", "HYB_CNSGC6": "CNSGC-6", "HYB_CJY527": "CJY-527",
         "HYB_LP05": "LP-05", "HYB_LP106": "LP-106", "HYB_LP108": "LP-108", "HYB_LP50": "LP-50", "HYB_LP70": "LP-70",
         "HYB_JF31": "JF-31", "HYB_JF37": "JF-37", "HYB_HRM604": "HRM-604", "HYB_GB4": "GB-4",
         "HYB_ARIZEDHANIH07002": "Arize Dhan (IH07002)"}
PAT = [(r"^BR(\d+)$", "BR{}"), (r"^BRRI_DHAN(\d+)$", "BRRI dhan{}"), (r"^BRRI_HYBRID(\d+)$", "BRRI hybrid dhan{}"),
       (r"^BINADHAN(\d+)$", "Binadhan-{}"), (r"^BINA_HYBRID(\d+)$", "BINA hybrid dhan{}"), (r"^IRATOM(\d+)$", "Iratom-{}"),
       (r"^BU_AROMATIC_HYBRID(\d+)$", "BU Aromatic Hybrid dhan{}"), (r"^BU_AROMATIC_DHAN(\d+)$", "BU Aromatic dhan{}"),
       (r"^BU_DHAN(\d+)$", "BU dhan{}"), (r"^GAU_DHAN(\d+)$", "GAU dhan{}"), (r"^BAU_DHAN(\d+)$", "BAU dhan{}"),
       (r"^BRAC_DHAN(\d+)$", "BRAC dhan{}"), (r"^PVT_ACI_DHAN(\d+)$", "ACI dhan{}"), (r"^IR(\d+)$", "IR{}")]


def variety_name(key, code=""):
    if key in FIXED:
        return FIXED[key]
    for p, f in PAT:
        m = re.match(p, key)
        if m:
            return f.format(int(m.group(1)))
    if key.startswith("HYB_"):
        s = key[4:]
        cc = re.sub(r"[^A-Z0-9]", "", code.upper()) if code else ""
        tail = f" ({code})" if code and not re.fullmatch(r"\d+", code) else ""
        m = re.match(r"^([A-Z]+?)HYBRID(DHAN|SEED)?(\d+)(.*)$", s)
        if m and m.group(1) in CO:
            kind = {"DHAN": "hybrid dhan", "SEED": "hybrid seed", None: "hybrid"}[m.group(2)]
            return f"{CO[m.group(1)]} {kind}{'' if kind.endswith('dhan') else ' '}{int(m.group(3))}{tail}"
        if cc and len(cc) >= 2 and s.endswith(cc) and len(s) > len(cc):
            return f"{s[:-len(cc)].title()}-{code}" if code.isdigit() else f"{s[:-len(cc)].title()} ({code})"
        m = re.match(r"^([A-Z]+?)(\d+)$", s)
        if m:
            return f"{m.group(1).title()}-{int(m.group(2))}{tail if cc != m.group(2) else ''}"
        return s.title() + tail
    return key
