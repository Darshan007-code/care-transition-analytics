"""
Care Transition Efficiency & Placement Outcome Analytics
Interactive Streamlit Web Dashboard for UAC Pipeline Evaluation.
U.S. Department of Health and Human Services (HHS) & Customs and Border Protection (CBP).
Unified Mentor Research Project.
"""

import os
import sys
from datetime import datetime
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data_loader import get_prepared_dataset
from src.pipeline_metrics import (
    compute_executive_kpis,
    analyze_day_of_week_dynamics,
    analyze_monthly_trends,
    generate_sankey_data,
    detect_bottleneck_episodes
)
from src.anomaly_detector import detect_discharge_anomalies, get_active_alerts_summary
from src.scenario_simulator import run_pipeline_simulation
from src.pdf_exporter import generate_executive_briefing_pdf, generate_research_paper_pdf


# ---------------------------------------------------------
# Page Configuration & Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="Care Transition Efficiency & Placement Outcomes",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Federal Policy / HHS Executive Aesthetic)
st.markdown("""
<style>
    /* Metric Cards */
    .metric-card {
        background: #ffffff;
        border-radius: 8px;
        padding: 16px 20px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.06);
        border-left: 4px solid #1B365D;
        margin-bottom: 12px;
    }
    .metric-title {
        font-size: 0.82rem;
        font-weight: 600;
        color: #555555;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-value {
        font-size: 1.85rem;
        font-weight: 700;
        color: #1B365D;
        margin-top: 4px;
        margin-bottom: 2px;
    }
    .metric-subtitle {
        font-size: 0.78rem;
        color: #777777;
    }
    .alert-badge-danger {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.8rem;
        background-color: #F8D7DA;
        color: #721C24;
        border: 1px solid #F5C6CB;
    }
    .alert-badge-warning {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.8rem;
        background-color: #FFF3CD;
        color: #856404;
        border: 1px solid #FFEEBA;
    }
    .alert-badge-success {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.8rem;
        background-color: #D4EDDA;
        color: #155724;
        border: 1px solid #C3E6CB;
    }
    /* Section Headers */
    .section-title {
        color: #1B365D;
        font-weight: 700;
        border-bottom: 2px solid #E2E8F0;
        padding-bottom: 6px;
        margin-top: 18px;
        margin-bottom: 14px;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# Data Loading & Session Cache
# ---------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_and_cache_data():
    data_path = os.path.join(os.path.dirname(__file__), "data", "HHS_Unaccompanied_Alien_Children_Program.csv")
    df = get_prepared_dataset(data_path)
    df = detect_discharge_anomalies(df)
    return df


full_df = load_and_cache_data()


# ---------------------------------------------------------
# Sidebar Controls & User Configuration
# ---------------------------------------------------------
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/United_States_Department_of_Health_and_Human_Services_seal.svg/200px-United_States_Department_of_Health_and_Human_Services_seal.svg.png", width=70)
st.sidebar.title("Pipeline Controls")
st.sidebar.caption("UAC Care Transition & Placement Analytics")

# Quick Period Presets
preset = st.sidebar.selectbox(
    "Reporting Cohort Preset",
    ["Full Historical (2023 - 2025)", "2023 Baseline", "2024 Surge Phase", "2025 Policy Retraction", "Custom Date Range"]
)

min_date = full_df['Date'].min().date()
max_date = full_df['Date'].max().date()

if preset == "2023 Baseline":
    default_start = datetime(2023, 1, 1).date()
    default_end = datetime(2023, 12, 31).date()
elif preset == "2024 Surge Phase":
    default_start = datetime(2024, 1, 1).date()
    default_end = datetime(2024, 12, 31).date()
elif preset == "2025 Policy Retraction":
    default_start = datetime(2025, 1, 1).date()
    default_end = datetime(2025, 12, 31).date()
else:
    default_start = min_date
    default_end = max_date

# Date range selector
date_range = st.sidebar.date_input(
    "Select Reporting Window",
    value=(default_start, default_end),
    min_value=min_date,
    max_value=max_date
)

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_filter, end_filter = date_range
else:
    start_filter, end_filter = default_start, default_end

# Filter dataset
mask = (full_df['Date'].dt.date >= start_filter) & (full_df['Date'].dt.date <= end_filter)
filtered_df = full_df[mask].copy().reset_index(drop=True)

if filtered_df.empty:
    st.error("No reporting records found in the selected date range. Please broaden your selection.")
    st.stop()

# Metric Smoothing Toggle
st.sidebar.markdown("---")
st.sidebar.subheader("Metric Smoothing")
smoothing_option = st.sidebar.radio(
    "Moving Average Display",
    ["Raw Daily", "7-Day Moving Average", "30-Day Moving Average"],
    index=1
)

ma_suffix = ""
if smoothing_option == "7-Day Moving Average":
    ma_suffix = "_MA7"
elif smoothing_option == "30-Day Moving Average":
    ma_suffix = "_MA30"

# Alert Threshold Configurations
st.sidebar.markdown("---")
st.sidebar.subheader("Threshold Alert Settings")
cbp_trans_thresh = st.sidebar.slider(
    "CBP Transfer Efficiency Minimum (%)",
    min_value=20, max_value=80, value=40, step=5,
    help="Flags alert when Transfer Efficiency Ratio drops below this legal turnover limit."
) / 100.0

backlog_surge_thresh = st.sidebar.slider(
    "Net System Backlog Surge Alert (Children/Day)",
    min_value=10, max_value=150, value=50, step=10,
    help="Triggers backlog warning when daily intake exceeds discharges by this margin."
)

st.sidebar.markdown("---")
st.sidebar.info(
    "**Operational Note:**\n"
    "By TVPRA mandate, CBP must transfer minors to HHS within 72 hours (3 days). "
    "A Transfer Efficiency Ratio >= 0.33 indicates continuous 3-day turnover compliance."
)


# ---------------------------------------------------------
# Header & Executive Summary Scorecards
# ---------------------------------------------------------
kpis = compute_executive_kpis(filtered_df)

st.title("Care Transition Efficiency & Placement Outcome Analytics")
st.markdown(
    f"**U.S. Department of Health and Human Services (HHS) & Customs and Border Protection (CBP)** | "
    f"Reporting Period: `{start_filter.strftime('%b %d, %Y')}` to `{end_filter.strftime('%b %d, %Y')}` "
    f"({kpis.get('days_analyzed', 0)} Active Reports)"
)

# Executive KPI Cards (Row 1)
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    eff = kpis.get('mean_transfer_efficiency', 0) * 100.0
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Transfer Efficiency</div>
        <div class="metric-value">{eff:.1f}%</div>
        <div class="metric-subtitle">Transfers ÷ CBP Custody (Target: >70%)</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    disc_eff = kpis.get('mean_discharge_effectiveness', 0) * 100.0
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Discharge Effectiveness</div>
        <div class="metric-value">{disc_eff:.2f}%</div>
        <div class="metric-subtitle">Discharges ÷ HHS Care Census</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    tp = kpis.get('global_throughput', 0)
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Pipeline Throughput</div>
        <div class="metric-value">{tp:.2f}x</div>
        <div class="metric-subtitle">Total Discharges ÷ Total Intake</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    tvpra = kpis.get('tvpra_compliance_pct', 0)
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">TVPRA 72h Compliance</div>
        <div class="metric-value">{tvpra:.1f}%</div>
        <div class="metric-subtitle">Days Meeting 72-Hour Turnover</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    stability = kpis.get('mean_stability_score', 0)
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Outcome Stability</div>
        <div class="metric-value">{stability:.1f} <span style="font-size:1rem;color:#777">/100</span></div>
        <div class="metric-subtitle">Reunification Consistency Index</div>
    </div>
    """, unsafe_allow_html=True)

