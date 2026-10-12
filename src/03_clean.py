"""
Step 3: Clean the combined raw data.

Every cleaning decision is a named setting below so it is visible, can be
changed, and is written to the cleaning log. Nothing is fixed silently.

Input : data/processed/combined_raw.csv
Output: data/processed/clean.csv
        data/processed/revisions_superseded.csv   (older versions of revised weeks, kept for audit)
        reports/cleaning_log.md                    (what changed, and how many rows)
"""
from pathlib import Path

import pandas as pd

from common import TEST_POSITIVE_PAIRS

# ----------------------------------------------------------------------------------
# DECISIONS (change these and rerun to see the effect)
# ----------------------------------------------------------------------------------
# 1. Revisions: the source republishes weeks when labs correct their numbers.
#    "latest" keeps only the most recent version of each week.
REVISION_POLICY = "latest"

# 2. One record has the truncated label 'province of'. Its values continue Alberta's
#    trend in the neighbouring weeks, and it sits exactly where Alberta has a missing
#    week. True = relabel as 'ab' and flag it as inferred. False = leave unchanged.
RELABEL_PROVINCE_OF_AS_AB = True

# 3. Positives greater than tests are impossible. We cannot tell which number is wrong.
#    "null_positive": blank the positive count, keep the row and the tests count
#    "flag_only"    : keep every value, just flag it
#    "drop_row"     : remove the whole row
BAD_COUNT_POLICY = "null_positive"

# 4. Alberta reports RSV positives as 0 in every week of 2017-18 to 2020-21 while testing tens
#    of thousands of specimens; BC, SK, MB and ON report thousands of RSV positives in the
#    same seasons (validation check C20). These zeros look like "not reported".
#    Each entry is (geo_value, positive column, seasons).
#    SUSPECT_ZERO_POLICY: "flag_only" keeps the values as published and only flags them;
#                         "blank" sets them to blank (treated as not reported).
#    Caution: RSV did largely disappear in 2020-21 during pandemic restrictions, so zeros in
#    that season may be partly real.
#    DECISION (analyst): keep values as published and flag them.
SUSPECT_ZERO_POLICY = "flag_only"
SUSPECT_ZERO_SERIES = [
    ("ab", "rsv_positive_tests", ["2017-2018", "2018-2019", "2019-2020", "2020-2021"]),
]
# ----------------------------------------------------------------------------------

IN_FILE = Path("data/processed/combined_raw.csv")
OUT_FILE = Path("data/processed/clean.csv")
REVISIONS_FILE = Path("data/processed/revisions_superseded.csv")
LOG_FILE = Path("reports/cleaning_log.md")

REVISION_KEY = ["epiweek", "geo_type", "geo_value"]
HELPER_COLS_TO_DROP = ["week", "weekorder", "year"]  # inconsistent across seasons; derivable

log = []


def note(step, rows_before, rows_after, detail):
    log.append((step, rows_before, rows_after, detail))


