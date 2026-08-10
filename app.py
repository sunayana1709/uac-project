"""
Care Transition Efficiency & Placement Outcome Analytics — Streamlit Dashboard
Run with: streamlit run app.py
"""

import os
import sys

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
from data_loader import load_pipeline_data, compute_derived_metrics  # noqa: E402

st.set_page_config(page_title="UAC Care Transition Analytics", layout="wide")


@st.cache_data
def load_data():
    df = load_pipeline_data()
    df = compute_derived_metrics(df)
    return df


try:
    df = load_data()
except FileNotFoundError as e:
    st.error(str(e))
    st.stop()

# ---------- Sidebar: date range + toggles ----------
st.sidebar.header("Filters")

min_date, max_date = df["Date"].min().date(), df["Date"].max().date()
date_range = st.sidebar.date_input("Date Range", (min_date, max_date), min_value=min_date, max_value=max_date)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

metric_toggle = st.sidebar.radio(
    "Ratio Metric to Highlight",
    ["Transfer Efficiency Ratio", "Discharge Effectiveness", "Daily Throughput"],
)

st.sidebar.subheader("Threshold Alerts")
transfer_floor = st.sidebar.slider("Transfer Efficiency floor", 0.0, 3.0, 0.3, 0.05)
discharge_floor = st.sidebar.slider("Discharge Effectiveness floor", 0.0, 0.5, 0.02, 0.005)

f = df[(df["Date"].dt.date >= start_date) & (df["Date"].dt.date <= end_date)]

# ---------- Header + KPI cards ----------
st.title("🧭 Care Transition Efficiency & Placement Outcome Analytics")
st.caption("HHS Unaccompanied Alien Children (UAC) Program — CBP custody → HHS care → sponsor placement pipeline")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Transfer Efficiency Ratio", f"{f['TransferEfficiencyRatio'].mean():.3f}")
c2.metric("Discharge Effectiveness", f"{f['DischargeEffectiveness'].mean():.3f}")
throughput = f["Discharged"].sum() / f["Apprehended"].sum() if f["Apprehended"].sum() else np.nan
c3.metric("Pipeline Throughput", f"{throughput:.2f}" if not np.isnan(throughput) else "—")
c4.metric("Backlog Accum. Rate", f"{f['BacklogChange'].mean():+.1f} /day")
cv = f["DischargeEffectiveness"].std() / f["DischargeEffectiveness"].mean() if f["DischargeEffectiveness"].mean() else np.nan
stability = max(0, 1 - cv) if not np.isnan(cv) else np.nan
c5.metric("Outcome Stability", f"{stability:.2f}" if not np.isnan(stability) else "—")

# ---------- Threshold alerts ----------
alert_days_transfer = f[f["TransferEfficiencyRatio"] < transfer_floor]
alert_days_discharge = f[f["DischargeEffectiveness"] < discharge_floor]
if len(alert_days_transfer) or len(alert_days_discharge):
    st.warning(
        f"⚠️ {len(alert_days_transfer)} day(s) below Transfer Efficiency floor, "
        f"{len(alert_days_discharge)} day(s) below Discharge Effectiveness floor in the selected range."
    )
else:
    st.success("✅ No threshold breaches in the selected date range.")

st.divider()

tab1, tab2, tab3, tab4 = st.tabs([
    "🔀 Pipeline Flow", "⚙️ Efficiency Panels", "🚧 Bottleneck Detection", "📈 Outcome Trends"
])

with tab1:
    st.subheader("Care Pipeline Flow: CBP Custody vs HHS Care")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=f["Date"], y=f["CBP_Custody"], name="CBP Custody", line=dict(color="#C44E52")))
    fig.add_trace(go.Scatter(x=f["Date"], y=f["HHS_Care"], name="HHS Care", line=dict(color="#4C72B0")))
    fig.update_layout(title="Children in Care by Stage", yaxis_title="Children")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Daily Flow Volumes")
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=f["Date"], y=f["Apprehended"], name="Apprehended (in)", marker_color="#55A868"))
    fig2.add_trace(go.Bar(x=f["Date"], y=f["Discharged"], name="Discharged (out)", marker_color="#8172B2"))
    fig2.update_layout(barmode="overlay", title="Inflow (Apprehensions) vs Outflow (Discharges)")
    st.plotly_chart(fig2, use_container_width=True)

