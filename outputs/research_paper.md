# Care Transition Efficiency & Placement Outcome Analytics

## 1. Introduction
The Unaccompanied Alien Children (UAC) Program operates as a multi-stage care and reunification
pipeline: apprehension and CBP custody, transfer to HHS care, medical screening and case
management, and finally discharge to a vetted sponsor. This analysis shifts focus from raw
capacity counts to **process efficiency** — how fast, consistent, and reliable that pipeline is —
using 720 daily reports spanning Jan 12, 2023 to Dec 21, 2025.

## 2. Data Overview
- Daily records analyzed: **720**
- Date range: **Jan 12, 2023 to Dec 21, 2025**
- Total children apprehended (period): **67,337**
- Total children discharged (period): **124,853**

## 3. Key Performance Indicators
| KPI | Value | Interpretation |
|---|---|---|
| Transfer Efficiency Ratio | 0.691 | Avg daily transfers out of CBP as a share of CBP custody |
| Discharge Effectiveness Index | 0.024 | Avg daily discharges as a share of HHS care load |
| Pipeline Throughput | 1.854 | Total discharges ÷ total apprehensions over the period |
| Backlog Accumulation Rate | -5.73 / day | Avg daily net change in total children in care (positive = growing backlog) |
| Outcome Stability Score | 0.439 | Consistency of discharge effectiveness (closer to 1 = more stable) |

## 4. Care Pipeline Volumes Over Time
See `figures/01_pipeline_volumes_over_time.png`. This tracks CBP custody and HHS care loads across
the full period, showing how the two stages of the pipeline rise and fall together (or diverge).

## 5. Transfer Efficiency (CBP → HHS)
See `figures/02_transfer_efficiency_over_time.png`. Average transfer efficiency ratio was
**0.691**, meaning on a typical day roughly
69%
of the CBP custody population was transferred out to HHS.

## 6. Discharge Effectiveness
See `figures/03_discharge_effectiveness_over_time.png`. Average discharge effectiveness was
**0.024**, i.e. HHS discharged roughly that fraction of its
active care load per day on average.

## 7. Backlog & Delay Identification
See `figures/04_backlog_change.png`. The system's total in-care population changed by an average of
**-5.73 children/day** over the period.
The pipeline trended toward net backlog reduction overall.

The most severe sustained backlog-accumulation period identified was
**Jul 31, 2023 to Aug 17, 2023**
(11 days, net growth of
1965 children in care).

## 8. Temporal & Pattern Analysis
See `figures/05_weekday_vs_weekend.png` and `figures/06_monthly_discharges.png`.
Weekday avg transfer efficiency: **0.689**; weekend avg: **0.7**.
Weekend processing kept pace with, or exceeded, weekday processing.

## 9. Outcome Stability
The Outcome Stability Score of **0.439** reflects how consistent daily
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
