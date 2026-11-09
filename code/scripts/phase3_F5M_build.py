"""F5M builder: every NSB rice decision (F3M register, 562 rows + F5M additions) with the full verbatim agenda-item
text, the raw OCR / raw text layer, and structured attributes.

Inputs
  04_working/F3M_decisions_index.csv           F3M register (decision rows, keys, meeting, page)
  04_working/_F3M_decisions_manual.tsv         F3M find-regex per decision (anchor)
  04_working/_F5M_additions.tsv                rice decisions F3M missed (same columns as the index + find)
  03_extracted/text/F5M/<stem>.txt             page text (phase3_F5M_bijoytext.py, phase3_F5M_text.py)
  03_extracted/text/F5M/nsb_minutes_058-075.raw.txt  raw SutonnyMJ layer, line-parallel
  03_extracted/text/ocr/<stem>/pNNN_psm6.txt   raw Tesseract OCR
  04_working/_F5M_manual_fields.tsv            hand-read values (dec_id, field, value, note); value '-' blanks a field
  04_working/_F5M_visual_checks.tsv            crops opened with Read (dec_id, field, value, crop, result, note)
  04_working/_F5M_cgiar.tsv                    CGIAR element per decision (dec_id, lineage, role, center, quote, note)
  04_working/_F5M_anchor_overrides.tsv         dec_id, stem, page, find   (when the automatic anchor is wrong)
Outputs
  05_output/final/bgd_nsb_decisions_full.csv, 04_working/evidence_F5M.csv,
  03_extracted/text/F5M/review/*.md (reading aid), 04_working/_F5M_crop_queue.tsv (numbers still to check)"""
import csv, json, re, sys, pathlib
from collections import Counter, defaultdict
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import phase3_F5M_items as IT
from phase3_F5M_fields import extract, sentences, lat
from lib_names import variety_name

ROOT = pathlib.Path(__file__).resolve().parents[1]
W = ROOT / "04_working"; T = ROOT / "03_extracted/text/F5M"; OCRD = ROOT / "03_extracted/text/ocr"
OUT = ROOT / "05_output/final/bgd_nsb_decisions_full.csv"
csv.field_size_limit(10 ** 9)
OTHER_CROP = re.compile(r"আলু|গম|পাট|আখ|ইক্ষু|ভুট্টা|সরিষা|তুলা|potato|wheat|jute|maize|sugarcane|mustard")


def tsv(path):
    if not path.exists():
        return []
    rows = []
    with open(path, encoding="utf-8") as f:
        hdr = f.readline().rstrip("\n").split("\t")
        for l in f:
            if not l.strip() or l.startswith("#"):
                continue
            v = l.rstrip("\n").split("\t"); v += [""] * (len(hdr) - len(v))
            rows.append(dict(zip(hdr, [x.strip() for x in v])))
    return rows


# ---------------------------------------------------------------- raw text, line-parallel to IT.pages()
_RAW = {}


def raw_lines(stem):
    if stem in _RAW:
        return _RAW[stem]
    P = IT.pages(stem)
    if stem == "nsb_minutes_058-075":
        rl = [l for l in (T / f"{stem}.raw.txt").read_text(encoding="utf-8").splitlines() if not l.startswith("=== page")]
    else:
        rl = [None] * len(P)       # psm6 pages: the text line IS the raw line unless the page has a table
    _RAW[stem] = rl
    return rl


_TABPAGES = {}


def table_pages(stem):
    if stem not in _TABPAGES:
        g = T / "grid" / f"{stem}.json"
        _TABPAGES[stem] = {int(k[1:4]) for k, v in json.loads(g.read_text()).items() if v} if g.exists() else set()
        sp = T / f"{stem}.splitpages.json"
        if sp.exists():
            _TABPAGES[stem] |= set(json.loads(sp.read_text()))
    return _TABPAGES[stem]


def _yrange(stem, s, e):
    """per page: (ymin, ymax) of the item's lines (300-dpi px) from the .lines.json metadata"""
    P = IT.pages(stem)
    R = {}
    for i in range(s, e):
        m = P[i][2]
        if m and m.get("bbox"):
            b = m["bbox"]
            t, btm = (b[0], b[2]) if m.get("kind") in ("psm6", "split", "cell") else (b[1], b[3])
            pg = P[i][0]
            lo, hi = R.get(pg, (10 ** 9, -1))
            R[pg] = (min(lo, t), max(hi, btm))
    return R


def raw_text(stem, s, e):
    P = IT.pages(stem)
    if stem == "nsb_minutes_058-075":
        rl = raw_lines(stem)
        out, pg = [], None
        for i in range(s, e):
            if P[i][0] != pg:
                pg = P[i][0]; out.append(f"[p.{pg}]")
            out.append(rl[i])
        return "\n".join(out)
    tp = table_pages(stem)
    out, pg = [], None
    done = set()
    for i in range(s, e):
        p = P[i][0]
        if p in tp:
            if p not in done:
                done.add(p)
                yr = _yrange(stem, s, e).get(p)
                import phase3_F5M_text as TX
                tl = TX.tsv_lines(OCRD / stem / f"p{p:03d}_psm6.tsv")
                if yr:
                    tl = [t for t in tl if yr[0] - 15 <= (t[0] + t[2]) / 2 <= yr[1] + 15]
                out.append(f"[p.{p} — Tesseract psm6 OCR lines, unmodified, of the part of the page this item occupies; the page is a two-column table and psm6 interleaves the columns]")
                out.append(chr(10).join(t[4] for t in tl))
            continue
        if p != pg:
            pg = p; out.append(f"[p.{p}]")
        out.append(P[i][1])
    return "\n".join(out)


