"""F3H: evidence rows from the other hybrid sources, matched to the MoA 2026 keys.

Sources: NSB activities report no.5 decisions (_F3H_r5_decisions.csv), MoA list 2018 edition (_F3H_moa2018_cells.csv),
MoA list 1998-2016 edition (_F3H_moa2016_list.csv), SCA compendium hybrid table (_F3H_compendium_hybrids.csv),
SCA annual registered-hybrid lists (_F3H_sca_hybrid_lists.csv). Files that do not exist yet are skipped.
Every match is written to 04_working/_F3H_match_report.csv for review.
"""
import csv, re, pathlib, collections
import phase3_F3H_build as B
from phase3_F3H_match import Matcher, norm

W = B.W
REPORT = []
NEWKEYS = {}  # key -> crosswalk row for hybrids not in the MoA 2026 list


def kc(mt, dt):
    return dt in B.KEY.get(int(mt), set())


def newkey(key, name, latin, code, company, src, note):
    if key not in NEWKEYS:
        NEWKEYS[key] = dict(key=key, moa2026_serial="", name_bn_as_printed=name, name_latin_as_printed=latin, code=code,
                            company=company, aliases_seen="", notes=f"NOT IN MoA 2026 LIST; found only in {src}. {note}".strip())
    else:
        NEWKEYS[key]["notes"] += f"; also in {src}"


def r5(ev, keyset):
    p = W / "_F3H_r5_decisions.csv"
    if not p.exists():
        return
    first = {}
    rows = list(csv.DictReader(open(p, encoding="utf-8")))
    for r in rows:
        first.setdefault(r["key"], int(r["meeting"]))
        first[r["key"]] = min(first[r["key"]], int(r["meeting"]))
    for r in rows:
        k, mt = r["key"], int(r["meeting"])
        dt = sorted(B.KEY.get(mt, {""}))[0]
        loc = f"report no.5, {B.ordn(mt)} meeting, text line {r['line']}"
        okk = kc(mt, dt)
        ext = r["kind"] == "extension"
        note = ("extension: " if ext else "") + r["notes"]
        ev.add(k, "approval_date", dt, f"{mt}তম সভা".translate(B.LAT2BN),
               "NSB_R5", r["page"], loc, "bijoy2unicode", "key_check" if okk else "unvalidated", "high",
               note + f"; date = the {B.ordn(mt)} meeting's own date from the meeting key (minutes heading gives the meeting number)")
        ev.add(k, "approval_reference", f"NSB {B.ordn(mt)} meeting: " + ("regional extension" if ext else "registration") + f" ({r['regions_en']})",
               r["quote"], "NSB_R5", r["page"], loc, "bijoy2unicode", "unvalidated", "high", note)
        ev.add(k, "region_scope", r["regions_en"] + (" (added)" if ext else ""), r["quote"], "NSB_R5", r["page"], loc,
               "bijoy2unicode", "unvalidated", "high", note)
        if not ext:
            m = re.search(r"(নিবন্ধিকরণের অনুমোদন|নিবন্ধনের অনুমোদন|নিবন্ধনের জন্য ছাড়করণ|নিবন্ধনের জন্য সুপারিশ|নিবন্ধন করা হলো|সাময়িকভাবে নিবন্ধিকরণ|ছাড়করণের অনুমোদন|সাময়িকভাবে শতর্ সাপেÿে নিবন্ধন|বিপণন ও চাষাবাদ)", r["quote"])
            ev.add(k, "release_category", "NSB_registration", m.group(1) if m else r["quote"][:120], "NSB_R5", r["page"], loc,
                   "bijoy2unicode", "unvalidated", "high",
                   "minutes wording for a hybrid; registration route" + ("; minutes mix 'ছাড়করণ' (release) and 'নিবন্ধন' (registration)" if m and "ছাড়করণ" in m.group(1) else ""))
        if k not in keyset:
            newkey(k, "সুবর্ণ-৩ (RH-664)" if k == "HYB_SUBARNA3RH664" else "", "RH-664" if k == "HYB_SUBARNA3RH664" else "",
                   "RH-664", "সুপ্রিম সীড কোঃ লিঃ", "NSB 75th minutes (report no.5 p.100)",
                   "name read on the page image, crop 04_working/crops/F3H/r5_p100_subarna3.png")
            if k == "HYB_SUBARNA3RH664":
                ev.add(k, "official_name_bn", "সুবর্ণ-৩", "সুবর্ণ-৩  (RH-664)", "NSB_R5", r["page"], loc + "; crop 04_working/crops/F3H/r5_p100_subarna3.png",
                       "visual_check", "visual_check", "high", "registered at NSB 75th; absent from the MoA 2026 cumulative list")
                ev.add(k, "official_name_en", "RH-664", "(RH-664)", "NSB_R5", r["page"], loc, "visual_check", "visual_check", "high", "")
                ev.add(k, "developer", "সুপ্রিম সীড কোঃ লিঃ", "সুপ্রিম সীড কোঃ লিঃ", "NSB_R5", r["page"], loc, "visual_check", "visual_check", "high", "")
                ev.add(k, "type", "hybrid", "হাইব্রিড জাতটি", "NSB_R5", r["page"], loc, "visual_check", "visual_check", "high", "")
                ev.add(k, "approving_body", "NSB", "জাতীয় বীজ বোর্ড", "NSB_R5", r["page"], loc, "bijoy2unicode", "unvalidated", "high", "")
                ev.add(k, "status", "unknown", "", "NSB_R5", r["page"], loc, "bijoy2unicode", "unvalidated", "medium",
                       "registered at 75th meeting but missing from MoA cumulative lists 2016, 2018, 2026: possibly dropped, renamed or omitted; no withdrawal record found")


