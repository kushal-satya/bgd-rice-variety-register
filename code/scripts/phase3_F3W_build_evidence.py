"""F3W: build 04_working/evidence_F3W.csv from CGIAR websites saved under 02_raw (see notes_F3W.md).

Every value_raw quote is checked verbatim (whitespace/quote-normalised) against the text of local_file;
the script stops if a quote is not found. Keys: lib_keys.make_key on the variety name as printed;
manual keys only where make_key returns None and the identity is stated on the same page (see decisions_F3W.md).
"""
import csv, json, re, html, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_keys import make_key
from phase3_F3W_lib import text_of
ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "04_working/evidence_F3W.csv"
COLS = ["pilot_key", "field", "value", "value_raw", "source_id", "source_title", "authority_rank", "local_file", "page",
        "locator", "method", "validation", "confidence", "notes"]

# ---- sources: id -> (title, local_file, method, site-year label)
S = {
 "F3W-W01": ("Rice Today (IRRI), 'IRRI in Bangladesh', P. Ferrer, 9 Jan 2012", "02_raw/cgiar_web/irri/ricetoday_irri_in_bangladesh.html", "html", "IRRI Rice Today 2012"),
 "F3W-W02": ("Rice Today (IRRI), 'Bangladesh combats the white plague', 1 Jul 2011", "02_raw/cgiar_web/irri/ricetoday_white_plague.html", "html", "IRRI Rice Today 2011"),
 "F3W-W03": ("Rice Today (IRRI), 'New rice variety creates game-changing opportunities for farmers in the Haor Basin of Bangladesh', 23 Aug 2023", "02_raw/cgiar_web/irri/ricetoday_haor_new_variety.html", "html", "IRRI Rice Today 2023"),
 "F3W-W04": ("Rice Today (IRRI), 'The farmers who till the harsh coastal lands of Bangladesh and the salt-tolerant rice varieties that changed their story', 1 Aug 2023", "02_raw/cgiar_web/irri/ricetoday_coastal_salt_tolerant.html", "html", "IRRI Rice Today 2023"),
 "F3W-W05": ("Rice Today (IRRI), 'Transforming rice cultivation in the hilly regions of Bangladesh', 8 Apr 2025", "02_raw/cgiar_web/irri/ricetoday_hilly_regions.html", "html", "IRRI Rice Today 2025"),
 "F3W-W06": ("Rice Today (IRRI), head-to-head trials of Sub1 and drought-tolerant varieties in Bangladesh (?p=27298), 24 Oct 2022", "02_raw/cgiar_web/irri/ricetoday_p27298.html", "html", "IRRI Rice Today 2022"),
 "F3W-W07": ("Rice Today (IRRI), 'In retrospect: IRRI annual report 1972' (?p=23617), 12 Jun 2020", "02_raw/cgiar_web/irri/ricetoday_p23617.html", "html", "IRRI Rice Today 2020 (reprint of IRRI AR 1972)"),
 "F3W-W08": ("Rice Today (IRRI), ?p=27440 (STRASA text on BRRI dhan51), 21 Nov 2022", "02_raw/cgiar_web/irri/ricetoday_p27440.html", "html", "IRRI Rice Today 2022"),
 "F3W-W09": ("Rice Today (IRRI), 'Bangladesh Seed Board approves two new boro rice varieties', 10 Jan 2024", "02_raw/cgiar_web/irri/ricetoday_nsb_two_new_boro.html", "html", "IRRI Rice Today 2024"),
 "F3W-W10": ("IRRI news (irri.org/node/1289), 'Reducing farmers' risk through the flood-tolerant BINA Dhan-11', 31 Oct 2021", "02_raw/cgiar_web/irri/irri_node1289.html", "html", "IRRI news 2021"),
 "F3W-W11": ("IRRI news, 'IRRI and BADC organize crop cafeteria field day to evaluate suitability of rice varieties', 27 May 2025", "02_raw/cgiar_web/irri/irri_news_badc_crop_cafeteria.html", "html", "IRRI news 2025"),
 "F3W-W12": ("STRASA (strasa.irri.org) featured article 'As floodwaters recede, farmers' hopes emerge in Bangladesh', post date 5 Apr 2018", "02_raw/cgiar_web/strasa/strasa_fa_floodwaters_bangladesh.html", "html", "STRASA 2018"),
 "F3W-W13": ("STRASA (strasa.irri.org) featured article 'A successful salt-tolerant rice variety in Sreefalkathi Village', post date 24 Jun 2015", "02_raw/cgiar_web/strasa/strasa_fa_sreefalkathi_salt.html", "html", "STRASA 2015"),
 "F3W-W14": ("STRASA legacy site home page (strasa.irri.org/home), undated (project ended 2019)", "02_raw/cgiar_web/strasa/strasa_home.html", "html", "STRASA c.2019"),
 "F3W-W15": ("HarvestPlus news 'Bangladesh releases new improved zinc rice variety', 5 Aug 2015", "02_raw/cgiar_web/harvestplus/hp_new_improved_zinc_rice.html", "html", "HarvestPlus 2015"),
 "F3W-W16": ("HarvestPlus news 'Bangladesh welcomes newest zinc rice variety: BRRI dhan100', 1 Mar 2021", "02_raw/cgiar_web/harvestplus/hp_brri_dhan100.html", "html", "HarvestPlus 2021"),
 "F3W-W17": ("HarvestPlus country page Bangladesh (harvestplus.org/node/1652), accessed 2026-10-07", "02_raw/cgiar_web/harvestplus/hp_node1652.html", "html", "HarvestPlus country page (accessed 2026)"),
 "F3W-W18": ("HarvestPlus news 'Barobari Seed Bazar: the famous zinc rice market hub in Bangladesh', 22 Jan 2024", "02_raw/cgiar_web/harvestplus/hp_barobari_seed_bazar.html", "html", "HarvestPlus 2024"),
 "F3W-W19": ("CGIAR Research Program on Rice, Innovation #1945 'Promising lines were released for irrigated lowland conditions in Bangladesh' (Rice Annual Report 2020), CGSpace 10568/122323", "02_raw/cgiar_lit/crp_rice_innovation_IN1945.pdf", "pdf_text", "CGIAR CRP Rice innovation record 2020"),
 "F3W-W20": ("CGIAR A4NH Innovation #2629 'BRRI dhan 100: A new zinc biofortified rice variety released in Bangladesh' (A4NH AR 2021), CGSpace 10568/122813", "02_raw/cgiar_lit/a4nh_innovation_IN2629_brri_dhan100.pdf", "pdf_text", "CGIAR A4NH innovation record 2021"),
 "F3W-W21": ("CGIAR A4NH Innovation #117 'Zinc Rice: BRRI Dhan84' (A4NH AR 2017), CGSpace 10568/123131", "02_raw/cgiar_web/cgspace/10568_123131__ProjectInnovationSummary-A4NH-P333-I117.pdf", "pdf_text", "CGIAR A4NH innovation record 2017"),
 "F3W-W22": ("CGIAR A4NH Innovation #92 'Zinc Rice: Binadhan 20' (A4NH AR 2017), CGSpace 10568/122930", "02_raw/cgiar_web/cgspace/10568_122930__ProjectInnovationSummary-A4NH-P333-I92.pdf", "pdf_text", "CGIAR A4NH innovation record 2017"),
 "F3W-W23": ("CGIAR Research Program on Rice, Innovation #650 'Flood-tolerant rice varieties for Bangladesh (sub1)' (Rice AR 2018), CGSpace 10568/122434", "02_raw/cgiar_web/cgspace/10568_122434__ProjectInnovationSummary-Rice-P1573-I650.pdf", "pdf_text", "CGIAR CRP Rice innovation record 2018"),
 "F3W-W24": ("CGIAR Research Program on Rice, Innovation #651 'Premium Quality Rice (PQR) varieties BRRI Dhan 50 and BRRI Dhan 63' (Rice AR 2018), CGSpace 10568/122435", "02_raw/cgiar_web/cgspace/10568_122435__ProjectInnovationSummary-Rice-P1573-I651.pdf", "pdf_text", "CGIAR CRP Rice innovation record 2018"),
 "F3W-W25": ("CGIAR Research Program on Rice, MELIA study #2371 'Adoption and impact of Green Super Rice (GSR) varieties in Bangladesh' (Rice AR 2019), CGSpace 10568/124161", "02_raw/cgiar_web/cgspace/10568_124161__OutcomesCaseStudySummary-Rice-P1584-OICS2371.pdf", "pdf_text", "CGIAR CRP Rice MELIA record 2019"),
 "F3W-W26": ("CGIAR Research Program on Rice, OICR #4254 'Flood-tolerant rice improves climate resilience ... in Bangladesh' (Rice AR 2021), CGSpace 10568/121709", "02_raw/cgiar_web/cgspace/10568_121709__OutcomesCaseStudySummary-Rice-P1584-OICS4254.pdf", "pdf_text", "CGIAR CRP Rice OICR 2021"),
 "F3W-W27": ("ISPC-SPIA Impact Brief No. 50 'BD56, an early-maturing and drought-tolerant variety for Bangladesh', Sep 2016, CGSpace 10568/128882", "02_raw/cgiar_web/cgspace/10568_128882__SPIA_Impact-Brief-50_Sep2016.pdf", "pdf_text", "CGIAR SPIA 2016"),
 "F3W-W28": ("IRRI News blog (news.irri.org) label feed 'BRRI' (Blogger JSON), posts 2015-09-11 and 2018-05-16", "02_raw/cgiar_web/irri/newsirri_feed_label_BRRI.json", "api_json", "IRRI news blog"),
 "F3W-W29": ("IRRI News blog (news.irri.org) label feed 'Bangladesh', post 2023-02-10 'Learning Visit to IRRI in India by Delegates from Bangladesh'", "02_raw/cgiar_web/irri/newsirri_feed_label_Bangladesh.json", "api_json", "IRRI news blog 2023"),
 "F3W-W30": ("WorldFish brochure 'WorldFish-developed Generation 3 rohu grows more than 30% faster than conventional rohu strains', 15 Nov 2022, hdl 20.500.12348/5429", "02_raw/cgiar_web/worldfish/hdl5429_g3_rohu_30pct_faster.pdf", "pdf_text", "WorldFish 2022"),
 "F3W-W31": ("WorldFish update 'First Commercial Sale of GIFT to Bangladesh Hatchery to Expand Access for Fish Farmers', 13 Mar 2025", "02_raw/cgiar_web/worldfish/wf_first_commercial_sale_gift_bangladesh.html", "html", "WorldFish 2025"),
 "F3W-W32": ("WorldFish impact story 'Amping up aquaculture gains with genetic insights', 1 Jul 2024", "02_raw/cgiar_web/worldfish/wf_impact_story_amping_aquaculture_genetics.html", "html", "WorldFish 2024"),
 "F3W-W33": ("IFPRI/HarvestPlus Biofortification Progress Brief 1 'Zinc rice' (Virk 2014), CGSpace 10568/150610", "02_raw/cgiar_web/cgspace/10568_150610__128491.pdf", "pdf_text", "HarvestPlus/IFPRI 2014"),
}

