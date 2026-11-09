"""Variety event history and status as of 2026, from the National Seed Board (NSB) decision table.

Inputs  05_output/final/bgd_nsb_decisions_full.csv (one row per variety decision, NSB meetings 1-115, 1974-2026)
        05_output/final/bgd_rice_varieties.csv     (the rice register, for the variety list and register approval dates)
Outputs 05_output/final/bgd_variety_events.csv     one row per (variety, event)
        05_output/final/bgd_variety_status.csv     one row per variety: status_as_of_2026, basis, last_event_date

Run: python scripts/build_status_events.py

Event rows
----------
Only decision rows linked to a variety_id become events (general policy items are left out; the validation report
lists the ones that bear on variety status). Rows repeating the same (variety, meeting, event_type) are merged.

event_type is set from decision_type, then refined by keyword rules on the variety's own text (variety_segment_verbatim,
else variety_passage_verbatim, else decision_text) and the English minutes note (f3m_notes):

  decision_type                       event_type
  release                             release; full_release_after_provisional when the variety already had a
                                      provisional release or registration; extension_season_or_region when it had
                                      already been released and this decision only adds a season or region
  release_provisional                 provisional_release
  registration_provisional /
  registration_conditional            registration (detail says provisional or conditional); a second registration
                                      at a later meeting is extension_season_or_region
  registration_full                   full_release_after_provisional if an earlier registration exists, else registration
  registration_extension              extension_season_or_region; registration_renewal_or_extension when the text speaks
                                      of a term (নবায়ন, মেয়াদ বৃদ্ধি, renew, extend ... period)
  suspension                          suspension (স্থগিত / স্হগিত, 'suspended')
  rename                              rename
  approval_denied                     rejection; import_permission when the refusal concerns seed import
  approval_deferred, re_trial         recommendation_pending/deferred
  denotification_proposed             denotification_proposed_deferred (proposal not adopted; see report)
  status_change, condition_change     keyword rules on the English minutes note plus the variety's own segment (the
                                      whole agenda passage only when no segment exists), first match wins:
                                        registration_renewal_or_ext. 'no time limit', সময় সীমা বেঁধে দেয়া হবে না,
                                                                     'approval period amended' (term lifted or moved)
                                        status_change_other          'continued' (approval confirmed, e.g. Iratom-24 1981)
                                        cancellation/denotification  বাতিল করা হলো/হইল, প্রত্যাহার করা হলো, ডিনোটিফাই করা হলো,
                                                                     'cancelled', 'withdrawn', 'denotified' (decided, past
                                                                     tense; skipped whenever the text is a conditional
                                                                     threat: 'বাতিল করা হইবে' = will be cancelled, 're-
                                                                     evaluated or cancelled', 'must reapply')
                                        suspension                   স্থগিত/স্হগিত + রাখা/করা, 'suspended'
                                        rename                       নাম পরিবর্তন, নামকরণ, 'commercial name', 'renam'
                                        transfer_of_registration     হস্তান্তর, 'transfer'
                                        registration_renewal_or_ext. নবায়ন, মেয়াদ বৃদ্ধি, 'renew', 'production period'
                                        import_permission            আমদানি/আমদানী, 'import'
                                        extension_season_or_region   'also for', 'approved also', পাশাপাশি
                                        otherwise condition_change / status_change_other
  gazette                             gazette_notification

Three event types extend the requested list because the minutes contain them and no listed type fits:
denotification_proposed_deferred, condition_change (a new condition on an existing approval) and status_change_other
(e.g. Pajam reclassified as an improved, not high-yielding, variety in 1976).

detail is an English summary (event, meeting, season/region when the table gives them in English, and the English
minutes note). decision_text_excerpt is the Bangla source text, verbatim from the OCR or text layer, cut to 400 characters.

Status as of 2026
-----------------
The NSB minutes run to meeting 115 (5 Feb 2026). For every register variety, and for the two non-register varieties with
NSB events (Iratom-38, Jirashail):
  cancelled   a decided cancellation/denotification with no later approval. (None found.)
  suspended   a suspension (of cultivation or of seed multiplication) with no later approval or reinstatement.
  unknown     (a) no NSB approval on record and none in the register (pre-NSB recommendations, landraces);
              (b) the latest approval was provisional or time-limited ('N বছর মেয়াদে', 'approved/released for N years') and no later
                  approval, extension or renewal is recorded, so the approval may have lapsed but no minute says so;
              (c) a later decision made the approval conditional on re-evaluation ('অনুমোদন বাতিল করা হইবে' unless ...,
                  'must reapply') and no outcome is recorded.
  active      approved (released or registered) by the NSB, or recorded as approved in the register, with none of
              the above. A denotification proposal that the NSB did not adopt leaves the variety active and is named
              in basis.
'registration expired' is never assigned: no minute records an expiry, and the status is not inferred from elapsed time.

legal_status_2026 (version 1.2, REV2 2026-11-10; review A1-06)
-----------------------------------------------------------------
status_as_of_2026 is kept for compatibility. legal_status_2026 states the same finding in words a reader cannot mistake for
seed availability or cultivation:
  active                                           approved, no adverse decision recorded
  active, withdrawal proposed 2021 and deferred    one of the 20 varieties the SCA proposed for denotification at NSB 105;
                                                   the Board ordered re-evaluation and no withdrawal is recorded
  time-limited registration, renewal not recorded  the latest approval was provisional or for a fixed term (status unknown (b))
  provisional, re-evaluation outcome not recorded  status unknown (c)
  seed multiplication suspended                    the Board stopped seed multiplication (IR8 and IR20, NSB 7, 1976)
  suspended                                        the Board stopped cultivation (Iratom-38, NSB 14, 1981)
  recommended before the Board, no later decision  pre-NSB recommendations of 1966-1973 (status unknown (a))
  not approved                                     names outside the register (Jirashail)
Legal status says nothing about whether seed is produced or the variety is grown.

hybrid_seed_source (version 1.2; review A1-09)
------------------------------------------------
For hybrids only: imported | produced in Bangladesh | both | unknown, with hybrid_seed_source_evidence naming the NSB
meeting. Filled only where an NSB decision states it (HYBRID_SEED below: 'imported and trialled', F1 import permissions,
parent-line imports for F1 production in Bangladesh); every other hybrid is 'unknown', and nothing is inferred from
origin_country or from the company. Blank for inbreds.
"""
import pathlib
import re
import unicodedata

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
FINAL = ROOT / "05_output" / "final"
LAST_MEETING = ("115", "2026-02-05")

