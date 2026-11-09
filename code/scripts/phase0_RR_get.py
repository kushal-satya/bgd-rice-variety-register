import requests, sys, re, time
from bs4 import BeautifulSoup
UA = "Mozilla/5.0 (research archive; contact via https://github.com/kushal-satya/bgd-rice-variety-register) python-requests"
def get(u):
    r = requests.get(u, headers={"User-Agent": UA}, timeout=60, verify=False)
    return r
if __name__ == "__main__":
    for u in sys.argv[1:]:
        r = get(u)
        print("==", u, r.status_code, r.headers.get("content-type"), len(r.content))
        if "html" in (r.headers.get("content-type") or ""):
            s = BeautifulSoup(r.text, "html.parser")
            print("TITLE:", s.title.string if s.title else None)
            seen=set()
            for a in s.find_all("a", href=True):
                t = a.get_text(" ", strip=True)[:90]; h=a["href"]
                if (t,h) in seen: continue
                seen.add((t,h)); print(f"  {t} -> {h}")
        time.sleep(2.5)
