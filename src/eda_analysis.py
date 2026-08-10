"""
eda_analysis.py
Runs the full Care Transition Efficiency & Placement Outcome analysis:
  - Computes the 5 KPIs from the brief
  - Saves charts to outputs/figures/
  - Auto-writes outputs/research_paper.md and outputs/executive_summary.md with real numbers

Run with: python src/eda_analysis.py
"""

import os
import sys
import json
import warnings

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

sys.path.append(os.path.dirname(__file__))
from data_loader import load_pipeline_data, compute_derived_metrics  # noqa: E402

warnings.filterwarnings("ignore")
sns.set_theme(style="whitegrid")

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
OUT_DIR = os.path.join(BASE_DIR, "outputs")
FIG_DIR = os.path.join(OUT_DIR, "figures")
os.makedirs(FIG_DIR, exist_ok=True)


def compute_kpis(df: pd.DataFrame) -> dict:
    kpis = {}
    kpis["transfer_efficiency_ratio"] = round(df["TransferEfficiencyRatio"].mean(), 3)
    kpis["discharge_effectiveness_index"] = round(df["DischargeEffectiveness"].mean(), 3)

    throughput = df["Discharged"].sum() / df["Apprehended"].sum() if df["Apprehended"].sum() else np.nan
    kpis["pipeline_throughput"] = round(throughput, 3)

    # Backlog Accumulation Rate: average daily net change in total children in care (custody + HHS)
    kpis["backlog_accumulation_rate"] = round(df["BacklogChange"].mean(), 2)

    # Outcome Stability Score: 1 - coefficient of variation of discharge effectiveness (clipped to [0,1])
    cv = df["DischargeEffectiveness"].std() / df["DischargeEffectiveness"].mean()
    kpis["outcome_stability_score"] = round(max(0, 1 - cv), 3)

    return kpis


def make_charts(df: pd.DataFrame) -> dict:
    paths = {}

    # 1. Pipeline volumes over time
    plt.figure(figsize=(9, 4.5))
    plt.plot(df["Date"], df["CBP_Custody"], label="CBP Custody", color="#C44E52")
    plt.plot(df["Date"], df["HHS_Care"], label="HHS Care", color="#4C72B0")
    plt.title("Children in Custody Over Time: CBP vs HHS")
    plt.ylabel("Children in Care")
    plt.legend()
    plt.tight_layout()
    p = os.path.join(FIG_DIR, "01_pipeline_volumes_over_time.png")
    plt.savefig(p, dpi=150); plt.close()
    paths["pipeline_volumes"] = p

    # 2. Transfer Efficiency Ratio over time
    plt.figure(figsize=(9, 4))
    plt.plot(df["Date"], df["TransferEfficiencyRatio"], color="#55A868", alpha=0.8)
    plt.axhline(df["TransferEfficiencyRatio"].mean(), color="black", linestyle="--", linewidth=1,
                label=f"Mean = {df['TransferEfficiencyRatio'].mean():.2f}")
    plt.title("Transfer Efficiency Ratio Over Time (Transfers / CBP Custody)")
    plt.legend()
    plt.tight_layout()
    p = os.path.join(FIG_DIR, "02_transfer_efficiency_over_time.png")
    plt.savefig(p, dpi=150); plt.close()
    paths["transfer_efficiency"] = p

    # 3. Discharge Effectiveness over time
    plt.figure(figsize=(9, 4))
    plt.plot(df["Date"], df["DischargeEffectiveness"], color="#8172B2", alpha=0.8)
    plt.axhline(df["DischargeEffectiveness"].mean(), color="black", linestyle="--", linewidth=1,
                label=f"Mean = {df['DischargeEffectiveness'].mean():.3f}")
    plt.title("Discharge Effectiveness Over Time (Discharges / HHS Care)")
    plt.legend()
    plt.tight_layout()
    p = os.path.join(FIG_DIR, "03_discharge_effectiveness_over_time.png")
    plt.savefig(p, dpi=150); plt.close()
    paths["discharge_effectiveness"] = p

    # 4. Backlog change (bottleneck detection)
    plt.figure(figsize=(9, 4))
    colors_ = ["#C44E52" if v > 0 else "#55A868" for v in df["BacklogChange"].fillna(0)]
    plt.bar(df["Date"], df["BacklogChange"], color=colors_, width=2)
    plt.title("Daily Net Change in Total Children in Care (Backlog Growth in Red)")
    plt.ylabel("Net Change")
    plt.tight_layout()
    p = os.path.join(FIG_DIR, "04_backlog_change.png")
    plt.savefig(p, dpi=150); plt.close()
    paths["backlog_change"] = p

    # 5. Weekday vs weekend transfer/discharge speed
    wk = df.groupby("IsWeekend")[["TransferEfficiencyRatio", "DischargeEffectiveness"]].mean()
    wk.index = ["Weekday", "Weekend"]
    plt.figure(figsize=(6, 4))
    wk.plot(kind="bar", ax=plt.gca(), color=["#4C72B0", "#DD8452"])
    plt.title("Weekday vs Weekend: Efficiency Metrics")
    plt.xticks(rotation=0)
    plt.tight_layout()
    p = os.path.join(FIG_DIR, "05_weekday_vs_weekend.png")
    plt.savefig(p, dpi=150); plt.close()
    paths["weekday_weekend"] = p

    # 6. Month-over-month discharge trend
    monthly = df.groupby("Month")["Discharged"].sum()
    plt.figure(figsize=(10, 4))
    plt.plot(monthly.index, monthly.values, marker="o", color="#4C72B0")
    plt.title("Month-over-Month Total Discharges")
    plt.xticks(rotation=90, fontsize=7)
    plt.tight_layout()
    p = os.path.join(FIG_DIR, "06_monthly_discharges.png")
    plt.savefig(p, dpi=150); plt.close()
    paths["monthly_discharges"] = p

    return paths


