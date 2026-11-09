"""Shared rules for the source archive (02_raw): reading the manifest safely, media types, archive status,
rights classes, document types, issuing bodies and dates inferred from paths and addresses.

Used by build_catalogue.py, build_deposit.py, check_fixity.py, repair_manifest.py and build_evidence_public.py.
Every rule here is mechanical (folder, host, file name or file content); nothing is guessed. A value that no rule
supports is left blank. The rights classes and their treatment are explained in
00_admin/rights_and_personal_data_policy.md; change the two documents together.
"""
import csv
import hashlib
import io
import pathlib
import re
import time
import urllib.parse as up

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "02_raw"
MANIFEST = RAW / "manifest.csv"
BASE_COLS = ["file_path", "source_url", "archived_url", "download_date", "sha256", "file_type", "agent", "notes"]
# files kept in 02_raw that describe the archive rather than belong to it (never manifest rows)
NOT_SOURCES = {"02_raw/manifest.csv", "02_raw/CATALOGUE.csv", "02_raw/README.md"}
NOT_SOURCE_DIRS = ("02_raw/_robots/", "02_raw/_manifest_parts/")


def read_manifest(path=MANIFEST, tries=6):
    """Read the manifest as a list of dicts. A background job (archive_wayback.py) rewrites the whole file, so a read
    that lands mid-write is retried; the result is accepted only if every row has the header's columns."""
    last = None
    for i in range(tries):
        try:
            b1 = pathlib.Path(path).read_bytes(); time.sleep(0.5); b2 = pathlib.Path(path).read_bytes()
            if b1 != b2:                      # the file changed while being read
                raise ValueError("manifest changed during read")
            raw = b1.decode("utf-8-sig")
            rows = list(csv.DictReader(io.StringIO(raw)))
            if rows and all(None not in r and all(v is not None for v in r.values()) for r in rows):
                for r in rows:
                    r["file_path"] = r["file_path"].replace("\\", "/")
                return rows
            last = "incomplete rows"
        except Exception as e:  # noqa  (partial file, decode error)
            last = repr(e)
        time.sleep(2 + 2 * i)
    raise RuntimeError(f"could not read a complete manifest from {path}: {last}")


def strip_mailto(url):
    """Remove the OpenAlex/Crossref polite-pool e-mail parameter (mailto=...) from a URL; the response does not depend on it."""
    if not url or "mailto" not in url:
        return url
    p = up.urlsplit(url)
    q = [(k, v) for k, v in up.parse_qsl(p.query, keep_blank_values=True) if k.lower() != "mailto"]
    return up.urlunsplit((p.scheme, p.netloc, p.path, up.urlencode(q, safe="*:/,'()$ "), p.fragment))


def sha256(fp, buf=1 << 20):
    h = hashlib.sha256()
    with open(fp, "rb") as fh:
        for b in iter(lambda: fh.read(buf), b""):
            h.update(b)
    return h.hexdigest()


MIME = {"pdf": "application/pdf", "html": "text/html", "htm": "text/html", "json": "application/json",
        "xml": "application/xml", "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "csv": "text/csv",
        "txt": "text/plain", "zip": "application/zip", "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
        "md": "text/markdown"}


def mime_type(path):
    return MIME.get(pathlib.PurePosixPath(path).suffix.lower().lstrip("."), "application/octet-stream")


def host(url):
    return up.urlsplit(url or "").netloc.lower()


def original_host(url):
    """Host of the original address; for a Wayback address, the host of the captured page."""
    m = re.match(r"https?://web\.archive\.org/web/\d+[a-z_]*/(.+)$", url or "")
    return host(m.group(1) if m.group(1).startswith("http") else "http://" + m.group(1)) if m else host(url)


API_RX = re.compile(r"(^api\.|/api/|/_api/|webservices/rest|/cdx/)", re.I)


def is_api_response(path, url):
    ext = pathlib.PurePosixPath(path).suffix.lower()
    return ext in (".json", ".xml") and bool(API_RX.search(host(url) + up.urlsplit(url or "").path)) or "/literature_api/" in path


