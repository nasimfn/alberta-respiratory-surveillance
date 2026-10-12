"""
Step 2: Data quality validation on the combined RAW data.

Each check is a named rule. Failures are written to reports/qa_issues.csv
(one row per failing record) and summarised in reports/qa_summary.md.
Nothing is modified here; this script only reports.

Severity levels
  ERROR   - value is impossible or structurally invalid; must be fixed/excluded
  WARNING - suspicious or inconsistent; should be reviewed and documented
  INFO    - expected characteristic of the source; documented for users
"""
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from common import TEST_POSITIVE_PAIRS, mmwr_epiweek

IN_FILE = Path("data/processed/combined_raw.csv")
ISSUES_FILE = Path("reports/qa_issues.csv")
SUMMARY_FILE = Path("reports/qa_summary.md")

# C20 settings: viruses expected to be detected in every season by a lab testing at volume
ENDEMIC_VIRUSES = {"RSV", "Influenza A", "hMPV"}
C20_MIN_SEASON_TESTS = 5000

REQUIRED_COLUMNS = ["epiweek", "time_value", "issue", "geo_type", "geo_value", "season"]


issues = []  # list of dict records
checks_run = []  # (check_id, description, severity, n_failures)


def record(check_id, description, severity, failing: pd.DataFrame, detail=None):
    """Log every failing row for a check, and remember the check's totals."""
    n = len(failing)
    n_latest = int(failing["is_latest"].sum()) if "is_latest" in failing.columns else n
    checks_run.append((check_id, description, severity, n, n_latest))
    for idx, row in failing.iterrows():
        issues.append({
            "check_id": check_id,
            "severity": severity,
            "is_latest_revision": row.get("is_latest"),
            "season": row.get("season"),
            "epiweek": row.get("epiweek"),
            "geo_type": row.get("geo_type"),
            "geo_value": row.get("geo_value"),
            "detail": detail(row) if detail else description,
        })


