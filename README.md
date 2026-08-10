# Care Transition Efficiency & Placement Outcome Analytics

Process-efficiency analytics for the HHS Unaccompanied Alien Children (UAC) Program care pipeline:
CBP custody → HHS care → sponsor placement.

```
uac_project/
├── data/
│   └── HHS_Unaccompanied_Alien_Children_Program.csv
├── src/
│   ├── data_loader.py         <- loads & cleans the daily pipeline data
│   ├── eda_analysis.py        <- computes KPIs, saves charts, writes reports
│   └── build_pdf_report.py    <- builds the polished PDF research paper
├── outputs/                   <- generated after you run eda_analysis.py
│   ├── kpis.json
│   ├── research_paper.md
│   ├── executive_summary.md
│   ├── backlog_periods.csv
│   ├── UAC_Research_Paper.pdf
│   └── figures/*.png
├── app.py                     <- Streamlit dashboard
└── requirements.txt
```

## 1. Install Python (one-time)
Python 3.10+ from https://www.python.org/downloads/ (Windows: tick "Add to PATH").
Check with `python --version` (or `python3 --version` on Mac/Linux).

## 2. Set up the project (one-time)

```bash
cd uac_project
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 3. Run the analysis (KPIs, charts, research paper, executive summary)

```bash
python src/eda_analysis.py
python src/build_pdf_report.py    # builds the polished PDF version
```

Outputs land in `outputs/`:
- `kpis.json` — the 5 KPIs from the brief
- `research_paper.md` — full EDA write-up with real numbers
- `executive_summary.md` — short stakeholder-facing summary
- `backlog_periods.csv` — every sustained backlog-accumulation window found
- `UAC_Research_Paper.pdf` — polished, submission-ready PDF with all charts embedded
- `figures/*.png` — the 6 charts referenced in the report

## 4. Run the live dashboard

```bash
streamlit run app.py
```

Opens a browser tab (usually `http://localhost:8501`) with:
- KPI cards + live threshold alerts
- **Pipeline Flow** — CBP vs HHS care over time, inflow vs outflow
- **Efficiency Panels** — toggle between Transfer Efficiency / Discharge Effectiveness / Throughput
- **Bottleneck Detection** — backlog change chart + sustained backlog-period table
- **Outcome Trends** — weekday vs weekend, month-over-month discharges, rolling stability
- Sidebar: date range picker, ratio toggle, adjustable threshold-alert sliders

Press `Ctrl+C` to stop it.

## 5. Next time you open the project

```bash
cd uac_project
source venv/bin/activate      # Windows: venv\Scripts\activate
streamlit run app.py
```

## Data notes
- The raw CSV has some numbers stored as comma-formatted strings (e.g. `"2,484"`) and ~450 trailing
  empty rows — `data_loader.py` handles both automatically.
- Valid data covers **720 daily reports** from **Jan 12, 2023** to **Dec 21, 2025**. Reporting days
  are irregular (mostly weekdays, sparse Fridays) — this is a property of the source data, not a bug.

## Troubleshooting
- **"Could not find the data file"** → confirm the CSV is in `data/` with its original filename.
- **`pip`/`python` not found** → use `pip3`/`python3` on Mac/Linux.