_txt = {}
def norm(s):
    s = html.unescape(s).replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"').replace("ﬁ", "fi")
    return re.sub(r"\s+", " ", s).strip()

def text(sid):
    if sid not in _txt:
        lf = S[sid][1]
        if lf.endswith(".json"):
            d = json.loads((ROOT / lf).read_text(encoding="utf-8"))
            parts = [e["title"]["$t"] + " " + re.sub(r"<[^>]+>", " ", e["content"]["$t"]) for e in d["feed"].get("entry", [])]
            _txt[sid] = norm(" ".join(parts))
        else:
            _txt[sid] = norm(text_of(lf))
    return _txt[sid]

def page_of(sid, q):
    lf = S[sid][1]
    if not lf.endswith(".pdf"): return ""
    t = text_of(lf)
    for m in re.finditer(r"\[\[p(\d+)\]\]", t):
        pass
    pages = re.split(r"\[\[p(\d+)\]\]", t)
    for i in range(1, len(pages), 2):
        if norm(q) in norm(pages[i + 1]): return pages[i]
    return ""

ROWS = []
def row(name, field, value, quote, sid, locator="", validation="unvalidated", confidence="high", notes="", key=None):
    q = norm(quote)
    if q not in text(sid):
        raise SystemExit(f"QUOTE NOT FOUND in {sid}: {quote!r}")
    if len(q.split()) > 25:
        raise SystemExit(f"QUOTE TOO LONG ({len(q.split())} words): {quote!r}")
    k = key or make_key(name) or "UNMATCHED"
    title, lf, method, _ = S[sid]
    ROWS.append({"pilot_key": k, "field": field, "value": value, "value_raw": q, "source_id": sid, "source_title": title,
                 "authority_rank": "4_cgiar_record", "local_file": lf, "page": page_of(sid, q), "locator": locator or q[:120],
                 "method": method, "validation": validation, "confidence": confidence, "notes": notes})

