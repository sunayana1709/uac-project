"""
data_loader.py
Loads and cleans the HHS Unaccompanied Alien Children (UAC) Program daily report.

Expected file: data/HHS_Unaccompanied_Alien_Children_Program.csv
Columns (raw):
  Date, Children apprehended and placed in CBP custody*, Children in CBP custody,
  Children transferred out of CBP custody, Children in HHS Care,
  Children discharged from HHS Care
"""

import os
import pandas as pd

DEFAULT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "HHS_Unaccompanied_Alien_Children_Program.csv"
)

RENAME_MAP = {
    "Date": "Date",
    "Children apprehended and placed in CBP custody*": "Apprehended",
    "Children apprehended and placed in CBP custody": "Apprehended",
    "Children in CBP custody": "CBP_Custody",
    "Children transferred out of CBP custody": "Transferred_Out_CBP",
    "Children in HHS Care": "HHS_Care",
    "Children discharged from HHS Care": "Discharged",
}


def _clean_numeric(series: pd.Series) -> pd.Series:
    """Handle numbers stored as strings with thousands separators (e.g. '2,484')."""
    return pd.to_numeric(
        series.astype(str).str.replace(",", "", regex=False).str.strip(),
        errors="coerce",
    )


def load_pipeline_data(path: str = DEFAULT_PATH) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Could not find the data file at '{path}'.\n"
            "Place 'HHS_Unaccompanied_Alien_Children_Program.csv' into the data/ folder."
        )

    df = pd.read_csv(path)
    df = df.rename(columns={k: v for k, v in RENAME_MAP.items() if k in df.columns})

    # Drop fully-empty trailing/footer rows
    df = df.dropna(subset=["Date"]).copy()

    # Parse date (format like "December 21, 2025")
    df["Date"] = pd.to_datetime(df["Date"], format="%B %d, %Y", errors="coerce")
    df = df.dropna(subset=["Date"])

    numeric_cols = ["Apprehended", "CBP_Custody", "Transferred_Out_CBP", "HHS_Care", "Discharged"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = _clean_numeric(df[col])

    df = df.sort_values("Date").reset_index(drop=True)
    df["Weekday"] = df["Date"].dt.day_name()
    df["IsWeekend"] = df["Date"].dt.dayofweek.isin([5, 6])
    df["Month"] = df["Date"].dt.to_period("M").astype(str)

    return df


def compute_derived_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Adds daily process-efficiency metrics to the dataframe."""
    df = df.copy()

    # Transfer Efficiency Ratio = Transfers out of CBP / CBP Custody
    df["TransferEfficiencyRatio"] = df["Transferred_Out_CBP"] / df["CBP_Custody"].replace(0, pd.NA)

    # Discharge Effectiveness = Discharges / HHS Care
    df["DischargeEffectiveness"] = df["Discharged"] / df["HHS_Care"].replace(0, pd.NA)

    # Net daily change in total system backlog (CBP custody + HHS care)
    df["TotalInCare"] = df["CBP_Custody"] + df["HHS_Care"]
    df["BacklogChange"] = df["TotalInCare"].diff()

    # Daily throughput: exits (discharges) vs entries (new apprehensions)
    df["DailyThroughput"] = df["Discharged"] / df["Apprehended"].replace(0, pd.NA)

    return df


if __name__ == "__main__":
    df = load_pipeline_data()
    df = compute_derived_metrics(df)
    print(df.shape)
    print(df.head())
    print(df.describe())
