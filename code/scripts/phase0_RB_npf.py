"""Fetch a bangladesh.gov.bd-style (new NPF) static page and print its main content text + content links.
Usage: python phase0_RB_npf.py URL outname"""
import requests, re, sys, time, os, html
UA = "Mozilla/5.0 (research archive; contact via https://github.com/kushal-satya/bgd-rice-variety-register) python-requests"
SCR = str(__import__("pathlib").Path(__file__).resolve().parents[1] / "logs" / "phase0_scratch")   # working files of the phase-0 crawl
url, out = sys.argv[1], sys.argv[2]
time.sleep(2.5)
r = requests.get(url, headers={"User-Agent": UA}, timeout=90, verify=False)
open(os.path.join(SCR, out), "wb").write(r.content)
t = r.text
print("STATUS", r.status_code, len(r.content))
m = re.search(r"শেষ হাল-নাগাদ করা হয়েছে:([^<]+)", t)
print("UPDATED", m.group(1).strip() if m else None)
i = t.find("কন্টেন্ট:")
j = t.find("এই কনটেন্টটি শেয়ার", i)
seg = t[i:j] if i > 0 else t
seg = re.sub(r'="[A-Za-z0-9+/=]{200,}"', '=""', seg)
seg2 = re.sub(r"</(tr|p|div|li|h\d)>", "\n", seg)
seg2 = re.sub(r"</t[dh]>", " | ", seg2)
txt = html.unescape(re.sub(r"<[^>]+>", " ", seg2))
txt = re.sub(r"[ \t\xa0]+", " ", txt)
txt = re.sub(r"\n\s*\n+", "\n", txt)
print(txt[: int(os.environ.get("NTXT", "6000"))])
for h, a in re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', seg, re.S):
    print("LINK", h, "|", html.unescape(re.sub("<[^>]+>", "", a)).strip()[:80])
for h in re.findall(r'(?:src|data)="([^"]+\.(?:pdf|jpg|png|jpeg))"', seg):
    print("EMBED", h)