def ci(name, sid, what, quote, **kw):
    row(name, "cgiar_independent", f"{S[sid][3]}: {what}", quote, sid, **kw)

def mention_rows(sid, sentence, names, what):
    """Varieties only listed/tested on a CGIAR page: one cgiar_independent row each, quote = short verbatim window."""
    s = norm(sentence)
    if s not in text(sid): raise SystemExit(f"SENTENCE NOT FOUND {sid}: {sentence[:80]}")
    for n in names:
        i = s.find(n)
        if i < 0: raise SystemExit(f"name {n} not in sentence")
        st = i
        for _ in range(4):
            k2 = s.rfind(" ", 0, st - 1)
            if k2 < 0: st = 0; break
            st = k2 + 1
        en = i + len(n)
        for _ in range(3):
            k2 = s.find(" ", en + 1)
            if k2 < 0: en = len(s); break
            en = k2
        frag = s[st:en].strip()
        ci(n, sid, what, frag, locator=s[:160], confidence="high", notes="mention only; the page makes no development or origin claim for this variety")

# ======================= IRRI / Rice Today =======================
ci("IR8", "F3W-W01", "IRRI variety IR8 introduced into (East Pakistan/) Bangladesh in 1967", "In 1967, the first widely distributed semidwarf rice variety called IR8 was introduced into the country.")
row("IR8", "approval_date", "1967", "In 1967, the first widely distributed semidwarf rice variety called IR8 was introduced into the country.", "F3W-W01",
    confidence="medium", notes="year of introduction into the country per IRRI, not an approval; archive approval_date for IR8 is 1966 (IRRI naming year)")
row("BRRI hybrid dhan", "cgiar_independent", "IRRI Rice Today 2012: IRRI 'facilitated' 55 HYVs in Bangladesh incl. four BRRI hybrids, five BINA HYVs, one each by two universities, two flood-tolerant (names not given)",
    "IRRI's efforts in this area facilitated the development of 55 high-yielding varieties, which include four hybrid rice varieties by BRRI", "F3W-W01",
    key="UNMATCHED", confidence="medium", notes="aggregate claim, no variety names; by Jan 2012 BRRI had released hybrid dhan1-4; archive codes only hybrid dhan1 and dhan4 as CGIAR (hybrid dhan2, dhan3 = 4). See crosscheck.")