with tab2:
    st.subheader(f"{metric_toggle} Over Time")
    col_map = {
        "Transfer Efficiency Ratio": "TransferEfficiencyRatio",
        "Discharge Effectiveness": "DischargeEffectiveness",
        "Daily Throughput": "DailyThroughput",
    }
    col = col_map[metric_toggle]
    fig = px.line(f, x="Date", y=col, title=f"{metric_toggle} — Daily")
    fig.add_hline(y=f[col].mean(), line_dash="dash", annotation_text="Mean")
    st.plotly_chart(fig, use_container_width=True)

    colA, colB = st.columns(2)
    with colA:
        fig = px.histogram(f, x="TransferEfficiencyRatio", nbins=30, title="Transfer Efficiency Distribution")
        st.plotly_chart(fig, use_container_width=True)
    with colB:
        fig = px.histogram(f, x="DischargeEffectiveness", nbins=30, title="Discharge Effectiveness Distribution")
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("Backlog Accumulation (Bottleneck Detection)")
    colors_ = np.where(f["BacklogChange"].fillna(0) > 0, "#C44E52", "#55A868")
    fig = go.Figure(go.Bar(x=f["Date"], y=f["BacklogChange"], marker_color=colors_))
    fig.update_layout(title="Daily Net Change in Total Children in Care (red = backlog growing)")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Sustained Backlog-Growth Periods (14-day window, 5+ consecutive growth days)")
    df2 = f.copy()
    df2["BacklogGrowing"] = df2["BacklogChange"] > 0
    df2["StreakID"] = (df2["BacklogGrowing"] != df2["BacklogGrowing"].shift()).cumsum()
    streaks = (
        df2[df2["BacklogGrowing"]]
        .groupby("StreakID")
        .agg(Start=("Date", "min"), End=("Date", "max"), Days=("Date", "count"),
             TotalGrowth=("BacklogChange", "sum"))
    )
    streaks = streaks[streaks["Days"] >= 5].sort_values("TotalGrowth", ascending=False)
    st.dataframe(streaks, use_container_width=True)

with tab4:
    st.subheader("Weekday vs Weekend Efficiency")
    wk = f.groupby("IsWeekend")[["TransferEfficiencyRatio", "DischargeEffectiveness"]].mean()
    wk.index = ["Weekday", "Weekend"]
    fig = px.bar(wk.reset_index(), x="index", y=["TransferEfficiencyRatio", "DischargeEffectiveness"],
                 barmode="group", title="Weekday vs Weekend Processing Speed")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Month-over-Month Discharge Trend")
    monthly = f.groupby("Month")["Discharged"].sum().reset_index()
    fig = px.line(monthly, x="Month", y="Discharged", markers=True, title="Total Discharges by Month")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Outcome Stability — Rolling 30-day Coefficient of Variation")
    roll = f.set_index("Date")["DischargeEffectiveness"].rolling(30)
    rolling_cv = (roll.std() / roll.mean()).reset_index()
    rolling_cv.columns = ["Date", "RollingCV"]
    fig = px.line(rolling_cv, x="Date", y="RollingCV", title="Rolling 30-day Volatility of Discharge Effectiveness (lower = more stable)")
    st.plotly_chart(fig, use_container_width=True)

st.divider()
st.subheader("Raw Data (filtered)")
st.dataframe(
    f[["Date", "Apprehended", "CBP_Custody", "Transferred_Out_CBP", "HHS_Care", "Discharged",
       "TransferEfficiencyRatio", "DischargeEffectiveness"]],
    use_container_width=True, height=300
)
