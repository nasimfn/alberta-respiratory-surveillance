"""
Step 1: Combine raw RVDSS season files into one table, WITHOUT changing any values.

Why: validation (step 2) must run on the data exactly as published, so that
problems in the source are detected rather than silently fixed. Cleaning
happens separately in step 3.

Input : data/raw/season_<YYYY>_<YYYY>_respiratory_detections.csv
Output: data/processed/combined_raw.csv
"""
import re
from pathlib import Path

import pandas as pd

RAW_DIR = Path("data/raw")
OUT_FILE = Path("data/processed/combined_raw.csv")


def combine_raw() -> pd.DataFrame:
    frames = []
    for f in sorted(RAW_DIR.glob("season_*_respiratory_detections.csv")):
        m = re.search(r"season_(\d{4})_(\d{4})", f.name)
        df = pd.read_csv(f, low_memory=False)
        df["season"] = f"{m.group(1)}-{m.group(2)}"
        df["source_file"] = f.name
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


if __name__ == "__main__":
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    combined = combine_raw()
    combined.to_csv(OUT_FILE, index=False)
    print(f"Combined {combined['season'].nunique()} seasons -> {len(combined):,} rows, "
          f"{combined.shape[1]} columns")
    print(f"Saved to {OUT_FILE}")