def moa2018(ev, M, by_key):
    rows = list(csv.DictReader(open(W / "_F3H_moa2018_cells.csv", encoding="utf-8")))
    hdr = re.compile(r"\s*\|?\s*(অনুমোদিত জাতের নাম|উৎস|উদ্ভাবনকারী/আমদানীকারক|অনুমোদিত অঞ্চল|অনুমোদনের তারিখ ও \| সভা|অনুমোদনের তারিখ ও)\s*$")
    for r in rows:
        for c in ["name", "origin", "developer", "region", "date"]:
            r[c] = hdr.sub("", r[c]).strip(" |")
        name = B.j(r["name"])
        k, how = M.match("MOA_HYB18", r["serial"], name)
        REPORT.append(dict(source_id="MOA_HYB18", row_id=r["serial"], name=name, key=k or "", how=how))
        if not k:
            continue
        recs_k = by_key[k]
        rec = min(recs_k, key=lambda x: abs(x["serial"] - int(r["serial"])))
        nz = lambda x: norm(re.sub(r"আমন|বোরো|আউশ", "", x))
        page = r["pages"].split(";")[0]
        loc = f"MoA 2018 list row {r['serial']}"
        nik = bool(r["nikosh_cols"])
        if all(nz(name) != nz(x["name"]) for x in recs_k) and not nik:
            ev.add(k, "aliases", name, name, "MOA_HYB18", page, loc, "bijoy2unicode", "unvalidated", "medium",
                   f"name as printed in the 2018 edition differs from MoA 2026 row {rec['serial']} '{rec['name']}'")
        try:
            prs = B.pairs_of(r["date"])
        except Exception:
            prs = []
        for mt, dt, raw in prs:
            okk = kc(mt, dt)
            note = f"2018 edition row {r['serial']}"
            if (mt, dt) not in [(a, b) for a, b, _ in rec["pairs"]]:
                note += f"; DIFFERS from MoA 2026 row {rec['serial']} ({'; '.join(f'{a}={b}' for a, b, _ in rec['pairs'])})"
            ev.add(k, "approval_date", dt, raw.translate(B.LAT2BN), "MOA_HYB18", page, loc, "bijoy2unicode",
                   "key_check" if okk else "unvalidated", "high" if okk else "medium", note)
        reg = B.j(r["region"])
        if reg and all(norm(reg) != norm(x["region"]) for x in recs_k) and not nik:
            ev.add(k, "region_scope", B.region_en(reg), reg, "MOA_HYB18", page, loc, "bijoy2unicode", "unvalidated", "high",
                   f"2018 edition region differs from MoA 2026 row {rec['serial']}")
        dev = B.j(r["developer"])
        if dev and all(nz(dev) != nz(B.strip_transfer(x["dev"])[0]) for x in recs_k) and not nik:
            ev.add(k, "developer", B.strip_transfer(dev)[0], dev, "MOA_HYB18", page, loc, "bijoy2unicode", "unvalidated", "high",
                   f"2018 edition developer cell differs from MoA 2026 row {rec['serial']}")


