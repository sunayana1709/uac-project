"""
build_pdf_report.py
Turns the auto-generated research findings + figures/ into a polished, submittable PDF.
Run with: python src/build_pdf_report.py
"""
import json
import os
import sys

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
)

sys.path.append(os.path.dirname(__file__))
from data_loader import load_pipeline_data, compute_derived_metrics  # noqa: E402
from eda_analysis import identify_backlog_periods  # noqa: E402

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
OUT_DIR = os.path.join(BASE_DIR, "outputs")
FIG_DIR = os.path.join(OUT_DIR, "figures")
PDF_PATH = os.path.join(OUT_DIR, "UAC_Research_Paper.pdf")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="Justify", parent=styles["Normal"], alignment=4, spaceAfter=10, leading=15))
styles.add(ParagraphStyle(name="H1", parent=styles["Heading1"], spaceBefore=18, spaceAfter=8, textColor=colors.HexColor("#1F3864")))
styles.add(ParagraphStyle(name="H2", parent=styles["Heading2"], spaceBefore=12, spaceAfter=6, textColor=colors.HexColor("#2E5395")))
styles.add(ParagraphStyle(name="Center", parent=styles["Normal"], alignment=1))


def kpi_table(kpis):
    labels = {
        "transfer_efficiency_ratio": "Transfer Efficiency Ratio",
        "discharge_effectiveness_index": "Discharge Effectiveness Index",
        "pipeline_throughput": "Pipeline Throughput",
        "backlog_accumulation_rate": "Backlog Accumulation Rate (children/day)",
        "outcome_stability_score": "Outcome Stability Score",
    }
    data = [["KPI", "Value"]] + [[labels.get(k, k), str(v)] for k, v in kpis.items()]
    t = Table(data, colWidths=[3.8 * inch, 2.0 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F3864")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F5FA")]),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def df_table(rows, header, colWidths=None):
    data = [header] + rows
    t = Table(data, colWidths=colWidths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E5395")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F5FA")]),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def fig(path, width=6.3 * inch):
    img = Image(path)
    ratio = img.imageHeight / img.imageWidth
    img.drawWidth = width
    img.drawHeight = width * ratio
    return img


