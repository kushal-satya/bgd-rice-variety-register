"""F3I: CGIAR lineage from documented pedigrees (called by phase3_F3I_build_evidence.py).

Rules (decisions_F3I.md):
- code 1: breeding line carries a CGIAR designation (IR..., IRRI..., NERICA...), or an institute/CGIAR record states the
  line was bred at / introduced from IRRI (Rice Profile, TRIVSA Method 'Introduction' + Institution 'IRRI').
- code 2: an IR/CGIAR-designated token in the stated cross (parent), an IRGC accession as donor, a parent that is itself
  a released CGIAR line (e.g. BR6 = IR2061-214-3-8-2), or an IR element in the documented pedigree of a parent
  variety/line (grandparent; both rows cited).
- code 3: collaboration or funding documented only (Rice Profile joint/INGER statements, HarvestPlus funded_by).
- code 4: pedigree known, no CGIAR element at parent or grandparent level. code 5: no pedigree.
Parents are recognised only from pedigree text, never from variety names alone. lib_keys.make_key is applied only
to tokens that look like variety names (BR n / BRRI dhan n / Iratom n / Binadhan n), never to line codes."""
import re

SRC_PREF = ["RB-S01", "RB-S04", "DS-S04", "DS-S01", "RB-S22", "RB-S13", "F3I-ABA84826"]
BL_PREF = ["RB-S01", "RB-S04", "DS-S04", "DS-S01", "DS-S07", "F3I-ACI", "F3I-ABA84826"]
CG_TOK = re.compile(r"\b(IRRI\s?\d+|IRBB\s?\d+|IRBL\s?-?\d+[A-Z0-9]*(?:\([A-Z]+\))?|IR\s?-?\d+[A-Z0-9]*(?:\s?-\s?[0-9A-Z]+)*)", re.I)
IRGC = re.compile(r"IRGC\s*(?:acc\.?\s*no\.?|Acc\.?\s*No\.?|no\.?)?\s*(\d{5,6})", re.I)
NERICA = re.compile(r"NERICA\s?-?\s?\d+", re.I)
VAR = re.compile(r"(?<![A-Za-z0-9])(BR\s?-?(\d{1,2})|BRR?II?\s*[Dd]h?[an]+\s*-?\s*(\d+)|Iratom\s*-?\s*(\d+)|Bina\s?dhan\s*-?\s*(\d+))(?![\d])(?!\s?-\s?\d)", re.I)
LINE = re.compile(r"(?<![A-Za-z])(HUA\s?\d+|BR\s?\d{2,5}(?:\s?-\s?[0-9A-Z]+)+|BR\s?\d{3,5}|BG\s?\d+(?:-\d+)*)", re.I)
norm = lambda s: re.sub(r"\s", "", str(s)).upper()


def vkey(m):
    n = int(next(g for g in m.groups()[1:] if g))
    t = m.group(1).upper()
    if t.startswith("BR") and not re.match(r"BRR?II?\s*D", t):
        return f"BR{n}" if n <= 26 else f"BRRI_DHAN{n}"
    if t.startswith("BR"):
        return f"BR{n}" if n <= 26 else f"BRRI_DHAN{n}"
    if t.startswith("IRATOM"):
        return f"IRATOM{n}"
    return f"BINADHAN{n}"


def cg_designation(s):
    s = str(s)
    if NERICA.search(s):
        return "AfricaRice", NERICA.search(s).group(0)
    m = CG_TOK.search(s)
    if m and not re.match(r"IRRI\s*$", m.group(0), re.I):
        return "IRRI", m.group(0).strip()
    return None, None


def split_annot(ped):
    """Return (parent_text, grandparent annotations). '(a cross of IR20/...)' or '(IR20/IR5-114-3-1)' after a parent
    is ancestry of that parent; '(IR28)', '(NSIC Rc 9)', '(IRGC acc...)' are aliases at parent level."""
    gp = []
    def rep(m):
        inner = m.group(1)
        if "/" in inner or re.search(r"cross of", inner, re.I):
            gp.append(inner); return " "
        return " (" + inner + ")"
    return re.sub(r"\(([^()]*)\)", rep, ped), gp


