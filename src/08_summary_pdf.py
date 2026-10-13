"""
Step 8: Build the PDF project summary to attach to a job application.

Set GITHUB_URL below once the repository is published, then rerun this script.
Output: docs/Project_Summary_Nasim_Feizinazhad.pdf
"""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

# ----------------------------------------------------------------------------
GITHUB_URL = ""  # e.g. "https://github.com/your-username/alberta-respiratory-surveillance"
# ----------------------------------------------------------------------------

OUT = Path("docs/Project_Summary_Nasim_Feizinazhad.pdf")
FIG = Path("reports/figures")

NAVY = colors.HexColor("#1f3a5f")
GREY = colors.HexColor("#555555")
LIGHT = colors.HexColor("#eef2f7")

base = getSampleStyleSheet()
body = ParagraphStyle("body", parent=base["Normal"], fontName="Helvetica", fontSize=9.2, leading=12.2,
                      alignment=TA_LEFT, spaceAfter=3)
small = ParagraphStyle("small", parent=body, fontSize=8, leading=10.4, textColor=GREY)
cell = ParagraphStyle("cell", parent=body, fontSize=8.4, leading=10.6, spaceAfter=0)
cellb = ParagraphStyle("cellb", parent=cell, fontName="Helvetica-Bold")
h1 = ParagraphStyle("h1", parent=base["Title"], fontName="Helvetica-Bold", fontSize=15.5, leading=19,
                    textColor=NAVY, alignment=TA_LEFT, spaceAfter=2)
h2 = ParagraphStyle("h2", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=10.5, leading=13,
                    textColor=NAVY, spaceBefore=7, spaceAfter=3, keepWithNext=1)
bullet = ParagraphStyle("bullet", parent=body, leftIndent=11, bulletIndent=1, spaceAfter=2)


def bullets(items):
    return [Paragraph(t, bullet, bulletText="-") for t in items]


def mapping_table():
    rows = [
        ("Posting requirement", "Evidence in this project"),
        ("Standardized, reproducible practices",
         "Nine scripts rerun end to end from empty folders with no manual steps. Every cleaning "
         "decision is a named setting and is logged."),
        ("Data preparation, validation, quality assurance",
         "20 check types (56 rules) run on 68,862 records. Every failing record is saved to an issue log."),
        ("Surveillance reporting products",
         "Alberta weekly table, SQL queries and four charts, each stating its source and latest week."),
        ("Technical documentation and metadata",
         "Data dictionary (31 fields), cleaning log, and a README listing decisions and limitations."),
        ("SQL, Git and analytical workflows",
         "SQL with window functions (SQLite), Python (pandas), version-controlled code. R is on my "
         "resume; this project uses Python."),
        ("Coordination and handover",
         "Assumptions, open questions and rerun instructions are written for someone taking over the work."),
    ]
    data = [[Paragraph(a, cellb if i == 0 else cell), Paragraph(b, cellb if i == 0 else cell)]
            for i, (a, b) in enumerate(rows)]
    t = Table(data, colWidths=[1.85 * inch, 5.0 * inch], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), LIGHT),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#c9d1dc")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


def steps_table():
    rows = [
        ("#", "Step", "What it does", "Result"),
        ("1", "Download and combine",
         "Downloads 12 season files (2013-14 to 2024-25) from the public RVDSS compilation and stacks them "
         "into one table without changing any value, so validation sees the data as published.",
         "68,862 raw rows"),
        ("2", "Validate",
         "Runs 20 check types (56 rules) on the raw data: dates, duplicates, impossible counts, label "
         "problems, missing weeks, all-season zeros. Every failing record is logged.",
         "Issue log of 7,193 records and a summary table"),
        ("3", "Clean",
         "Applies four documented decisions (republished weeks, one broken label, impossible counts, "
         "suspect zeros). Each is a named setting, and each step logs rows before and after.",
         "24,828 rows kept; 44,034 older versions set aside; 53 values blanked; 204 values flagged"),
        ("4", "Build the Alberta table",
         "Filters to Alberta and lays the data on a complete weekly calendar, so a missing week appears "
         "as a blank row instead of silently disappearing.",
         "626 weeks, 8 of them missing"),
        ("5", "Query in SQL",
         "Loads the table into SQLite and runs four queries: weekly positivity, peak week per season "
         "(weeks with fewer than 100 tests excluded), season totals, and completeness.",
         "4 result tables"),
        ("6", "Chart",
         "Draws four charts. Missing weeks show as gaps, flagged weeks are shaded, and each chart states "
         "its source and latest week.",
         "4 figures"),
        ("7", "Document",
         "Writes a data dictionary for all 31 fields. The script stops with an error if any column is "
         "undocumented, so the dictionary cannot fall out of date.",
         "Dictionary, README, this summary"),
        ("8", "Verify",
         "Clones the repository fresh and reruns every script from the README.",
         "Outputs identical to the originals"),
    ]
    data = []
    for i, r in enumerate(rows):
        st = cellb if i == 0 else cell
        data.append([Paragraph(c, st) for c in r])
    t = Table(data, colWidths=[0.25 * inch, 1.2 * inch, 3.6 * inch, 1.8 * inch], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), LIGHT),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#c9d1dc")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ]))
    return t