ci("BRRI dhan47", "F3W-W02", "IRRI-bred line IR63307-4B-4-3 released as BRRI dhan47 (2007) by BRRI with IRRI salinity team", "It is an IRRI-bred variety, labeled as IR63307-4B-4-3, which was evaluated and released by the Bangladesh Rice Research Institute (BRRI)")
row("BRRI dhan47", "breeding_line", "IR63307-4B-4-3", "It is an IRRI-bred variety, labeled as IR63307-4B-4-3", "F3W-W02", validation="two_source", notes="matches archive breeding_line (NSB/Rice Profile)")
row("BRRI dhan47", "approval_date", "2007", "One of these varieties is BRRI dhan47, which was released in Bangladesh in 2007.", "F3W-W02", validation="two_source", notes="matches archive approval_date 2007-01-18 (NSB)")

ci("BRRI dhan-96", "F3W-W03", "BRRI-developed (BRRI dhan28 x Oryza rufipogon), released 2020; IRRI role stated as introduction/testing/scaling; no IRGC/genebank mention",
   "It was developed by the Bangladesh Rice Research Institute (BRRI) through the hybridization of BRRI dhan28 with Oryza rufipogon, a wild variety.",
   notes="archive codes BRRI dhan96 = 2 (IRGC 103404 as parent); the IRRI page names O. rufipogon but not its IRGC source")
row("BRRI dhan-96", "pedigree", "BRRI dhan28 x Oryza rufipogon", "through the hybridization of BRRI dhan28 with Oryza rufipogon, a wild variety", "F3W-W03", validation="two_source", notes="consistent with archive pedigree (IRGC103404 accession not named here)")
row("BRRI dhan-96", "approval_date", "2020", "It was released in 2020 for cultivation in the boro season.", "F3W-W03", validation="two_source", notes="matches archive approval_date 2020-02-11")
ci("BRRI dhan-96", "F3W-W03", "IRRI claims role in introduction, testing and scaling of BRRI dhan96 (dissemination, not development)",
   "The collaboration between IRRI and its national research and extension systems partners has resulted in the successful introduction, testing, and scaling of BRRI dhan-96")
mention_rows("F3W-W03", "Mr. Islam took part in IRRI Seed System Program HHATs to evaluate the performances of BRRI dhan-88, BRRI dhan-96, BRRI dhan-101 with BRRI dhan-28 and BRRI dhan-67 as the local check and benchmark varieties, respectively.",
             ["BRRI dhan-88", "BRRI dhan-101", "BRRI dhan-28", "BRRI dhan-67"], "tested in IRRI Seed System Program head-to-head adaptive trials (HHAT) in the Haor")

ci("BRRI dhan-99", "F3W-W04", "salt-tolerant BRRI dhan99 released 2020; BRRI/BINA salt-tolerant varieties said to be released 'through IRRI'", "BRRI dhan-99, released in 2020, is a long-maturing, high-yielding variety with medium bold grain.")
row("BRRI dhan-99", "approval_date", "2020", "BRRI dhan-99, released in 2020, is a long-maturing, high-yielding variety with medium bold grain.", "F3W-W04", validation="two_source", notes="matches archive approval_date 2020-09-08")
for n in ["BRRI dhan-99", "BRRI dhan-97", "BINA dhan-10"]:
    ci(n, "F3W-W04", "listed with BRRI dhan99/97/BINA dhan10 as salt-tolerant varieties 'developed to thrive in adverse environments'; generic claim that BRRI and BINA released them 'through IRRI'",
       "she heard that BRRI and the Bangladesh Institute of Nuclear Agriculture (BINA) released new high-yielding salt-tolerant varieties through IRRI.", confidence="medium",
       notes="attributed to a farmer's understanding in a feature story; the varieties are named in the same paragraph/page (BRRI dhan-99, BRRI dhan-97, BINA dhan-10)")

ci("BRRI dhan88", "F3W-W05", "released by BRRI in 2018; tested in IRRI on-farm trials (no IRRI development claim)", "BRRI dhan88 is a Boro season rice variety released by the Bangladesh Rice Research Institute (BRRI) in 2018.")
row("BRRI dhan88", "approval_date", "2018", "BRRI dhan88 is a Boro season rice variety released by the Bangladesh Rice Research Institute (BRRI) in 2018.", "F3W-W05", validation="two_source", notes="matches archive approval_date 2018-10-09")
ci("BRRI dhan100", "F3W-W05", "zinc-enriched BRRI dhan100 released by BRRI in 2021; tested in IRRI on-farm trials", "BRRI dhan100, a Boro season rice variety released by BRRI in 2021, has a medium slender grain")
row("BRRI dhan100", "approval_date", "2021", "BRRI dhan100, a Boro season rice variety released by BRRI in 2021, has a medium slender grain", "F3W-W05", validation="two_source", notes="matches archive approval_date 2021-02-09")
mention_rows("F3W-W05", "The On-Farm Trial was conducted in Khagrachari and Rangamati districts using various varietal entries like BRRI dhan28, BRRI dhan74, BRRI dhan84, BRRI dhan88 and BRRI dhan100.",
             ["BRRI dhan74", "BRRI dhan84"], "used in IRRI-supervised on-farm trials in the Chittagong hill districts")