# Secondary System Volumes (Row 2)
vcol1, vcol2, vcol3, vcol4, vcol5 = st.columns(5)
with vcol1:
    st.metric("Total Apprehended", f"{kpis.get('total_intake', 0):,}")
with vcol2:
    st.metric("Total Transferred", f"{kpis.get('total_transfers', 0):,}")
with vcol3:
    st.metric("Total Sponsor Placements", f"{kpis.get('total_discharges', 0):,}")
with vcol4:
    st.metric("Avg CBP Residence Time", f"{kpis.get('avg_cbp_residence_days', 0):.1f} Days")
with vcol5:
    st.metric("Avg HHS Length of Stay", f"{kpis.get('avg_hhs_residence_days', 0):.1f} Days")


# ---------------------------------------------------------
# Operational Alert Banner
# ---------------------------------------------------------
alerts = get_active_alerts_summary(filtered_df)
cbp_alerts = (filtered_df['Transfer_Efficiency_Ratio'] < cbp_trans_thresh).sum()
backlog_alerts = (filtered_df['Total_System_Net_Change'] > backlog_surge_thresh).sum()

alert_cols = st.columns([1, 1, 1, 3])
with alert_cols[0]:
    if cbp_alerts > 0:
        st.markdown(f'<div class="alert-badge-danger">⚠️ {cbp_alerts} CBP Transfer Slowdowns</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="alert-badge-success">✅ CBP Transfer Speed Normal</div>', unsafe_allow_html=True)