def identify_backlog_periods(df: pd.DataFrame, window: int = 14, min_streak: int = 5) -> pd.DataFrame:
    """Finds sustained periods where backlog change is consistently positive (accumulating)."""
    df = df.copy()
    df["BacklogGrowing"] = df["BacklogChange"] > 0
    df["StreakID"] = (df["BacklogGrowing"] != df["BacklogGrowing"].shift()).cumsum()
    streaks = (
        df[df["BacklogGrowing"]]
        .groupby("StreakID")
        .agg(Start=("Date", "min"), End=("Date", "max"), Days=("Date", "count"),
             TotalGrowth=("BacklogChange", "sum"))
    )
    streaks = streaks[streaks["Days"] >= min_streak].sort_values("TotalGrowth", ascending=False)
    return streaks


def write_reports(kpis: dict, df: pd.DataFrame, streaks: pd.DataFrame):
    wk = df.groupby("IsWeekend")[["TransferEfficiencyRatio", "DischargeEffectiveness"]].mean()
    weekday_transfer = wk.loc[False, "TransferEfficiencyRatio"] if False in wk.index else np.nan
    weekend_transfer = wk.loc[True, "TransferEfficiencyRatio"] if True in wk.index else np.nan

    date_min, date_max = df["Date"].min().strftime("%b %d, %Y"), df["Date"].max().strftime("%b %d, %Y")

    top_streak = streaks.iloc[0] if len(streaks) else None

    research = f"""# Care Transition Efficiency & Placement Outcome Analytics

## 1. Introduction
The Unaccompanied Alien Children (UAC) Program operates as a multi-stage care and reunification
pipeline: apprehension and CBP custody, transfer to HHS care, medical screening and case
management, and finally discharge to a vetted sponsor. This analysis shifts focus from raw
capacity counts to **process efficiency** — how fast, consistent, and reliable that pipeline is —
using {len(df)} daily reports spanning {date_min} to {date_max}.

## 2. Data Overview
- Daily records analyzed: **{len(df)}**
- Date range: **{date_min} to {date_max}**
- Total children apprehended (period): **{int(df['Apprehended'].sum()):,}**
- Total children discharged (period): **{int(df['Discharged'].sum()):,}**

## 3. Key Performance Indicators
| KPI | Value | Interpretation |
|---|---|---|
| Transfer Efficiency Ratio | {kpis['transfer_efficiency_ratio']} | Avg daily transfers out of CBP as a share of CBP custody |
| Discharge Effectiveness Index | {kpis['discharge_effectiveness_index']} | Avg daily discharges as a share of HHS care load |
| Pipeline Throughput | {kpis['pipeline_throughput']} | Total discharges ÷ total apprehensions over the period |
| Backlog Accumulation Rate | {kpis['backlog_accumulation_rate']} / day | Avg daily net change in total children in care (positive = growing backlog) |
| Outcome Stability Score | {kpis['outcome_stability_score']} | Consistency of discharge effectiveness (closer to 1 = more stable) |

## 4. Care Pipeline Volumes Over Time
See `figures/01_pipeline_volumes_over_time.png`. This tracks CBP custody and HHS care loads across
the full period, showing how the two stages of the pipeline rise and fall together (or diverge).

## 5. Transfer Efficiency (CBP → HHS)
See `figures/02_transfer_efficiency_over_time.png`. Average transfer efficiency ratio was
**{kpis['transfer_efficiency_ratio']}**, meaning on a typical day roughly
{'{:.0%}'.format(kpis['transfer_efficiency_ratio']) if kpis['transfer_efficiency_ratio'] and kpis['transfer_efficiency_ratio'] < 5 else 'a very high share'}
of the CBP custody population was transferred out to HHS.

## 6. Discharge Effectiveness
See `figures/03_discharge_effectiveness_over_time.png`. Average discharge effectiveness was
**{kpis['discharge_effectiveness_index']}**, i.e. HHS discharged roughly that fraction of its
active care load per day on average.

## 7. Backlog & Delay Identification
See `figures/04_backlog_change.png`. The system's total in-care population changed by an average of
**{kpis['backlog_accumulation_rate']} children/day** over the period.
{"The pipeline trended toward net backlog growth overall." if kpis['backlog_accumulation_rate'] > 0 else "The pipeline trended toward net backlog reduction overall."}

The most severe sustained backlog-accumulation period identified was
**{top_streak['Start'].strftime('%b %d, %Y') if top_streak is not None else 'N/A'} to {top_streak['End'].strftime('%b %d, %Y') if top_streak is not None else 'N/A'}**
({int(top_streak['Days']) if top_streak is not None else 0} days, net growth of
{int(top_streak['TotalGrowth']) if top_streak is not None else 0} children in care).

## 8. Temporal & Pattern Analysis
See `figures/05_weekday_vs_weekend.png` and `figures/06_monthly_discharges.png`.
Weekday avg transfer efficiency: **{round(weekday_transfer, 3)}**; weekend avg: **{round(weekend_transfer, 3)}**.
{"Weekday processing was notably faster than weekend processing." if (weekday_transfer or 0) > (weekend_transfer or 0) else "Weekend processing kept pace with, or exceeded, weekday processing."}

## 9. Outcome Stability
The Outcome Stability Score of **{kpis['outcome_stability_score']}** reflects how consistent daily
discharge effectiveness was across the period; lower scores indicate periods of sudden drops in
reunification throughput worth investigating operationally.

## 10. Recommendations
1. Target case-management staffing/resources at the identified backlog-accumulation windows
   (Section 7) to prevent recurrence.
2. Investigate the weekday/weekend efficiency gap — if weekend staffing is lighter, targeted
   coverage could smooth throughput.
3. Use the Outcome Stability Score as an ongoing operational health metric to flag sudden drops in
   discharge performance early.
4. Set threshold-based alerts (e.g. Transfer Efficiency Ratio or Discharge Effectiveness dropping
   below a defined floor) to surface emerging bottlenecks before they compound.

## 11. Conclusion
This analysis reframes the UAC dataset from a capacity-monitoring lens to a process-efficiency and
outcome-evaluation lens, surfacing where and when the CBP→HHS→sponsor pipeline slows down —
providing an evidence base for faster reunification and stronger child welfare outcomes.
"""

    with open(os.path.join(OUT_DIR, "research_paper.md"), "w") as f:
        f.write(research)

    exec_summary = f"""# Executive Summary — Care Transition Efficiency & Placement Outcomes

**Prepared for:** U.S. Department of Health and Human Services / policy stakeholders
**Scope:** {len(df)} daily reports, {date_min} to {date_max}

## Headline Numbers
- Transfer Efficiency Ratio: **{kpis['transfer_efficiency_ratio']}**
- Discharge Effectiveness Index: **{kpis['discharge_effectiveness_index']}**
- Pipeline Throughput (period): **{kpis['pipeline_throughput']}**
- Backlog Accumulation Rate: **{kpis['backlog_accumulation_rate']} children/day net**
- Outcome Stability Score: **{kpis['outcome_stability_score']}**

## What This Means
The care pipeline {"is trending toward backlog growth" if kpis['backlog_accumulation_rate'] > 0 else "is trending toward backlog reduction"},
with an average net change of {kpis['backlog_accumulation_rate']} children/day across both CBP
custody and HHS care combined. The most severe sustained backlog window ran
**{top_streak['Start'].strftime('%b %d, %Y') if top_streak is not None else 'N/A'} to {top_streak['End'].strftime('%b %d, %Y') if top_streak is not None else 'N/A'}**.

## Recommended Actions
1. Direct case-management resources toward recurring backlog windows.
2. Address the weekday/weekend processing gap through staffing adjustments.
3. Adopt the Outcome Stability Score as a standing operational KPI, with threshold alerts.

*Full methodology and charts are in `research_paper.md` and the `figures/` folder.*
"""

    with open(os.path.join(OUT_DIR, "executive_summary.md"), "w") as f:
        f.write(exec_summary)


def main():
    df = load_pipeline_data()
    df = compute_derived_metrics(df)

    kpis = compute_kpis(df)
    with open(os.path.join(OUT_DIR, "kpis.json"), "w") as f:
        json.dump(kpis, f, indent=2)

    make_charts(df)
    streaks = identify_backlog_periods(df)
    streaks.to_csv(os.path.join(OUT_DIR, "backlog_periods.csv"))

    write_reports(kpis, df, streaks)

    print("Done. See outputs/ for kpis.json, research_paper.md, executive_summary.md, figures/*.png")


if __name__ == "__main__":
    main()