ci("BRRI dhan52", "F3W-W06", "BRRI dhan52 identified with BR11-Sub1 (Sub1 introgression)", "such as BRRI dhan52 (BR11-Sub1) and BRRI dhan51 ( Swarna-Sub1 )")
row("BRRI dhan52", "aliases", "BR11-Sub1", "such as BRRI dhan52 (BR11-Sub1)", "F3W-W06", validation="two_source", notes="alias consistent with archive pedigree BR11/IR40931-33-1-3-2")
ci("BRRI dhan51", "F3W-W06", "BRRI dhan51 identified with Swarna-Sub1 (IRRI Sub1 line)", "and BRRI dhan51 ( Swarna-Sub1 )")
row("BRRI dhan51", "aliases", "Swarna-Sub1", "and BRRI dhan51 ( Swarna-Sub1 )", "F3W-W06", validation="two_source", notes="alias consistent with archive pedigree Swarna/IR49830-7-1-2-3")
for n in ["BRRI dhan56", "BRRI dhan71"]:
    ci(n, "F3W-W06", "described as drought-tolerant variety 'developed in Bangladesh' by breeding programs led by BRRI/BINA (IRRI magazine does not claim IRRI origin here)",
       "Our study has been able to generate substantial evidence for multiple new drought-tolerant varieties developed in Bangladesh.", confidence="medium",
       notes="archive codes both as IRRI line released directly (IR74371-70-1-1; IR82589-B-B-84-3); this page attributes them to national breeding programs; not a coding conflict but a framing difference")
mention_rows("F3W-W06", "Farmers in Bangladesh cultivate varieties such as BR10, BR11, and Swarna that have duration greater than 145 days as well as shorter duration varieties (<135 days) such as Binadhan-7, BRRI dhan39, and BRRI dhan49.",
             ["Binadhan-7", "BRRI dhan39", "BRRI dhan49"], "farmer check varieties in IRRI/BRRI head-to-head trials")

ci("IR20", "F3W-W07", "IRRI variety IR20 spread to Bangladesh, where it was 'the most popular variety'; government imported ~7,000 t of IR20 seed in 1972",
   "In 1972, the Bangladesh government imported about 7,000 tons of IR20 seed from the Philippines", notes="IRRI Annual Report 1972 text reprinted in Rice Today; archive IR20 approval_date 1969 (IRRI naming year)")

ci("BRRI dhan51", "F3W-W08", "varieties 'Developed by IRRI in conjunction with' BRRI include BRRI dhan51", "Developed by IRRI in conjunction with its national partners such as the Bangladesh Rice Research Institute , these varieties include BRRI dhan51")

ci("BRRI dhan-107", "F3W-W09", "BRRI-developed; no CGIAR involvement stated", "Developed by the Bangladesh Rice Research Institute, BRRI dhan-107 is a premium quality variety")
ci("BRRI dhan-108", "F3W-W09", "approved by NSB with BRRI dhan107 (BRRI-developed per page); no CGIAR involvement stated", "The National Seed Board has approved the release of BRRI dhan-107 and BRRI dhan-108 rice varieties for the boro season.",
   confidence="medium", notes="archive codes BRRI dhan108 = 2 (IRRI CMS line IR80561A as parent); the IRRI magazine does not mention it")

ci("BINA Dhan-11", "F3W-W10", "Sub1 variety BINA Dhan-11 'developed and released through BINA' in 2013; later released in India via IRRI-facilitated Seeds Without Borders",
   "BINA Dhan-11 was developed and released through the Bangladesh Institute of Nuclear Agriculture (BINA) in 2013", notes="archive codes Binadhan-11 = 1 (Ciherang*2/IRRI 149); this IRRI page credits BINA only")
row("BINA Dhan-11", "approval_date", "2013", "BINA Dhan-11 was developed and released through the Bangladesh Institute of Nuclear Agriculture (BINA) in 2013", "F3W-W10", validation="two_source", notes="matches archive approval_date 2013-08-26")

mention_rows("F3W-W11", "Fourteen rice varieties were evaluated at the event, including BRRI dhan96, BRRI dhan99, BRRI dhan74 (benchmark), BRRI dhan67, BRRI dhan88, BRRI dhan97, BRRI dhan100, BRRI dhan28 (local check), Binadhan-25, BRRI dhan101, BRRI dhan102, BRRI dhan92, BRRI dhan104, and BRRI dhan105.",
             ["BRRI dhan97", "BRRI dhan102", "BRRI dhan92", "Binadhan-25", "BRRI dhan104", "BRRI dhan105"], "evaluated in IRRI-BADC crop cafeteria (Noakhali, May 2025)")