def archive_status(row):
    """archived | not archivable: API response | address unstable: deposit file | no public address: deposit file |
    archivable, retry. Object-storage PDFs of the national portal change address when a ministry re-uploads them."""
    url = row.get("source_url", "")
    if row.get("archived_url", "").strip():
        return "archived"
    if not url.strip():
        return "no public address: deposit file"
    if is_api_response(row["file_path"], url):
        return "not archivable: API response"
    if "oraclecloud" in host(url) or "objectstorage" in host(url):
        return "address unstable: deposit file"
    return "archivable, retry"


GOV_HOSTS = ("gov.bd", "oraclecloud15.com", "knowledgebank-brri.org")
CGIAR_HOSTS = ("cgiar.org", "irri.org", "worldfishcenter.org", "harvestplus.org", "africarice.org")
OPEN_HOSTS = {"www.frontiersin.org": "CC BY 4.0 (Frontiers open-access article)",
              "journals.plos.org": "CC BY 4.0 (PLOS open-access article)",
              "dataverse.harvard.edu": "CC0 (Dataverse metadata record)"}


def rights_class(path, url, content_head=b""):
    """Return (rights_class, rights_basis). Classes: gov_bd_official, cgiar_open, open_licence, openalex_cc0,
    crossref_metadata, withhold. 'withhold' files are listed in the deposit with address and hash, not redistributed."""
    h = original_host(url)
    if "/spia_bd2025/" in path:
        return "withhold", ("SPIA Bangladesh Study 2025 replication package (GitHub CGIAR-SPIA/SPIA-Bangladesh-Study-2025): repository "
                            "licence not verified and some files carry household identifiers; cite the repository instead")
    if "/spia_stocktake/" in path:
        return "withhold", "SPIA stocktake workbook copied from a local disk; no public address or licence"
    if "/openalex/" in path or h == "api.openalex.org":
        return "openalex_cc0", "OpenAlex data are released under CC0"
    if "/crossref/" in path or h == "api.crossref.org":
        if b'"abstract"' in content_head:
            return "withhold", "Crossref API response containing abstracts, which remain the publishers' copyright; re-fetchable from the query URL"
        return "crossref_metadata", "Crossref bibliographic metadata (no abstracts), which Crossref treats as facts free to reuse"
    if path.startswith("02_raw/wayback_cdx/"):
        return "open_licence", "Internet Archive CDX index listing (machine-generated metadata)"
    if any(h == g or h.endswith("." + g) for g in GOV_HOSTS):
        return "gov_bd_official", "Government of Bangladesh official publication (gazette, act, minutes, list, notice or institute page)"
    if any(h == g or h.endswith("." + g) for g in CGIAR_HOSTS):
        return "cgiar_open", "CGIAR output under the CGIAR Open and FAIR Data Assets Policy; item licence to be confirmed (mostly CC BY or CC BY-NC-SA)"
    if h in OPEN_HOSTS:
        return "open_licence", OPEN_HOSTS[h]
    if not h:
        return "withhold", "no public address; provenance by personal communication"
    return "withhold", "third-party document or web page without an open licence; metadata, address and hash only"


def rights_includable(cls):
    return cls != "withhold"


def deposit_group(cls):
    return {"gov_bd_official": "government_bd", "cgiar_open": "cgiar"}.get(cls, "other_open")