def generic(ev, M, by_key, fname, sid_of, rowid_of, page_of, loc_of):
    p = W / fname
    if not p.exists():
        return []
    rows = list(csv.DictReader(open(p, encoding="utf-8")))
    out = []
    for r in rows:
        sid = sid_of(r)
        name = B.j(r.get("name_as_printed", ""))
        latin = B.j(r.get("latin_code_as_printed", "") or r.get("latin_as_printed", ""))
        k, how = M.match(sid, rowid_of(r), (name + (f" ({latin})" if latin and latin not in name else "")).strip(),
                         extra_codes=[latin] if latin else [])
        REPORT.append(dict(source_id=sid, row_id=rowid_of(r), name=name + (f" | {latin}" if latin else ""), key=k or "", how=how))
        out.append((r, k, how, sid))
    return out


def emit(ev, rows, by_key, label, page_of, loc_of, has_traits):
    for r, k, how, sid in rows:
        if not k:
            continue
        page, loc = page_of(r), loc_of(r)
        unc = r.get("uncertain", "")
        name = B.j(r.get("name_as_printed", ""))
        latin = B.j(r.get("latin_code_as_printed", "") or r.get("latin_as_printed", ""))
        nn = (f"match: {how}" + (f"; uncertain: {unc}" if unc else "") + (f"; {r['notes']}" if r.get("notes") else ""))[:600]
        V = "visual_check"
        if name:
            ev.add(k, "official_name_bn", name, name, sid, page, loc, V, V, "high", nn)
        if latin:
            ev.add(k, "official_name_en", latin, latin, sid, page, loc, V, V, "high", nn)
            mir = re.search(r"IR-?\s?\d{4,}", latin)
            if mir:
                ev.add(k, "cgiar_evidence", f"IRRI line designation printed: {mir.group(0)}", latin, sid, page, loc, V, V, "high", "IR-prefixed breeding line printed with the variety name")
                ev.add(k, "cgiar_lineage", "IRRI line released directly", latin, sid, page, loc, V, V, "medium", f"line {mir.group(0)} printed as the variety's code")
                ev.add(k, "cgiar_center", "IRRI", latin, sid, page, loc, V, V, "high", "")
        if r.get("developer_as_printed"):
            ev.add(k, "developer", B.strip_transfer(B.j(r["developer_as_printed"]))[0], B.j(r["developer_as_printed"]), sid, page, loc, V, V, "high", nn)
        o = B.j(r.get("origin_as_printed", ""))
        if o:
            ov = B.ORIGIN.get(o) or next((v for kk, v in B.ORIGIN.items() if kk in o), None)
            if ov:
                ev.add(k, "origin_country", ov, o, sid, page, loc, V, V, "high" if o not in ("নিজস্ব",) else "medium", nn)
                if o == "ইরি":
                    ev.add(k, "cgiar_evidence", f"{label} gives origin 'ইরি' (IRRI)", o, sid, page, loc, V, V, "high", "")
            elif "ইরি" in o:
                ev.add(k, "cgiar_evidence", f"{label} origin cell mentions IRRI", o, sid, page, loc, V, V, "high", "")
        if r.get("region_as_printed"):
            ev.add(k, "region_scope", B.region_en(r["region_as_printed"]), B.j(r["region_as_printed"]), sid, page, loc, V, V, "high", nn)
        s = B.j(r.get("season_as_printed", ""))
        if s and B.seasons_in(s):
            ev.add(k, "season", "; ".join(B.seasons_in(s)), s, sid, page, loc, V, V, "high", nn)
        if has_traits:
            d = B.j(r.get("duration_days_as_printed", ""))
            y = B.j(r.get("yield_t_ha_as_printed", ""))
            t = B.j(r.get("traits_as_printed", ""))
            if d:
                ev.add(k, "key_traits", f"duration {re.sub(r'[^0-9.-]', '', d.translate(B.BN))} days", d, sid, page, loc, V, V, "high", "growth duration (জীবনকাল, দিন)")
            if y:
                ev.add(k, "key_traits", f"yield {re.sub(r'[^0-9.-]', '', y.translate(B.BN)).strip('.')} " + ("t/acre (as printed)" if "একর" in y else "t/ha"), y, sid, page, loc, V, V, "high", "average yield (ফলন, টন/হেঃ)")
            if t:
                ev.add(k, "key_traits", t, t, sid, page, loc, V, V, "high", "identifying traits as printed (Bangla)")
        nos = [x for x in re.split(r"[;,\s]+", r.get("meeting_nos", "") or r.get("meeting_no", "")) if x]
        dts = (r.get("meeting_dates_iso", "") or r.get("meeting_date_iso", "")).split(";")
        raw_cell = B.j(r.get("meeting_cell_as_printed", "") or (r.get("meeting_no_as_printed", "") + " " + r.get("meeting_date_as_printed", "")))
        rec = by_key.get(k, [None])[0]
        moa_pairs = [(a, b) for a, b, _ in rec["pairs"]] if rec else []
        for i, mt in enumerate(nos):
            try:
                mt = int(mt)
            except ValueError:
                continue
            dt = dts[i].strip() if i < len(dts) else ""
            note = nn
            if moa_pairs and mt not in [a for a, _ in moa_pairs]:
                note += f"; meeting not in the MoA 2026 row ({'; '.join(f'{a}={b}' for a, b in moa_pairs)})"
            if dt:
                okk = kc(mt, dt)
                ev.add(k, "approval_date", dt, raw_cell, sid, page, loc, V, "key_check" if okk else V, "high", note +
                       ("" if okk else f"; meeting/date pair not in validated key (key: {sorted(B.KEY.get(mt, []))})"))
            ev.add(k, "approval_reference", f"NSB {B.ordn(mt)} meeting" + (f" ({dt})" if dt else ""), raw_cell, sid, page, loc, V, V, "high", note)
        ev.add(k, "release_category", "NSB_registration", label, sid, page, loc, V, V, "high", "listed as a registered (নিবন্ধিত) hybrid")