def main():
    df = pd.read_csv(IN_FILE, low_memory=False)
    note("Load combined raw data", len(df), len(df), f"{df['season'].nunique()} seasons")

    # --- 1. Standardise text labels ------------------------------------------------
    n = len(df)
    df["geo_value"] = df["geo_value"].astype(str).str.strip().str.lower()
    df["geo_inferred"] = False
    if RELABEL_PROVINCE_OF_AS_AB:
        mask = df["geo_value"] == "province of"
        df.loc[mask, "geo_value"] = "ab"
        df.loc[mask, "geo_inferred"] = True
        note("Relabel truncated 'province of' as 'ab'", n, len(df),
             f"{int(mask.sum())} row(s) relabelled and flagged geo_inferred=True")

    # --- 2. Types and derived calendar fields --------------------------------------
    n = len(df)
    df["time_value"] = pd.to_datetime(df["time_value"], format="%Y-%m-%d")
    df["issue"] = pd.to_datetime(df["issue"], format="%Y-%m-%d")
    df["epiweek"] = df["epiweek"].astype(int)
    df["epi_year"] = df["epiweek"] // 100
    df["epi_week"] = df["epiweek"] % 100
    df = df.drop(columns=[c for c in HELPER_COLS_TO_DROP if c in df.columns])
    note("Parse dates, derive epi_year / epi_week, drop inconsistent helper columns",
         n, len(df), f"dropped columns: {HELPER_COLS_TO_DROP}")

    # --- 3. Revisions --------------------------------------------------------------
    n = len(df)
    if REVISION_POLICY == "latest":
        latest = df.groupby(REVISION_KEY)["issue"].transform("max")
        superseded = df[df["issue"] < latest]
        df = df[df["issue"] == latest].copy()
        superseded.to_csv(REVISIONS_FILE, index=False)
        note("Keep latest revision of each week", n, len(df),
             f"{len(superseded):,} superseded rows moved to {REVISIONS_FILE.name}")

    # --- 4. Impossible counts (positives > tests) ----------------------------------
    n = len(df)
    df["qa_flags"] = ""
    n_flagged = 0
    to_drop = pd.Series(False, index=df.index)
    for tests_col, pos_col, label in TEST_POSITIVE_PAIRS:
        if tests_col not in df.columns or pos_col not in df.columns:
            continue
        bad = df[pos_col] > df[tests_col]
        if not bad.any():
            continue
        n_flagged += int(bad.sum())
        df.loc[bad, "qa_flags"] += f"{pos_col}>tests;"
        if BAD_COUNT_POLICY == "null_positive":
            df.loc[bad, pos_col] = pd.NA
        elif BAD_COUNT_POLICY == "drop_row":
            to_drop |= bad
    if BAD_COUNT_POLICY == "drop_row":
        df = df[~to_drop]
    note(f"Handle positives > tests (policy: {BAD_COUNT_POLICY})", n, len(df),
         f"{n_flagged} impossible value(s) found")


    # --- 4b. Suspect all-season zeros (explicit, reviewed decision) -----------------
    n = len(df)
    n_blanked = 0
    for geo, col, seasons in SUSPECT_ZERO_SERIES:
        m = (df["geo_value"] == geo) & df["season"].isin(seasons) & (df[col] == 0)
        if SUSPECT_ZERO_POLICY == "blank":
            df.loc[m, col] = pd.NA
        df.loc[m, "qa_flags"] += f"{col}:suspect_zero;"
        n_blanked += int(m.sum())
    note(f"Flag suspect all-season zeros (policy: {SUSPECT_ZERO_POLICY})", n, len(df),
         f"{n_blanked} value(s) flagged" + (" and set to blank" if SUSPECT_ZERO_POLICY == "blank" else ", values kept as published"))

    # --- 5. Derived fields -----------------------------------------------------------
    n = len(df)
    # Total influenza positives: use the reported total where present, else A + B.
    # (Validation check C16 showed A + B equals the reported total wherever both exist.)
    total = df["flu_positive_tests"]
    df["flu_total_positive"] = total.fillna(df["flua_positive_tests"] + df["flub_positive_tests"])

    # Percent positive, recomputed from counts; blank when there were no tests.
    for tests_col, pos_col, _ in TEST_POSITIVE_PAIRS:
        pct_col = pos_col.replace("_positive_tests", "_pct_positive")
        df[pct_col] = (df[pos_col] / df[tests_col].where(df[tests_col] > 0) * 100).round(2)
    df["flu_total_pct_positive"] = (
        df["flu_total_positive"] / df["flu_tests"].where(df["flu_tests"] > 0) * 100).round(2)
    note("Add flu_total_positive and recomputed % positive columns", n, len(df),
         "% positive is blank when tests = 0 or missing")

    # --- 6. Counts as whole numbers ---------------------------------------------------
    count_cols = [c for c in df.columns if c.endswith("_tests") or c.endswith("flu_total_positive")]
    for c in count_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")
    note("Store counts as whole numbers (blank stays blank)", len(df), len(df), f"{len(count_cols)} columns")

    df = df.sort_values(["geo_type", "geo_value", "time_value"]).reset_index(drop=True)
    df.to_csv(OUT_FILE, index=False)

    lines = ["# Cleaning Log", "",
             f"Settings: REVISION_POLICY=`{REVISION_POLICY}`, "
             f"RELABEL_PROVINCE_OF_AS_AB=`{RELABEL_PROVINCE_OF_AS_AB}`, "
             f"BAD_COUNT_POLICY=`{BAD_COUNT_POLICY}`, "
             f"SUSPECT_ZERO_POLICY=`{SUSPECT_ZERO_POLICY}`", "",
             "| Step | Rows before | Rows after | Detail |", "|---|---|---|---|"]
    for step, b, a, d in log:
        lines.append(f"| {step} | {b:,} | {a:,} | {d} |")
    LOG_FILE.write_text("\n".join(lines))
    print("\n".join(lines))
    print(f"\nSaved {OUT_FILE} ({len(df):,} rows)")


if __name__ == "__main__":
    main()