with alert_cols[1]:
    if backlog_alerts > 0:
        st.markdown(f'<div class="alert-badge-warning">⚠️ {backlog_alerts} Net Backlog Surges</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="alert-badge-success">✅ Backlog Balance Stable</div>', unsafe_allow_html=True)
with alert_cols[2]:
    if alerts['high_severity_count'] > 0:
        st.markdown(f'<div class="alert-badge-danger">🚨 {alerts["high_severity_count"]} High ML Anomalies</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="alert-badge-success">✅ ML Risk Baseline Normal</div>', unsafe_allow_html=True)
with alert_cols[3]:
    st.caption("Active monitoring thresholds applied from sidebar controls. Anomalies detected via Isolation Forest & Statistical Z-Scores.")


# ---------------------------------------------------------
# Core Navigation Tabs
# ---------------------------------------------------------
tab_flow, tab_efficiency, tab_bottlenecks, tab_patterns, tab_stability, tab_simulator, tab_data = st.tabs([
    "🌊 Care Pipeline Flow",
    "⚡ Transfer & Discharge Efficiency",
    "🛑 Bottlenecks & Backlog Diagnostic",
    "📅 Temporal & Pattern Dynamics",
    "🎯 Outcome Stability & Anomalies",
    "🧪 Policy & Surge Simulator",
    "📊 Data Explorer & Executive Reports"
])


# =========================================================
# TAB 1: Care Pipeline Flow Visualization
# =========================================================
with tab_flow:
    st.subheader("End-to-End Care Pipeline Flow Visualization")
    st.markdown(
        "Interactive Sankey diagram tracking aggregate cohort movements across all transition stages: "
        "**Apprehension &rarr; CBP Holding &rarr; Inter-Agency Gate &rarr; HHS Shelters &rarr; Sponsor Placement**."
    )

    sankey_data = generate_sankey_data(filtered_df)

    fig_sankey = go.Figure(data=[go.Sankey(
        node=dict(
            pad=20,
            thickness=25,
            line=dict(color="black", width=0.5),
            label=sankey_data['labels'],
            color=sankey_data['colors']
        ),
        link=dict(
            source=sankey_data['sources'],
            target=sankey_data['targets'],
            value=sankey_data['values'],
            color="rgba(180, 200, 220, 0.45)"
        )
    )])
    fig_sankey.update_layout(
        title_text="Care Transition Stage Flow Volumes (Selected Date Range)",
        font_size=12,
        height=420,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig_sankey, use_container_width=True)

    # Stock & Flow Comparative Timelines
    st.markdown("### Active Institutional Inventory (Stock) vs Movement (Flow)")
    flow_col1, flow_col2 = st.columns(2)

    with flow_col1:
        fig_stock = go.Figure()
        fig_stock.add_trace(go.Scatter(
            x=filtered_df['Date'],
            y=filtered_df['HHS_Care' + ma_suffix] if ('HHS_Care' + ma_suffix) in filtered_df else filtered_df['HHS_Care'],
            name="HHS Active Care Census",
            line=dict(color="#1f77b4", width=2.5),
            fill='tozeroy',
            fillcolor='rgba(31, 119, 180, 0.1)'
        ))
        fig_stock.update_layout(
            title="HHS Active Shelter Bed Census (Total In-Care Roster)",
            xaxis_title="Date",
            yaxis_title="Children in Care",
            height=350,
            hovermode="x unified"
        )
        st.plotly_chart(fig_stock, use_container_width=True)

    with flow_col2:
        fig_cbp = go.Figure()
        fig_cbp.add_trace(go.Scatter(
            x=filtered_df['Date'],
            y=filtered_df['CBP_Custody' + ma_suffix] if ('CBP_Custody' + ma_suffix) in filtered_df else filtered_df['CBP_Custody'],
            name="CBP Custody Load",
            line=dict(color="#ff7f0e", width=2),
            fill='tozeroy',
            fillcolor='rgba(255, 127, 14, 0.15)'
        ))
        # Add TVPRA advisory threshold line
        fig_cbp.add_hline(y=300, line_dash="dash", line_color="red", annotation_text="High Custody Stress Advisory (300)")
        fig_cbp.update_layout(
            title="CBP Custody Roster (Short-Term Holding Buffer)",
            xaxis_title="Date",
            yaxis_title="Children in CBP Custody",
            height=350,
            hovermode="x unified"
        )
        st.plotly_chart(fig_cbp, use_container_width=True)

    # Daily Intake vs Daily Sponsor Placement
    st.markdown("### Daily Inflow (Apprehensions) vs Outflow (Discharges)")
    fig_inout = go.Figure()
    fig_inout.add_trace(go.Bar(
        x=filtered_df['Date'],
        y=filtered_df['Apprehended'],
        name="Daily Apprehensions (Inflow)",
        marker_color="rgba(235, 87, 87, 0.7)"
    ))
    fig_inout.add_trace(go.Bar(
        x=filtered_df['Date'],
        y=filtered_df['HHS_Discharges'],
        name="Daily Discharges (Reunifications)",
        marker_color="rgba(39, 174, 96, 0.7)"
    ))
    fig_inout.update_layout(
        barmode='group',
        title="Intake vs Successful Reunifications per Reporting Date",
        xaxis_title="Date",
        yaxis_title="Children Count",
        height=360,
        hovermode="x unified"
    )
    st.plotly_chart(fig_inout, use_container_width=True)


