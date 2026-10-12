"""
Step 5: Run the SQL queries in sql/queries.sql against the Alberta weekly table.

Loads data/processed/alberta_weekly.csv into an SQLite database, runs each query
(marked with '-- name: <name>'), and saves each result to reports/sql/<name>.csv.
"""
import re
import sqlite3
from pathlib import Path

import pandas as pd

DATA = Path("data/processed/alberta_weekly.csv")
QUERIES = Path("sql/queries.sql")
DB = Path("reports/rvdss.db")
OUT_DIR = Path("reports/sql")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    weekly = pd.read_csv(DATA)
    weekly["missing_week"] = weekly["missing_week"].astype(int)  # SQLite has no boolean type

    DB.unlink(missing_ok=True)
    with sqlite3.connect(DB) as con:
        weekly.to_sql("alberta_weekly", con, index=False)
        blocks = re.split(r"^-- name: (\w+)\s*$", QUERIES.read_text(), flags=re.M)[1:]
        for name, sql in zip(blocks[0::2], blocks[1::2]):
            result = pd.read_sql_query(sql, con)
            result.to_csv(OUT_DIR / f"{name}.csv", index=False)
            print(f"\n=== {name} ({len(result)} rows) ===")
            print(result.head(15).to_string(index=False))


if __name__ == "__main__":
    main()
