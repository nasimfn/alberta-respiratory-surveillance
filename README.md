# Alberta Respiratory Virus Surveillance: Data Quality & Reporting Pipeline

A reproducible workflow that takes 12 seasons of weekly respiratory virus laboratory data, checks it
against explicit quality rules, documents every cleaning decision, and produces Alberta weekly
surveillance tables, SQL queries and report charts.

**This is a personal portfolio project built on public data.** It is not work experience, it does not
use any Alberta Health or Government of Alberta internal data, and nothing here is an official
surveillance product.

## Why this project

Surveillance reporting is only as reliable as the data behind it. The aim here was to practise the part
of the work that comes before any chart: validating the data, deciding what to do with problems,
writing those decisions down, and making the whole process repeatable by someone else.

## Data source

- **Source:** Public Health Agency of Canada (PHAC), Respiratory Virus Detection Surveillance System
  (RVDSS): weekly laboratory tests and positive detections, by reporting laboratory or region.
- **Access:** a public third-party compilation of the weekly PHAC reports,
  [dajmcdon/rvdss-canada](https://github.com/dajmcdon/rvdss-canada), seasons 2013-14 to 2024-25.
  **This is not an official PHAC file.**
- **Spot check:** Alberta values for the week ending 2022-04-30 were compared with PHAC's published
  report for that week (flu tested 2,592, flu A positive 227, RSV tested 1,021, RSV positive 90) and matched.
  Only one week was checked, so this supports but does not prove the compilation is accurate.
- **Not redistributed:** raw data is downloaded by `src/00_download_data.py`, not stored in this repository.
  Check the source's terms of use before reusing it.
- **Official files:** PHAC's current national file and data dictionary were reviewed for reference.
  The national lab file available at the time held only the first weeks of the 2026-27 season, so the
  historical compilation was used for this analysis.

## What the pipeline does

| Script | Purpose |
|---|---|
| `src/00_download_data.py` | Download the 12 season files |
| `src/01_combine_raw.py` | Combine them into one table without changing any value |
| `src/02_validate.py` | Run the data quality checks on the raw data; write `reports/qa_summary.md` and `reports/qa_issues.csv` |
| `src/03_clean.py` | Apply documented cleaning decisions; write `reports/cleaning_log.md` |
| `src/04_alberta_weekly.py` | Build the Alberta table on a complete weekly calendar |
| `src/05_run_sql.py` | Run `sql/queries.sql` (SQLite) and save results to `reports/sql/` |
| `src/06_charts.py` | Draw the report charts in `reports/figures/` |
| `src/07_data_dictionary.py` | Build `docs/data_dictionary.md/.csv`; stops with an error if a column is undocumented |
| `src/08_summary_pdf.py` | Build the 2-page PDF project summary in `docs/` |

Validation deliberately runs on the **raw** data, before cleaning, so that source problems are found
and reported rather than quietly fixed.

## Key findings

All numbers below come from `reports/qa_summary.md` and `reports/cleaning_log.md`.

1. **Many records are republished versions.** Of 68,862 raw rows, 44,034 are earlier versions of a week
   that was published again. 2,050 weeks were published more than once, but only 990 had values that
   actually changed. One week appears in up to 46 versions (2024-25 stores weekly snapshots).
2. **Alberta reports zero RSV positives for four seasons.** In every week of 2017-18 to 2020-21,
   Alberta records 0 RSV positives while testing 32,000 to 102,000 specimens per season. In
   2017-18 to 2019-20, BC, Saskatchewan, Manitoba and Ontario report hundreds to thousands of RSV
   positives per season (for example BC 721, 1,468 and 2,512; Ontario 2,157 to 3,444), so Alberta's
   zeros in those three seasons stand out. In 2020-21 the same provinces report only 4 to 67, so
   Alberta's zeros that season are consistent with RSV largely disappearing during pandemic
   restrictions. The cause of the earlier zeros is unknown; it may be "not reported" recorded as
   zero. (Chart 4; check C20.)
3. **Alberta is missing 8 weeks across 12 seasons.** Five of the eight fall in the last two weeks of
   December. The source does not give a reason. The weeks are left blank, not estimated.
4. **53 impossible counts** (more positives than tests) at laboratories outside Alberta, for several
   viruses. None are in the Alberta data.
5. **Nothing found** on: invalid or non-Saturday dates, duplicate records, negative or fractional counts,
   epiweek values that disagree with the date, or influenza A + B not matching the reported total.
6. **One truncated label** (`province of`) whose values continue Alberta's trend; treated as Alberta
   and flagged (see decisions).
7. **Observation, not investigated:** Alberta influenza testing falls from about 3,700 to 1,600 tests a
   week in early June 2025.

## Decisions and why

Each decision is a named setting at the top of `src/03_clean.py`, so it can be changed and rerun.

| Decision | Choice | Reason |
|---|---|---|
| Weeks published more than once | Keep the latest version; older versions saved to `revisions_superseded.csv` | Latest is the best available figure; nothing is deleted |
| Truncated label `province of` | Relabel as Alberta, flag `geo_inferred = True` | Its values continue Alberta's trend and it sits in Alberta's only gap that season. This is an inference, so it is flagged. Set `RELABEL_PROVINCE_OF_AS_AB = False` to undo |
| Positives greater than tests | Blank the positive count, keep the row and the tests count | Which number is wrong is unknown; tests is shared by several virus columns, so the rest of the row is kept |
| Alberta RSV zeros (2017-18 to 2020-21) | Keep as published and flag in `qa_flags` | Cause cannot be established from the data, and 2020-21 matches other provinces' near-zero RSV; flagged on every table and chart instead of being changed |
| Missing weeks | Leave blank, show as `missing_week = True` | Estimating them would put numbers in the data that nobody measured |

## Limitations

- The data is a third-party compilation of PHAC reports, checked against the source for one week only.
- RVDSS is a sentinel laboratory system. Counts do not represent all testing in Alberta and cannot be
  read as case counts.
- Alberta's own respiratory dashboard may use different definitions. This project did not assume the
  two match, and it does not reproduce Alberta's dashboard.
- Percent positive is recomputed here from counts (positives divided by tests). The source file has no
  percentage columns.
- Data ends with the 2024-25 season. Values can be revised after publication.
- The RSV zeros for 2017-18 to 2020-21 appear in tables and charts as published; read them with the flag.
- Influenza subtype counts can exceed the Influenza A total because PHAC notes that some labs subtype
  specimens received from other labs. This is flagged as a warning (check C15), not corrected.

## How to run

Requires Python 3.

```
pip install -r requirements.txt
python src/00_download_data.py
python src/01_combine_raw.py
python src/02_validate.py
python src/03_clean.py
python src/04_alberta_weekly.py
python src/05_run_sql.py
python src/06_charts.py
python src/07_data_dictionary.py
python src/08_summary_pdf.py
```

Reproducibility check: the repository was cloned fresh and all nine scripts were run in order from the
instructions above. They completed without errors, and the Alberta table, QA summary, cleaning log, SQL
results and data dictionary were identical to the original outputs. There are no manual steps and no
random components. The source compilation may be updated over time, so rerunning later could download
different data.

## Repository layout

```
data/raw/            downloaded source files (not tracked)
data/processed/      combined, cleaned and Alberta tables (large files not tracked)
docs/                data dictionary and PDF project summary
reports/             QA summary, QA issue log, cleaning log, SQL results, figures
sql/queries.sql      SQL queries
src/                 pipeline scripts
```

## Data quality checks

Twenty check types (56 rules once each virus is checked separately) cover: required columns, date
validity, Saturday week-ends, epiweek format and agreement with the date, duplicate records, republished
weeks, negative and fractional counts, positives greater than tests, positives with no tests, influenza
subtype and total consistency, geography labels, Alberta week continuity, percent positive range, and
all-season zeros for common viruses. See `reports/qa_summary.md` for results and `reports/qa_issues.csv`
for every failing record. Validation counts every published version; the summary also shows the latest
revision only. Because validation runs on the raw data, it reports 9 missing Alberta weeks; the cleaned
table has 8 because of the relabelling decision above.

## Process notes

Two errors in the first version of the validation script were found and fixed during development:
a check counted blank cells as non-whole numbers (27,054 false failures), and counting every republished
version as a separate failure inflated the results. Both are corrected, and the summary now reports
all versions and latest-revision-only counts separately.

## AI assistance

This project was developed with assistance from Claude (Anthropic) for drafting and reviewing code.
The analytical decisions listed above were reviewed and chosen by the author.

## Author

Nasim Feizinazhad
