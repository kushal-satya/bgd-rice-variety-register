"""Polite fetch helper for RB discovery. Usage: python phase0_RB_fetch.py URL [outname]
Prints status, visible text (trimmed) and links. Saves HTML to scratchpad."""
import requests, re, sys, time, os, html
UA = "Mozilla/5.0 (research archive; contact via https://github.com/kushal-satya/bgd-rice-variety-register) python-requests"
SCR = str(__import__("pathlib").Path(__file__).resolve().parents[1] / "logs" / "phase0_scratch")   # working files of the phase-0 crawl
url = sys.argv[1]
out = sys.argv[2] if len(sys.argv) > 2 else None
time.sleep(2.5)
r = requests.get(url, headers={"User-Agent": UA}, timeout=90, verify=False)
print("STATUS", r.status_code, r.headers.get("content-type"), len(r.content), r.url)
if out:
    open(os.path.join(SCR, out), "wb").write(r.content)
if "html" in (r.headers.get("content-type") or ""):
    t = r.text
    body = re.sub(r"(?s)<(script|style)[^>]*>.*?</\1>", " ", t)
    m = re.search(r'(?s)id="main-content".*', body)
    seg = m.group(0) if m else body
    txt = html.unescape(re.sub(r"<[^>]+>", " ", seg))
    txt = re.sub(r"\s+", " ", txt)
    print("TEXT:", txt[: int(os.environ.get("NTXT", "4000"))])
    links = set()
    for h, a in re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', seg, re.S):
        a = html.unescape(re.sub("<[^>]+>", "", a)).strip()
        if any(k in h.lower() for k in (".pdf", ".doc", ".xls", "upload", "files", "storage")) or os.environ.get("ALL"):
            links.add((h, a[:80]))
    for h, a in sorted(links):
        print("LINK", h, "|", a)