# ======================= STRASA =======================
ci("BRRI dhan51", "F3W-W12", "STRASA: BRRI dhan51 among varieties 'Developed by IRRI in conjunction with' BRRI", "Developed by IRRI in conjunction with its national partners such as the Bangladesh Rice Research Institute (BRRI), these varieties include BRRI dhan51")
for n, w in [("Binadhan-8", "developed by BINA 'under collaboration with IRRI'"), ("Binadhan-10", "developed by BINA 'under collaboration with IRRI'")]:
    ci(n, "F3W-W13", f"STRASA: salt-tolerant {n} {w}", "Under collaboration with IRRI, BINA developed 'Binadhan-8' ( photo at right ) and 'Binadhan-10', whereas BRRI developed 'BRRI dhan47' and 'BRRI dhan55'.")
for n in ["BRRI dhan47", "BRRI dhan55"]:
    ci(n, "F3W-W13", f"STRASA: salt-tolerant {n} 'developed' by BRRI, within IRRI-BRRI-BINA joint collaboration that developed four salt-tolerant boro varieties",
       "under a joint collaboration with the Bangladesh Rice Research Institute (BRRI) and Bangladesh Institute of Nuclear Agriculture (BINA), developed four sal", confidence="high")
ci("BRRI dhan78", "F3W-W14", "STRASA Phase 3 (2014-19): BRRI dhan78 the one Bangladesh multiple-stress-tolerant variety released and disseminated under STRASA", "one from Bangladesh (BRRI dhan78)",
   notes="same page: STRASA Phase 3 released/disseminated 6 STRVs in Bangladesh (not named)")

# ======================= HarvestPlus =======================
ci("BRRI dhan72", "F3W-W15", "zinc rice BRRI dhan72 'developed with support from HarvestPlus' (HarvestPlus-funded/co-developed)", "The variety, developed with support from HarvestPlus, has higher zinc content and is higher yielding than two previously released varieties.")
row("BRRI dhan62", "approval_date", "2013", "The earlier varieties, BRRI dhan62 (2013) and BRRIdhan64 (2014), were released for the monsoon ( Aman ) and dry ( Boro ) seasons, respectively.", "F3W-W15", validation="two_source", notes="matches archive 2013-08-26")
row("BRRIdhan64", "approval_date", "2014", "The earlier varieties, BRRI dhan62 (2013) and BRRIdhan64 (2014), were released for the monsoon ( Aman ) and dry ( Boro ) seasons, respectively.", "F3W-W15", validation="two_source", notes="matches archive 2014-08-20")
ci("BRRIdhan64", "F3W-W15", "listed by HarvestPlus as an earlier zinc rice variety (Boro, 2014)", "The earlier varieties, BRRI dhan62 (2013) and BRRIdhan64 (2014), were released for the monsoon ( Aman ) and dry ( Boro ) seasons, respectively.")
ci("BRRI dhan100", "F3W-W16", "developed by BRRI; HarvestPlus assists BRRI in crop development and breeder seed production of zinc rice", "HarvestPlus assists BRRI in crop development and breeder seed production of biofortified zinc rice.")
ci("BRRI dhan62", "F3W-W16", "first zinc rice variety, developed and released by BRRI in 2013 'through HarvestPlus support'", "In 2013, BRRI succeeded in developing and releasing the first biofortified zinc rice variety in the world, BRRI dhan62, through HarvestPlus support.")
for n in ["BRRI dhan74", "BRRI dhan84"]:
    ci(n, "F3W-W16", "named by HarvestPlus as a Boro-season zinc rice variety (no developer statement)", "The other zinc rice varieties for boro season are BRRI dhan74 which has a medium-bold grain with high yield, and BRRI dhan84 with medium-slender grain.", confidence="medium")
ci("BRRI dhan62", "F3W-W17", "HarvestPlus country page: BRRI dhan62 released 2013 through HarvestPlus support; HarvestPlus crop development with BRRI and IRRI since 2004; 'Number of Varieties Released to Date: 10' zinc rice (nine in body text)",
   "BRRI succeeded in developing and releasing the first-ever biofortified zinc rice variety in the world, BRRI dhan62, through HarvestPlus support.")
row("zinc rice (count)", "cgiar_independent", "HarvestPlus country page: Bangladesh zinc rice varieties released to date = 10 (table) vs 'nine' (text); no list on page", "Through support of the HarvestPlus Bangladesh program, Bangladesh has released nine zinc rice varieties so far.", "F3W-W17",
    key="UNMATCHED", confidence="medium", notes="aggregate count only; same page table: 'Zinc Rice Year of First Release: 2013 Number of Varieties Released to Date: 10'")
mention_rows("F3W-W18", "In 2023, these enterprises collectively produced 700 metric tons (MT) of biofortified zinc rice seed of the BRRI dhan74, BRRI dhan84, Bangabandhu dhan100, BRRI dhan102, and BRRI dhan72 variety.",
             ["BRRI dhan102"], "listed by HarvestPlus among biofortified zinc rice varieties whose seed is promoted (no developer statement)")
