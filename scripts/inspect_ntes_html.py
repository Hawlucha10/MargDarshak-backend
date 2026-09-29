import urllib.request
import ssl
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

url = "https://enquiry.indianrail.gov.in/mntes/q?opt=TrainSchedule&subOpt=show&trainNo=22182"
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
    html = resp.read().decode("utf-8", errors="ignore")

# Find table or text
print(f"HTML length: {len(html)}")
lines = [l.strip() for l in html.split("\n") if l.strip()]
for l in lines[:40]:
    print(f"  {l[:100]}")

# Look for table rows
tables = re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.DOTALL | re.I)
print(f"Found {len(tables)} table rows")
for tr in tables[:15]:
    # extract cell text
    cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.DOTALL | re.I)
    clean_cells = [re.sub(r"<[^>]+>", "", c).strip() for c in cells]
    if any(clean_cells):
        print("  ROW:", clean_cells)
