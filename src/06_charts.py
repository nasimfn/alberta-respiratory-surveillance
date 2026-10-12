"""
Step 6: Report charts for Alberta respiratory virus surveillance.

Input : data/processed/alberta_weekly.csv
Output: reports/figures/*.png

Design rules
  - Missing weeks are NOT interpolated: lines break where a week has no data.
  - Weeks flagged 'suspect_zero' are shaded and labelled on the chart, not hidden.
  - Every figure states its source and the week of the latest data.
"""
import textwrap
from datetime import date
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from common import mmwr_epiweek

IN_FILE = Path("data/processed/alberta_weekly.csv")
OUT_DIR = Path("reports/figures")

SOURCE = ("Source: PHAC Respiratory Virus Detection Surveillance System (RVDSS), via a public "
          "third-party compilation (github.com/dajmcdon/rvdss-canada). "
          "Sentinel laboratory data, preliminary, not all Alberta testing.")
COLORS = {"Influenza": "#1b6ca8", "RSV": "#d1495b", "SARS-CoV-2": "#2a9d8f"}
MIN_TESTS = 100  # weeks with fewer tests are drawn but not used for peaks (see SQL)


def footer(fig, extra=""):
    text = "\n".join(textwrap.fill(t, 140) for t in ([extra] if extra else []) + [SOURCE])
    fig.text(0.01, 0.01, text, fontsize=7, color="#555", va="bottom")


def load():
    df = pd.read_csv(IN_FILE, parse_dates=["time_value"])
    df["flagged_zero"] = df["qa_flags"].fillna("").str.contains("suspect_zero")
    return df


def chart_latest_season(df):
    season = df["season"].max()
    d = df[df["season"] == season].sort_values("time_value")
    fig, ax = plt.subplots(figsize=(10, 5.2))
    for name, col in [("Influenza", "flu_total_pct_positive"), ("RSV", "rsv_pct_positive"),
                      ("SARS-CoV-2", "sarscov2_pct_positive")]:
        ax.plot(d["time_value"], d[col], label=name, color=COLORS[name], lw=2, marker="o", ms=3)
    ax.set_title(f"Alberta: weekly % of tests positive, {season} season", loc="left", fontweight="bold")
    ax.set_ylabel("% of tests positive")
    ax.set_xlabel("Week ending")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.grid(axis="y", alpha=0.3)
    ax.legend(frameon=False, loc="upper left")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    last = d.dropna(subset=["flu_tests"])["time_value"].max()
    fig.subplots_adjust(bottom=0.27)
    footer(fig, f"Latest week in data: {last:%Y-%m-%d}. Missing weeks appear as gaps, not estimates.")
    fig.savefig(OUT_DIR / "01_weekly_positivity_latest_season.png", dpi=150)
    plt.close(fig)


def chart_testing_volume(df):
    season = df["season"].max()
    d = df[df["season"] == season].sort_values("time_value")
    fig, ax = plt.subplots(figsize=(10, 4.6))
    ax.bar(d["time_value"], d["flu_tests"], width=5, color="#8d99ae")
    ax.set_title(f"Alberta: influenza tests performed per week, {season} season", loc="left", fontweight="bold")
    ax.set_ylabel("Number of tests")
    ax.set_xlabel("Week ending")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.grid(axis="y", alpha=0.3)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.subplots_adjust(bottom=0.27)
    footer(fig, "Testing volume matters when reading % positive: small denominators make percentages unstable.")
    fig.savefig(OUT_DIR / "02_testing_volume_latest_season.png", dpi=150)
    plt.close(fig)


def season_anchor(season):
    """Saturday ending epi-week 35 of the season's first calendar year (surveillance season start)."""
    year = int(season[:4])
    for day in range(15, 31 + 15):
        d = date(year, 8, 1) + pd.Timedelta(days=day).to_pytimedelta()
        if d.weekday() == 5 and mmwr_epiweek(d) == (year, 35):
            return pd.Timestamp(d)
    raise ValueError(f"no anchor found for {season}")


def chart_season_comparison(df):
    d = df.copy()
    anchors = {s: season_anchor(s) for s in d["season"].unique()}
    d["idx"] = ((d["time_value"] - d["season"].map(anchors)).dt.days // 7) + 1
    seasons = sorted(d["season"].unique())
    fig, ax = plt.subplots(figsize=(10, 5.2))
    for s in seasons:
        x = d[d["season"] == s].sort_values("idx")
        recent = s in seasons[-3:]
        ax.plot(x["idx"], x["flu_total_pct_positive"], color=("#1b6ca8" if recent else "#c9ced6"),
                lw=2.2 if recent else 1, label=s if recent else None, zorder=3 if recent else 2)
    ax.set_title("Alberta: influenza % positive by week of season, all seasons (latest three highlighted)",
                 loc="left", fontweight="bold", fontsize=11)
    ticks = list(range(1, 53, 4))
    ax.set_xticks(ticks)
    ax.set_xticklabels([str((34 + t - 1) % 52 + 1) for t in ticks])
    ax.set_xlabel("Epidemiological week (season begins in week 35)")
    ax.set_ylabel("% of tests positive")
    ax.grid(axis="y", alpha=0.3)
    ax.legend(frameon=False, title="Recent seasons")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.subplots_adjust(bottom=0.27)
    footer(fig, "Grey lines: 2013-14 to 2021-22 seasons. 2020-21 is near zero. Week labels are approximate in 53-week years.")
    fig.savefig(OUT_DIR / "03_influenza_season_comparison.png", dpi=150)
    plt.close(fig)


def chart_rsv_data_quality(df):
    d = df.sort_values("time_value")
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(d["time_value"], d["rsv_pct_positive"], color=COLORS["RSV"], lw=1.6)
    flagged = d[d["flagged_zero"]]
    if not flagged.empty:
        ax.axvspan(flagged["time_value"].min(), flagged["time_value"].max(), color="#ffd166", alpha=0.35)
        mid = flagged["time_value"].min() + (flagged["time_value"].max() - flagged["time_value"].min()) / 2
        ax.text(mid, ax.get_ylim()[1] * 0.92,
                "Reported as 0 positives in all four seasons\n(2017-18 to 2020-21). See QA check C20",
                ha="center", va="top", fontsize=9)
    ax.set_title("Alberta: RSV % positive, 2013-2025, with flagged data-quality period",
                 loc="left", fontweight="bold")
    ax.set_ylabel("% of tests positive")
    ax.set_xlabel("Week ending")
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.grid(axis="y", alpha=0.3)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.subplots_adjust(bottom=0.27)
    footer(fig, "In 2017-18 to 2019-20, BC, SK, MB and ON report hundreds to thousands of RSV positives per season; "
                "in 2020-21 only 4 to 67 (pandemic). Alberta values shown as published.")
    fig.savefig(OUT_DIR / "04_rsv_data_quality_flag.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data = load()
    chart_latest_season(data)
    chart_testing_volume(data)
    chart_season_comparison(data)
    chart_rsv_data_quality(data)
    print("Saved:", *sorted(p.name for p in OUT_DIR.glob("*.png")), sep="\n  ")