# ---------------------------------------------------------------- cleaning (line-break noise only)
NOISE = re.compile(r"^[\W_]{0,4}$|^[\W]*[০-৯0-9]{1,3}[\W]*$|C:\\Users|\.doc\b|^\W*(?:[a-zA-Z]{1,3}\W*){1,3}$")


def clean_lines(lines):
    """lines: list of str (one agenda item). Joins wrapped lines into paragraphs, drops page numbers / file-path
    footers / stray 1-3 character OCR specks, turns a sentence-final '|' (OCR for '।') into '।'. Nothing else."""
    paras, cur = [], []
    for u in lines:
        if u.startswith("[কলাম"):
            if cur:
                paras.append(cur); cur = []
            cur.append(u); continue
        if not u.strip():
            if cur:
                paras.append(cur); cur = []
            continue
        if NOISE.search(u.strip()) and not re.search(r"[A-Z]{2,}\d|\d{3,}", u):
            continue
        u = re.sub(r"^[|'!:;,.\"“”‘’`~_\-–—\s]{1,4}(?=\S)", "", u.strip())
        u = re.sub(r"\s*\|\s*$", "।", u)
        u = re.sub(r"\s+\|\s+(?=[\u0980-\u09FF])", "। ", u) if "¦" not in u else u
        if IT.ENUM.match(u) and cur:
            paras.append(cur); cur = []
        cur.append(u)
    if cur:
        paras.append(cur)
    out = []
    for p in paras:
        s = ""
        for u in p:
            if not s:
                s = u
            elif s.endswith("-") and re.match(r"^[A-Za-z0-9০-৯(]", u):
                s += u
            elif s.startswith("[কলাম") and s.endswith("]"):
                s += " " + u
            else:
                s += " " + u
        out.append(re.sub(r"[ \t]+", " ", s).strip())
    return "\n\n".join(x for x in out if x)


# ---------------------------------------------------------------- Latin runs garbled by bijoy2unicode in F3M's report-5 names
_GM = None


def ungarble(v):
    """F3M took report-5 names from the P2A unicode file, where Latin-font codes were run through bijoy2unicode
    ('QDR 3' -> 'ছউজ ৩'). Restore them font-aware from the PDF's own Latin spans (as phase3_fix_bijoy_latin.py)."""
    global _GM
    if _GM is None:
        import fitz
        from bijoy2unicode import converter
        C = converter.Unicode()
        _GM, amb = {}, set()
        for page in fitz.open(ROOT / "02_raw/sca/nsb_minutes_058-075.pdf"):
            for blk in page.get_text("dict")["blocks"]:
                for ln in blk.get("lines", []):
                    for sp in ln["spans"]:
                        if "Sutonny" in sp["font"] or not re.search(r"[A-Za-z]", sp["text"]):
                            continue
                        for tok in re.findall(r"[A-Za-z0-9][A-Za-z0-9\-/. ]*[A-Za-z0-9]|[A-Za-z]+", sp["text"]):
                            try:
                                g = C.convertBijoyToUnicode(tok + "  ").strip()
                            except Exception:
                                continue
                            if g and g != tok and len(g) >= 2 and re.search(r"[A-Za-z]", tok):
                                if g in _GM and _GM[g] != tok:
                                    amb.add(g)
                                _GM.setdefault(g, tok)
        for g in amb:
            _GM.pop(g, None)
    for g in sorted(_GM, key=len, reverse=True):
        if g in v:
            v = v.replace(g, _GM[g])
    return v


# ---------------------------------------------------------------- variety tokens
DIG = {str(i): f"[{i}{'০১২৩৪৫৬৭৮৯'[i]}{'8' if i == 4 else ''}]" for i in range(10)}
for k, v in zip("০১২৩৪৫৬৭৮৯", "0123456789"):
    DIG[k] = DIG[v]


def drx(digs):
    return "".join(DIG.get(c, re.escape(c)) for c in digs)


