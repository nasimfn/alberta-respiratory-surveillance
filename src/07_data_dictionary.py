"""
Step 7: Build the data dictionary for data/processed/alberta_weekly.csv.

Descriptions are written by hand below. Data types and the share of blank values are
computed from the real file, and the script stops with an error if any column in the
data has no description (or a description has no column), so the dictionary cannot
silently drift out of date.

Output: docs/data_dictionary.csv, docs/data_dictionary.md
"""
from pathlib import Path

import pandas as pd

DATA = Path("data/processed/alberta_weekly.csv")
OUT_DIR = Path("docs")

SRC = "RVDSS compilation (dajmcdon/rvdss-canada)"
DERIVED = "Derived in this project"

VIRUS_NOTES = {
    "flu": "influenza", "rsv": "respiratory syncytial virus (RSV)", "sarscov2": "SARS-CoV-2 (COVID-19)",
    "adv": "adenovirus", "hmpv": "human metapneumovirus (hMPV)",
    "evrv": "enterovirus/rhinovirus (EV/RV)",
    "hcov": "seasonal human coronavirus (229E, OC43, NL63, HKU1; does not include SARS-CoV-2)",
}

# column -> (description, source, transformation / notes)
DESCRIPTIONS = {
    "season": ("Surveillance season, written YYYY-YYYY. A season starts in epidemiological week 35 "
               "(late August) and runs about 52 weeks.", SRC,
               "Taken from the name of the source file each row came from."),
    "epiweek": ("Epidemiological week as YYYYWW (year and week number). Weeks run Sunday to Saturday.", SRC,
                "Recalculated from time_value for every row, including weeks with no data. "
                "For weeks with data it matches the source value (QA check C06 found no mismatches)."),
    "time_value": ("Date of the last day (Saturday) of the surveillance week.", SRC,
                   "Parsed to a date. Weeks with no data are added from a complete weekly calendar."),
    "missing_week": ("True if no Alberta record exists for this week. All count and percent columns "
                     "are blank on these rows.", DERIVED,
                     "Added by building a complete weekly calendar for each season. Missing weeks "
                     "are not estimated or filled."),
    "geo_inferred": ("True for the one record whose source label was truncated ('province of') and "
                     "was treated as Alberta.", DERIVED,
                     "Inference, not a source fact: its values continue Alberta's trend in the "
                     "neighbouring weeks and it falls in a week where Alberta otherwise has no row. "
                     "Switch off with RELABEL_PROVINCE_OF_AS_AB in src/03_clean.py."),
    "qa_flags": ("Data quality flags for this row, separated by semicolons. Blank means no flag.", DERIVED,
                 "Set by src/03_clean.py. 'rsv_positive_tests:suspect_zero' marks Alberta RSV positives "
                 "reported as 0 in 2017-18 to 2020-21 (QA check C20); values are kept as published."),
    "flu_total_positive": ("Total specimens positive for influenza (types A and B combined).", DERIVED,
                           "Uses the source's reported total where present, otherwise influenza A + B. "
                           "QA check C16 found A + B equals the reported total wherever all three exist."),
    "flu_total_pct_positive": ("Percent of influenza tests that were positive.", DERIVED,
                               "flu_total_positive / flu_tests * 100, rounded to 2 decimals. "
                               "Blank when tests are 0 or missing."),
}

for prefix, virus in VIRUS_NOTES.items():
    DESCRIPTIONS[f"{prefix}_tests"] = (
        f"Number of specimens tested for {virus} in the week.", SRC,
        "Whole number. Blank means not reported." + (
            " Alberta reports SARS-CoV-2 from the 2022-23 season onward; earlier seasons are blank by design."
            if prefix == "sarscov2" else ""))
    if prefix != "flu":
        DESCRIPTIONS[f"{prefix}_positive_tests"] = (
            f"Number of specimens positive for {virus} in the week.", SRC,
            "Whole number. Positives greater than tests are set to blank (QA check C12)."
            + (" RSV: see qa_flags for flagged zeros." if prefix == "rsv" else ""))
        DESCRIPTIONS[f"{prefix}_pct_positive"] = (
            f"Percent of {virus} tests that were positive.", DERIVED,
            f"{prefix}_positive_tests / {prefix}_tests * 100, rounded to 2 decimals. "
            "Blank when tests are 0 or missing. The source file has no percentage columns.")

DESCRIPTIONS["flua_positive_tests"] = ("Number of specimens positive for influenza A in the week.", SRC,
                                       "Whole number. Positives greater than tests are set to blank (QA check C12).")
DESCRIPTIONS["flub_positive_tests"] = ("Number of specimens positive for influenza B in the week.", SRC,
                                       "Whole number. Positives greater than tests are set to blank (QA check C12).")
DESCRIPTIONS["flua_pct_positive"] = ("Percent of influenza tests that were positive for influenza A.", DERIVED,
                                     "flua_positive_tests / flu_tests * 100, rounded to 2 decimals.")
DESCRIPTIONS["flub_pct_positive"] = ("Percent of influenza tests that were positive for influenza B.", DERIVED,
                                     "flub_positive_tests / flu_tests * 100, rounded to 2 decimals.")


def friendly_type(col, series):
    if col == "time_value":
        return "date (YYYY-MM-DD)"
    if col in ("missing_week", "geo_inferred"):
        return "boolean"
    if col == "epiweek":
        return "integer (YYYYWW)"
    if col.endswith("_pct_positive"):
        return "decimal (percent)"
    if col in ("season", "qa_flags"):
        return "text"
    return "integer (count)"


def main():
    df = pd.read_csv(DATA)
    undocumented = set(df.columns) - set(DESCRIPTIONS)
    unused = set(DESCRIPTIONS) - set(df.columns)
    if undocumented or unused:
        raise SystemExit(f"Dictionary out of sync. Undocumented columns: {sorted(undocumented)}; "
                         f"descriptions with no column: {sorted(unused)}")

    reported = df[~df["missing_week"]]
    rows = []
    for col in df.columns:
        desc, src, note = DESCRIPTIONS[col]
        rows.append({
            "field": col,
            "type": friendly_type(col, df[col]),
            "description": desc,
            "source": src,
            "transformation_notes": note,
            "pct_blank_in_reported_weeks": round(reported[col].isna().mean() * 100, 1),
        })
    out = pd.DataFrame(rows)

    OUT_DIR.mkdir(exist_ok=True)
    out.to_csv(OUT_DIR / "data_dictionary.csv", index=False)

    lines = ["# Data Dictionary: `data/processed/alberta_weekly.csv`", "",
             f"One row per week per season for Alberta ({len(df):,} rows, {df['season'].nunique()} seasons). "
             f"{int(df['missing_week'].sum())} weeks have no data and are shown as blank rows.", "",
             "Blank in a count column means not reported. `pct_blank` is calculated over weeks that have data.", "",
             "| Field | Type | Description | Source | Notes | % blank |", "|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| `{r['field']}` | {r['type']} | {r['description']} | {r['source']} | "
                     f"{r['transformation_notes']} | {r['pct_blank_in_reported_weeks']} |")
    (OUT_DIR / "data_dictionary.md").write_text("\n".join(lines))
    print(f"Documented {len(out)} fields -> {OUT_DIR}/data_dictionary.csv and .md")


if __name__ == "__main__":
    main()