N115 = [  # NSB 115th minutes, read by eye on crops nsb115_p11_top/bot.png, nsb115_p12_top.png
    ("BRRI_HYBRID9", 11, "agenda 13 (salinity-tolerant Boro hybrids)", "ব্রি হাইব্রিড ধান৯", "", "বাংলাদেশ ধান গবেষণা ইনস্টিটিউট", "Bangladesh",
     "Chittagong, Khulna, Barisal", "8.44", "138", "চাল মাঝারি চিকন; লবণাক্ততা সহনশীল", "nsb115_p11_top.png"),
    ("BRRI_HYBRID10", 11, "agenda 13 (salinity-tolerant Boro hybrids)", "ব্রি হাইব্রিড ধান১০", "", "বাংলাদেশ ধান গবেষণা ইনস্টিটিউট", "Bangladesh",
     "Chittagong, Khulna, Barisal", "9.17", "139", "চাল মাঝারি চিকন; লবণাক্ততা সহনশীল", "nsb115_p11_top.png"),
    ("HYB_SYNGENTAHYBRIDDHAN11", 11, "misc. agenda 01 (2022-23 Boro trials)", "সিনজেনটা হাইব্রিড ধান১১", "S-1207", "সিনজেনটা বাংলাদেশ লিমিটেড", "Bangladesh",
     "nationwide", "8.68", "145", "চাল চিকন", "nsb115_p11_bot.png"),
    ("HYB_DUPONTHYBRIDDHAN9", 11, "misc. agenda 01", "ডুপন্ট হাইব্রিড ধান৯", "Pioneer 28P94", "ডুপন্ট বাংলাদেশ লিমিটেড", "",
     "nationwide", "8.86", "145", "চাল চিকন", "nsb115_p11_bot.png"),
    ("HYB_ACIHYBRIDDHAN17", 11, "misc. agenda 01", "এসিআই হাইব্রিড ধান১৭", "BGH46", "এসিআই লিমিটেড লিমিটেড", "",
     "nationwide", "9.36", "144", "চাল মোটা", "nsb115_p11_bot.png"),
    ("HYB_NAFCOHYBRIDDHAN3", 11, "misc. agenda 01", "নাফকো হাইব্রিড ধান৩", "CQR-2", "নাফকো (প্রা:) লিমিটেড", "",
     "Dhaka, Chittagong, Khulna", "9.28", "143", "চাল চিকন", "nsb115_p11_bot.png; nsb115_p12_top.png"),
    ("HYB_NATIONALAGRICAREHYBRIDDHAN10", 12, "misc. agenda 01", "ন্যাশনাল এগ্রিকেয়ার হাইব্রিড ধান১০", "", "ন্যাশনাল এগ্রিকেয়ার ইমপোর্ট এন্ড এক্সপোর্ট লি:", "",
     "Chittagong, Khulna, Barisal (decision); Chittagong, Khulna, Rangpur (discussion)", "8.83", "142", "", "nsb115_p12_top.png; nsb115_p11_bot.png"),
]


