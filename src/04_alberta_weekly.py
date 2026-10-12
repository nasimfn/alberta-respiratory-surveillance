"""
Step 4: Build the Alberta weekly table.

Takes the cleaned data, keeps Alberta, and lays it on a COMPLETE weekly calendar
for each season (first to last reported week). Weeks with no data appear as rows
with missing_week = True. They are NOT filled with estimates.

Input : data/processed/clean.csv
Output: data/processed/alberta_weekly.csv
"""
from pathlib import Path

import pandas as pd

from common import mmwr_epiweek

IN_FILE = Path("data/processed/clean.csv")
OUT_FILE = Path("data/processed/alberta_weekly.csv")

KEEP = [
    "flu_tests", "flua_positive_tests", "flub_positive_tests", "flu_total_positive",
    "flu_total_pct_positive", "flua_pct_positive", "flub_pct_positive",
    "rsv_tests", "rsv_positive_tests", "rsv_pct_positive",
    "sarscov2_tests", "sarscov2_positive_tests", "sarscov2_pct_positive",
    "adv_tests", "adv_positive_tests", "adv_pct_positive",
    "hmpv_tests", "hmpv_positive_tests", "hmpv_pct_positive",
    "evrv_tests", "evrv_positive_tests", "evrv_pct_positive",
    "hcov_tests", "hcov_positive_tests", "hcov_pct_positive",
]


def main():
    df = pd.read_csv(IN_FILE, parse_dates=["time_value", "issue"], low_memory=False)
    ab = df[(df["geo_value"] == "ab") & (df["geo_type"] == "lab")]

    seasons = []
    for season, grp in ab.groupby("season"):
        calendar = pd.DataFrame({"time_value": pd.date_range(grp["time_value"].min(),
                                                             grp["time_value"].max(), freq="7D")})
        calendar["season"] = season
        seasons.append(calendar.merge(grp, on=["season", "time_value"], how="left"))
    out = pd.concat(seasons, ignore_index=True)

    out["missing_week"] = out["epiweek"].isna()
    # epiweek is blank for missing weeks, so recompute it from the date for every row
    out["epiweek"] = out["time_value"].map(
        lambda d: (lambda y, w: y * 100 + w)(*mmwr_epiweek(d.date())))
    out["geo_inferred"] = out["geo_inferred"].fillna(False)
    out = out[["season", "epiweek", "time_value", "missing_week", "geo_inferred", "qa_flags"] + KEEP]
    out.to_csv(OUT_FILE, index=False)

    print(f"Alberta weekly table: {len(out):,} weeks, {out['season'].nunique()} seasons")
    print(f"Weeks with no data (left blank, not estimated): {int(out['missing_week'].sum())}")
    print(f"Weeks with an inferred label: {int(out['geo_inferred'].sum())}")
    print(f"Saved {OUT_FILE}")


if __name__ == "__main__":
    main()