# =========================================================
# TAB 2: Transfer & Discharge Efficiency Panels
# =========================================================
with tab_efficiency:
    st.subheader("Process Velocity & Efficiency Metrics")
    st.markdown(
        "Evaluating transition speed: **Transfer Efficiency Ratio** measures CBP &rarr; HHS handoff velocity; "
        "**Discharge Effectiveness** measures sponsor placement speed relative to shelter capacity."
    )

    eff_col1, eff_col2 = st.columns(2)

    with eff_col1:
        fig_te = go.Figure()
        fig_te.add_trace(go.Scatter(
            x=filtered_df['Date'],
            y=filtered_df['Transfer_Efficiency_Ratio'],
            name="Daily Transfer Ratio",
            mode='markers',
            marker=dict(color="#3498db", size=4, opacity=0.4)
        ))
        fig_te.add_trace(go.Scatter(
            x=filtered_df['Date'],
            y=filtered_df['Transfer_Efficiency_MA7'],
            name="7-Day Moving Avg",
            line=dict(color="#1B365D", width=2.5)
        ))
        fig_te.add_trace(go.Scatter(
            x=filtered_df['Date'],
            y=filtered_df['Transfer_Efficiency_MA30'],
            name="30-Day Moving Avg",
            line=dict(color="#f39c12", width=2, dash="dot")
        ))
        # TVPRA 72h benchmark: >= 0.33 turnover per day
        fig_te.add_hline(y=0.333, line_dash="dash", line_color="#e74c3c", annotation_text="TVPRA 72h Compliance Bound (0.33)")
        fig_te.update_layout(
            title="Transfer Efficiency Ratio (Transfers ÷ CBP Custody)",
            xaxis_title="Date",
            yaxis_title="Ratio (Daily Turnover)",
            height=380,
            hovermode="x unified"
        )
        st.plotly_chart(fig_te, use_container_width=True)

    with eff_col2:
        fig_de = go.Figure()
        fig_de.add_trace(go.Scatter(
            x=filtered_df['Date'],
            y=filtered_df['Discharge_Effectiveness'] * 100.0,
            name="Daily Effectiveness (%)",
            mode='markers',
            marker=dict(color="#2ecc71", size=4, opacity=0.4)
        ))
        fig_de.add_trace(go.Scatter(
            x=filtered_df['Date'],
            y=filtered_df['Discharge_Effectiveness_MA7'] * 100.0,
            name="7-Day Moving Avg (%)",
            line=dict(color="#27ae60", width=2.5)
        ))
        fig_de.add_trace(go.Scatter(
            x=filtered_df['Date'],
            y=filtered_df['Discharge_Effectiveness_MA30'] * 100.0,
            name="30-Day Moving Avg (%)",
            line=dict(color="#8e44ad", width=2, dash="dot")
        ))
        fig_de.update_layout(
            title="Discharge Effectiveness Index (Discharges ÷ HHS Care %)",
            xaxis_title="Date",
            yaxis_title="Daily Discharge Rate (%)",
            height=380,
            hovermode="x unified"
        )
        st.plotly_chart(fig_de, use_container_width=True)

    # Queue Residence Time & Turnover Days (Little's Law)
    st.markdown("### Little's Law Queue Residence Time Estimates")
    st.caption("Estimated days required to clear active custody at current transition velocities: W = L / λ")

    res_col1, res_col2 = st.columns(2)
    with res_col1:
        fig_cbp_days = px.histogram(
            filtered_df[filtered_df['Est_CBP_Turnover_Days'] <= 7],
            x="Est_CBP_Turnover_Days",
            nbins=35,
            title="Distribution of Estimated CBP Custody Residence Time (Days)",
            labels={"Est_CBP_Turnover_Days": "Estimated Turnover Days (CBP)"},
            color_discrete_sequence=["#2980b9"]
        )
        fig_cbp_days.add_vline(x=3.0, line_dash="dash", line_color="red", annotation_text="TVPRA 72h Limit (3 Days)")
        fig_cbp_days.update_layout(height=320)
        st.plotly_chart(fig_cbp_days, use_container_width=True)

    with res_col2:
        fig_hhs_days = px.histogram(
            filtered_df[filtered_df['Est_HHS_Stay_Days'] <= 100],
            x="Est_HHS_Stay_Days",
            nbins=35,
            title="Distribution of Estimated HHS Care Length of Stay (Days)",
            labels={"Est_HHS_Stay_Days": "Estimated Length of Stay (HHS Shelters)"},
            color_discrete_sequence=["#16a085"]
        )
        fig_hhs_days.add_vline(x=35.0, line_dash="dash", line_color="#d35400", annotation_text="ORR Historical Baseline (35 Days)")
        fig_hhs_days.update_layout(height=320)
        st.plotly_chart(fig_hhs_days, use_container_width=True)