ISSUER_BY_HOST = [
    ("brri.gov.bd", "Bangladesh Rice Research Institute (BRRI)"), ("knowledgebank-brri.org", "Bangladesh Rice Research Institute (BRRI)"),
    ("bina.gov.bd", "Bangladesh Institute of Nuclear Agriculture (BINA)"), ("fri.gov.bd", "Bangladesh Fisheries Research Institute (BFRI)"),
    ("fisheries.gov.bd", "Department of Fisheries (DoF)"), ("mofl.gov.bd", "Ministry of Fisheries and Livestock (MoFL)"),
    ("moa.gov.bd", "Ministry of Agriculture (MoA)"), ("moa.portal.gov.bd", "Ministry of Agriculture (MoA)"),
    ("sca.gov.bd", "Seed Certification Agency (SCA)"), ("sca.portal.gov.bd", "Seed Certification Agency (SCA)"),
    ("dpp.gov.bd", "Bangladesh Government Press (Department of Printing and Publications)"),
    ("bdlaws.minlaw.gov.bd", "Legislative and Parliamentary Affairs Division (Laws of Bangladesh)"),
    ("ais.gov.bd", "Agriculture Information Service (AIS)"), ("dae.gov.bd", "Department of Agricultural Extension (DAE)"),
    ("bangladeshcustoms.gov.bd", "Bangladesh Customs"),
    ("glomip.cgiar.org", "CGIAR (GloMIP product catalogue)"), ("asti.cgiar.org", "ASTI, IFPRI (CGIAR)"),
    ("iaes.cgiar.org", "CGIAR Independent Advisory and Evaluation Service (SPIA)"), ("cgspace.cgiar.org", "CGIAR (CGSpace repository)"),
    ("cgiar.org", "CGIAR"), ("irri.org", "International Rice Research Institute (IRRI)"),
    ("worldfishcenter.org", "WorldFish"), ("harvestplus.org", "HarvestPlus"), ("africarice.org", "AfricaRice"),
    ("api.openalex.org", "OpenAlex"), ("api.crossref.org", "Crossref"), ("ebi.ac.uk", "Europe PMC (EMBL-EBI)"),
    ("iaea.org", "International Atomic Energy Agency (IAEA)"), ("fao.org", "Food and Agriculture Organization (FAO)"),
    ("dataverse.harvard.edu", "Harvard Dataverse"), ("fishinnovationlab.msstate.edu", "Feed the Future Fish Innovation Lab"),
    ("fnca.mext.go.jp", "Forum for Nuclear Cooperation in Asia (FNCA)"),
]
ISSUER_BY_FOLDER = {"sca": "Seed Certification Agency (SCA)", "sca_laws": "Seed Certification Agency (SCA)",
                    "sca_wayback": "Seed Certification Agency (SCA)", "moa": "Ministry of Agriculture (MoA)",
                    "moa_wayback": "Ministry of Agriculture (MoA)", "bgpress": "Bangladesh Government Press (Department of Printing and Publications)",
                    "gazette_weekly": "Bangladesh Government Press (Department of Printing and Publications)",
                    "brri": "Bangladesh Rice Research Institute (BRRI)", "brri_riceprofile": "Bangladesh Rice Research Institute (BRRI)",
                    "bina": "Bangladesh Institute of Nuclear Agriculture (BINA)", "bfri": "Bangladesh Fisheries Research Institute (BFRI)",
                    "fri": "Bangladesh Fisheries Research Institute (BFRI)", "mofl": "Ministry of Fisheries and Livestock (MoFL)",
                    "dof": "Department of Fisheries (DoF)", "fisheries": "Department of Fisheries (DoF)", "ais": "Agriculture Information Service (AIS)",
                    "wayback_cdx": "Internet Archive (Wayback Machine CDX index)"}


def issuing_body(path, url, doc_type=""):
    if doc_type == "NSB minutes":
        return "National Seed Board (NSB); secretariat Seed Certification Agency (SCA)"
    if doc_type == "TC minutes":
        return "Technical Committee of the National Seed Board; secretariat Seed Certification Agency (SCA)"
    h = original_host(url)
    for k, v in ISSUER_BY_HOST:
        if h == k or h.endswith("." + k):
            return v
    parts = path.split("/")
    sub = parts[2] if len(parts) > 3 and parts[1] == "fish_governance" else parts[1]
    return ISSUER_BY_FOLDER.get(sub, ISSUER_BY_FOLDER.get(parts[1], ""))


MONTHS = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}