APPROVAL = {"release", "provisional_release", "registration", "full_release_after_provisional",
            "extension_season_or_region", "registration_renewal_or_extension"}
PROVISIONAL_HINT = re.compile(r"সাময়িক|provision|conditional|শর্তসাপেক্ষ", re.I)
TERM_RX = re.compile(r"(\S{1,3})\s*(বছর|বৎসর)\s*মেয়াদ|(?:approved|released|registered)[^;.]{0,40}?for (\d+) years?", re.I)
THREAT_RX = re.compile(r"বাতিল করা হইবে|বাতিল করা হবে|re-?evaluated or cancelled|must reapply|reapply", re.I)

KEYWORD_RULES = [
    ("registration_renewal_or_extension", r"no time limit|সময় ?সীমা বেঁধে দেয়া হবে না|approval period amended"),
    ("status_change_other", r"\bcontinued\b"),
    ("cancellation/denotification", r"বাতিল করা হ(লো|ল|ইল)|প্রত্যাহার করা হ(লো|ল|ইল)|ডিনোটিফাই করা হ(লো|ল)|\bcancelled\b"
                                    r"|\bwithdrawn\b|\bdenotified\b"),
    ("suspension", r"(স্থগিত|স্হগিত|স্হাঁগত|স্থাঁগত)\s*(রাখা|করা)|\bsuspend"),
    ("rename", r"নাম পরিবর্তন|নামকরণ|commercial name|renam"),
    ("transfer_of_registration", r"হস্তান্তর|\btransfer"),
    ("registration_renewal_or_extension", r"নবায়ন|মেয়াদ বৃদ্ধি|\brenew|production period"),
    ("import_permission", r"আমদানি|আমদানী|\bimport"),
    ("extension_season_or_region", r"also for|approved also|পাশাপাশি"),
]