# =========================================================
# TAB 3: Bottlenecks & Backlog Diagnostic
# =========================================================
with tab_bottlenecks:
    st.subheader("Bottleneck Detection & Backlog Diagnostics")
    st.markdown(
        "Identifying sustained imbalance periods where border apprehension volume exceeds downstream sponsor discharges, "
        "causing systemic backlogs to accumulate in holding facilities and shelters."
    )

    # Daily Net Balance vs Cumulative Backlog
    b_col1, b_col2 = st.columns(2)

    with b_col1:
        # Net Daily Balance (Apprehended - Discharged)
        fig_net = go.Figure()
        colors_net = np.where(filtered_df['Total_System_Net_Change'] > 0, '#e74c3c', '#27ae60')
        fig_net.add_trace(go.Bar(
            x=filtered_df['Date'],
            y=filtered_df['Total_System_Net_Change'],
            marker_color=colors_net,
            name="Daily Net Accumulation"
        ))
        fig_net.add_hline(y=backlog_surge_thresh, line_dash="dash", line_color="orange", annotation_text="Surge Threshold")
        fig_net.update_layout(
            title="Daily System Net Flow (Intake − Discharges)",
            xaxis_title="Date",
            yaxis_title="Net Children Added / Cleared",
            height=370,
            hovermode="x unified"
        )
        st.plotly_chart(fig_net, use_container_width=True)

    with b_col2:
        # Cumulative Backlog Curve
        fig_cum = go.Figure()
        fig_cum.add_trace(go.Scatter(
            x=filtered_df['Date'],
            y=filtered_df['Cumulative_System_Backlog'],
            name="Net Cumulative System Backlog",
            line=dict(color="#8e44ad", width=2.5),
            fill='tozeroy',
            fillcolor='rgba(142, 68, 173, 0.1)'
        ))
        fig_cum.update_layout(
            title="Cumulative Net Inflow-Exit Gap Trajectory",
            xaxis_title="Date",
            yaxis_title="Cumulative Net Balance",
            height=370,
            hovermode="x unified"
        )
        st.plotly_chart(fig_cum, use_container_width=True)

    # Bottleneck Episodes Table
    st.markdown("### Sustained Bottleneck Episodes (Inflows > Discharges for >= 5 Consecutive Reports)")
    episodes_df = detect_bottleneck_episodes(filtered_df, min_consecutive_days=5)
    if not episodes_df.empty:
        st.dataframe(
            episodes_df.style.background_gradient(subset=['Accumulated_Backlog'], cmap='Reds'),
            use_container_width=True
        )
    else:
        st.info("No sustained bottleneck episodes (>= 5 consecutive days of inflow deficit) detected in the selected timeframe.")

    # CBP Handoff Friction: Apprehended vs Transferred
    st.markdown("### CBP Custodial Flow Balance (Apprehended vs Transferred to HHS)")
    fig_cbp_balance = go.Figure()
    fig_cbp_balance.add_trace(go.Scatter(
        x=filtered_df['Date'],
        y=filtered_df['CBP_Net_Change'],
        name="CBP Daily Net Intake Gap",
        line=dict(color="#e67e22", width=1.8)
    ))
    fig_cbp_balance.add_hline(y=0, line_dash="solid", line_color="gray")
    fig_cbp_balance.update_layout(
        title="CBP Custodial Net Intake Gap (Apprehensions − Transfers to HHS)",
        xaxis_title="Date",
        yaxis_title="Net CBP Accumulation",
        height=320,
        hovermode="x unified"
    )
    st.plotly_chart(fig_cbp_balance, use_container_width=True)