def tokens(d, strict=True):
    """strict (REV3): a hybrid name keeps its brand word; the loose form (anchoring only) also accepts 'ধান২০' alone."""
    rx = []
    for f in ("breeding_line_raw", "variety_raw", "key_name_hint"):
        v = IT.norm(d.get(f, ""))
        for part in re.split(r"[();/,]|\bproposed\b", v):
            part = part.strip()
            runs = re.findall(r"[0-9০-৯]+", part)
            if not runs:
                continue
            letters = re.findall(r"[A-Za-z]{2,}", part)
            if len(runs) >= 2 and sum(len(r) for r in runs) >= 4:
                rx.append(r"(?<![0-9০-৯])" + r"\D{1,8}".join(drx(r) for r in runs[:4]) + r"(?![0-9০-৯])")
            big = max(runs, key=len)
            if len(big) >= 3:
                pre = re.escape(letters[0]) + r"\W{0,3}" if letters and part.find(letters[0]) < part.find(big) else ""
                rx.append(pre + r"(?<![0-9০-৯])" + drx(big) + r"(?![0-9০-৯])")
            words = re.findall(r"[\u0980-\u09FF]+|[A-Za-z]+", re.sub(r"[0-9০-৯]+", " ", part))
            if words and len(big) <= 3:
                w = [x for x in words if x not in ("ও", "এবং")]
                # REV3: 'হাইব্রিড ধান-৩' alone also matches another firm's 'ব্যাবিলন হাইব্রিড ধান-৩'; a hybrid name keeps its brand word
                hyb = any(re.fullmatch(r"হাইব্রিড|hybrid", x, re.I) for x in w[-2:])
                w = w[-3:] if hyb and strict and len(w) >= 3 else w[-2:]
                if w and hyb and strict:
                    # OCR spellings: হাইবিড / হাইব্রেড for হাইব্রিড, a dropped র-phala (বি for ব্রি)
                    fz = lambda x: (r"(?:হাই\S{0,4}ড|hybrid)" if re.fullmatch(r"হাইব্রিড|hybrid", x, re.I)
                                    else re.escape(x).replace("্র", "(?:্র)?"))
                    rx.append(r"\s*-?\s*".join(fz(x) for x in w) + r"\s*-?\s*" + drx(big) + r"(?![0-9০-৯])")
                elif w:
                    rx.append(r"\s*-?\s*".join(re.escape(x) for x in w) + r"\s*-?\s*" + drx(big) + r"(?![0-9০-৯])")
                    if not hyb or not strict:
                        rx.append(re.escape(w[-1]) + r"\s*-?\s*" + drx(big) + r"(?![0-9০-৯])")
    seen = []
    for r in rx:
        if r not in seen:
            seen.append(r)
    return [re.compile(r, re.I) for r in seen]


# ---------------------------------------------------------------- main
FIELDS = ["breeding_line", "pedigree_cross", "pedigree_statements", "hybrid_parent_female_A_line", "hybrid_maintainer_B_line",
          "hybrid_parent_male_R_line", "hybrid_parent_statements", "germplasm_source", "origin_country", "origin_statements",
          "developer_applicant", "season", "region_scope", "region_text", "dus_result", "dus_statements", "dus_years",
          "dus_distinct_traits_n", "dus_check_variety", "vcu_statements", "vcu_regions_n", "vcu_sites_n", "vcu_trial_type",
          "check_variety", "yield_t_ha", "yield_advantage_pct", "yield_statements", "duration_days", "duration_statements",
          "special_traits_official", "identifying_traits_official", "grain_type", "grain_quality_statements", "amylose_pct",
          "lb_ratio", "grain_wt_1000_g", "protein_pct", "zinc_mg_kg", "iron_mg_kg", "stress_tolerance",
          "tc_recommendation_text", "decision_text", "decision_conditions", "import_period", "provisional_years",
          "label_requirements", "cgiar_mentions", "cgiar_lineage", "cgiar_role", "cgiar_center", "cgiar_quote"]
NUMERIC = ["yield_t_ha", "yield_advantage_pct", "duration_days", "dus_distinct_traits_n", "dus_years", "vcu_regions_n",
           "vcu_sites_n", "amylose_pct", "lb_ratio", "grain_wt_1000_g", "protein_pct", "zinc_mg_kg", "iron_mg_kg", "provisional_years"]


LABEL_WORD = r"(?:সি(?:দ্ধ|ন্ধ|দ্দ|দ্ব)ান্ত|সদ্ধান্ত)"
DEC_LABEL = re.compile(r"^\W{0,3}(" + LABEL_WORD + r"|\[কলাম ২\])")
ENUM = re.compile(r"^\W{0,3}\(?([ক-হ]{1,2}|[০-৯0-9]{1,2})(?:\)|।|\.(?![0-9০-৯]))")
NON_VARIETY = re.compile(r"নননোটিফাইড|নন-নোটিফাইড|বীজমান|মাঠমান|Seed Standard|Field Standard")
DEC_VERB = re.compile(r"(?:করা|দেয়া|দেওয়া|দেয়া)\s*হ(?:লো|ল(?!ে)|য়েছে|য়েছে)|গৃহীত\s*হ(?:লো|ল(?!ে))")
DISCUSSION = re.compile(r"সুপারিশ\s*কর(?:েছে|েন|া হয়)|আলোচনা|প্রস্তাব\s*কর")


NEXT_ITEM = re.compile(r"\s(?:আলোচ্য\s*(?:সূচী|সূচি|বিষয়|বিষয়)\s*[-–:]?\s*\S{1,4}\s*[:ঃ।]|সভায় আর কোন\S* আলোচ্য)")


def cut_next_item(t):
    """A paragraph that OCR ran on into the next agenda heading (or the closing sentence) is cut there."""
    m = NEXT_ITEM.search(t)
    return t[:m.start()].rstrip() if m and m.start() > 0 else t


def is_dec_label(p):
    return bool(DEC_LABEL.match(p)) or bool(re.search(LABEL_WORD, p[:25]))


