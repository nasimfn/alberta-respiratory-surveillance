"""
Step 0: Download the raw data.

Source: public compilation of PHAC's Respiratory Virus Detection Surveillance System
(RVDSS) weekly reports, github.com/dajmcdon/rvdss-canada.
NOTE: this is a third-party compilation, not an official PHAC file.

Output: data/raw/season_<YYYY>_<YYYY>_respiratory_detections.csv  (12 seasons)
"""
from pathlib import Path
import urllib.request

BASE = "https://raw.githubusercontent.com/dajmcdon/rvdss-canada/main/data"
SEASONS = [f"{y}_{y + 1}" for y in range(2013, 2025)]
OUT = Path("data/raw")
OUT.mkdir(parents=True, exist_ok=True)

for s in SEASONS:
    url = f"{BASE}/season_{s}/respiratory_detections.csv"
    dest = OUT / f"season_{s}_respiratory_detections.csv"
    if dest.exists():
        print(f"already have {dest.name}")
        continue
    print(f"downloading {dest.name} ...")
    urllib.request.urlretrieve(url, dest)
print("Done.")
