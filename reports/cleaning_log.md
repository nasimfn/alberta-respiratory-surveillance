# Cleaning Log

Settings: REVISION_POLICY=`latest`, RELABEL_PROVINCE_OF_AS_AB=`True`, BAD_COUNT_POLICY=`null_positive`, SUSPECT_ZERO_POLICY=`flag_only`

| Step | Rows before | Rows after | Detail |
|---|---|---|---|
| Load combined raw data | 68,862 | 68,862 | 12 seasons |
| Relabel truncated 'province of' as 'ab' | 68,862 | 68,862 | 1 row(s) relabelled and flagged geo_inferred=True |
| Parse dates, derive epi_year / epi_week, drop inconsistent helper columns | 68,862 | 68,862 | dropped columns: ['week', 'weekorder', 'year'] |
| Keep latest revision of each week | 68,862 | 24,828 | 44,034 superseded rows moved to revisions_superseded.csv |
| Handle positives > tests (policy: null_positive) | 24,828 | 24,828 | 53 impossible value(s) found |
| Flag suspect all-season zeros (policy: flag_only) | 24,828 | 24,828 | 204 value(s) flagged, values kept as published |
| Add flu_total_positive and recomputed % positive columns | 24,828 | 24,828 | % positive is blank when tests = 0 or missing |
| Store counts as whole numbers (blank stays blank) | 24,828 | 24,828 | 26 columns |