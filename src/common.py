"""Definitions shared by several scripts, kept in one place so they cannot drift apart."""
from datetime import date, timedelta

# (tests column, positives column, label)
TEST_POSITIVE_PAIRS = [
    ("flu_tests", "flua_positive_tests", "Influenza A"),
    ("flu_tests", "flub_positive_tests", "Influenza B"),
    ("flu_tests", "flu_positive_tests", "Influenza (total)"),
    ("rsv_tests", "rsv_positive_tests", "RSV"),
    ("hpiv_tests", "hpiv1_positive_tests", "HPIV-1"),
    ("hpiv_tests", "hpiv2_positive_tests", "HPIV-2"),
    ("hpiv_tests", "hpiv3_positive_tests", "HPIV-3"),
    ("hpiv_tests", "hpiv4_positive_tests", "HPIV-4"),
    ("adv_tests", "adv_positive_tests", "Adenovirus"),
    ("hmpv_tests", "hmpv_positive_tests", "hMPV"),
    ("evrv_tests", "evrv_positive_tests", "EV/RV"),
    ("hcov_tests", "hcov_positive_tests", "Seasonal HCoV"),
    ("sarscov2_tests", "sarscov2_positive_tests", "SARS-CoV-2"),
]


def mmwr_epiweek(end_saturday: date):
    """(year, week) of the Sunday-Saturday epi-week ending on the given Saturday."""
    start = end_saturday - timedelta(days=6)

    def week1_start(year):
        jan1 = date(year, 1, 1)
        dow = (jan1.weekday() + 1) % 7  # 0 = Sunday
        return jan1 - timedelta(days=dow) if dow <= 3 else jan1 + timedelta(days=7 - dow)

    for yr in (end_saturday.year + 1, end_saturday.year, end_saturday.year - 1):
        w1 = week1_start(yr)
        if start >= w1:
            return yr, (start - w1).days // 7 + 1
    return None, None
