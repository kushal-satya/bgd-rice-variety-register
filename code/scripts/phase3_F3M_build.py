"""F3M builder: NSB minutes (meetings 1-115) -> every rice decision.

Inputs (all in 04_working/):
  _F3M_decisions_manual.tsv   one row per decision, hand-read from the minutes (see notes_F3M.md)
  _F3M_visual_checks.tsv      crops opened with Read: id, what (line|name|date|region), seen, crop, result
  _F3M_cgiar.tsv              CGIAR links stated in the minutes (id, lineage, role, center, quote_rx)
  nsb_meeting_key.csv         meeting -> date key (for key_check)
  hybrid_key_crosswalk.csv    F3H's private/public hybrid keys (exact token match only)
  _F3M_key_overrides.tsv      id -> key, for hybrids whose name could be matched by eye to a crosswalk row
Outputs:
  F3M_decisions_index.csv     master register (one row per decision)
  evidence_F3M.csv            Phase-2 long format
  key_crosswalk_other.csv     OLD_ keys appended (append only)
Re-runnable; reads cached text only.
"""
import csv, re, sys, pathlib, unicodedata
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_keys import make_key

ROOT = pathlib.Path(__file__).resolve().parents[1]
W = ROOT / "04_working"
BN = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
COLS = ["pilot_key", "field", "value", "value_raw", "source_id", "source_title", "authority_rank", "local_file", "page",
        "locator", "method", "validation", "confidence", "notes"]

BUNDLES = {
    "B1": ("nsb_minutes_001-018", "NSB_R1", "NSB activities report no.1 (minutes summaries, NSB 1st-18th meetings, 1974-1984)"),
    "B2": ("nsb_minutes_019-028", "NSB_19_28", "NSB minutes 19th-28th meetings (1984-1992), activities report no.2"),
    "B3": ("nsb_minutes_029-042", "NSB_29_42", "NSB minutes 29th-42nd meetings (1993-1999), activities report no.3"),
    "B4": ("nsb_minutes_043-057", "NSB_43_57", "NSB minutes 43rd-57th meetings (2000-2005), activities report no.4 (June 2005)"),
    "B5": ("nsb_minutes_058-075", "NSB_R5", "NSB minutes 58th-75th meetings (2005-2011), activities report no.5 (Nov 2011)"),
    "B6": ("nsb_minutes_076-082", "NSB_76_82", "NSB minutes 76th-83rd meetings (2012-2014), activities report no.6 (file named 076-082)"),
}


def src_info(src):
    if src in BUNDLES:
        return BUNDLES[src]
    n = int(src[1:])
    return (f"nsb_minutes_{n:03d}", f"NSB_{n:03d}", f"NSB {n}th meeting minutes (single file, sca.gov.bd)")


def norm(s):
    s = unicodedata.normalize("NFC", s or "")
    return s.replace("য়", "য়").replace("ড়", "ড়").replace("ঢ়", "ঢ়")


_TXT = {}


def pages_of(src):
    """dict page -> list of lines"""
    if src in _TXT:
        return _TXT[src]
    if src == "B5":
        f = ROOT / "03_extracted/text/P2A/nsb_058-075_unicode.txt"
    else:
        f = ROOT / "03_extracted/text/F3M" / f"{src_info(src)[0]}.txt"
    P, page = {}, 0
    if f.exists():
        for u in f.read_text(encoding="utf-8").splitlines():
            m = re.match(r"=== page (\d+)", u)
            if m:
                page = int(m.group(1)); P.setdefault(page, []); continue
            P.setdefault(page, []).append(norm(u))
    _TXT[src] = P
    return P


AGENDA = re.compile(r"(?:আলোচ্য\s*সূ?ু?চী|আলোচ্যসূচী|আলোচ্যসুচী|আলোচন্যসূচি|আলোচ্যসূচি)\s*[-–:ঃ]?\s*\(?\s*([০-৯0-9]{1,2}|[ক-ঞ]|বিবিধ)")
SECTION = re.compile(r"^\W{0,3}([০-৯0-9]{1,2}\s*[.৷:]\s*[০-৯0-9]{1,2})")


