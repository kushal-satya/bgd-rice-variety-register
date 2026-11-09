"""Canonical variety keys shared by every Phase 3 agent.

    from lib_keys import make_key
    make_key("ব্রি ধান-৮৯")          -> "BRRI_DHAN89"
    make_key("BRRI hybrid dhan 1")    -> "BRRI_HYBRID1"
    make_key("বিনা ধান২৭")            -> "BINADHAN27"
    make_key("BR-11 (Mukta)")         -> "BR11"
    make_key("Iratom 24")             -> "IRATOM24"

Rules
- Public series are recognised from Bangla or English: BR<n> (n<=26), BRRI_DHAN<n> (n>=27),
  BRRI_HYBRID<n>, BINADHAN<n>, BINA_HYBRID<n>, BU_DHAN<n>, BU_AROMATIC_DHAN<n>,
  BU_AROMATIC_HYBRID<n>, GAU_DHAN<n>, BAU_DHAN<n>, BRAC_DHAN<n>, IR<n> (IRRI line names such as IR8),
  IRATOM<n>, BINASHAIL.
- Anything else (private hybrids, local, old introductions) returns None. Those keys come from
  04_working/hybrid_key_crosswalk.csv (built by agent F3H) as HYB_<SLUG>, or from
  04_working/key_crosswalk_other.csv as OLD_<SLUG>. Never invent a key by fuzzy similarity:
  if make_key returns None and the name is not in a crosswalk, write the row with
  pilot_key = "UNMATCHED" and the raw name in value_raw. The coordinator resolves it.
"""
import re

BN = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
PAT = [
    (r"(?:ব্রি|brri|bri)\s*হাইব্রিড\s*ধান|brri\s*hybrid\s*(?:dhan)?|bri\s*hybrid", "BRRI_HYBRID"),
    (r"(?:ব্রি|brri|bri)\s*ধান|brri\s*dhan|bri\s*dhan", "BRRI_DHAN"),
    (r"বিনা\s*হাইব্রিড\s*ধান|bina\s*hybrid\s*(?:dhan)?", "BINA_HYBRID"),
    (r"বিনা\s*ধান|বিনাধান|binadhan|bina\s*dhan", "BINADHAN"),
    (r"বিনাশাইল|binashail|binasail", "BINASHAIL"),
    (r"ইরাটম|iratom", "IRATOM"),
    (r"বিইউ\s*এরোমেটিক\s*হাইব্রিড\s*ধান|bu\s*aromatic\s*hybrid\s*(?:dhan)?", "BU_AROMATIC_HYBRID"),
    (r"বিইউ\s*এরোমেটিক\s*ধান|bu\s*aromatic\s*(?:dhan)?", "BU_AROMATIC_DHAN"),
    (r"বিইউ\s*ধান|bu\s*dhan", "BU_DHAN"),
    (r"জিএইউ\s*ধান|gau\s*dhan", "GAU_DHAN"),
    (r"বাউ\s*ধান|bau\s*dhan|bau-?dhan", "BAU_DHAN"),
    (r"ব্র্যাক\s*ধান|brac\s*dhan", "BRAC_DHAN"),
    (r"বিআর|(?<![a-z])br(?![a-z])", "BR"),
    (r"আইআর|(?<![a-z])ir(?![a-z])", "IR"),
]


def make_key(name):
    if not name:
        return None
    s = str(name).translate(BN).lower()
    s = re.sub(r"[‌‍]", "", s)
    for pat, pref in PAT:
        m = re.search("(?:" + pat + r")\s*[-–:]*\s*(\d+)", s)
        if m:
            n = int(m.group(1))
            if pref == "BINASHAIL":
                return "BINASHAIL"
            if pref == "BRRI_DHAN" and n <= 26:      # 'BRRI dhan 11' style references to BR11
                pref = "BR"
            if pref == "BR" and n >= 27:              # 'BR 28' style references to BRRI dhan28
                pref = "BRRI_DHAN"
            return f"{pref}{n}"
        if pref == "BINASHAIL" and re.search(pat, s):
            return "BINASHAIL"
    return None


if __name__ == "__main__":
    for t in ["ব্রি ধান-৮৯", "BRRI hybrid dhan 1", "বিনা ধান২৭", "BR-11 (Mukta)", "Iratom 24", "BRRI dhan 29",
              "বিআর ২৮", "ব্রি হাইব্রিড ধান-১", "Binashail", "BU Aromatic Hybrid Dhan-1", "IR 8", "হীরা-২"]:
        print(t, "->", make_key(t))