row("Bangabandhu dhan100", "aliases", "Bangabandhu dhan100", "Bangabandhu dhan100, BRRI dhan102, and BRRI dhan72 variety", "F3W-W18", key="BRRI_DHAN100", confidence="high",
    notes="manual key: make_key returns None for 'Bangabandhu dhan100'; the renamed BRRI dhan100 (ব্রি বঙ্গবন্ধু ধান১০০, see archive aliases); HarvestPlus also writes 'Bangabandhu dhan100 is a zinc rice'")

# ======================= CGIAR reporting records (CGSpace) =======================
ci("BRRI Dhan 97", "F3W-W19", "CGIAR innovation: line IR83484-3-B-7-1-1-1 released as BRRI dhan97; lead organisation IRRI, contributing BRRI and PhilRice", "Two promising lines BRRI Dhan 97 (IR83484-3-B-7-1-1-1) and BRRI Dhan99 (HHZ5-DT20-DT2-DT1) were released for irrigated lowland conditions in Bangladesh")
row("BRRI Dhan 97", "breeding_line", "IR83484-3-B-7-1-1-1", "BRRI Dhan 97 (IR83484-3-B-7-1-1-1)", "F3W-W19", validation="two_source", notes="matches archive breeding_line IR 83484-3-B-7-1-1-1")
ci("BRRI Dhan99", "F3W-W19", "CGIAR innovation: line HHZ5-DT20-DT2-DT1 released as BRRI dhan99; lead organisation IRRI", "Name of lead organization/entity to take innovation to this stage: IRRI - International Rice Research Institute")
row("BRRI Dhan99", "breeding_line", "HHZ5-DT20-DT2-DT1", "BRRI Dhan99 (HHZ5-DT20-DT2-DT1)", "F3W-W19", validation="two_source", notes="matches archive breeding_line HHZ5-DT20-DT2-DT1")
ci("BRRI dhan 100", "F3W-W20", "CGIAR A4NH innovation (zinc rice BRRI dhan100): lead organisation BRRI; top contributors IRRI and HarvestPlus", "Name of lead organization/entity to take innovation to this stage: BRRI - Bangladesh Rice Research Insitute",
   notes="contributors on same record: 'IRRI - International Rice Research Institute', 'HarvestPlus'")
ci("BRRI Dhan84", "F3W-W21", "CGIAR A4NH reports BRRI dhan84 as a HarvestPlus biofortified (zinc) rice innovation from HarvestPlus-CGIAR-NARS collaboration", "Collaboration between HarvestPlus, CGIAR breeding centers, and NARS resulted in the release of 29 new varieties")
ci("Binadhan 20", "F3W-W22", "CGIAR A4NH reports Binadhan-20 as a HarvestPlus biofortified (zinc) rice innovation from HarvestPlus-CGIAR-NARS collaboration", "Collaboration between HarvestPlus, CGIAR breeding centers, and NARS resulted in the release of 29 new varieties",
   notes="archive codes Binadhan-20 = 4 (BCR funded_by 'Country Initiative'); CGIAR's own reporting claims it as an A4NH/HarvestPlus innovation. Disagreement flagged.")
for n in ["BRRI dhan51", "BRRI dhan52", "BRRI dhan79", "BINA Dhan 11", "BINA Dhan 12"]:
    ci(n, "F3W-W23", "CGIAR CRP Rice innovation #650: one of five Sub1 varieties developed by BRRI/BINA 'in collaboration with' IRRI; lead organisation IRRI",
       "in collaboration with the International Rice Research Institute (IRRI), have already developed and promoted five Sub1 rice varieties")
for n in ["BRRI Dhan 50", "BRRI Dhan 63"]:
    ci(n, "F3W-W24", "CGIAR CRP Rice innovation #651: BRRI-released PQR variety introduced and popularised with CSISA support; lead BRRI, contributor IRRI",
       "both of which were introduced and popularized with support from the Cereal Systems Initiative for South Asia (CSISA)", notes="dissemination claim, not development")
ci("BINA Dhan17", "F3W-W25", "CGIAR CRP Rice MELIA: BINA dhan17 is a Green Super Rice (GSR) variety, released 2015", "Two GSR varieties were considered: BINA Dhan17 (released in 2015) and BRRI Dhan75 (released in 2016).",
   notes="GSR project led by CAAS with IRRI (see CRP Rice innovation #679, CGSpace 10568/122459); archive codes Binadhan-17 = 4 with lineage text 'IRRI collaboration: Green Super Rice line SAGC-7'")
row("BINA Dhan17", "approval_date", "2015", "BINA Dhan17 (released in 2015)", "F3W-W25", validation="two_source", notes="matches archive 2015-07-12")
ci("BRRI Dhan75", "F3W-W25", "CGIAR CRP Rice MELIA: BRRI dhan75 is a Green Super Rice (GSR) variety, released 2016", "BRRI Dhan75 (released in 2016)")
row("BRRI Dhan75", "approval_date", "2016", "BRRI Dhan75 (released in 2016)", "F3W-W25", validation="two_source", notes="matches archive 2016-05-29")
ci("BRRI dhan51", "F3W-W26", "CGIAR OICR: IRRI developed Swarna-Sub1 by marker-assisted backcrossing (Swarna-Sub1 = BRRI dhan51 in Bangladesh)", "IRRI developed submergence-tolerant variety Swarna-Sub1 (SS1) through marker-assisted backcrossing",
   confidence="medium", notes="manual mapping Swarna-Sub1 -> BRRI_DHAN51 via alias on F3W-W06; the OICR itself names Swarna-Sub1 only", key="BRRI_DHAN51")
