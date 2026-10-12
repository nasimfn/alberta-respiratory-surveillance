# Data Quality Summary

- Records checked: **68,862**
- Seasons: **12** (2013-2014 to 2024-2025)
- Checks run: **56**
- Checks with failures: **30**
- 'All versions' counts every published revision; 'Latest' counts only the most recent revision of each week.

## Results by check

| Check | Description | Severity | Failures (all versions) | Failures (latest revision) |
|---|---|---|---|---|
| C01 | Required columns present | ERROR | 0 | 0 |
| C02 | time_value is a valid YYYY-MM-DD date | ERROR | 0 | 0 |
| C03 | issue is a valid YYYY-MM-DD date | ERROR | 0 | 0 |
| C04 | time_value falls on a Saturday | ERROR | 0 | 0 |
| C05 | epiweek is YYYYWW with week 01-53 | ERROR | 0 | 0 |
| C06 | epiweek matches the epi-week calculated from time_value | ERROR | 0 | 0 |
| C07 | issue (revision) date is not before time_value | ERROR | 0 | 0 |
| C08 | No duplicate (epiweek, issue, geo_type, geo_value) records | ERROR | 0 | 0 |
| C09a | Weeks published more than once (multiple issue dates) | INFO | 2,050 | 2,050 |
| C09b | ...of which values actually changed between versions | INFO | 990 | 990 |
| C10 | Counts are non-negative | ERROR | 0 | 0 |
| C11 | Counts are whole numbers | ERROR | 0 | 0 |
| C12 | Positives <= tests (Influenza A) | ERROR | 1 | 1 |
| C12 | Positives <= tests (Influenza B) | ERROR | 0 | 0 |
| C12 | Positives <= tests (Influenza (total)) | ERROR | 0 | 0 |
| C12 | Positives <= tests (RSV) | ERROR | 3 | 3 |
| C12 | Positives <= tests (HPIV-1) | ERROR | 3 | 3 |
| C12 | Positives <= tests (HPIV-2) | ERROR | 3 | 3 |
| C12 | Positives <= tests (HPIV-3) | ERROR | 2 | 2 |
| C12 | Positives <= tests (HPIV-4) | ERROR | 4 | 4 |
| C12 | Positives <= tests (Adenovirus) | ERROR | 2 | 2 |
| C12 | Positives <= tests (hMPV) | ERROR | 3 | 3 |
| C12 | Positives <= tests (EV/RV) | ERROR | 25 | 25 |
| C12 | Positives <= tests (Seasonal HCoV) | ERROR | 7 | 7 |
| C12 | Positives <= tests (SARS-CoV-2) | ERROR | 0 | 0 |
| C13 | Positives reported without tests (Influenza A) | ERROR | 1 | 1 |
| C13 | Positives reported without tests (Influenza B) | ERROR | 0 | 0 |
| C13 | Positives reported without tests (Influenza (total)) | ERROR | 0 | 0 |
| C13 | Positives reported without tests (RSV) | ERROR | 3 | 3 |
| C13 | Positives reported without tests (HPIV-1) | ERROR | 3 | 3 |
| C13 | Positives reported without tests (HPIV-2) | ERROR | 2 | 2 |
| C13 | Positives reported without tests (HPIV-3) | ERROR | 2 | 2 |
| C13 | Positives reported without tests (HPIV-4) | ERROR | 4 | 4 |
| C13 | Positives reported without tests (Adenovirus) | ERROR | 1 | 1 |
| C13 | Positives reported without tests (hMPV) | ERROR | 3 | 3 |
| C13 | Positives reported without tests (EV/RV) | ERROR | 18 | 18 |
| C13 | Positives reported without tests (Seasonal HCoV) | ERROR | 3 | 3 |
| C13 | Positives reported without tests (SARS-CoV-2) | ERROR | 0 | 0 |
| C15 | Sum of influenza A subtypes <= total Influenza A | WARNING | 7,067 | 662 |
| C16 | Influenza A + B equals total influenza positives | WARNING | 0 | 0 |
| C17 | Geography labels are clean and complete | WARNING | 1 | 1 |
| C18 | Alberta has no missing weeks within a season | WARNING | 9 | 9 |
| C19 | Recomputed % positive within 0-100 (Influenza A) | ERROR | 0 | 0 |
| C19 | Recomputed % positive within 0-100 (Influenza B) | ERROR | 0 | 0 |
| C19 | Recomputed % positive within 0-100 (Influenza (total)) | ERROR | 0 | 0 |
| C19 | Recomputed % positive within 0-100 (RSV) | ERROR | 0 | 0 |
| C19 | Recomputed % positive within 0-100 (HPIV-1) | ERROR | 0 | 0 |
| C19 | Recomputed % positive within 0-100 (HPIV-2) | ERROR | 1 | 1 |
| C19 | Recomputed % positive within 0-100 (HPIV-3) | ERROR | 0 | 0 |
| C19 | Recomputed % positive within 0-100 (HPIV-4) | ERROR | 0 | 0 |
| C19 | Recomputed % positive within 0-100 (Adenovirus) | ERROR | 1 | 1 |
| C19 | Recomputed % positive within 0-100 (hMPV) | ERROR | 0 | 0 |
| C19 | Recomputed % positive within 0-100 (EV/RV) | ERROR | 7 | 7 |
| C19 | Recomputed % positive within 0-100 (Seasonal HCoV) | ERROR | 4 | 4 |
| C19 | Recomputed % positive within 0-100 (SARS-CoV-2) | ERROR | 0 | 0 |
| C20 | Common virus has >= 5,000 tests but zero positives all season | WARNING | 10 | 10 |

## Missing values (columns with any missing)

| Column | % missing | Count |
|---|---|---|
| week | 57.8 | 39,834 |
| weekorder | 57.8 | 39,834 |
| year | 57.8 | 39,834 |
| flu_positive_tests | 32.6 | 22,425 |
| sarscov2_tests | 28.0 | 19,287 |
| sarscov2_positive_tests | 28.0 | 19,287 |
| evrv_tests | 11.1 | 7,678 |
| evrv_positive_tests | 11.1 | 7,678 |
| hcov_tests | 9.5 | 6,566 |
| fluauns_positive_tests | 9.5 | 6,522 |
| hcov_positive_tests | 9.5 | 6,567 |
| hpiv1_positive_tests | 8.7 | 5,972 |
| hpiv_tests | 8.7 | 5,972 |
| hpiv3_positive_tests | 8.7 | 5,972 |
| hpiv2_positive_tests | 8.7 | 5,972 |
| hpivother_positive_tests | 8.7 | 5,972 |
| hpiv4_positive_tests | 8.7 | 5,972 |
| hmpv_positive_tests | 5.3 | 3,660 |
| adv_positive_tests | 5.3 | 3,660 |
| adv_tests | 5.3 | 3,660 |
| hmpv_tests | 5.3 | 3,660 |
| rsv_tests | 1.1 | 731 |
| rsv_positive_tests | 1.1 | 731 |
| flub_positive_tests | 1.1 | 733 |
| flu_tests | 1.1 | 733 |
| fluah1n1pdm09_positive_tests | 1.1 | 733 |
| fluah3_positive_tests | 1.1 | 733 |
| flua_positive_tests | 1.1 | 733 |