# =========================================================
# TAB 4: Temporal & Pattern Dynamics
# =========================================================
with tab_patterns:
    st.subheader("Temporal Dynamics & Administrative Friction")
    st.markdown(
        "Analysis of operational rhythms, including **weekday vs. weekend transition velocity**, "
        "administrative batching schedules, and month-over-month placement volume trends."
    )

    dow_df = analyze_day_of_week_dynamics(filtered_df)

    p_col1, p_col2 = st.columns(2)
    with p_col1:
        fig_dow_eff = px.bar(
            dow_df.reset_index(),
            x='Day_Of_Week',
            y='Transfer_Efficiency',
            title="Transfer Efficiency Ratio by Day of Week",
            labels={'Day_Of_Week': 'Day of Week', 'Transfer_Efficiency': 'Mean Transfer Efficiency'},
            color='Transfer_Efficiency',
            color_continuous_scale='Blues'
        )
        fig_dow_eff.update_layout(height=350)
        st.plotly_chart(fig_dow_eff, use_container_width=True)

    with p_col2:
        fig_dow_disc = px.bar(
            dow_df.reset_index(),
            x='Day_Of_Week',
            y='Avg_Discharges',
            title="Average Daily Sponsor Discharges by Day of Week",
            labels={'Day_Of_Week': 'Day of Week', 'Avg_Discharges': 'Mean Daily Discharges'},
            color='Avg_Discharges',
            color_continuous_scale='Greens'
        )
        fig_dow_disc.update_layout(height=350)
        st.plotly_chart(fig_dow_disc, use_container_width=True)

    # Detailed Day of Week Breakdown Table
    st.markdown("### Operational Day-of-Week Summary Table")
    st.dataframe(dow_df, use_container_width=True)

    # Month over Month Trends
    st.markdown("### Month-over-Month Longitudinal Flow Trajectory")
    monthly_df = analyze_monthly_trends(filtered_df)
    if not monthly_df.empty:
        fig_mom = px.line(
            monthly_df,
            x='Period_Str',
            y=['Total_Apprehended', 'Total_Transfers', 'Total_Discharges'],
            title="Monthly Aggregate Pipeline Movement (2023 - 2025)",
            labels={'Period_Str': 'Reporting Month', 'value': 'Monthly Children Volume', 'variable': 'Stage Flow'},
            markers=True
        )
        fig_mom.update_layout(height=380, xaxis_tickangle=-45)
        st.plotly_chart(fig_mom, use_container_width=True)