def main():
    kpis = json.load(open(os.path.join(OUT_DIR, "kpis.json")))
    df = load_pipeline_data()
    df = compute_derived_metrics(df)
    streaks = identify_backlog_periods(df)

    date_min, date_max = df["Date"].min().strftime("%b %d, %Y"), df["Date"].max().strftime("%b %d, %Y")

    wk = df.groupby("IsWeekend")[["TransferEfficiencyRatio", "DischargeEffectiveness"]].mean()
    weekday_transfer = wk.loc[False, "TransferEfficiencyRatio"]
    weekend_transfer = wk.loc[True, "TransferEfficiencyRatio"]

    top_streaks = streaks.head(5).reset_index()
    streak_rows = [
        [r["Start"].strftime("%b %d, %Y"), r["End"].strftime("%b %d, %Y"), str(int(r["Days"])), f"{int(r['TotalGrowth']):+,}"]
        for _, r in top_streaks.iterrows()
    ]

    doc = SimpleDocTemplate(PDF_PATH, pagesize=letter,
                             topMargin=0.7 * inch, bottomMargin=0.7 * inch,
                             leftMargin=0.75 * inch, rightMargin=0.75 * inch)
    story = []

    # Title page
    story.append(Spacer(1, 1.6 * inch))
    story.append(Paragraph("Care Transition Efficiency &<br/>Placement Outcome Analytics", styles["Title"]))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("Process Efficiency Analysis of the HHS Unaccompanied Alien<br/>Children (UAC) Program Care Pipeline", styles["Center"]))
    story.append(Spacer(1, 1.2 * inch))
    story.append(Paragraph(f"Data: {len(df)} daily reports &middot; {date_min} to {date_max}", styles["Center"]))
    story.append(PageBreak())

    # 1. Introduction
    story.append(Paragraph("1. Introduction", styles["H1"]))
    story.append(Paragraph(
        "The Unaccompanied Alien Children (UAC) Program operates as a multi-stage care and "
        "reunification pipeline: apprehension and CBP custody, transfer to HHS care, medical "
        "screening and case management, and discharge to a vetted sponsor. While aggregate custody "
        "counts are routinely monitored, process efficiency &mdash; how fast and reliably children move "
        "through this pipeline &mdash; is largely unmeasured. This analysis builds a structured "
        "transition-efficiency framework to surface bottlenecks, backlog periods, and outcome "
        "stability trends that aggregate counts alone would hide.", styles["Justify"]))

    story.append(Paragraph("2. Data Overview", styles["H1"]))
    story.append(Paragraph(
        f"The dataset covers <b>{len(df)}</b> daily reports from <b>{date_min}</b> to <b>{date_max}</b>, "
        f"tracking apprehensions, CBP custody load, transfers to HHS, HHS care load, and discharges. "
        f"Total children apprehended over the period: <b>{int(df['Apprehended'].sum()):,}</b>. "
        f"Total children discharged: <b>{int(df['Discharged'].sum()):,}</b>.", styles["Justify"]))

    # 3. KPIs
    story.append(Paragraph("3. Key Performance Indicators", styles["H1"]))
    story.append(kpi_table(kpis))
    story.append(Spacer(1, 12))

    story.append(PageBreak())

    # 4. Pipeline volumes
    story.append(Paragraph("4. Care Pipeline Volumes Over Time", styles["H1"]))
    story.append(Paragraph(
        "CBP custody and HHS care loads tracked across the full period. A sharp structural decline "
        "in HHS care load is visible starting around early 2025, reflecting a major shift in system "
        "load rather than a gradual trend.", styles["Justify"]))
    story.append(fig(os.path.join(FIG_DIR, "01_pipeline_volumes_over_time.png")))

    story.append(PageBreak())

    # 5. Transfer efficiency
    story.append(Paragraph("5. Transfer Efficiency (CBP → HHS)", styles["H1"]))
    story.append(Paragraph(
        f"Average Transfer Efficiency Ratio across the period was <b>{kpis['transfer_efficiency_ratio']}</b> "
        "(transfers out of CBP custody as a share of the CBP custody load).", styles["Justify"]))
    story.append(fig(os.path.join(FIG_DIR, "02_transfer_efficiency_over_time.png")))

    story.append(PageBreak())

    # 6. Discharge effectiveness
    story.append(Paragraph("6. Discharge Effectiveness", styles["H1"]))
    story.append(Paragraph(
        f"Average Discharge Effectiveness Index was <b>{kpis['discharge_effectiveness_index']}</b> "
        "(daily discharges as a share of the active HHS care load).", styles["Justify"]))
    story.append(fig(os.path.join(FIG_DIR, "03_discharge_effectiveness_over_time.png")))

    story.append(PageBreak())

    # 7. Backlog
    story.append(Paragraph("7. Backlog & Delay Identification", styles["H1"]))
    trend = "net backlog growth" if kpis["backlog_accumulation_rate"] > 0 else "net backlog reduction"
    story.append(Paragraph(
        f"The system's total in-care population (CBP + HHS combined) changed by an average of "
        f"<b>{kpis['backlog_accumulation_rate']} children/day</b> over the full period, trending "
        f"toward {trend} overall. The table below lists the most severe sustained backlog-growth "
        "windows identified (5+ consecutive days of net growth):", styles["Justify"]))
    story.append(fig(os.path.join(FIG_DIR, "04_backlog_change.png")))
    story.append(Spacer(1, 10))
    if streak_rows:
        story.append(df_table(streak_rows, ["Start", "End", "Days", "Net Growth"],
                               colWidths=[1.4*inch, 1.4*inch, 0.8*inch, 1.2*inch]))

    story.append(PageBreak())

    # 8. Temporal patterns
    story.append(Paragraph("8. Temporal & Pattern Analysis", styles["H1"]))
    faster = "Weekday" if weekday_transfer > weekend_transfer else "Weekend"
    story.append(Paragraph(
        f"Weekday average Transfer Efficiency Ratio: <b>{round(weekday_transfer, 3)}</b>; weekend "
        f"average: <b>{round(weekend_transfer, 3)}</b>. {faster} processing was faster on this "
        "measure over the period.", styles["Justify"]))
    story.append(fig(os.path.join(FIG_DIR, "05_weekday_vs_weekend.png")))
    story.append(Spacer(1, 10))
    story.append(fig(os.path.join(FIG_DIR, "06_monthly_discharges.png")))

    story.append(PageBreak())

    # 9. Outcome stability
    story.append(Paragraph("9. Outcome Stability Analysis", styles["H1"]))
    story.append(Paragraph(
        f"The Outcome Stability Score of <b>{kpis['outcome_stability_score']}</b> quantifies how "
        "consistent day-to-day discharge effectiveness was across the period. Lower scores reflect "
        "periods with sharp swings in reunification throughput, which merit operational review.",
        styles["Justify"]))

    # 10. Recommendations
    story.append(Paragraph("10. Recommendations", styles["H1"]))
    recs = [
        "Direct case-management staffing and resources toward the recurring backlog-accumulation "
        "windows identified in Section 7 to prevent their recurrence.",
        f"Investigate the {'weekday' if faster=='Weekday' else 'weekend'} processing shortfall — "
        "if it reflects staffing gaps, targeted coverage could smooth throughput.",
        "Adopt the Outcome Stability Score as an ongoing operational-health metric, with alerts on "
        "sudden drops in discharge effectiveness.",
        "Set threshold-based alerts on Transfer Efficiency Ratio and Discharge Effectiveness to "
        "surface emerging bottlenecks before they compound into system-wide backlog.",
        "Examine the structural drop in HHS care load beginning in early 2025 to determine whether "
        "it reflects a policy change, reduced inflow, or a data reporting change — and whether it "
        "should inform future capacity planning.",
    ]
    for r in recs:
        story.append(Paragraph(f"&bull; {r}", styles["Justify"]))

    story.append(Paragraph("11. Conclusion", styles["H1"]))
    story.append(Paragraph(
        "This analysis reframes the UAC dataset from a capacity-monitoring lens to a "
        "process-efficiency and outcome-evaluation lens, surfacing where and when the CBP → HHS → "
        "sponsor pipeline slows down. It provides an evidence base for faster reunification, "
        "reduced delays, and stronger child welfare outcomes.", styles["Justify"]))

    doc.build(story)
    print(f"PDF written to {PDF_PATH}")


if __name__ == "__main__":
    main()