def document_date(path):
    """Date written into the file name by the archiving agent (YYYY-MM-DD or DD-Mon-YYYY); blank otherwise."""
    name = pathlib.PurePosixPath(path).name
    m = re.search(r"(?<!\d)((?:19|20)\d\d)-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])(?!\d)", name)
    if m:
        return "-".join(m.groups())
    m = re.search(r"(?<!\d)(0[1-9]|[12]\d|3[01])-([A-Za-z]{3})-((?:19|20)\d\d)(?!\d)", name)
    if m and m.group(2).lower() in MONTHS:
        return f"{m.group(3)}-{MONTHS[m.group(2).lower()]:02d}-{m.group(1)}"
    return ""


def document_type(path, url):
    p = path.lower()
    name = pathlib.PurePosixPath(p).name
    ext = pathlib.PurePosixPath(p).suffix
    h = original_host(url)
    if p.startswith("02_raw/wayback_cdx/"):
        return "Wayback CDX listing"
    if is_api_response(path, url):
        return "API response"
    if ext in (".jpg", ".jpeg", ".png"):
        return "image"
    if "nsb_minutes" in name or "nsb_meeting" in name:
        return "NSB minutes"
    if "tc_minutes" in name or "technical_committee" in name:
        return "TC minutes"
    if "/sca/" in p and re.search(r"approved|registered|variet|hybrid|list|compendium", name):
        return "SCA list"
    if "/moa" in p and "hybrid" in name and ext == ".pdf":
        return "MoA hybrid list"
    if re.search(r"gazette|release_notification|/bgpress|weekly_", p) or h.endswith("dpp.gov.bd"):
        return "gazette"
    if re.search(r"(^|_|-)(act|acts|rules?|ordinance|sro\d*)(_|-|\.|$)", name) or "/bdlaws/" in p or "/sca_laws/" in p or "/faolex/" in p:
        return "act/rule"
    if re.search(r"notice|circular|prajnapan|letter|memo", name) and any(x in p for x in ("/dof/", "/mofl/", "/fisheries/")):
        return "government notice"
    if any(h == c or h.endswith("." + c) for c in CGIAR_HOSTS) or "/cgiar" in p or "/worldfish/" in p or "/spia_cgspace/" in p:
        return "CGIAR report" if ext in (".pdf", ".docx") else ("CGIAR dataset" if ext in (".xlsx", ".csv", ".zip") else "CGIAR web page")
    if "/literature" in p or h in ("www.banglajol.info", "www.frontiersin.org", "journals.plos.org", "linkinghub.elsevier.com"):
        return "journal article"
    if "/news" in p or h in ("www.tbsnews.net", "thefinancialexpress.com.bd"):
        return "news article"
    if any(h == g or h.endswith("." + g) for g in GOV_HOSTS) or any(f"/{x}/" in p for x in ("brri", "bina", "bfri", "fri", "brri_riceprofile", "dof", "fisheries", "mofl", "moa", "sca")):
        return "institute page" if ext in (".html", ".htm") else "government document"
    if ext in (".xlsx", ".csv", ".zip"):
        return "dataset"
    if ext in (".html", ".htm"):
        return "web page"
    return "document" if ext in (".pdf", ".docx", ".txt") else ""


BN = re.compile(r"[ঀ-৿]")
LAT = re.compile(r"[A-Za-z]")
BIJOY = re.compile(r"[‡ˆ‰Š†Ñ¨©]")   # characters that SutonnyMJ (Bijoy) text layers produce


def language(text):
    """bn | en | mixed from the share of Bangla letters; Bijoy-encoded text layers count as Bangla. Blank if under 40 letters."""
    if not text:
        return ""
    bn, lat, bij = len(BN.findall(text)), len(LAT.findall(text)), len(BIJOY.findall(text))
    if bij > 0.02 * max(lat, 1):
        bn, lat = bn + lat, 0
    tot = bn + lat
    if tot < 40:
        return ""
    s = bn / tot
    return "bn" if s >= 0.8 else ("en" if s <= 0.2 else "mixed")