# =========================================================
# TAB 5: Outcome Stability & Anomalies
# =========================================================
with tab_stability:
    st.subheader("Outcome Stability & Anomaly Diagnostic")
    st.markdown(
        "Monitoring consistency of sponsor reunifications, sudden drops in placement success, "
        "and machine-learning detected multi-dimensional pipeline abnormalities."
    )

    s_col1, s_col2 = st.columns(2)

    with s_col1:
        # Rolling Outcome Stability Score
        fig_stab = go.Figure()
        fig_stab.add_trace(go.Scatter(
            x=filtered_df['Date'],
            y=filtered_df['Outcome_Stability_Score'],
            name="30-Day Stability Score",
            line=dict(color="#16a085", width=2.5),
            fill='tozeroy',
            fillcolor='rgba(22, 160, 133, 0.1)'
        ))
        fig_stab.add_hline(y=75, line_dash="dash", line_color="green", annotation_text="Stable Benchmark (75)")
        fig_stab.add_hline(y=50, line_dash="dash", line_color="orange", annotation_text="Moderate Volatility (50)")
        fig_stab.update_layout(
            title="Outcome Stability Score (Consistency of Reunifications: 0-100)",
            xaxis_title="Date",
            yaxis_title="Stability Score",
            height=370,
            hovermode="x unified"
        )
        st.plotly_chart(fig_stab, use_container_width=True)

    with s_col2:
        # Multi-variate Anomaly Scatter
        fig_anom = px.scatter(
            filtered_df,
            x="HHS_Care",
            y="HHS_Discharges",
            color="Alert_Severity",
            color_discrete_map={"Normal": "#2980b9", "Medium": "#f39c12", "High": "#e74c3c"},
            size=np.where(filtered_df['ML_Anomaly'], 12, 5),
            hover_data=['Date', 'Transfer_Efficiency_Ratio', 'Discharge_Effectiveness'],
            title="Multi-Dimensional Anomaly Cluster (HHS Care Census vs Discharges)"
        )
        fig_anom.update_layout(height=370)
        st.plotly_chart(fig_anom, use_container_width=True)

    # Anomaly Incident Log
    st.markdown("### Automated Anomaly Incident Log")
    anom_table = (
        filtered_df[filtered_df['Alert_Severity'] != 'Normal']
        .sort_values('Date', ascending=False)
        [['Date', 'Alert_Severity', 'Apprehended', 'CBP_Custody', 'CBP_Transfers', 'HHS_Care', 'HHS_Discharges', 'Transfer_Efficiency_Ratio', 'Discharge_Effectiveness']]
    )
    if not anom_table.empty:
        st.dataframe(anom_table, use_container_width=True)
    else:
        st.success("No operational anomalies detected in the selected reporting timeframe.")


# =========================================================
# TAB 6: Policy & Surge Simulator
# =========================================================
with tab_simulator:
    st.subheader("Forward Policy Scenario & Surge Stress-Testing")
    st.markdown(
        "Interactive discrete-flow simulator projecting CBP custody loads and HHS shelter occupancy under "
        "intake shocks, inter-agency transfer capacity adjustments, and sponsor case management accelerations."
    )

    sim_ctrl1, sim_ctrl2, sim_ctrl3, sim_ctrl4 = st.columns(4)

    with sim_ctrl1:
        sim_days = st.slider("Simulation Horizon (Days)", min_value=15, max_value=120, value=60, step=15)
    with sim_ctrl2:
        sim_intake = st.slider("Intake Surge / Contraction Multiplier", min_value=0.2, max_value=3.0, value=1.25, step=0.15)
    with sim_ctrl3:
        sim_trans_boost = st.slider("CBP Transfer Efficiency Boost (%)", min_value=-50, max_value=100, value=15, step=5) / 100.0
    with sim_ctrl4:
        sim_vet_boost = st.slider("Sponsor Vetting Acceleration (%)", min_value=-50, max_value=100, value=20, step=5) / 100.0

    sim_df = run_pipeline_simulation(
        filtered_df,
        days_horizon=sim_days,
        intake_multiplier=sim_intake,
        transfer_efficiency_boost=sim_trans_boost,
        sponsor_vetting_boost=sim_vet_boost
    )

    sim_col1, sim_col2 = st.columns(2)

    with sim_col1:
        fig_sim_stocks = go.Figure()
        fig_sim_stocks.add_trace(go.Scatter(
            x=sim_df['Date'],
            y=sim_df['Simulated_HHS_Care'],
            name="Projected HHS Care Beds",
            line=dict(color="#1f77b4", width=2.5)
        ))
        fig_sim_stocks.add_trace(go.Scatter(
            x=sim_df['Date'],
            y=sim_df['Simulated_CBP_Custody'],
            name="Projected CBP Custody Load",
            line=dict(color="#ff7f0e", width=2.5)
        ))
        fig_sim_stocks.update_layout(
            title="Projected Institutional Rosters (CBP & HHS)",
            xaxis_title="Date",
            yaxis_title="Projected Children Count",
            height=370,
            hovermode="x unified"
        )
        st.plotly_chart(fig_sim_stocks, use_container_width=True)

    with sim_col2:
        fig_sim_flows = go.Figure()
        fig_sim_flows.add_trace(go.Scatter(
            x=sim_df['Date'],
            y=sim_df['Simulated_Intake'],
            name="Simulated Intake",
            line=dict(color="#e74c3c", dash="dot")
        ))
        fig_sim_flows.add_trace(go.Scatter(
            x=sim_df['Date'],
            y=sim_df['Simulated_Discharges'],
            name="Simulated Reunifications",
            line=dict(color="#27ae60", width=2.5)
        ))
        fig_sim_flows.add_trace(go.Scatter(
            x=sim_df['Date'],
            y=sim_df['Cumulative_Backlog'],
            name="Simulated Net Backlog",
            line=dict(color="#8e44ad", width=2)
        ))
        fig_sim_flows.update_layout(
            title="Projected Flows & Net Backlog Accumulation",
            xaxis_title="Date",
            yaxis_title="Simulated Volume",
            height=370,
            hovermode="x unified"
        )
        st.plotly_chart(fig_sim_flows, use_container_width=True)