def nsb115(ev):
    for k, pg, ag, nm, lat, dev, orig, reg, y, d, tr, crop in N115:
        loc = f"NSB 115th minutes {ag}; crop 04_working/crops/F3H/{crop}"
        V = "visual_check"
        ev.add(k, "official_name_bn", nm, nm, "NSB_115", pg, loc, V, V, "high", "absent from the MoA 2026 cumulative list")
        if lat:
            ev.add(k, "official_name_en", lat, lat, "NSB_115", pg, loc, V, V, "high", "")
        ev.add(k, "developer", dev, dev, "NSB_115", pg, loc, V, V, "high", "proposer (প্রস্তাবিত) as printed")
        if orig:
            ev.add(k, "origin_country", orig, "ধানটির উৎস বাংলাদেশ", "NSB_115", pg, loc, V, V, "high", "")
        ev.add(k, "type", "hybrid", "হাইব্রিড ধানের জাত", "NSB_115", pg, loc, V, V, "high", "")
        ev.add(k, "release_category", "NSB_registration", "সাময়িকভাবে নিবন্ধনের জন্য অনুমোদন করা হলো", "NSB_115", pg, loc, V, V, "high", "provisional registration")
        ev.add(k, "approving_body", "NSB (on TC recommendation)", "কারিগরি কমিটি সুপারিশকৃত ... অনুমোদন করা হলো", "NSB_115", pg, loc, V, V, "high", "")
        ev.add(k, "approval_date", "2026-02-05", "১১৫তম সভা", "NSB_115", pg, loc, V, "key_check", "high", "NSB 115 = 2026-02-05 in meeting key")
        ev.add(k, "approval_reference", f"NSB 115th meeting, {ag}", ag, "NSB_115", pg, loc, V, V, "high", "")
        ev.add(k, "region_scope", reg, reg, "NSB_115", pg, loc, V, V, "high", "")
        ev.add(k, "season", "Boro", "বোরো মৌসুমে", "NSB_115", pg, loc, V, V, "high", "")
        ev.add(k, "key_traits", f"yield {y} t/ha", f"ফলন: {y} মে.টন", "NSB_115", pg, loc, V, V, "high", "")
        ev.add(k, "key_traits", f"duration {d} days", f"জীবনকাল: {d} দিন", "NSB_115", pg, loc, V, V, "high", "")
        if tr:
            ev.add(k, "key_traits", tr, tr, "NSB_115", pg, loc, V, V, "high", "")
        ev.add(k, "status", "active", "সাময়িকভাবে নিবন্ধন", "NSB_115", pg, loc, V, V, "medium", "provisional registration (Feb 2026)")


