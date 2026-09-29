import pypdf
import re
from pathlib import Path

pdf_path = Path("D:/Sih58/NishkarshFoundData/Content/Station_Code_Index.pdf")
reader = pypdf.PdfReader(str(pdf_path))
print(f"Total pages: {len(reader.pages)}")

stations = {}
for p_idx, p in enumerate(reader.pages):
    text = p.extract_text()
    lines = text.split("\n")
    print(f"Page {p_idx+1}: {len(lines)} lines")
    for line in lines:
        line = line.strip()
        # Look for station name and code
        m = re.match(r"^(.*?)\s+([A-Z0-9]{1,6})$", line)
        if m:
            name, code = m.group(1).strip(), m.group(2).strip()
            if not name.startswith("TAG-") and name != "Station Name":
                stations[name.upper()] = code

print(f"Total parsed stations: {len(stations)}")

# Check key stations
for test_name in ["PUNE", "RAIPUR", "KOTA", "SAWAI MADHOPUR", "LUCKNOW", "JHANSI", "VIRANGANA LAKSHMIBAI", "GWALIOR", "NEW DELHI", "DELHI", "MUMBAI CSMT", "AYODHYA"]:
    found = [f"{k} -> {v}" for k, v in stations.items() if test_name in k]
    print(f"Query '{test_name}': {found}")