def lineage_rows(rows, ADC, TRIV, SPIA, RP, HP, MVD, SRC):
    out = []
    by = {}
    for r in rows:
        by.setdefault(r["pilot_key"], []).append(r)

    def pick(pk, field, pref):
        c = [r for r in by.get(pk, []) if r["field"] == field and r["source_id"] in pref and r["value"].strip()
             and not (field == "pedigree" and r["source_id"] == "DS-S01" and "/" not in r["value"] and not re.search(r"mutant|of\s", r["value"], re.I))]
        c.sort(key=lambda r: pref.index(r["source_id"]))
        return c[0] if c else None

    # line index: normalised breeding line -> key
    lidx = {}
    for pk, rs in by.items():
        for r in rs:
            if r["field"] == "breeding_line" and r["source_id"] in ("RB-S01", "DS-S04", "RB-S04"):
                lidx.setdefault(norm(r["value"]), set()).add(pk)

    def resolve_line(tok, self_pk):
        t = norm(tok)
        hit = set()
        for bl, ks in lidx.items():
            if bl == t or bl.startswith(t + "-"):
                hit |= ks
        hit.discard(self_pk)
        return sorted(hit)

    def mk(pk, field, value, raw, base, notes, conf="medium", val=None):
        out.append({"pilot_key": pk, "field": field, "value": value, "value_raw": raw, "source_id": base["source_id"],
                    "source_title": base["source_title"], "authority_rank": base["authority_rank"], "local_file": base["local_file"],
                    "page": base["page"], "locator": base["locator"], "method": base["method"],
                    "validation": val or base["validation"], "confidence": conf, "notes": notes})

    def cite(r):
        return f"{r['source_id']} {r['local_file']} p.{r['page']} {r['locator']}: '{r['value'][:160]}'"

    def parents_of(pk, ped):
        pt, _ = split_annot(ped["value"])
        ps = [(vkey(m), m.group(0)) for m in VAR.finditer(pt)]
        unres = []
        for m in LINE.finditer(pt):
            ks = resolve_line(m.group(0), pk)
            ps += [(k, m.group(0)) for k in ks]
            if not ks:
                unres.append(m.group(0))
        return [(k, t) for k, t in ps if k != pk], unres

    def deep_note(pk, ped):
        ps, unres = parents_of(pk, ped)
        notes = []
        if unres:
            notes.append(f"parent line(s) not resolvable to a documented variety: {sorted(set(unres))}")
        for k, t in ps:
            pp = pick(k, "pedigree", SRC_PREF)
            if not pp:
                continue
            gps, _ = parents_of(k, pp)
            for g, gt in gps:
                gp = pick(g, "pedigree", SRC_PREF); gb = pick(g, "breeding_line", BL_PREF)
                hit = (gb and cg_designation(gb["value"])[0] and not gb["value"].upper().startswith("BR")) or (gp and CG_TOK.search(split_annot(gp["value"])[0]))
                if hit:
                    notes.append(f"CGIAR element beyond grandparent level: {pk} <- {k} <- {g} (not coded; rule counts parents and grandparents only)")
        return ("; ".join(dict.fromkeys(notes)) + "; ") if notes else ""

    keys = sorted(by)
    for pk in keys:
        if pk in ("UNMATCHED",):
            continue
        ped = pick(pk, "pedigree", SRC_PREF)
        bl = pick(pk, "breeding_line", BL_PREF)
        links = []  # (code, lineage text, center, base row, notes)
        # ---- code 1 from breeding line designation
        if bl:
            c, d = cg_designation(bl["value"])
            if c and not re.match(r"^BR", bl["value"].strip(), re.I):
                links.append((1, f"{c} line released directly" + (f" (pure-line selection from {d})" if c == "AfricaRice" else ""), c, bl,
                              f"breeding line {bl['value']} carries the {c} designation {d}; {cite(bl)}"))
        # ---- pedigree-based
        if ped:
            txt = ped["value"]
            ptxt, gpann = split_annot(txt)
            if re.search(r"(?i)(advance line of|selection from)\s+IR", txt):
                c, d = cg_designation(txt)
                links.append((1, f"IRRI line released directly (selection from {d})", "IRRI", ped, f"pedigree '{txt}'; {cite(ped)}"))
            else:
                for m in IRGC.finditer(ptxt):
                    links.append((2, f"IRRI genebank (IRGC) accession as parent: IRGC {m.group(1)}", "IRRI", ped, f"donor parent; {cite(ped)}"))
                for m in NERICA.finditer(ptxt):
                    links.append((2, f"AfricaRice parent: {m.group(0)}", "AfricaRice", ped, f"NERICA = AfricaRice (WARDA) interspecific line designation; {cite(ped)}"))
                cleaned = IRGC.sub(" ", ptxt)
                for m in CG_TOK.finditer(cleaned):
                    tok = m.group(0).strip()
                    if re.match(r"IRRI\s*$", tok, re.I):
                        continue
                    mutant = re.search(r"(?i)mutant", txt)
                    links.append((2, f"IRRI parent: {tok}" + (" (mutagenised source variety)" if mutant else ""), "IRRI", ped,
                                  f"IR/IRRI-designated token in the stated cross; {cite(ped)}"))
            # parent varieties / lines -> grandparents
            parents = []
            for m in VAR.finditer(ptxt):
                parents.append((vkey(m), m.group(0)))
            for m in LINE.finditer(ptxt):
                for k in resolve_line(m.group(0), pk):
                    parents.append((k, m.group(0)))
            seen = set()
            for k, tok in parents:
                if k == pk or k in seen:
                    continue
                seen.add(k)
                pbl = pick(k, "breeding_line", BL_PREF)
                pped = pick(k, "pedigree", SRC_PREF)
                if pbl:
                    c, d = cg_designation(pbl["value"])
                    if c and not re.match(r"^BR", pbl["value"].strip(), re.I):
                        links.append((2, f"{c} parent: {k} (= {c} line {pbl['value']})", c, ped,
                                      f"parent {tok} = {k}, itself a released {c} line; variety row: {cite(ped)}; parent row: {cite(pbl)}"))
                        continue
                prp = RP.get(k)
                if prp and re.search(r"(?:আন্তর্জাতিক|আর্ন্তজাতিক) ধান গবেষ\S* ইন\S*(?:,)? ফিলিপ", prp["intro"]):
                    links.append((2, f"IRRI parent: {k} ({tok}; line bred at IRRI per Rice Profile)", "IRRI", ped,
                                  f"parent {tok} = {k}; Rice Profile {prp['local_file']} states the line was crossed/selected at IRRI Philippines; variety row: {cite(ped)}"))
                    continue
                if pped:
                    pt, _ = split_annot(pped["value"])
                    gtoks = [m.group(0).strip() for m in CG_TOK.finditer(IRGC.sub(" ", pt)) if not re.match(r"IRRI\s*$", m.group(0), re.I)]
                    gtoks += [f"IRGC {m.group(1)}" for m in IRGC.finditer(pt)] + [m.group(0) for m in NERICA.finditer(pt)]
                    if gtoks:
                        cen = "AfricaRice" if all("NERICA" in g.upper() for g in gtoks) else "IRRI"
                        links.append((2, f"{cen} grandparent: {', '.join(dict.fromkeys(gtoks))} via {k}" + (f" ({tok})" if norm(tok) != norm(k) else ""),
                                      cen, ped, f"variety row: {cite(ped)}; parent row: {cite(pped)}", ))
            for g in gpann:  # SPIA-style '(a cross of IR20/IR5...)' annotations
                gt = [m.group(0).strip() for m in CG_TOK.finditer(g)]
                if gt:
                    links.append((2, f"IRRI grandparent: {', '.join(gt)} (annotation in pedigree text)", "IRRI", ped,
                                  f"ancestry annotation '{g}' printed after a parent; {cite(ped)}"))
        # ---- institute / CGIAR statements
        for r in by.get(pk, []):
            if r["source_id"] == "DS-S07" and r["field"] in ("pedigree", "breeding_line"):
                pass
        rp = RP.get(pk)
        if rp:
            intro = rp["intro"]
            base = {"source_id": "DS-S07", "source_title": SRC["RP"][1], "authority_rank": SRC["RP"][2], "local_file": rp["local_file"],
                    "page": "", "locator": "জাত পরিচিতি", "method": "html", "validation": "unvalidated", "value": ""}
            for pat, code, lin in [
                (r"[^।]*ইরি থেকে প্রবর্তন[^।]*", 1, "IRRI line released directly (stated in Rice Profile: introduced from IRRI)"),
                (r"[^।]*(?:আন্তর্জাতিক|আর্ন্তজাতিক) ধান গবেষ\S* ইন\S*(?:,)? ফিলিপ[^।]*", 1, "IRRI line released directly (stated in Rice Profile: cross made at IRRI Philippines)"),
                (r"[^।]*(?:আন্তর্জাতিক|আর্ন্তজাতিক) ধান গবেষ\S* ইন\S* হতে Introduction[^।]*", 1, "IRRI line released directly (stated in Rice Profile: introduced from IRRI)"),
                (r"[^।]*যৌথ (?:সহযোগিতা|সহযগিতা|উদ্যোগ)[^।]*", 3, "IRRI collaboration (stated in Rice Profile)"),
                (r"[^।]*INGER[^।]*", 3, "IRRI collaboration (stated in Rice Profile: INGER)"),
                (r"[^।]*IRGC\s?103918[^।]*", 2, "IRRI genebank (IRGC) accession as parent: IRGC103918 (stated in Rice Profile)"),
                (r"[^।]*আন্তর্জাতিক ধান গবেষণা ইনষ্টিটিউট এর IR55419-4[^।]*", 2, "IRRI parent: IR55419-4 (stated in Rice Profile)")]:
                for m in re.finditer(pat, intro):
                    s = m.group(0).strip()
                    if code == 3 and "INGER" in lin and "IRRI থেকে প্রাপ্ত" in s:
                        lin2 = "IRRI collaboration (stated in Rice Profile: INGER material received from IRRI)"
                    else:
                        lin2 = lin
                    b = dict(base, locator="জাত পরিচিতি: '" + " ".join(s.split()[:24]) + "'")
                    links.append((code, lin2, "IRRI", b, f"Rice Profile sentence: '{s[:300]}'"))
                    break
        tr = TRIV.get(pk)
        if tr is not None:
            inst = str(tr["Institution that developed the variety"]); meth = str(tr["Method"])
            if inst == "IRRI":
                base = {"source_id": "DS-S04", "source_title": SRC["TRIVSA"][1], "authority_rank": SRC["TRIVSA"][2],
                        "local_file": SRC["TRIVSA"][3], "page": "", "locator": f"sheet Releases row {tr['xlsx_row']} (Ref ID {tr['Ref ID']})",
                        "method": "xlsx", "validation": "unvalidated", "value": ""}
                links.append((1, f"IRRI line released directly (stated in TRIVSA: Institution 'IRRI', Method '{meth if meth != 'nan' else 'blank'}')", "IRRI", base,
                              f"TRIVSA Method={meth if meth != 'nan' else '(blank)'}; Institution={inst}; Country of origin={tr['Country of origin ']}"))
        hp = HP.get(pk)
        if hp and "harvestplus" in (hp["funded_by"] + hp["breeder_organization"]).lower():
            base = {"source_id": "DS-S06", "source_title": SRC["HP"][1], "authority_rank": SRC["HP"][2], "local_file": SRC["HP"][3],
                    "page": "", "locator": f"result.data[{hp['json_index']}] id_variety {hp['id_variety']}", "method": "api_json",
                    "validation": "unvalidated", "value": ""}
            links.append((3, "HarvestPlus-funded/co-developed", "HarvestPlus", base,
                          f"HarvestPlus BCR: funded_by={hp['funded_by']}; breeder_organization={hp['breeder_organization']}; display_name={hp['display_name']}"))
        elif hp:
            base = {"source_id": "DS-S06", "source_title": SRC["HP"][1], "authority_rank": SRC["HP"][2], "local_file": SRC["HP"][3],
                    "page": "", "locator": f"result.data[{hp['json_index']}] id_variety {hp['id_variety']}", "method": "api_json",
                    "validation": "unvalidated", "value": ""}
            mk(pk, "cgiar_evidence", f"HarvestPlus BCR lists it as released biofortified rice; funded_by '{hp['funded_by']}' (not HarvestPlus): no CGIAR funding stated",
               f"funded_by={hp['funded_by']}; breeder_organization={hp['breeder_organization']}", base,
               "not coded as HarvestPlus-funded because funded_by is not HarvestPlus")
        # ---- write rows
        if not links:
            if ped:
                mk(pk, "cgiar_role", "4", ped["value"], ped, "pedigree known; no IR/CGIAR-designated parent or grandparent found in documented pedigrees; "
                   + deep_note(pk, ped) + cite(ped))
            else:
                base = bl or next((r for r in by[pk] if r["field"] in ("official_name_bn", "official_name_en")), by[pk][0])
                extra = [r["value"] for r in by[pk] if r["field"] == "pedigree"]
                mk(pk, "cgiar_role", "5", base["value"], base, "no documented pedigree (cross formula) in F3I sources"
                   + (f"; non-pedigree statements seen: {extra}" if extra else "")
                   + ("; breeding line has no CGIAR designation" if bl else ""), conf="low")
            continue
        seenlin = set()
        for code, lin, cen, base, note in links:
            if lin in seenlin:
                continue
            seenlin.add(lin)
            mk(pk, "cgiar_lineage", lin, base.get("value", ""), base, note, conf="high" if code in (1, 2) and base["source_id"] in ("RB-S01", "DS-S07", "RB-S04") else "medium")
        # role: best code per basis row
        best = {}
        for code, lin, cen, base, note in links:
            k = (base["source_id"], base["locator"])
            if k not in best or code < best[k][0]:
                best[k] = (code, lin, cen, base)
        for code, lin, cen, base in best.values():
            mk(pk, "cgiar_role", str(code), base.get("value", ""), base, f"crawl_plan 3a code {code}: {lin}",
               conf="high" if code in (1, 2) else "medium")
        if ped and not any(c <= 2 for c, _, _, _, _ in links):
            mk(pk, "cgiar_role", "4", ped["value"], ped, "pedigree basis: no IR/CGIAR element at parent or grandparent level in this pedigree "
               "(other rows code a CGIAR link from a different source/statement); " + cite(ped))
        for cen in dict.fromkeys(c for _, _, c, _, _ in links):
            b = next(bb for _, _, c, bb, _ in links if c == cen)
            mk(pk, "cgiar_center", cen, b.get("value", ""), b, "centre named by the documented link (see cgiar_lineage rows)")
    return out