def run_checks(df: pd.DataFrame) -> None:
    # --- C01: required columns --------------------------------------------------
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    checks_run.append(("C01", "Required columns present", "ERROR", len(missing_cols), len(missing_cols)))
    if missing_cols:
        raise SystemExit(f"Missing required columns: {missing_cols}")

    # --- C02/C03: date formats ---------------------------------------------------
    tv = pd.to_datetime(df["time_value"], format="%Y-%m-%d", errors="coerce")
    iss = pd.to_datetime(df["issue"], format="%Y-%m-%d", errors="coerce")
    record("C02", "time_value is a valid YYYY-MM-DD date", "ERROR", df[tv.isna()])
    record("C03", "issue is a valid YYYY-MM-DD date", "ERROR", df[iss.isna()])

    # --- C04: week ends on a Saturday (Sunday-Saturday surveillance weeks) -------
    not_sat = df[tv.notna() & (tv.dt.dayofweek != 5)]
    record("C04", "time_value falls on a Saturday", "ERROR", not_sat,
           lambda r: f"time_value={r['time_value']} is not a Saturday")

    # --- C05: epiweek format and agreement with the date ------------------------
    ew = pd.to_numeric(df["epiweek"], errors="coerce")
    bad_fmt = df[ew.isna() | (ew < 100001) | (ew > 999999) | ((ew % 100) < 1) | ((ew % 100) > 53)]
    record("C05", "epiweek is YYYYWW with week 01-53", "ERROR", bad_fmt)

    uniq_dates = tv.dropna().dt.date.unique()
    lookup = {d: mmwr_epiweek(d) for d in uniq_dates}
    derived = tv.dt.date.map(lambda d: lookup.get(d, (None, None)))
    derived_ew = derived.map(lambda t: t[0] * 100 + t[1] if t[0] else None)
    mismatch = df[(derived_ew.notna()) & (ew.notna()) & (derived_ew != ew)]
    record("C06", "epiweek matches the epi-week calculated from time_value", "ERROR", mismatch,
           lambda r: f"reported epiweek={int(r['epiweek'])}, time_value={r['time_value']}")

    # --- C07: issue date is not before the week it describes --------------------
    early = df[tv.notna() & iss.notna() & (iss < tv)]
    record("C07", "issue (revision) date is not before time_value", "ERROR", early)

    # --- C08: duplicate records ---------------------------------------------------
    key_full = ["epiweek", "issue", "geo_type", "geo_value"]
    dup_full = df[df.duplicated(key_full, keep=False)]
    record("C08", "No duplicate (epiweek, issue, geo_type, geo_value) records", "ERROR", dup_full)

    # --- C09: revisions (INFO) ---------------------------------------------------
    key_rev = ["epiweek", "geo_type", "geo_value"]
    n_issues = df.groupby(key_rev)["issue"].transform("nunique")
    revised = df[n_issues > 1]
    n_rev = revised[key_rev].drop_duplicates().shape[0]
    checks_run.append(("C09a", "Weeks published more than once (multiple issue dates)", "INFO", n_rev, n_rev))
    value_cols = [c for c in df.columns if c.endswith("_tests")]
    changed = revised.groupby(key_rev)[value_cols].nunique(dropna=False).max(axis=1)
    n_changed = int((changed > 1).sum())
    checks_run.append(("C09b", "...of which values actually changed between versions", "INFO", n_changed, n_changed))

    # --- count columns -----------------------------------------------------------
    count_cols = [c for c in df.columns if c.endswith("_tests")]
    counts = df[count_cols].apply(pd.to_numeric, errors="coerce")

    neg = df[(counts < 0).any(axis=1)]
    record("C10", "Counts are non-negative", "ERROR", neg)

    frac = df[(((counts % 1) != 0) & counts.notna()).any(axis=1)]  # exclude blanks (NaN != 0 is True)
    record("C11", "Counts are whole numbers", "ERROR", frac)

    # --- C12: positives cannot exceed tests ---------------------------------------
    for tests_col, pos_col, label in TEST_POSITIVE_PAIRS:
        if tests_col in df.columns and pos_col in df.columns:
            t = pd.to_numeric(df[tests_col], errors="coerce")
            p = pd.to_numeric(df[pos_col], errors="coerce")
            bad = df[(p > t)]
            record("C12", f"Positives <= tests ({label})", "ERROR", bad,
                   lambda r, a=tests_col, b=pos_col: f"{b}={r[b]} > {a}={r[a]}")

    # --- C13: positives reported without tests (or tests = 0 with positives) ------
    for tests_col, pos_col, label in TEST_POSITIVE_PAIRS:
        if tests_col in df.columns and pos_col in df.columns:
            t = pd.to_numeric(df[tests_col], errors="coerce")
            p = pd.to_numeric(df[pos_col], errors="coerce")
            bad = df[p.notna() & (p > 0) & (t.isna() | (t == 0))]
            record("C13", f"Positives reported without tests ({label})", "ERROR", bad)

    # --- C14: tests missing while positives present, per lab/region ---------------
    # (covered by C13). Missing-value profile is reported in the summary.

    # --- C15: influenza subtypes cannot exceed Influenza A ------------------------
    sub_cols = [c for c in ["fluah1n1pdm09_positive_tests", "fluah3_positive_tests",
                            "fluauns_positive_tests"] if c in df.columns]
    if sub_cols and "flua_positive_tests" in df.columns:
        sub_sum = df[sub_cols].apply(pd.to_numeric, errors="coerce").sum(axis=1, min_count=1)
        flua = pd.to_numeric(df["flua_positive_tests"], errors="coerce")
        bad = df[sub_sum.notna() & flua.notna() & (sub_sum > flua)]
        record("C15", "Sum of influenza A subtypes <= total Influenza A", "WARNING", bad,
               lambda r: "subtype sum exceeds total (PHAC notes subtyping may be done by other labs)")

    # --- C16: Influenza A + B vs total influenza -----------------------------------
    if {"flua_positive_tests", "flub_positive_tests", "flu_positive_tests"} <= set(df.columns):
        a = pd.to_numeric(df["flua_positive_tests"], errors="coerce")
        b = pd.to_numeric(df["flub_positive_tests"], errors="coerce")
        tot = pd.to_numeric(df["flu_positive_tests"], errors="coerce")
        bad = df[a.notna() & b.notna() & tot.notna() & ((a + b) != tot)]
        record("C16", "Influenza A + B equals total influenza positives", "WARNING", bad,
               lambda r: f"A={r['flua_positive_tests']}, B={r['flub_positive_tests']}, "
                         f"total={r['flu_positive_tests']}")

    # --- C17: geography labels -----------------------------------------------------
    geo = df["geo_value"].astype(str)
    odd = df[geo.str.contains(r"[^a-z0-9 \-\.\(\)àâçéèêëîïôûùüÿñæœ']", regex=True, case=False)
             | (geo.str.strip() != geo) | geo.isin(["province of", "nan", ""])]
    record("C17", "Geography labels are clean and complete", "WARNING", odd,
           lambda r: f"geo_value='{r['geo_value']}'")

    # --- C18: Alberta weekly continuity (no gaps within a season) ------------------
    ab = df[(df["geo_value"] == "ab")].copy()
    ab["tv"] = pd.to_datetime(ab["time_value"], errors="coerce")
    gap_rows = []
    for season, grp in ab.groupby("season"):
        dates = sorted(grp["tv"].dropna().unique())
        for prev, nxt in zip(dates, dates[1:]):
            gap = (nxt - prev).days
            if gap > 7:
                gap_rows.append({"season": season, "epiweek": None, "geo_type": "lab",
                                 "geo_value": "ab",
                                 "detail": f"{(gap // 7) - 1} missing week(s) between "
                                           f"{pd.Timestamp(prev).date()} and {pd.Timestamp(nxt).date()}"})
    gaps = pd.DataFrame(gap_rows)
    checks_run.append(("C18", "Alberta has no missing weeks within a season", "WARNING", len(gaps), len(gaps)))
    for _, r in gaps.iterrows():
        issues.append({"check_id": "C18", "severity": "WARNING", **r.to_dict()})

    # --- C19: recomputed positivity within 0-100% ----------------------------------
    for tests_col, pos_col, label in TEST_POSITIVE_PAIRS:
        if tests_col in df.columns and pos_col in df.columns:
            t = pd.to_numeric(df[tests_col], errors="coerce")
            p = pd.to_numeric(df[pos_col], errors="coerce")
            pct = (p / t.where(t > 0)) * 100
            bad = df[(pct < 0) | (pct > 100)]
            record("C19", f"Recomputed % positive within 0-100 ({label})", "ERROR", bad,
                   lambda r, a=tests_col, b=pos_col: f"{b}/{a} gives % outside 0-100")

    # --- C20: suspicious all-season zeros -----------------------------------------
    # A common virus with thousands of tests but zero positives in a whole season may be
    # "not reported" recorded as 0. Uses latest revision only, so repeated versions are not summed.
    latest = df[df["is_latest"] & (df["geo_type"] != "nation")]
    flagged_groups = []
    for tests_col, pos_col, label in TEST_POSITIVE_PAIRS:
        if label not in ENDEMIC_VIRUSES:
            continue
        grp = (latest.groupby(["season", "geo_type", "geo_value"])
               .agg(tests=(tests_col, "sum"), pos=(pos_col, "sum"), n_pos=(pos_col, "count"))
               .reset_index())
        hit = grp[(grp["tests"] >= C20_MIN_SEASON_TESTS) & (grp["pos"] == 0) & (grp["n_pos"] > 0)].copy()
        hit["epiweek"] = None
        hit["virus"] = label
        flagged_groups.append(hit)
    if flagged_groups:
        flagged = pd.concat(flagged_groups, ignore_index=True)
    else:
        flagged = pd.DataFrame(columns=["season", "geo_type", "geo_value", "epiweek", "tests", "virus"])
    record("C20", f"Common virus has >= {C20_MIN_SEASON_TESTS:,} tests but zero positives all season",
           "WARNING", flagged,
           lambda r: f"{r['virus']}: {int(r['tests']):,} tests, 0 positives in {r['season']} ({r['geo_value']})")