BASE_DETAIL = {
    "release": "Released by the NSB",
    "provisional_release": "Provisionally released by the NSB",
    "registration": "Registered by the NSB",
    "full_release_after_provisional": "Full release or registration after an earlier provisional approval",
    "extension_season_or_region": "Approval extended to a further season or region",
    "registration_renewal_or_extension": "Term of an existing approval renewed or extended",
    "suspension": "Suspended",
    "cancellation/denotification": "Approval cancelled or variety denotified",
    "rename": "Name or commercial name changed",
    "transfer_of_registration": "Registration transferred",
    "import_permission": "Decision on seed or parent-line import",
    "recommendation_pending/deferred": "Decision deferred, sent back to the Technical Committee, or re-trial ordered",
    "rejection": "Approval refused",
    "denotification_proposed_deferred": "Proposed for denotification; the NSB ordered re-evaluation instead of withdrawal",
    "condition_change": "New condition attached to an existing approval",
    "status_change_other": "Other change of status",
    "gazette_notification": "Gazette notification reported",
}


def _n(s):
    return unicodedata.normalize("NFC", str(s or ""))


def _has_bn(s):
    return bool(re.search(r"[ঀ-৿]", s))


def _variety_text(r):
    for c in ("variety_segment_verbatim", "variety_passage_verbatim"):
        if r[c].strip():
            return r[c]
    return r["decision_text"] + " " + r["decision_conditions"]


def _excerpt(r):
    dt = re.sub(r"সিদ্ধান্ত\s*[ঃ:]\s*", "", r["decision_text"]).strip(" .‖|")
    for t in (r["variety_segment_verbatim"], dt if len(dt) > 15 else "", r["variety_passage_verbatim"],
              r["decision_conditions"], r["item_text_verbatim"]):
        t = re.sub(r"\s+", " ", t or "").strip()
        if t:
            return t[:400]
    return ""


def _classify(r, history):
    """history: event types already recorded for this variety at earlier meetings."""
    dt = r["decision_type"]
    text = _variety_text(r) + " | " + r["f3m_notes"]
    had_prov = bool(history & {"provisional_release", "registration"})
    had_release = bool(history & {"release", "full_release_after_provisional"})
    if dt == "release":
        if had_release:
            return "extension_season_or_region"
        return "full_release_after_provisional" if had_prov else "release"
    if dt == "release_provisional":
        return "provisional_release"
    if dt in ("registration_provisional", "registration_conditional"):
        return "extension_season_or_region" if (history & APPROVAL) else "registration"
    if dt == "registration_full":
        return "full_release_after_provisional" if had_prov else "registration"
    if dt == "registration_extension":
        if re.search(r"নবায়ন|মেয়াদ বৃদ্ধি|\brenew|extend\w* (the )?(registration )?period", text, re.I):
            return "registration_renewal_or_extension"
        return "extension_season_or_region"
    if dt == "suspension":
        return "suspension"
    if dt == "rename":
        return "rename"
    if dt == "approval_denied":
        return "import_permission" if re.search(r"\bimport|আমদানি|আমদানী", r["f3m_notes"], re.I) else "rejection"
    if dt in ("approval_deferred", "re_trial"):
        return "recommendation_pending/deferred"
    if dt == "denotification_proposed":
        return "denotification_proposed_deferred"
    if dt == "gazette":
        return "gazette_notification"
    rule_text = r["f3m_notes"] + " | " + (r["variety_segment_verbatim"] or r["variety_passage_verbatim"])
    for etype, pat in KEYWORD_RULES:
        if etype == "cancellation/denotification" and THREAT_RX.search(rule_text):
            continue          # a conditional threat ('will be cancelled unless ...') is not a cancellation
        if re.search(pat, rule_text, re.I):
            return etype
    return "condition_change" if dt == "condition_change" else "status_change_other"