def scoped_decisions(paras, tks, rice_only):
    """REV3 (round-2 review V2-08): the decision text of one variety, taken only from its own part of the agenda item.

    An agenda item can hold several sub-items ((১) seed standards of 74 crops, (২) a potato variety, (৩) hybrid rice ...),
    each with its own 'সিদ্ধান্ত' paragraph, so a decision that does not name the variety must not be borrowed from
    another sub-item. Paragraphs are grouped into decision blocks: a 'সিদ্ধান্ত' paragraph plus the enumerated clauses that
    follow it ((১), (২) ... or (ক), (খ) ...; one marker class per block) when the label is bare or ends with a colon, or only
    lettered continuation clauses from (খ) on after a label that already states a decision. In order:
    1. blocks that name the variety: the label (when bare or introducing a list) and the clauses naming the variety;
    2. the variety's own paragraph when it states the decision inline ('... নিবন্ধনের জন্য ছাড়করণ করা হলো'), not a
       discussion or recommendation;
    3. the first decision block after the variety's first paragraph, if no new agenda heading intervenes and the block
       names no other crop and is not about seed standards (a generic decision such as 'the 13 varieties are registered');
    4. otherwise blank."""
    cur, cls, blocks, inblock = None, None, [], set()
    for i, p in enumerate(paras):
        m = ENUM.match(p)
        if is_dec_label(p):
            rest = re.sub(r"^\W{0,3}(\[কলাম ২\]\s*)?" + LABEL_WORD + r"\S*\s*[:ঃ§]?", "", p).strip()
            rest = re.sub(r"^-?\s*[০-৯0-9]+\s*তম সভার কার্যবিবরণী\s*", "", rest)     # running page header merged by OCR
            bare = len(rest) < 15
            lst = bare or bool(re.search(r"[:ঃ]\s*[-–]?\s*$", rest))
            cur = {"label": i, "bare": bare, "list": lst, "paras": [i]}; cls = None
            blocks.append(cur); inblock.add(i)
            continue
        if cur is not None and m:
            c = "digit" if re.match(r"[০-৯0-9]", m.group(1)) else "letter"
            ok = (cls is None or c == cls) and (cur["list"] or (c == "letter" and m.group(1) != "ক"))
            if ok:
                cls = c; cur["paras"].append(i); inblock.add(i)
                continue
        cur = None
    names = lambda p: any(t.search(p) for t in tks)
    out = []
    for b in blocks:
        hit = [i for i in b["paras"] if names(paras[i])]
        if hit:
            keep = ([b["label"]] if b["label"] not in hit and b["list"] else []) + hit
            out += [q for q in (rice_only(paras[i]) for i in keep) if q.strip()]
    if out:
        return out
    own = [i for i, p in enumerate(paras) if names(p) and i not in inblock]
    for i in own:
        p = paras[i]
        if DEC_VERB.search(p) and not DISCUSSION.search(p) and not OTHER_CROP.search(p):
            out.append(p)
    if out:
        return out
    first = own[0] if own else None
    cand = [b for b in blocks if first is not None and b["label"] > first] if first is not None else (blocks if len(blocks) == 1 else [])
    for b in cand[:1]:
        if first is not None and any(re.match(r"^\W{0,3}আলোচ্য", paras[j]) for j in range(first + 1, b["label"])):
            break
        txt = "\n\n".join(paras[i] for i in b["paras"])
        if not OTHER_CROP.search(txt) and not NON_VARIETY.search(txt) and not (b["bare"] and len(b["paras"]) == 1):
            out.append(txt)
    return out