ci("BD56", "F3W-W27", "SPIA: BD56 (BRRI dhan56) 'a recently released rice variety of IRRI'", "BD56 is a recently released rice variety of IRRI that offers both early maturity and drought tolerance.",
   key="BRRI_DHAN56", notes="manual key: make_key returns None for 'BD56'; brief title: 'BD56, an early-maturing and drought-tolerant variety for Bangladesh'")
ci("BRRI dhan 62", "F3W-W33", "HarvestPlus/IFPRI brief: first zinc rice Aman variety BRRI dhan62 released 2013; high-zinc lines introduced from IRRI each year", "In Bangladesh, the first zinc rice Aman (rainfed) season variety, \"BRRI dhan 62,\" was released in 2013.")

# ======================= IRRI news blog (news.irri.org) =======================
ci("BRRI dhan33", "F3W-W28", "BRRI dhan33 'jointly invented in 1997 and validated by BRRI and IRRI' (IRRI-BRRI collaboration)", "BRRI dhan33, a shorter duration rice variety jointly invented in 1997 and validated by BRRI and the International Rice Research Institute (IRRI)",
   locator="post 2018-05-16 'Bangladesh Government honors former IRRI Agronomist Dr. Md. M Abdul Mazid'", notes="archive codes BRRI dhan33 = 4 (pedigree BG388/BG367-4). Disagreement flagged.")
row("BRRI dhan33", "approval_date", "1997", "BRRI dhan33, a shorter duration rice variety jointly invented in 1997", "F3W-W28", validation="two_source", confidence="medium",
    locator="post 2018-05-16", notes="'invented' year, not stated as approval; archive approval_date 1997-07-16")
for n in ["BRRIdhan69", "BINAdhan17"]:
    ci(n, "F3W-W28", "IRRI: one of two Green Super Rice (GSR) varieties released in Bangladesh (GSR project, CAAS-IRRI)", "two GSR varieties—BRRIdhan69 and BINAdhan17GSR—have been released in Bangladesh",
       locator="post 2015-09-11 'Green Super Rice Project training course held in Bangladesh'")
ci("Binadhan11", "F3W-W29", "Binadhan-11 'originally developed and registered in Bangladesh' (grown in Odisha)", "Binadhan11, which was originally developed and registered in Bangladesh", locator="post 2023-02-10", confidence="medium")

# ======================= WorldFish (fish) =======================
def fish(key, field, value, quote, sid, **kw):
    row(key, field, value, quote, sid, key=key, **kw)
fish("FISH_WF_G3_ROHU", "cgiar_independent", "WorldFish 2022: 'WorldFish-developed' G3 rohu released as hatchlings to hatcheries in 2020 and 2021", "WorldFish released the genetically-improved 'Generation 3' or 'G3' rohu strain as hatchlings to several hatcheries on a limited scale.", "F3W-W30",
     notes="same statement as P2F FS016 (hdl 5428 metadata); this is the brochure PDF hdl 5429")
fish("FISH_WF_G3_ROHU", "release_date", "2020-2021", "In 2020 and 2021, WorldFish released the genetically-improved 'Generation 3' or 'G3' rohu strain", "F3W-W30", validation="two_source", notes="matches P2F FS016/FS022")
fish("FISH_WF_G3_ROHU", "cgiar_independent", "WorldFish 2024: transfer of WorldFish's G3 rohu to BFRI in 2023 after 11+ years of the WorldFish Carp Genetic Improvement Program", "In 2023, the transfer of WorldFish's G3 Rohu to the Bangladesh Fisheries Research Institute marked a significant milestone for the country.", "F3W-W32",
     notes="consistent with P2F FS023/FS024 (handover to BFRI 2023-08-08)")
fish("FISH_WF_GIFT_G19_EON_2025", "cgiar_independent", "WorldFish 2025: first commercial sale of GIFT (7,000 fry) to a Bangladesh hatchery, EON Aquaculture Limited; GIFT 'Developed by WorldFish in 1988'", "WorldFish has delivered 7,000 Genetically Improved Farmed Tilapia GIFT fry to EON Aquaculture Limited in Bangladesh.", "F3W-W31",
     notes="generation not stated on this page (P2F-S23 dataset says G19); page published 13 Mar 2025")
fish("FISH_WF_GIFT_G19_EON_2025", "release_date", "2025", "This is the first commercial sale of GIFT to a Bangladesh hatchery", "F3W-W31", confidence="medium", validation="two_source",
     notes="year from page publication date (13 Mar 2025); delivery date not printed; matches P2F-S23 (2025)")

with open(OUT, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=COLS); w.writeheader(); w.writerows(ROWS)
print(len(ROWS), "rows;", len({r["pilot_key"] for r in ROWS}), "keys")
from collections import Counter
print(Counter(r["pilot_key"] for r in ROWS))