def _term(r, etype):
    """Stated term of an approval: '3', 'unreadable', 'period' (a dated window), or '' (none / term lifted)."""
    if etype not in APPROVAL or re.search(r"no time limit|সময় ?সীমা বেঁধে দেয়া হবে না", r["f3m_notes"] + _variety_text(r), re.I):
        return ""
    if re.search(r"period amended to \d{4}-\d{4}", r["f3m_notes"]):
        return "period"
    m = TERM_RX.search(r["f3m_notes"]) or TERM_RX.search(_variety_text(r))
    if not m:
        return ""
    n = m.group(3) or m.group(1).translate(str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789"))
    return n if n.isdigit() else "unreadable"


def _detail(r, etype):
    parts = [BASE_DETAIL[etype] + f" (NSB meeting {r['meeting_no']})"]
    if etype == "registration" and PROVISIONAL_HINT.search(_variety_text(r) + r["decision_type"] + r["f3m_notes"]):
        parts[0] = "Registered provisionally or conditionally by the NSB" + f" (NSB meeting {r['meeting_no']})"
    if etype == "suspension":
        # REV3 (round-2 review V2-11): say what was suspended, as the minutes do: seed multiplication (IR8 and IR20, NSB 7)
        # or cultivation (Iratom-38, NSB 14)
        what = ("Seed multiplication suspended" if re.search(r"seed multiplication|বীজ বর্ধন", r["f3m_notes"] + _variety_text(r))
                else "Cultivation suspended" if re.search(r"cultivation|চাষাবাদ", r["f3m_notes"]) else "Suspended")
        parts[0] = what + f" by the NSB (NSB meeting {r['meeting_no']})"
    if r["season"] and not _has_bn(r["season"]):
        parts.append(f"season: {r['season']}")
    if r["region_scope"] and not _has_bn(r["region_scope"]):
        parts.append(f"region: {r['region_scope']}")
    n = _term(r, etype)
    if n:
        parts.append(f"time-limited approval ({n} years)" if n.isdigit() else
                     "time-limited approval (dated period)" if n == "period" else "time-limited approval (term unreadable in OCR)")
    if r["f3m_notes"].strip():
        parts.append("minutes note: " + r["f3m_notes"].strip())
    return "; ".join(parts)


def build_events(dec):
    dec = dec[dec.variety_id.str.strip() != ""].copy()
    dec["_m"] = pd.to_numeric(dec.meeting_no, errors="coerce")
    dec = dec.sort_values(["variety_id", "meeting_date", "_m", "dec_id"])
    rows, seen = [], set()
    for vid, g in dec.groupby("variety_id", sort=True):
        history_before = set()     # event types from earlier meetings
        current_meeting, current_types = None, set()
        for _, r in g.iterrows():
            if r["meeting_no"] != current_meeting:
                history_before |= current_types
                current_meeting, current_types = r["meeting_no"], set()
            etype = _classify(r, history_before)
            key = (vid, r["meeting_no"], etype)
            if key in seen:
                continue
            seen.add(key)
            current_types.add(etype)
            rows.append({
                "variety_id": vid,
                "variety_name": r["variety_name"],
                "event_date": r["meeting_date"],
                "meeting_no": r["meeting_no"],
                "event_type": etype,
                "detail": _detail(r, etype),
                "decision_text_excerpt": _excerpt(r),
                "source_file": r["source_file"],
                "page": r["pages"],
                "dec_id": r["dec_id"],
                "_time_limited": bool(_term(r, etype)),
                "_threat": bool(THREAT_RX.search(_variety_text(r) + " " + r["f3m_notes"])),
                "_provisional": etype in ("provisional_release",) or bool(
                    etype == "registration" and PROVISIONAL_HINT.search(r["decision_type"])),
            })
    return pd.DataFrame(rows)


HYBRID_SEED = {
    "RICE-HYB_ALOK6201": ("imported", "NSB 40 (1998-09-09): 'imported and trialled' hybrid, approved for 3 years on condition of local "
                                      "seed production from the fourth year; no later decision records that production"),
    "RICE-HYB_LOKNATH505": ("imported", "NSB 40 (1998-09-09): 'imported and trialled' hybrid (আমদানীকৃত এবং ট্রায়ালকৃত)"),
    "RICE-HYB_AMARSHRI1": ("imported", "NSB 40 (1998-09-09): 'imported and trialled' hybrid (আমদানীকৃত এবং ট্রায়ালকৃত)"),
    "RICE-HYB_CNSGC6": ("both", "NSB 40 (1998-09-09): imported and trialled; NSB 56: F1 import for 2004-05 not allowed because local "
                                "production was unsatisfactory, so seed was also produced in Bangladesh"),
    "RICE-HYB_GB4": ("both", "NSB 51: hybrid imported by BRAC; NSB 47 and 51: A-line and R-line parent seed imported for F1 "
                             "production in Bangladesh (Boro 2002-03)"),
    "RICE-HYB_SL8H": ("produced in Bangladesh", "NSB 61: BADC allowed to import A- and R-line seed of SL-8 from SL Agritech "
                                               "(Philippines) for joint F1 seed production"),
    "RICE-HYB_LP50": ("imported", "NSB 51: 'imported by Aftab Bahumukhi Farms' (আমদানিকৃত)"),
    "RICE-HYB_RAICHAR101": ("imported", "NSB 51: 'imported by Chens Crop Science' (আমদানিকৃত)"),
    "RICE-HYB_SUPREMEHYBRIDDHAN12": ("imported", "NSB 106: 'imported from India' (ভারত হতে আমদানিকৃত)"),
    "RICE-HYB_BADCHYBRIDDHAN2": ("imported", "NSB 84: Technical Committee note 'imported from China'"),
    "RICE-HYB_BAYERHYBRID4": ("imported", "NSB 80: registered subject to the conditions on hybrid seed import and marketing"),
}


def legal_status(status, basis, in_register):
    if status == "suspended":
        return "seed multiplication suspended" if "seed multiplication" in basis else "suspended"
    if status == "cancelled":
        return "cancelled"
    if status == "active":
        return "active, withdrawal proposed 2021 and deferred" if "proposed for denotification" in basis else "active"
    if not in_register:
        return "not approved"
    if "before the NSB was constituted" in basis:
        return "recommended before the Board, no later decision"
    if "conditional on re-evaluation" in basis:
        return "provisional, re-evaluation outcome not recorded"
    if "provisional or time-limited" in basis:
        return "time-limited registration, renewal not recorded"
    return "no NSB decision recorded"


def _fmt_event(e):
    return f"{e['event_type']} at NSB {e['meeting_no']} ({e['event_date']})"


def build_status(reg, ev):
    out = []
    vids = list(reg.variety_id) + sorted(set(ev.variety_id) - set(reg.variety_id))
    regi = reg.set_index("variety_id")
    for vid in vids:
        e = ev[ev.variety_id == vid].sort_values(["event_date", "meeting_no"]).to_dict("records")
        r = regi.loc[vid] if vid in regi.index else None
        last_date = e[-1]["event_date"] if e else (r["approval_date"] if r is not None else "")
        approvals = [x for x in e if x["event_type"] in APPROVAL]
        last_appr = approvals[-1] if approvals else None
        after = lambda x: last_appr is None or (x["event_date"], int(x["meeting_no"])) > (last_appr["event_date"], int(last_appr["meeting_no"]))
        adverse = [x for x in e if x["event_type"] in ("cancellation/denotification", "suspension") and after(x)]
        notes = []
        den = [x for x in e if x["event_type"] == "denotification_proposed_deferred"]
        if den:
            notes.append(f"proposed for denotification at NSB {den[-1]['meeting_no']} ({den[-1]['event_date']}); the NSB adopted "
                         "the TC sub-committee advice to re-evaluate for two more years, and no withdrawal is recorded "
                         f"through NSB {LAST_MEETING[0]} ({LAST_MEETING[1]})")
        if vid not in regi.index:
            notes.append("not in the rice register")
        if any(x["event_type"] == "cancellation/denotification" for x in adverse):
            x = [x for x in adverse if x["event_type"] == "cancellation/denotification"][-1]
            status, basis = "cancelled", f"{_fmt_event(x)}; no later approval"
        elif adverse:
            x = adverse[-1]
            status = "suspended"
            basis = f"{_fmt_event(x)}: {x['detail']}; no later approval or reinstatement recorded"
        elif last_appr is None:
            if r is not None and r["release_category"] in ("NSB_release", "NSB_registration") and r["approval_date"]:
                status = "active"
                basis = (f"approval recorded in the register ({r['approving_body'] or 'NSB'}, {r['approval_date']}); "
                         "no NSB approval decision linked to this variety and no adverse decision found")
            else:
                status = "unknown"
                what = "; ".join(_fmt_event(x) for x in e)
                if r is not None and r["release_category"] == "pre_NSB_recommended":
                    basis = (f"recommended for cultivation in {r['approval_date']}, before the NSB was constituted (1974); "
                             f"no NSB approval, suspension or withdrawal in minutes 1-{LAST_MEETING[0]}")
                else:
                    basis = "no NSB approval on record"
                basis += f"; NSB events: {what}" if what else "; no NSB decision linked to this variety"
        else:
            threats = [x for x in e if x["_threat"] and x["event_type"] in ("condition_change", "status_change_other") and after(x)]
            if threats:
                status = "unknown"
                basis = (f"last approval {_fmt_event(last_appr)}; later {', '.join(_fmt_event(x) for x in threats)} made the "
                         "approval conditional on re-evaluation, and no outcome is recorded")
            elif last_appr["_time_limited"] or (last_appr["_provisional"] and last_appr["event_type"] == "provisional_release"):
                status = "unknown"
                basis = (f"last approval {_fmt_event(last_appr)} was provisional or time-limited ({last_appr['detail']}); "
                         "no later approval, renewal or extension recorded; expiry is not itself recorded")
            else:
                status = "active"
                basis = f"last approval {_fmt_event(last_appr)}; no suspension or cancellation recorded through NSB {LAST_MEETING[0]}"
        if notes:
            basis += "; " + "; ".join(notes)
        hyb = r is not None and r.get("rice_type", "") == "hybrid"
        seed, seed_ev = HYBRID_SEED.get(vid, ("unknown", "") if hyb else ("", ""))
        out.append({"variety_id": vid, "status_as_of_2026": status,
                    "legal_status_2026": legal_status(status, basis, vid in regi.index), "basis": basis,
                    "last_event_date": last_date, "hybrid_seed_source": seed, "hybrid_seed_source_evidence": seed_ev})
    return pd.DataFrame(out)


def main():
    dec = pd.read_csv(FINAL / "bgd_nsb_decisions_full.csv", dtype=str, keep_default_na=False).map(_n)
    reg = pd.read_csv(FINAL / "bgd_rice_varieties.csv", dtype=str, keep_default_na=False).map(_n)
    ev = build_events(dec)
    st = build_status(reg, ev)
    cols = ["variety_id", "variety_name", "event_date", "meeting_no", "event_type", "detail", "decision_text_excerpt",
            "source_file", "page"]
    ev.sort_values(["variety_id", "event_date", "meeting_no"])[cols].to_csv(
        FINAL / "bgd_variety_events.csv", index=False, encoding="utf-8")
    st.to_csv(FINAL / "bgd_variety_status.csv", index=False, encoding="utf-8")
    print(f"events: {len(ev)} rows, {ev.variety_id.nunique()} varieties")
    print(ev.event_type.value_counts().to_string())
    print(st.status_as_of_2026.value_counts().to_string())
    print(st.legal_status_2026.value_counts().to_string())
    print(st.hybrid_seed_source.value_counts().to_string())


if __name__ == "__main__":
    main()