def main():
    IX = list(csv.DictReader(open(W / "F3M_decisions_index.csv", encoding="utf-8")))
    MD = {d["meeting_no"]: (d["meeting_date"], d["date_validation"]) for d in IX}
    for a in tsv(W / "_F5M_additions.tsv"):
        a["meeting_date"], a["date_validation"] = MD.get(a["meeting_no"], (a.get("meeting_date", ""), a.get("date_validation", "")))
        IX.append(a)
    # REV2 (2026-11-10): decision rows F3M could not key, linked by hand in 04_working/_F5M_key_overrides.tsv (dec_id, key,
    # note). A key list 'A;B' splits a decision that covers several register varieties (the generic 'Iratom' approval at
    # NSB 4) into one row per variety: the first keeps the dec_id, the others get dec_id + 'b', 'c', ...
    KO = {k["dec_id"]: k for k in tsv(W / "_F5M_key_overrides.tsv")}
    CLONE = {}
    for d in list(IX):
        if d["dec_id"] in KO:
            keys = [x.strip() for x in KO[d["dec_id"]]["key"].split(";") if x.strip()]
            note = KO[d["dec_id"]].get("note", "")
            d["pilot_key"] = keys[0]
            d["key_note"] = "; ".join(x for x in [d.get("key_note", ""), "linked by hand (REV2): " + note] if x)
            for j, k2 in enumerate(keys[1:]):
                c = dict(d); c["dec_id"] = d["dec_id"] + "bcdefgh"[j]; c["pilot_key"] = k2
                CLONE[c["dec_id"]] = d["dec_id"]; IX.append(c)
    for d in IX:
        if "058-075" in d["local_file"]:
            for f in ("variety_raw", "breeding_line_raw"):
                if d.get(f):
                    d[f] = ungarble(d[f])
    MAN = {m["id"]: m for m in tsv(W / "_F3M_decisions_manual.tsv")}
    for a in tsv(W / "_F5M_additions.tsv"):
        MAN[a["dec_id"]] = {"id": a["dec_id"], "find": a.get("find", ""), "src": ""}
    for cid, orig in CLONE.items():
        if orig in MAN:
            MAN[cid] = dict(MAN[orig], id=cid)
    AOV = {a["dec_id"]: a for a in tsv(W / "_F5M_anchor_overrides.tsv")}
    for cid, orig in CLONE.items():
        if orig in AOV:
            AOV[cid] = dict(AOV[orig], dec_id=cid)
    MF = defaultdict(dict)
    for m in tsv(W / "_F5M_manual_fields.tsv"):
        MF[m["dec_id"]][m["field"]] = (m["value"], m.get("note", ""))
    VC = defaultdict(dict)
    for v in tsv(W / "_F5M_visual_checks.tsv"):
        VC[v["dec_id"]][v["field"]] = v
    CGX = {c["dec_id"]: c for c in tsv(W / "_F5M_cgiar.tsv")}
    REMAP = {r["old_key"]: r["new_key"] for r in csv.DictReader(open(W / "key_remap.csv", encoding="utf-8"))}
    XW = {r["key"]: r for r in csv.DictReader(open(W / "hybrid_key_crosswalk.csv", encoding="utf-8"))}
    MANI = {r["file_path"]: r["source_url"] for r in csv.DictReader(open(ROOT / "02_raw/manifest.csv", encoding="utf-8"))}
    MK = defaultdict(set)
    for r in csv.DictReader(open(W / "nsb_meeting_key.csv", encoding="utf-8")):
        if r["validation"] in ("visual_check", "two_source") and r["kind"].startswith("minutes"):
            MK[int(r["meeting_no"])].add(r["meeting_date"])

    # 1. anchors and items
    loc = {}
    for d in IX:
        did = d["dec_id"]
        stem = pathlib.Path(d["local_file"]).stem
        m = MAN.get(did, {})
        page = int(d.get("page") or 1)
        find = m.get("find", "")
        if did in AOV:
            stem = AOV[did].get("stem") or stem; page = int(AOV[did].get("page") or page); find = AOV[did].get("find") or find
        alt = []
        for f in ("breeding_line_raw", "variety_raw"):
            for part in re.split(r"[();/,]|\s-\s", d.get(f, "")):
                part = part.strip()
                if len(part) >= 4 and re.search(r"[0-9০-৯]", part) and not re.search(r"proposed|varieties|names", part):
                    alt.append(part)
        if not (T / f"{stem}.txt").exists():
            loc[did] = dict(stem=stem, found="no_text", page=page)
            continue
        i, how = IT.locate(stem, page, find, alt)
        if i is None:
            for tk in tokens(d, strict=False):
                P = IT.pages(stem)
                cand = [j for j, (pg, u, mm) in enumerate(P) if abs(pg - page) <= 2 and tk.search(u)]
                if cand:
                    i, how = cand[0], "token"; break
        src = m.get("src") or ""
        if i is None:
            loc[did] = dict(stem=stem, found="not_found", page=page)
            continue
        s, e, kind = IT.item_bounds(src or ("B" if "-" in stem else "S"), stem, i)
        loc[did] = dict(stem=stem, found=how, anchor=i, s=s, e=e, kind=kind)
    TOK = {d["dec_id"]: tokens(d) for d in IX}
    items = defaultdict(list)
    for did, L in loc.items():
        if "s" in L:
            items[(L["stem"], L["s"])].append(did)

    rows, ev, queue = [], [], []
    review = defaultdict(list)
    for d in IX:
        did = d["dec_id"]; L = loc[did]; stem = L["stem"]
        key = d.get("pilot_key", "") or ""
        key2 = REMAP.get(key, key)
        code = XW.get(key2, {}).get("code", "")
        vid = f"RICE-{key2}" if key2 and key2 != "UNMATCHED" else ""
        lf = f"02_raw/sca/{stem}.pdf"
        row = {"dec_id": did, "variety_id": vid, "pilot_key": key2, "variety_name": variety_name(key2, code) if vid else "",
               "variety_name_as_printed": d.get("variety_raw", ""), "meeting_no": d.get("meeting_no", ""),
               "meeting_date": d.get("meeting_date", ""), "meeting_date_validation": d.get("date_validation", ""),
               "agenda_item": d.get("agenda_item", ""), "decision_type": d.get("decision_type", ""),
               "source_id": d.get("source_id", ""), "source_file": lf, "source_url": MANI.get(lf, ""),
               "f3m_notes": d.get("notes", ""), "breeding_line_validation": d.get("line_validation", "")}
        txt_source = "text_layer" if stem == "nsb_minutes_058-075" else "ocr"
        if "s" not in L:
            row.update({"pages": str(L.get("page", "")), "text_source": "", "anchor_status": "not_found"})
            for f in FIELDS:
                row[f] = ""
            rows.append(row)
            continue
        P = IT.pages(stem)
        s, e = L["s"], L["e"]
        lines = [P[j][1] for j in range(s, e)]
        p0, p1 = P[s][0], P[e - 1][0]
        tp = table_pages(stem)
        if txt_source == "ocr" and any(p in tp for p in range(p0, p1 + 1)):
            txt_source = "ocr_columns"     # ruled table: psm6 words re-assigned to table columns/cells (cell re-OCR where cached)
        item_clean = clean_lines(lines)
        heading = clean_lines(lines[:3]).split("\n\n")[0][:400]
        # variety passage
        sib = items[(stem, s)]
        tks = tokens(d)
        if len(sib) == 1 and len(item_clean) <= 2500:
            passage = item_clean
        else:
            paras = item_clean.split("\n\n")
            hit = [p for p in paras if any(t.search(p) for t in tks)]
            out = []
            for p in hit:
                if len(p) > 1500 or "¦" in p:
                    # long table/paragraph: keep only the sentences / table rows that name this variety (+ next row)
                    segs = re.split(r"(?<=।)\s+|(?<=\S)\s(?=[^\s¦]+(?:\s+[^\s¦]+){0,3}\s¦)", p) if "¦" in p else re.split(r"(?<=।)\s+", p)
                    for k, sg in enumerate(segs):
                        if any(t.search(sg) for t in tks):
                            out.append(sg + (" " + segs[k + 1] if "¦" in p and k + 1 < len(segs) else ""))
                else:
                    out.append(p)
            passage = "\n\n".join(dict.fromkeys(out))
        dec_paras = [p for p in item_clean.split("\n\n") if re.match(r"^\W{0,3}(সিদ্ধান্ত|সিদ্ধান্তঃ|\[কলাম ২\])", p) or "সিদ্ধান্ত" in p[:25]]
        def rice_only(p):
            """A decision paragraph that also disposes of other crops (potato, jute...) in the same agenda item is cut
            down to the sentences about this variety: from each sentence naming it, through following sentences that
            name no other crop and start no new sub-item."""
            if not OTHER_CROP.search(p):
                return p
            keep, on = [], False
            for s in re.split(r"(?<=।)\s+", p):
                if any(t.search(s) for t in tks):
                    on = True; keep.append(s)
                elif on and not OTHER_CROP.search(s) and not re.match(r"^\W{0,3}\(?[ক-হ০-৯0-9]{1,3}\)", s):
                    keep.append(s)
                else:
                    on = False
            return " ".join(keep)
        dec_var = [q for q in (cut_next_item(x) for x in scoped_decisions(item_clean.split("\n\n"), tks, rice_only)) if q.strip()]
        row.update({"pages": f"{p0}" if p0 == p1 else f"{p0}-{p1}", "text_source": txt_source, "anchor_status": L["found"],
                    "agenda_heading_verbatim": heading, "item_text_verbatim": item_clean, "variety_passage_verbatim": passage,
                    "raw_text": raw_text(stem, s, e), "n_decisions_in_item": len(sib)})
        if not passage.strip():
            # fall back to the paragraph that holds the anchor line (F3M's find regex)
            par = [pp for pp in IT.paragraphs([(j, P[j][1]) for j in range(s, e)]) if any(j == L["anchor"] for j, u in pp)]
            if par:
                passage = clean_lines([u for j, u in par[0]])
                row["anchor_status"] += "; passage=anchor_paragraph"
                row["variety_passage_verbatim"] = passage
        if not passage.strip():
            row["anchor_status"] += "; passage_not_isolated"
        # variety segment: in a multi-variety passage keep only the sentences from the first mention of this
        # variety up to the next sentence naming a sibling variety (or the next enumerated sub-item)
        seg_txt = passage
        if len(sib) > 1 and passage.strip():
            own = tks
            oth = [t for sd in sib if sd != did for t in TOK.get(sd, [])]
            seg, on = [], False
            for sn in sentences(passage):
                mo = any(t.search(sn) for t in own)
                mx = any(t.search(sn) for t in oth)
                if mo and not (mx and on and not seg):
                    on = True
                elif on and (mx or re.match(r"^\W{0,2}\(?[০-৯0-9]{1,2}\)|^\W{0,2}[০-৯0-9]{1,2}\s*[.।]", sn)):
                    on = False
                if on:
                    seg.append(sn)
            if seg:
                seg_txt = " ".join(seg)
        row["variety_segment_verbatim"] = seg_txt if seg_txt != passage else ""
        ex = extract(seg_txt) if seg_txt.strip() else {}
        if len(sib) > 1:
            # shared multi-variety passage: keep an auto-extracted value only when every source sentence names this
            # variety and no sibling variety (otherwise the value may belong to another decision of the same item)
            oth = [t for sd in sib if sd != did for t in TOK.get(sd, [])]
            keep = {}
            for k2, (v2, sx) in ex.items():
                parts = [p for p in sx.split(" ‖ ") if p]
                if parts and all(any(t.search(p) for t in tks) and not any(t.search(p) for t in oth) for p in parts):
                    keep[k2] = (v2, sx)
            ex = keep
        exi = extract(item_clean)
        vals, srcs = {}, {}
        for f in FIELDS:
            vals[f] = ""
        for k, (v, sx) in ex.items():
            vals[k] = v; srcs[k] = sx
        for k in ("decision_conditions", "tc_recommendation_text"):
            if not vals.get(k) and k in exi:
                vals[k], srcs[k] = exi[k]
        vals["decision_text"] = "\n\n".join(dec_var)
        vals["breeding_line"] = d.get("breeding_line_raw", "")
        vals["developer_applicant"] = d.get("developer", "")
        m = re.search(r"((?:[^\s।¦]+\s){1,8}?)(?:কর্তৃক|কতৃক|কর্তক)\s*(?:প্রস্তাবিত|উদ্ভাবিত|উত্তাবিত|আমদানিকৃত)", passage)
        if m:
            vals["developer_applicant"] = (vals["developer_applicant"] + " | as printed: " if vals["developer_applicant"] else "as printed: ") + m.group(1).strip()
        vals["season"] = d.get("season", "")
        vals["region_scope"] = d.get("region_scope", "")
        rt = [x for x in sentences("\n".join(dec_var) or passage) if re.search(r"সারা\s*দেশ|সারাদেশ|অঞ্চল|এলাকায়|জেলা", x)]
        vals["region_text"] = " ‖ ".join(rt)
        pr = d.get("pedigree_raw", "")
        if re.search(r"^from |origin|own development|imported|in-house|developed by|collected from", pr, re.I) and not re.search(r"\bx\b|×|/", pr):
            if not vals.get("germplasm_source"):
                vals["germplasm_source"] = "F3M (minutes): " + pr
            oc = {"chinese": "China", "china": "China", "indian": "India", "india": "India", "own development": "Bangladesh",
                  "in-house": "Bangladesh", "philippin": "Philippines", "vietnam": "Vietnam", "pakistan": "Pakistan"}
            hit = [v for k2, v in oc.items() if k2 in pr.lower()]
            if hit:
                vals["origin_country"] = hit[0]
            pr = ""
        vals["pedigree_cross"] = pr
        cond = vals.get("decision_conditions", "")
        ip = [x for x in sentences(cond) if re.search(r"আমদানি|আমদানী", x)]
        vals["import_period"] = " ‖ ".join(ip)
        m = re.search(r"([০-৯0-9]+)\s*(?:\(\S+\)\s*)?বছর(?:ের)?\s*(?:মেয়াদ|মেয়াদ|জন্য\s*সাময়িক|সাময়িক)", cond + " " + "\n".join(dec_var))
        vals["provisional_years"] = lat(m.group(1)) if m else ""
        lb = [x for x in sentences(cond + " " + item_clean) if re.search(r"প্যাকেট|লেবেল|মোড়ক|ট্যাগ", x)]
        vals["label_requirements"] = " ‖ ".join(dict.fromkeys(lb))
        dus = vals.get("dus_statements", "")
        if dus:
            vals["dus_result"] = dus
            m = re.search(r"([০-৯0-9]+)\s*(?:\(\S+\)\s*)?(?:বছর|মৌসুম)", dus)
            vals["dus_years"] = lat(m.group(1)) if m else ""
        vals["germplasm_source"] = vals.get("origin_statements", "")
        cg = CGX.get(did)
        if cg:
            vals["cgiar_lineage"], vals["cgiar_role"], vals["cgiar_center"], vals["cgiar_quote"] = cg["lineage"], cg["role"], cg["center"], cg["quote"]
        # manual overrides
        for f, (v, note) in MF.get(did, {}).items():
            vals[f] = "" if v == "-" else v
            srcs[f] = "manual: " + note
        # validation of numeric fields
        for f in NUMERIC:
            v = vals.get(f, "")
            if not v:
                row[f"val_{f}"] = ""
                continue
            vc = VC.get(did, {}).get(f)
            mfn = MF.get(did, {}).get(f, ("", ""))[1]
            if f in MF.get(did, {}) and mfn.startswith("visual:"):
                row[f"val_{f}"] = "visual_check"
            elif vc and vc["result"] == "ok":
                row[f"val_{f}"] = "visual_check"
            elif vc and vc["result"] == "corrected":
                vals[f] = vc["value"]; row[f"val_{f}"] = "visual_check"
            elif txt_source == "text_layer" and d.get("date_validation") == "key_check":
                row[f"val_{f}"] = "key_check"
            else:
                row[f"val_{f}"] = "unvalidated"
                queue.append((did, f, v, stem, p0, p1, srcs.get(f, "")[:300]))
        row["manual_field_sources"] = " | ".join(f"{f}: {n}" for f, (v, n) in MF.get(did, {}).items())
        row.update(vals)
        rows.append(row)
        review[stem].append((row, ex))

    # 2. write the main CSV
    front = ["dec_id", "variety_id", "variety_name", "pilot_key", "variety_name_as_printed", "meeting_no", "meeting_date",
             "meeting_date_validation", "agenda_item", "agenda_heading_verbatim", "decision_type", "source_id", "source_file",
             "pages", "source_url", "text_source", "anchor_status", "n_decisions_in_item"]
    texts = ["variety_passage_verbatim", "variety_segment_verbatim", "item_text_verbatim", "raw_text"]
    cols = front + FIELDS + [f"val_{f}" for f in NUMERIC] + ["breeding_line_validation", "manual_field_sources", "f3m_notes"] + texts
    OUT.parent.mkdir(parents=True, exist_ok=True)
    ren = lambda c: c.replace("yield_advantage_pct", "yield_criterion_pct")   # REV2 v1.2: a criterion, not a measured gain
    with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[ren(c) for c in cols], extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({ren(c): r.get(c, "") for c in cols})
    with open(W / "_F5M_crop_queue.tsv", "w", encoding="utf-8") as f:
        f.write("dec_id\tfield\tvalue\tstem\tp0\tp1\tsource_sentence\n")
        for q in queue:
            f.write("\t".join(str(x).replace("\t", " ").replace("\n", " ") for x in q) + "\n")
    # 3. review dumps
    R = T / "review"; R.mkdir(exist_ok=True)
    for stem, lst in review.items():
        with open(R / f"{stem}.md", "w", encoding="utf-8") as f:
            for row, ex in lst:
                f.write(f"\n\n######## {row['dec_id']} | NSB {row['meeting_no']} | p{row['pages']} | {row['decision_type']} | {row['variety_name_as_printed']} | {row['pilot_key']} | anchor={row['anchor_status']} | n_in_item={row['n_decisions_in_item']}\n")
                f.write("PASSAGE:\n" + row["variety_passage_verbatim"] + "\n")
                for k in FIELDS:
                    if row.get(k) and k not in ("decision_text",):
                        f.write(f"  - {k}: {str(row[k])[:600]}\n")
    # 4. evidence
    write_evidence(rows)
    st = Counter(r.get("anchor_status") for r in rows)
    print(len(rows), "rows;", dict(st))
    print("queue (unvalidated numbers):", len(queue))
    cov = {f: sum(1 for r in rows if r.get(f)) for f in FIELDS}
    print(cov)