# =========================================================
# TAB 7: Data Explorer & Executive Reports
# =========================================================
with tab_data:
    st.subheader("Data Explorer & Official Deliverable Reports")
    st.markdown(
        "Review raw and engineered records, export filtered datasets, and generate official "
        "executive briefing memorandums and research papers."
    )

    # Download Buttons for PDFs and CSV
    rep_col1, rep_col2, rep_col3 = st.columns(3)

    pdf_exec_path = os.path.join(os.path.dirname(__file__), "reports", "Executive_Briefing_HHS_CBP.pdf")
    pdf_paper_path = os.path.join(os.path.dirname(__file__), "reports", "Care_Transition_Analytics_Research_Paper.pdf")

    # Ensure PDFs exist
    if not os.path.exists(pdf_exec_path):
        generate_executive_briefing_pdf(kpis, pdf_exec_path)
    if not os.path.exists(pdf_paper_path):
        generate_research_paper_pdf(pdf_paper_path)

    with rep_col1:
        with open(pdf_exec_path, "rb") as f:
            st.download_button(
                label="📄 Download Executive Briefing (PDF)",
                data=f,
                file_name="Executive_Briefing_HHS_CBP.pdf",
                mime="application/pdf",
                use_container_width=True
            )

    with rep_col2:
        with open(pdf_paper_path, "rb") as f:
            st.download_button(
                label="📑 Download Full Research Paper (PDF)",
                data=f,
                file_name="Care_Transition_Analytics_Research_Paper.pdf",
                mime="application/pdf",
                use_container_width=True
            )

    with rep_col3:
        csv_data = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="💾 Export Filtered Data (CSV)",
            data=csv_data,
            file_name=f"UAC_Pipeline_Data_{start_filter}_to_{end_filter}.csv",
            mime="text/csv",
            use_container_width=True
        )

    # Filtered Data Table
    st.markdown("### Cleaned & Engineered Pipeline Dataset")
    st.dataframe(
        filtered_df[['Date', 'Apprehended', 'CBP_Custody', 'CBP_Transfers', 'HHS_Care', 'HHS_Discharges', 'Transfer_Efficiency_Ratio', 'Discharge_Effectiveness', 'Pipeline_Throughput_Rate', 'Outcome_Stability_Score', 'Alert_Severity']],
        use_container_width=True
    )

    st.markdown("### Descriptive Summary Statistics")
    st.dataframe(filtered_df[['Apprehended', 'CBP_Custody', 'CBP_Transfers', 'HHS_Care', 'HHS_Discharges', 'Transfer_Efficiency_Ratio', 'Discharge_Effectiveness', 'Pipeline_Throughput_Rate', 'Outcome_Stability_Score']].describe().T, use_container_width=True)


# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------
st.markdown("---")
st.markdown(
    "<center><small style='color:#666666;'>"
    "Care Transition Efficiency & Placement Outcome Analytics | Unified Mentor Research Project | "
    "Datasets sourced from U.S. Department of Health and Human Services (HHS) & CBP Public Reporting"
    "</small></center>",
    unsafe_allow_html=True
)
