-- Alberta respiratory virus surveillance queries (SQLite)
-- Table: alberta_weekly  (one row per week per season; missing_week = 1 means no data was reported)

-- name: weekly_positivity_latest_season
-- Weekly % positive for the most recent season in the data.
SELECT time_value AS week_ending,
       flu_tests,
       flu_total_pct_positive   AS influenza_pct,
       rsv_pct_positive         AS rsv_pct,
       sarscov2_pct_positive    AS sarscov2_pct
FROM alberta_weekly
WHERE season = (SELECT MAX(season) FROM alberta_weekly)
  AND missing_week = 0
ORDER BY time_value;

-- name: peak_week_by_season_and_virus
-- Week with the highest % positive for each season and virus.
-- Weeks with fewer than 100 tests are excluded: a tiny denominator can give a misleading percentage.
WITH long AS (
    SELECT season, time_value, 'Influenza'  AS virus, flu_total_pct_positive AS pct, flu_tests AS tests, qa_flags
    FROM alberta_weekly WHERE missing_week = 0 AND flu_total_pct_positive IS NOT NULL
    UNION ALL
    SELECT season, time_value, 'RSV', rsv_pct_positive, rsv_tests, qa_flags
    FROM alberta_weekly WHERE missing_week = 0 AND rsv_pct_positive IS NOT NULL
    UNION ALL
    SELECT season, time_value, 'SARS-CoV-2', sarscov2_pct_positive, sarscov2_tests, qa_flags
    FROM alberta_weekly WHERE missing_week = 0 AND sarscov2_pct_positive IS NOT NULL
),
ranked AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY season, virus ORDER BY pct DESC, time_value) AS rn
    FROM long
    WHERE tests >= 100
)
SELECT virus, season, time_value AS peak_week_ending, pct AS peak_pct_positive, tests AS tests_that_week,
       CASE WHEN qa_flags LIKE '%suspect_zero%' THEN 'CHECK DATA QUALITY' ELSE '' END AS data_quality_note
FROM ranked
WHERE rn = 1
ORDER BY virus, season;

-- name: season_totals
-- Season-level testing volume and positivity.
-- Positivity = total positives / total tests (not an average of weekly percentages).
SELECT season,
       SUM(flu_tests)            AS flu_tests,
       SUM(flu_total_positive)   AS flu_positives,
       ROUND(100.0 * SUM(flu_total_positive) / NULLIF(SUM(flu_tests), 0), 2)   AS flu_pct_positive,
       SUM(rsv_tests)            AS rsv_tests,
       SUM(rsv_positive_tests)   AS rsv_positives,
       ROUND(100.0 * SUM(rsv_positive_tests) / NULLIF(SUM(rsv_tests), 0), 2)   AS rsv_pct_positive,
       SUM(sarscov2_tests)       AS sarscov2_tests,
       ROUND(100.0 * SUM(sarscov2_positive_tests) / NULLIF(SUM(sarscov2_tests), 0), 2) AS sarscov2_pct_positive,
       SUM(CASE WHEN qa_flags LIKE '%suspect_zero%' THEN 1 ELSE 0 END) AS weeks_flagged_suspect_zero
FROM alberta_weekly
WHERE missing_week = 0
GROUP BY season
ORDER BY season;

-- name: completeness_by_season
-- How many weeks each season should have, how many have data, and how many are missing.
SELECT season,
       COUNT(*)                                AS weeks_in_calendar,
       SUM(1 - missing_week)                   AS weeks_with_data,
       SUM(missing_week)                       AS weeks_missing,
       ROUND(100.0 * SUM(missing_week) / COUNT(*), 1) AS pct_missing,
       MIN(CASE WHEN missing_week = 1 THEN time_value END) AS first_missing_week
FROM alberta_weekly
GROUP BY season
ORDER BY season;