def locate(src, page, rx):
    P = pages_of(src)
    if not P:
        return None
    rx = re.compile(norm(rx)) if rx else None
    order = [page]
    for k in range(1, 9):
        order += [page + k, page - k]
    for p in order:
        L = P.get(p, [])
        for i, u in enumerate(L):
            if not u.strip():
                continue
            if rx is None or rx.search(u):
                return p, i, u.strip()
            j = i + 1
            while j < len(L) and not L[j].strip():
                j += 1
            if j < len(L) and rx.search(u + " " + L[j]) and not rx.search(L[j]):
                return p, i, (u.strip() + " " + L[j].strip())
    return None


def agenda_of(src, p, i):
    P = pages_of(src)
    pp, ii = p, i
    for _ in range(400):
        L = P.get(pp, [])
        if 0 <= ii < len(L):
            u = L[ii]
            m = AGENDA.search(u)
            if m:
                return m.group(1).translate(BN), u.strip()[:90]
            if src in ("B1", "B2", "B3"):
                m = SECTION.match(u)
                if m:
                    return re.sub(r"\s", "", m.group(1)).translate(BN).replace("৷", ".").replace(":", "."), u.strip()[:90]
            ii -= 1
        else:
            pp -= 1
            if pp not in P:
                break
            ii = len(P[pp]) - 1
    return "", ""


def tsv(path):
    if not path.exists():
        return []
    out = []
    lines = path.read_text(encoding="utf-8").splitlines()
    hdr = lines[0].split("\t")
    for l in lines[1:]:
        if not l.strip():
            continue
        v = l.split("\t")
        v += [""] * (len(hdr) - len(v))
        out.append(dict(zip(hdr, [x.strip() for x in v])))
    return out


# ---------- hybrid crosswalk (exact normalized token match) ----------
def ntok(s):
    s = norm(s).translate(BN).lower()
    return re.sub(r"[\s\-–._/()]", "", s)


XW = list(csv.DictReader(open(W / "hybrid_key_crosswalk.csv", encoding="utf-8"))) if (W / "hybrid_key_crosswalk.csv").exists() else []
XT = {}
for r in XW:
    toks = set()
    for f in ("name_bn_as_printed", "name_latin_as_printed", "code"):
        v = r.get(f, "")
        if v:
            toks.add(ntok(v))
            for part in re.split(r"[()/|]", v):
                if len(ntok(part)) >= 3:
                    toks.add(ntok(part))
    for a in (r.get("aliases_seen") or "").split("|"):
        if len(ntok(a)) >= 3:
            toks.add(ntok(a))
    for t in toks:
        XT.setdefault(t, set()).add(r["key"])


KEYS = {r["key"] for r in XW}


def hyb_key(d):
    # 1) trade-name slug equal to a crosswalk key (HYB_<SLUG>), e.g. 'Jagoron-2' -> HYB_JAGORON2
    for f in ("key_name", "variety_raw"):
        for part in re.split(r"[()/|;]", d.get(f, "")):
            slug = re.sub(r"[^A-Z0-9]", "", part.upper())
            if len(slug) >= 4 and "HYB_" + slug in KEYS:
                return "HYB_" + slug, ""
    cands = []
    for f in ("variety_raw", "key_name"):
        v = d.get(f, "")
        for part in [v] + re.split(r"[()/|]", v):
            t = ntok(part)
            if len(t) >= 3 and t in XT:
                cands.append(XT[t])
    if not cands:
        return None, "no crosswalk token match"
    inter = set.intersection(*cands) if len(cands) > 1 else cands[0]
    allk = set().union(*cands)
    if len(inter) == 1:
        return next(iter(inter)), ""
    if len(allk) == 1:
        return next(iter(allk)), ""
    return None, "ambiguous crosswalk match: " + " / ".join(sorted(allk))