def decisions_table():
    rows = [
        ("Decision", "Choice and reason"),
        ("Weeks published more than once",
         "Keep the latest version; older versions saved separately. Only 990 of 2,050 republished "
         "weeks actually changed value."),
        ("Positives greater than tests",
         "Blank the positive count, keep the row. Which number is wrong cannot be known."),
        ("Alberta RSV zeros",
         "Kept as published and flagged on every table and chart. The cause cannot be established from the data."),
        ("Missing weeks",
         "Left blank and shown as missing, not estimated. Estimates would add numbers nobody measured."),
        ("Truncated label 'province of'",
         "Treated as Alberta and flagged as an inference; can be switched off with one setting."),
    ]
    data = [[Paragraph(a, cellb if i == 0 else cell), Paragraph(b, cellb if i == 0 else cell)]
            for i, (a, b) in enumerate(rows)]
    t = Table(data, colWidths=[1.85 * inch, 5.0 * inch], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), LIGHT),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#c9d1dc")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


def fit_image(path, width):
    from PIL import Image as PILImage
    w, h = PILImage.open(path).size
    return Image(str(path), width=width, height=width * h / w)


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(GREY)
    canvas.drawString(0.8 * inch, 0.5 * inch,
                      "Nasim Feizinazhad | Supporting document: Surveillance Data Coordinator (Requisition 87695)")
    canvas.drawRightString(letter[0] - 0.8 * inch, 0.5 * inch, f"Page {doc.page}")
    canvas.restoreState()


def main():
    OUT.parent.mkdir(exist_ok=True)
    doc = SimpleDocTemplate(str(OUT), pagesize=letter, leftMargin=0.8 * inch, rightMargin=0.8 * inch,
                            topMargin=0.65 * inch, bottomMargin=0.8 * inch,
                            title="Alberta Respiratory Virus Surveillance: Data Quality and Reporting Pipeline",
                            author="Nasim Feizinazhad")
    link = (f'Code and documentation: <font color="#1f3a5f">{GITHUB_URL}</font>' if GITHUB_URL
            else "Code and documentation: (GitHub link to be added)")

    s = []
    s.append(Paragraph("Alberta Respiratory Virus Surveillance:<br/>Data Quality &amp; Reporting Pipeline", h1))
    s.append(Paragraph("Personal portfolio project built on public data. It is not work experience and "
                       "does not use any Government of Alberta internal data.", small))
    s.append(Paragraph(link, small))

    s.append(Paragraph("Purpose", h2))
    s.append(Paragraph(
        "I built a reproducible workflow that takes 12 seasons of weekly respiratory virus laboratory data, "
        "checks it against explicit quality rules, documents each cleaning decision, and produces Alberta "
        "weekly tables, SQL queries and report charts. The aim was to practise the work that comes before "
        "any chart: validating the data, deciding what to do about problems, writing those decisions down, "
        "and making the process repeatable by someone else.", body))

    s.append(Paragraph("How the project works, step by step", h2))
    s.append(steps_table())

    s.append(Paragraph("How it relates to this position", h2))
    s.append(mapping_table())

    s.append(Paragraph("What the data quality checks found", h2))
    s += bullets([
        "<b>Alberta reports 0 RSV positives for four seasons</b> (2017-18 to 2020-21) while testing "
        "32,000 to 102,000 specimens a season. In the three seasons before the pandemic, BC, Saskatchewan, "
        "Manitoba and Ontario report hundreds to thousands of positives. In 2020-21 they report only 4 to 67, "
        "so those zeros match the pandemic. The cause of the earlier zeros is unknown, so I flagged them "
        "instead of changing them.",
        "<b>Alberta is missing 8 weeks across 12 seasons;</b> five fall in the last two weeks of December. "
        "They are left blank, not estimated.",
        "<b>44,034 of 68,862 rows are older versions of republished weeks.</b> Only 990 of the 2,050 "
        "republished weeks had values that actually changed.",
        "<b>53 impossible counts</b> (more positives than tests) at laboratories outside Alberta.",
        "<b>Checks that found nothing</b> include invalid dates, duplicates, negative counts, and epiweek "
        "values that disagree with the date.",
    ])

    s.append(Paragraph("Decisions made, and why", h2))
    s.append(decisions_table())

    s.append(KeepTogether([Paragraph("Chart: Alberta RSV, with the flagged period shown", h2),
                           fit_image(FIG / "04_rsv_data_quality_flag.png", 6.1 * inch)]))
    s.append(KeepTogether([Paragraph("Chart: Alberta weekly percent positive, 2024-25 season", h2),
                           fit_image(FIG / "01_weekly_positivity_latest_season.png", 6.1 * inch)]))

    s.append(Paragraph("Limitations", h2))
    s += bullets([
        "The data is a third-party compilation of PHAC reports, not an official file. I checked one Alberta "
        "week against PHAC's published report and it matched, which supports but does not prove accuracy.",
        "RVDSS is a sentinel laboratory system, so counts do not represent all testing in Alberta. "
        "This project does not reproduce Alberta's own respiratory dashboard, and I did not assume its "
        "definitions match.",
        "Data ends with the 2024-25 season, and published values can be revised.",
    ])
    s.append(Spacer(1, 4))
    s.append(Paragraph(
        "<b>Tools:</b> Python (pandas, matplotlib), SQL (SQLite), Git. Developed with assistance from "
        "Claude (Anthropic) for drafting and reviewing code; the analytical decisions above were reviewed "
        "and chosen by me.", small))

    doc.build(s, onFirstPage=footer, onLaterPages=footer)
    print(f"Saved {OUT}")


if __name__ == "__main__":
    main()
