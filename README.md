# Care Transition Efficiency & Placement Outcome Analytics

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://care-transition-analytics-enmyann9v6ewdfyv4ophmp.streamlit.app/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.49%2B-red.svg)](https://streamlit.io/)
[![Plotly](https://img.shields.io/badge/Plotly-5.18%2B-blueviolet.svg)](https://plotly.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> 🚀 **Live Production Deployment:** [https://care-transition-analytics-enmyann9v6ewdfyv4ophmp.streamlit.app/](https://care-transition-analytics-enmyann9v6ewdfyv4ophmp.streamlit.app/)

An end-to-end analytical framework, interactive decision-support dashboard, and policy research platform evaluating process efficiency, transition velocity, and placement outcomes across the **U.S. Unaccompanied Alien Children (UAC) care pipeline**.

Developed for **Unified Mentor** in collaboration with datasets from the **U.S. Department of Health and Human Services (HHS)** and **U.S. Customs and Border Protection (CBP)**.

---

## 🏛️ Executive Background & Problem Statement

The Unaccompanied Alien Children (UAC) Program operates as an inter-agency care and reunification pipeline:
1. **Apprehension & CBP Custody:** Short-term border patrol processing and security intake.
2. **Transfer Gate:** Handoff from CBP (DHS) to HHS Office of Refugee Resettlement (ORR).
3. **HHS Sheltered Care:** Medical screening, residential care, and case management.
4. **Sponsor Discharge:** Safe reunification with vetted parents, relatives, or legal guardians.

While government agencies regularly monitor aggregate custody headcounts, **process efficiency and flow velocity metrics have traditionally been absent**. Without structured transition analytics:
- Custodial transfer bottlenecks remain hidden until holding facilities overflow.
- Compliance with the 72-hour **Trafficking Victims Protection Reauthorization Act (TVPRA)** mandate cannot be dynamically monitored.
- Administrative batching on weekends decelerates family reunifications.
- Downstream shelter capacity cannot be accurately forecasted during intake surges.

This project reframes the UAC dataset from a static capacity-monitoring lens to a **dynamic process-efficiency and outcome-evaluation lens**.

---

## 📈 Key Performance Indicators (KPIs)

| KPI Name | Mathematical Formula | Operational Purpose |
| :--- | :---: | :--- |
| **Transfer Efficiency Ratio** | $\frac{\text{CBP Transfers}_t}{\text{CBP Custody}_t}$ | Measures CBP &rarr; HHS handoff velocity and turnover rate. |
| **Discharge Effectiveness Index** | $\frac{\text{HHS Discharges}_t}{\text{HHS Care}_t}$ | Evaluates daily placement success relative to shelter bed census. |
| **Pipeline Throughput Rate** | $\frac{\text{HHS Discharges}_t}{\text{Apprehended}_t}$ | Assesses whether exits keep pace with incoming border intake. |
| **Net Backlog Accumulation** | $\text{Apprehended}_t - \text{HHS Discharges}_t$ | Tracks daily deficit and cumulative system backlogs. |
| **Estimated CBP Turnover Time** | $\frac{\text{CBP Custody}_t}{\text{CBP Transfers}_t}$ | Little's Law queue residence proxy ($W = L / \lambda$) for TVPRA 72h limit. |
| **Estimated HHS Length of Stay** | $\frac{\text{HHS Care}_t}{\text{HHS Discharges}_t}$ | Little's Law queue residence proxy for shelter stay duration. |
| **Outcome Stability Score** | $\frac{100}{1 + \text{CV}_{30d}(\text{Discharges})}$ | Quantifies consistency and predictability of reunifications (0–100). |

---

## 🚀 Key Features & Dashboard Modules

The application is built with **Streamlit** and **Plotly** to provide executive-grade decision support:

1. **Care Pipeline Flow Visualization:**
   - Multi-stage interactive **Sankey Diagram** mapping end-to-end cohort movements.
   - Dual-axis institutional stock timelines (CBP holding buffer vs. HHS shelter census).
   - Inflow vs. outflow daily comparative bars.
2. **Transfer & Discharge Efficiency Panels:**
   - Dynamic tracking of Transfer Efficiency and Discharge Effectiveness with 7-day and 30-day moving averages.
   - TVPRA 72-hour compliance gauge and distribution histograms.
3. **Bottleneck Detection & Backlog Diagnostics:**
   - Daily net accumulation and cumulative deficit curves.
   - Automated detection of sustained bottleneck episodes ($\ge 5$ consecutive days of inflow surplus).
4. **Temporal Dynamics & Friction Analysis:**
   - Day-of-week breakdown exposing weekend administrative slowdowns and Thursday/Sunday batching.
   - Month-over-month aggregate volume trends from 2023 through 2025.
5. **Outcome Stability & Anomaly Diagnostic:**
   - 30-day rolling Outcome Stability Score tracking placement volatility.
   - Multidimensional anomaly detection powered by `IsolationForest` and statistical Z-Scores.
6. **Policy & Surge Stress-Testing Simulator:**
   - Forward discrete-flow simulation (30 to 120 days) testing intake shocks (0.2x to 3.0x), transfer capacity adjustments, and sponsor case management acceleration.
7. **Automated Official Deliverables:**
   - One-click downloads for the **Executive Briefing PDF** and **Full Research Paper PDF** (generated using ReportLab).
   - Filtered dataset export in CSV format.

---

## 📂 Repository Structure

```
care-transition-analytics/
├── data/
│   └── HHS_Unaccompanied_Alien_Children_Program.csv  # Cleaned official daily dataset
├── src/
│   ├── __init__.py
│   ├── data_loader.py          # Data ingestion, date alignment, feature engineering
│   ├── pipeline_metrics.py     # KPI formulas, queueing metrics, backlog tracking
│   ├── anomaly_detector.py     # Isolation Forest & statistical threshold alerts
│   ├── scenario_simulator.py   # Discrete-time queueing & what-if policy simulator
│   └── pdf_exporter.py         # ReportLab publication PDF generator
├── reports/
│   ├── Executive_Briefing_HHS_CBP.pdf                # Generated Executive Policy Memo
│   └── Care_Transition_Analytics_Research_Paper.pdf  # Generated Formal Research Paper
├── tests/
│   └── test_analytics.py       # Unit tests verifying mathematical consistency & Little's Law
├── app.py                      # Interactive multi-tab Streamlit dashboard
├── EXECUTIVE_SUMMARY.md        # Executive briefing document for government stakeholders
├── RESEARCH_PAPER.md           # Formal academic/policy research paper
├── requirements.txt            # Python dependencies
└── README.md                   # Project documentation
```

---

## 🛠️ Quickstart Installation & Execution

### 1. Prerequisites
- Python 3.10+ installed.

### 2. Install Dependencies
```bash
cd E:\agy-cli\care-transition-analytics
pip install -r requirements.txt
```

### 3. Run Automated Unit Tests
```bash
python tests/test_analytics.py
```
*All 7 unit tests validate data integrity, metric boundaries, Little's Law relationships, and simulation stability.*

### 4. Launch the Streamlit Web Application
```bash
streamlit run app.py
```
Once launched, open your browser to `http://localhost:8501`.

---

## 📑 Deliverables Included in this Submission

1. **Interactive Streamlit Web Dashboard (`app.py`):** Live analytics, scenario simulator, and alerts.
2. **Executive Summary for Government Stakeholders (`EXECUTIVE_SUMMARY.md`):** High-level decision briefing for HHS Secretary, ORR Director, and CBP leadership.
3. **Comprehensive Research Paper (`RESEARCH_PAPER.md`):** Full academic research paper covering statutory context, queueing theory derivations, empirical findings, and policy reforms.
4. **Publication-Ready PDF Reports (`reports/`):**
   - `reports/Executive_Briefing_HHS_CBP.pdf`
   - `reports/Care_Transition_Analytics_Research_Paper.pdf`

---

## ⚖️ Legal & Statutory References
- **TVPRA of 2008:** 8 U.S.C. § 1232 (72-hour transfer mandate).
- **Homeland Security Act of 2002:** 6 U.S.C. § 279 (ORR custody mandate).
- **Flores Settlement Agreement:** CV 85-4544-RJK (C.D. Cal. 1997).