def main():
    D = tsv(W / "_F3M_decisions_manual.tsv")
    VC = {}
    for v in tsv(W / "_F3M_visual_checks.tsv"):
        VC[(v["id"], v["what"])] = v
    CG = {c["id"]: c for c in tsv(W / "_F3M_cgiar.tsv")}
    OV = {o["id"]: o["key"] for o in tsv(W / "_F3M_key_overrides.tsv")}
    OVN = {o["id"]: o.get("note", "") for o in tsv(W / "_F3M_key_overrides.tsv")}
    MK = {}
    for r in csv.DictReader(open(W / "nsb_meeting_key.csv", encoding="utf-8")):
        if r["validation"] in ("visual_check", "two_source") and r["kind"].startswith("minutes"):
            MK.setdefault(int(r["meeting_no"]), set()).add(r["meeting_date"])
    old_rows = []
    idx, ev = [], []
    for d in D:
        src = d["src"]
        stem, sid, stitle = src_info(src)
        local = f"02_raw/sca/{stem}.pdf"
        method = "bijoy2unicode" if src == "B5" else "ocr"
        hit = locate(src, int(d["page"] or 0), d["find"])
        if hit:
            page, li, quote = hit
            ag_no, ag_txt = agenda_of(src, page, li)
        else:
            page, quote, ag_no, ag_txt = d["page"], "", "", ""
            v = VC.get((d["id"], "name"))
            if v and v["result"] == "ok":
                quote = "[read on page image " + v["crop"] + "] " + d["variety_raw"]
        if (d["id"], "agenda") in VC:
            ag_no = VC[(d["id"], "agenda")]["seen"]
        mtg = int(d["mtg"])
        date = d["date_iso"]
        # ---- key ----
        knote = ""
        kn = d["key_name"]
        if d["id"] in OV:
            key = OV[d["id"]]
            knote = "key set by hand: " + OVN.get(d["id"], "")
        elif kn.startswith("OLD_") or kn.startswith("IRATOM_"):
            key = kn if kn.startswith("OLD_") else "UNMATCHED"
            if kn.startswith("OLD_"):
                old_rows.append((kn, d["variety_raw"], f"{sid} p{page}"))
        else:
            key = make_key(kn) if kn else None
            hybrid = d["type"].startswith("registration") or "hybrid" in kn.lower() or d["type"] == "re_trial" or "হাইব্রিড" in d["variety_raw"]
            if key and hybrid and not re.search(r"(?i)brri|bina|bu ", kn):
                key = None   # make_key would mis-key private hybrid names (e.g. 'BRAC hybrid dhan12')
            if not key and hybrid:
                key, knote = hyb_key(d)
            if not key:
                key = "UNMATCHED" if (kn or d["variety_raw"]) and not d["variety_raw"].startswith(("BRRI varieties", "approved varieties", "parent lines", "registered hybrids")) else ""
        # ---- validations ----
        date_val = "key_check" if (date and date in MK.get(mtg, set())) else "unvalidated"
        line_vc = VC.get((d["id"], "line"))
        name_vc = VC.get((d["id"], "name"))
        line_val = "visual_check" if line_vc and line_vc["result"] == "ok" else "unvalidated"
        name_val = "visual_check" if name_vc and name_vc["result"] == "ok" else ("key_check" if (key and make_key(d["key_name"] or "") == key and date_val == "key_check") else "unvalidated")
        if src == "B5" and date_val == "key_check":
            # typed SutonnyMJ text layer (not OCR): meeting number/date checked against the key
            if name_val == "unvalidated":
                name_val = "key_check"
            if line_val == "unvalidated":
                line_val = "key_check"
        vis = any(v and v["result"] == "ok" for v in (line_vc, name_vc))
        other_val = "visual_check" if vis else ("key_check" if (src == "B5" and date_val == "key_check") else "unvalidated")
        idx.append({"dec_id": d["id"], "meeting_no": mtg, "meeting_date": date, "agenda_item": ag_no, "agenda_heading": ag_txt,
                     "decision_type": d["type"], "variety_raw": d["variety_raw"], "pilot_key": key, "key_note": knote,
                     "breeding_line_raw": d["line_raw"], "developer": d["developer"], "season": d["season"], "region_scope": d["region"],
                     "pedigree_raw": d["pedigree"], "source_id": sid, "local_file": local, "page": page, "quote": quote[:200],
                     "date_validation": date_val, "line_validation": line_val if d["line_raw"] else "",
                     "name_validation": name_val, "notes": d["notes"]})
        if not key:
            continue
        ref = f"NSB {mtg}th meeting" + (f", agenda {ag_no}" if ag_no else "")
        loc = (f"agenda {ag_no}: " if ag_no else "") + (f"'{quote[:110]}'" if quote else "")
        base = dict(pilot_key=key, source_id=sid, source_title=stitle, authority_rank="1_primary_legal", local_file=local,
                    page=page, method=method, confidence="high" if src == "B5" else "medium")

        def add(field, value, raw, val, notes="", conf=None, loc_=None):
            r = dict(base); r.update(field=field, value=value, value_raw=raw, validation=val, notes=notes,
                                     locator=loc_ or loc)
            if conf:
                r["confidence"] = conf
            ev.append(r)
        t = d["type"]
        grant = t in ("release", "release_provisional", "registration_provisional", "registration_full", "registration_conditional")
        if grant or t == "registration_extension":
            if grant:
                add("approval_date", date, f"{date} (date of NSB {mtg}th meeting)", date_val,
                    "meeting date from nsb_meeting_key.csv" + ("" if date_val == "key_check" else "; meeting date not yet validated in the key"))
                add("approval_reference", ref, ag_txt or quote[:80], date_val if ag_no else "unvalidated")
                cat = "NSB_registration" if t.startswith("registration") else "NSB_release"
                note = {"release_provisional": "provisional release (time-limited)", "registration_conditional": "conditional"}.get(t, "")
                if t == "registration_provisional":
                    note = "provisional/regional registration (সাময়িক নিবন্ধন)"
                add("release_category", cat, quote[:80], date_val, note)
            if d["region"]:
                add("region_scope", d["region"], quote[:120], other_val,
                    ("registration extended to these regions (re-trial) at NSB %d" % mtg) if t == "registration_extension" else "")
        if re.search(r"[ঀ-৿]", d["variety_raw"]) and t not in ("condition_change", "gazette"):
            add("official_name_bn", d["variety_raw"], quote[:120], name_val, "name as printed in the minutes" + ("; OCR text" if method == "ocr" else ""))
        if d["line_raw"] and not re.match(r"^H-\d", d["line_raw"]) and t in ("release", "release_provisional", "approval_deferred", "registration_provisional"):
            fld = "breeding_line"
            if t.startswith("registration"):
                fld = "aliases"
            add(fld, re.sub(r"\s*;\s*H-.*$", "", d["line_raw"]), quote[:120], line_val, "line/code as printed" + ("" if line_val == "visual_check" else "; OCR, not yet crop-checked" if method == "ocr" else "; typed text layer, not crop-checked"))
        if d["season"]:
            add("season", d["season"], quote[:80], other_val)
        if d["developer"] and (grant or t == "registration_extension"):
            add("developer", d["developer"], quote[:80], other_val)
        if d["pedigree"]:
            add("pedigree", d["pedigree"], quote[:120], other_val)
        if t in ("suspension", "withdrawal", "denotification_proposed"):
            st = "withdrawn" if (t == "withdrawal" or "cultivation suspended" in d["notes"]) else "unknown"
            add("status", st, quote[:120], other_val if t == "denotification_proposed" else date_val,
                ("denotification proposed, not decided: " if t == "denotification_proposed" else "") + d["notes"])
        if t == "rename":
            add("aliases", d["variety_raw"], quote[:120], name_val, d["notes"])
        if d["id"] in CG:
            c = CG[d["id"]]
            add("cgiar_lineage", c["lineage"], c.get("quote", "") or quote[:120], other_val)
            add("cgiar_role", c["role"], c.get("quote", "") or quote[:120], other_val)
            add("cgiar_center", c["center"], c.get("quote", "") or quote[:120], other_val)
            add("cgiar_evidence", c.get("quote", "") or quote[:150], c.get("quote", "") or quote[:150], other_val)
    # ---- write ----
    with open(W / "F3M_decisions_index.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(idx[0].keys())); w.writeheader(); w.writerows(idx)
    with open(W / "evidence_F3M.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS); w.writeheader(); w.writerows(ev)
    # OLD_ keys: append only
    kx = W / "key_crosswalk_other.csv"
    have = set()
    if kx.exists():
        have = {r["key"] for r in csv.DictReader(open(kx, encoding="utf-8"))}
    new = {}
    for k, nm, s in old_rows:
        if k not in have and k not in new:
            new[k] = (nm, s)
    if new:
        exists = kx.exists()
        with open(kx, "a", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            if not exists:
                w.writerow(["key", "name_as_printed", "source", "notes"])
            for k, (nm, s) in new.items():
                w.writerow([k, nm, s, "F3M: name in NSB minutes"])
    from collections import Counter
    print("decisions", len(idx), "evidence", len(ev), "keys", len({r['pilot_key'] for r in ev}))
    print(Counter(r["validation"] for r in ev))
    print("unlocated:", [d["dec_id"] for d in idx if not d["quote"]])
    print("UNMATCHED:", sum(1 for d in idx if d["pilot_key"] == "UNMATCHED"))


if __name__ == "__main__":
    main()