def missing_profile(df: pd.DataFrame) -> pd.DataFrame:
    prof = df.isna().mean().mul(100).round(1).rename("pct_missing").to_frame()
    prof["n_missing"] = df.isna().sum()
    return prof[prof["n_missing"] > 0].sort_values("pct_missing", ascending=False)


def write_reports(df: pd.DataFrame) -> None:
    ISSUES_FILE.parent.mkdir(parents=True, exist_ok=True)
    issues_df = pd.DataFrame(issues)
    issues_df.to_csv(ISSUES_FILE, index=False)

    summary = pd.DataFrame(checks_run, columns=["check_id", "description", "severity", "n_failures", "n_failures_latest"])
    prof = missing_profile(df)

    lines = ["# Data Quality Summary", "",
             f"- Records checked: **{len(df):,}**",
             f"- Seasons: **{df['season'].nunique()}** ({df['season'].min()} to {df['season'].max()})",
             f"- Checks run: **{len(summary)}**",
             f"- Checks with failures: **{(summary['n_failures'] > 0).sum()}**",
             "- 'All versions' counts every published revision; 'Latest' counts only the most recent revision of each week.", "",
             "## Results by check", "",
             "| Check | Description | Severity | Failures (all versions) | Failures (latest revision) |", "|---|---|---|---|---|"]
    for _, r in summary.iterrows():
        lines.append(f"| {r.check_id} | {r.description} | {r.severity} | {r.n_failures:,} | {r.n_failures_latest:,} |")
    lines += ["", "## Missing values (columns with any missing)", "",
              "| Column | % missing | Count |", "|---|---|---|"]
    for col, r in prof.iterrows():
        lines.append(f"| {col} | {r.pct_missing} | {int(r.n_missing):,} |")
    SUMMARY_FILE.write_text("\n".join(lines))

    print(summary[summary["n_failures"] > 0].to_string(index=False))
    print(f"\nIssue log: {ISSUES_FILE} ({len(issues_df):,} rows)")
    print(f"Summary  : {SUMMARY_FILE}")


if __name__ == "__main__":
    data = pd.read_csv(IN_FILE, low_memory=False)
    rev_key = ["epiweek", "geo_type", "geo_value"]
    data["is_latest"] = data["issue"] == data.groupby(rev_key)["issue"].transform("max")
    run_checks(data)
    write_reports(data)