EVF = {"breeding_line": "breeding_line", "pedigree_cross": "pedigree", "pedigree_statements": "pedigree",
       "hybrid_parent_female_A_line": "hybrid_parent_female", "hybrid_parent_male_R_line": "hybrid_parent_male",
       "hybrid_maintainer_B_line": "hybrid_parent_maintainer", "origin_country": "origin_country", "check_variety": "check_variety",
       "yield_t_ha": "yield_t_ha", "yield_advantage_pct": "yield_advantage_pct", "duration_days": "duration_days",
       "special_traits_official": "special_traits_official", "identifying_traits_official": "identifying_traits_official",
       "dus_result": "dus_result", "vcu_sites_n": "vcu_sites", "stress_tolerance": "stress_tolerance",
       "decision_conditions": "decision_conditions"}
QUAL = ["grain_type", "amylose_pct", "lb_ratio", "grain_wt_1000_g", "protein_pct", "zinc_mg_kg", "iron_mg_kg"]
SRCT = {"nsb_minutes_001-018": "NSB activities report no.1 (minutes summaries, NSB 1st-18th meetings, 1974-1984)",
        "nsb_minutes_019-028": "NSB minutes 19th-28th meetings (1984-1992), activities report no.2",
        "nsb_minutes_029-042": "NSB minutes 29th-42nd meetings (1993-1999), activities report no.3",
        "nsb_minutes_043-057": "NSB minutes 43rd-57th meetings (2000-2005), activities report no.4 (June 2005)",
        "nsb_minutes_058-075": "NSB minutes 58th-75th meetings (2005-2011), activities report no.5 (Nov 2011)",
        "nsb_minutes_076-082": "NSB minutes 76th-83rd meetings (2012-2014), activities report no.6 (file named 076-082)"}


