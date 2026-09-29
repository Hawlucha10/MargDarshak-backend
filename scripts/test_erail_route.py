import urllib.request
import json
import re

# Test fetching complete route for 22182 from public open train route endpoint
url = "https://erail.in/data.aspx?Action=TRAINROUTE&TrainNo=22182"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

try:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as resp:
        content = resp.read().decode("utf-8", errors="ignore")
        print(f"Response length: {len(content)}")
        print("Sample content:")
        print(content[:500])
except Exception as e:
    print(f"Error: {e}")
