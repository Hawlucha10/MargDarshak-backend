import urllib.request
import ssl
import json
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# Test NTES official schedule query
urls_to_test = [
    "https://enquiry.indianrail.gov.in/mntes/q?opt=TrainSchedule&subOpt=show&trainNo=22182",
    "https://enquiry.indianrail.gov.in/ntes/NTES?action=getTrainData&trainNo=22182",
]

for url in urls_to_test:
    print(f"Testing URL: {url}")
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            data = resp.read().decode("utf-8", errors="ignore")
            print(f"  Status {resp.status}, length: {len(data)}")
            # look for stations
            found = re.findall(r"\b(Lalitpur|Bina|Malkhedi|Saugor|Katni|Jabalpur|NZM|VGLJ)\b", data, re.I)
            print(f"  Found keywords: {set(found)}")
            if len(data) > 0 and len(data) < 2000:
                print(f"  Snippet: {data[:300]}")
    except Exception as e:
        print(f"  Error: {e}")