def run(ev, recs):
    keyset = {r["key"] for r in recs}
    by_key = collections.defaultdict(list)
    for r in recs:
        by_key[r["key"]].append(r)
    M = Matcher(recs)
    r5(ev, keyset)
    nsb115(ev)
    moa2018(ev, M, by_key)
    # 1998-2016 edition
    rows = generic(ev, M, by_key, "_F3H_moa2016_list.csv", lambda r: "MOA_HYB16", lambda r: r["serial"], None, None)
    emit(ev, rows, by_key, "MoA hybrid list 1998-2016", lambda r: r["pdf_page"], lambda r: f"MoA 1998-2016 list row {r['serial']}; crop {r['crop_file']}", False)
    # compendium
    rows = generic(ev, M, by_key, "_F3H_compendium_hybrids.csv", lambda r: "SCA_COMP", lambda r: r["serial"], None, None)
    emit(ev, rows, by_key, "SCA compendium hybrid registration table (নিবন্ধনের সময়)", lambda r: r["pdf_page"],
         lambda r: f"compendium hybrid table row {r['serial']} (printed p.{r.get('printed_page', '')}); crop {r['crop_file']}", True)
    # SCA annual lists
    rows = generic(ev, M, by_key, "_F3H_sca_hybrid_lists.csv", lambda r: f"SCA_HYB_{r['fy']}", lambda r: f"{r['fy']}#p{r['page']}#{r['list_serial']}", None, None)
    emit(ev, rows, by_key, "SCA annual list 'হাইব্রিড ধানের জাত নিবন্ধন'", lambda r: r["page"],
         lambda r: f"SCA FY{r['fy']} list p.{r['page']} row {r['list_serial']}; crop {r['crop_file']}", True)
    # unmatched rows that the manual file assigns to new keys are already handled via Matcher.manual -> key;
    # if that key is not a MoA key, register it as a non-MoA hybrid
    for rr in REPORT:
        if rr["key"] and rr["key"] not in keyset and rr["key"] != "UNMATCHED":
            newkey(rr["key"], rr["name"].split(" | ")[0], rr["name"].split(" | ")[1] if " | " in rr["name"] else "", "", "",
                   f"{rr['source_id']} row {rr['row_id']}", "")
    for k, *_ in N115:
        if k in NEWKEYS:
            NEWKEYS[k]["notes"] += "; also NSB 115th minutes (05-02-2026), registered provisionally under " + ("agenda 13" if k.startswith("BRRI") else "misc. agenda 01")
    with open(W / "_F3H_match_report.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["source_id", "row_id", "name", "key", "how"])
        w.writeheader()
        w.writerows(REPORT)
    print("match report:", collections.Counter((r["source_id"][:7], bool(r["key"])) for r in REPORT))
    return list(NEWKEYS.values())