def write_evidence(rows):
    cols = ["pilot_key", "field", "value", "value_raw", "source_id", "source_title", "authority_rank", "local_file", "page",
            "locator", "method", "validation", "confidence", "notes"]
    out = []
    for r in rows:
        if not r.get("pilot_key") or r["pilot_key"] == "UNMATCHED" or not r.get("text_source"):
            continue
        stem = pathlib.Path(r["source_file"]).stem
        title = SRCT.get(stem, f"NSB {int(stem[-3:])}th meeting minutes (single file, sca.gov.bd)")
        method = {"text_layer": "bijoy2unicode", "ocr": "ocr", "ocr_columns": "ocr", "image_transcription": "visual_check"}[r["text_source"]]
        page = r["pages"].split("-")[0]
        loc = f"NSB {r['meeting_no']} ({r['meeting_date']}), agenda {r['agenda_item']}, {r['dec_id']}, pp.{r['pages']}"

        def add(field, value, raw, val, note=""):
            out.append({"pilot_key": r["pilot_key"], "field": field, "value": value, "value_raw": raw, "source_id": r["source_id"],
                        "source_title": title, "authority_rank": "1_primary_legal", "local_file": r["source_file"], "page": page,
                        "locator": loc, "method": method, "validation": val,
                        "confidence": "high" if val in ("visual_check", "key_check") else "medium", "notes": note})
        textval = "key_check" if (r["text_source"] == "text_layer" and r.get("meeting_date_validation") == "key_check") else "unvalidated"
        vis = {seg.split(": ", 1)[0] for seg in r.get("manual_field_sources", "").split(" | ") if ": visual:" in seg}
        for f, ef in EVF.items():
            v = r.get(f, "")
            if not v:
                continue
            val = r.get(f"val_{f}") or ("visual_check" if f in vis else textval)
            if f == "breeding_line" and r.get("breeding_line_validation") in ("visual_check", "key_check") and f not in vis:
                val = r["breeding_line_validation"]
            if f in ("pedigree_statements",) and r.get("pedigree_cross"):
                continue
            add(ef, v, v if len(v) < 2000 else v[:2000], val, f"F5M from {r['dec_id']} ({r['decision_type']}); text_source={r['text_source']}")
        q = "; ".join(f"{k}={r[k]}" for k in QUAL if r.get(k))
        if q:
            vv = [r.get(f"val_{k}") for k in QUAL if r.get(k) and k != "grain_type"]
            val = "unvalidated" if "unvalidated" in vv else (vv[0] if vv else textval)
            add("quality_traits", q, r.get("grain_quality_statements", "")[:2000], val, f"F5M from {r['dec_id']}")
        if r.get("cgiar_lineage"):
            add("cgiar_lineage", r["cgiar_lineage"], r.get("cgiar_quote", ""), "visual_check" if r["text_source"] != "text_layer" else textval, f"F5M {r['dec_id']}")
            add("cgiar_role", r["cgiar_role"], r.get("cgiar_quote", ""), "visual_check" if r["text_source"] != "text_layer" else textval, f"F5M {r['dec_id']}")
            add("cgiar_center", r["cgiar_center"], r.get("cgiar_quote", ""), "visual_check" if r["text_source"] != "text_layer" else textval, f"F5M {r['dec_id']}")
            add("cgiar_evidence", r.get("cgiar_quote", ""), r.get("cgiar_quote", ""), "visual_check" if r["text_source"] != "text_layer" else textval, f"F5M {r['dec_id']}")
    with open(W / "evidence_F5M.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(out)
    print("evidence rows:", len(out))


if __name__ == "__main__":
    main()
