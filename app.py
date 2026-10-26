"""
Care Transition Efficiency & Placement Outcome Analytics
Next-Generation Executive Decision-Support & Process Flow Analytics Platform
U.S. Department of Health and Human Services (HHS) & Customs and Border Protection (CBP)
Unified Mentor Research Project
"""

import os
import sys
from datetime import datetime
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

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
# Page Configuration & Metadata
# ---------------------------------------------------------
st.set_page_config(
    page_title="Care Transition Efficiency & Placement Outcomes | HHS & CBP",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# Modern CSS Design Theme (Palantir / Linear / USWDS Aesthetic)
# ---------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #0F172A;
    }

    /* Background Tint */
    .stApp {
        background: #F8FAFC;
    }

    /* Modern Hero Header Banner */
    .hero-banner {
        background: linear-gradient(135deg, #0B192C 0%, #1E3E62 60%, #000000 100%);
        color: #FFFFFF;
        padding: 30px 36px;
        border-radius: 16px;
        margin-bottom: 24px;
        box-shadow: 0 10px 30px -5px rgba(11, 25, 44, 0.25);
        border: 1px solid rgba(255, 255, 255, 0.08);
        position: relative;
        overflow: hidden;
    }
    .hero-banner::after {
        content: '';
        position: absolute;
        top: -60px;
        right: -60px;
        width: 260px;
        height: 260px;
        background: radial-gradient(circle, rgba(59, 130, 246, 0.25) 0%, rgba(0,0,0,0) 70%);
        border-radius: 50%;
        pointer-events: none;
    }
    .hero-badge {
        display: inline-flex;
        align-items: center;
        background: rgba(255, 255, 255, 0.12);
        backdrop-filter: blur(8px);
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.76rem;
        font-weight: 600;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        color: #93C5FD;
        margin-bottom: 12px;
        border: 1px solid rgba(255, 255, 255, 0.15);
    }
    .pulse-dot {
        width: 8px;
        height: 8px;
        background-color: #10B981;
        border-radius: 50%;
        display: inline-block;
        margin-right: 8px;
        box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
        animation: pulse-ring 2s infinite cubic-bezier(0.66, 0, 0, 1);
    }
    @keyframes pulse-ring {
        0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
        100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }
    .hero-title {
        font-size: 2.1rem;
        font-weight: 800;
        letter-spacing: -0.8px;
        line-height: 1.2;
        margin: 0 0 8px 0;
        background: linear-gradient(180deg, #FFFFFF 0%, #E2E8F0 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .hero-subtitle {
        font-size: 0.95rem;
        color: #94A3B8;
        max-width: 850px;
        line-height: 1.5;
        margin: 0;
    }
    .hero-meta-row {
        display: flex;
        gap: 24px;
        margin-top: 18px;
        padding-top: 16px;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        font-size: 0.85rem;
        color: #CBD5E1;
    }
    .hero-meta-item {
        display: flex;
        align-items: center;
        gap: 6px;
    }

    /* KPI Glassmorphism Cards */
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 16px;
        margin-bottom: 20px;
    }
    .kpi-card {
        background: #FFFFFF;
        border-radius: 14px;
        padding: 20px 18px 16px 18px;
        box-shadow: 0 4px 12px -2px rgba(15, 23, 42, 0.05);
        border: 1px solid #E2E8F0;
        position: relative;
        overflow: hidden;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .kpi-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 24px -6px rgba(15, 23, 42, 0.1);
        border-color: #CBD5E1;
    }
    .kpi-stripe {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
    }
    .stripe-blue { background: linear-gradient(90deg, #2563EB, #60A5FA); }
    .stripe-green { background: linear-gradient(90deg, #059669, #34D399); }
    .stripe-purple { background: linear-gradient(90deg, #7C3AED, #A78BFA); }
    .stripe-cyan { background: linear-gradient(90deg, #0891B2, #38BDF8); }
    .stripe-amber { background: linear-gradient(90deg, #D97706, #FBBF24); }

    .kpi-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }
    .kpi-label {
        font-size: 0.78rem;
        font-weight: 700;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.6px;
    }
    .kpi-icon {
        font-size: 1.1rem;
        opacity: 0.85;
    }
    .kpi-value {
        font-size: 2.15rem;
        font-weight: 800;
        color: #0F172A;
        letter-spacing: -0.8px;
        line-height: 1.1;
        margin-bottom: 6px;
    }
    .kpi-target-tag {
        font-size: 0.74rem;
        font-weight: 600;
        padding: 3px 8px;
        border-radius: 6px;
        display: inline-block;
    }
    .tag-success { background: #ECFDF5; color: #047857; }
    .tag-info { background: #EFF6FF; color: #1D4ED8; }
    .tag-warning { background: #FFFBEB; color: #B45309; }

    /* Secondary Metric Cards */
    .metric-pill-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 14px 18px;
        display: flex;
        flex-direction: column;
        box-shadow: 0 2px 6px -1px rgba(0,0,0,0.03);
    }
    .metric-pill-label {
        font-size: 0.75rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        margin-bottom: 2px;
    }
    .metric-pill-val {
        font-size: 1.35rem;
        font-weight: 700;
        color: #1E293B;
    }

    /* Custom Streamlit Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background-color: #EDF2F7;
        padding: 6px;
        border-radius: 12px;
        border: 1px solid #CBD5E1;
        margin-bottom: 18px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 42px;
        border-radius: 8px;
        padding: 0 16px;
        font-weight: 600;
        font-size: 0.88rem;
        color: #475569;
        background-color: transparent;
        border: none;
        transition: all 0.2s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #E2E8F0;
        color: #0F172A;
    }
    .stTabs [aria-selected="true"] {
        background-color: #0B192C !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 12px rgba(11, 25, 44, 0.2);
    }

    /* Chart Shell Card */
    .chart-shell {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 20px 22px 14px 22px;
        box-shadow: 0 4px 12px -2px rgba(15, 23, 42, 0.04);
        margin-bottom: 20px;
    }
    .chart-shell-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }
    .chart-shell-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #0F172A;
        margin: 0;
    }
    .chart-shell-badge {
        font-size: 0.74rem;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 6px;
        background: #F1F5F9;
        color: #475569;
    }

    /* Alert Badges */
    .alert-strip {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 12px 18px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 16px;
        flex-wrap: wrap;
    }
    .badge-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-red { background: #FEE2E2; color: #991B1B; border: 1px solid #FECACA; }
    .badge-amber { background: #FEF3C7; color: #92400E; border: 1px solid #FDE68A; }
    .badge-green { background: #D1FAE5; color: #065F46; border: 1px solid #A7F3D0; }

    /* Report Download Card */
    .download-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 22px;
        box-shadow: 0 4px 12px -2px rgba(15, 23, 42, 0.05);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        height: 100%;
        transition: transform 0.2s ease;
    }
    .download-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 18px -4px rgba(15, 23, 42, 0.08);
    }
    .doc-icon {
        font-size: 2.2rem;
        margin-bottom: 12px;
    }
    .doc-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #0F172A;
        margin-bottom: 6px;
    }
    .doc-desc {
        font-size: 0.82rem;
        color: #64748B;
        line-height: 1.4;
        margin-bottom: 16px;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# Plotly Custom Theme Function
# ---------------------------------------------------------
def apply_theme(fig: go.Figure, title: str = "", height: int = 370) -> go.Figure:
    """
    Applies executive design styling to any Plotly chart.
    """
    fig.update_layout(
        title=dict(
            text=f"<b>{title}</b>" if title else "",
            font=dict(family="Plus Jakarta Sans, sans-serif", size=15, color="#0F172A"),
            x=0.01,
            y=0.96
        ),
        font=dict(family="Plus Jakarta Sans, sans-serif", color="#475569", size=11),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=height,
        margin=dict(l=40, r=30, t=50 if title else 20, b=40),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11, color="#334155")
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor="#F1F5F9",
            zeroline=False,
            showline=True,
            linecolor="#E2E8F0"
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#F1F5F9",
            zeroline=False,
            showline=True,
            linecolor="#E2E8F0"
        ),
        hoverlabel=dict(
            bgcolor="#0F172A",
            font_size=12,
            font_family="Plus Jakarta Sans, sans-serif",
            font_color="#FFFFFF"
        )
    )
    return fig


# ---------------------------------------------------------
# Data Ingestion & Caching
# ---------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_data():
    data_path = os.path.join(os.path.dirname(__file__), "data", "HHS_Unaccompanied_Alien_Children_Program.csv")
    df = get_prepared_dataset(data_path)
    df = detect_discharge_anomalies(df)
    return df


full_df = load_data()


# ---------------------------------------------------------
# Sidebar Controls & User Configuration
# ---------------------------------------------------------
with st.sidebar:
    st.image(
        "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/United_States_Department_of_Health_and_Human_Services_seal.svg/200px-United_States_Department_of_Health_and_Human_Services_seal.svg.png",
        width=65
    )
    st.markdown("### **Operational Surveillance**")
    st.caption("UAC Care Transition & Reunification Pipeline")

    # Cohort Presets
    cohort_preset = st.selectbox(
        "📅 Reporting Cohort Preset",
        ["Full Historical Span (2023 - 2025)", "2023 Baseline", "2024 Surge Phase", "2025 Policy Retraction", "Custom Range"]
    )

    min_date = full_df['Date'].min().date()
    max_date = full_df['Date'].max().date()

    if cohort_preset == "2023 Baseline":
        def_start = datetime(2023, 1, 1).date()
        def_end = datetime(2023, 12, 31).date()
    elif cohort_preset == "2024 Surge Phase":
        def_start = datetime(2024, 1, 1).date()
        def_end = datetime(2024, 12, 31).date()
    elif cohort_preset == "2025 Policy Retraction":
        def_start = datetime(2025, 1, 1).date()
        def_end = datetime(2025, 12, 31).date()
    else:
        def_start = min_date
        def_end = max_date

    # Date Range Picker
    date_selection = st.date_input(
        "Active Reporting Range",
        value=(def_start, def_end),
        min_value=min_date,
        max_value=max_date
    )

    if isinstance(date_selection, tuple) and len(date_selection) == 2:
        start_d, end_d = date_selection
    else:
        start_d, end_d = def_start, def_end

    # Filtered DF
    mask = (full_df['Date'].dt.date >= start_d) & (full_df['Date'].dt.date <= end_d)
    df = full_df[mask].copy().reset_index(drop=True)

    st.markdown("---")
    st.markdown("#### **Trend Smoothing**")
    smooth_mode = st.radio(
        "Timeline Smoothing Filter",
        ["Raw Daily Roster", "7-Day Moving Average", "30-Day Moving Average"],
        index=1
    )

    suffix = ""
    if smooth_mode == "7-Day Moving Average":
        suffix = "_MA7"
    elif smooth_mode == "30-Day Moving Average":
        suffix = "_MA30"

    st.markdown("---")
    st.markdown("#### **Threshold Alert Sensitivity**")
    cbp_thresh = st.slider(
        "CBP Transfer Velocity Floor (%)",
        min_value=20, max_value=80, value=40, step=5,
        help="Alert triggers when Transfer Efficiency drops below this legal turnover limit."
    ) / 100.0

    backlog_thresh = st.slider(
        "Net Inflow Backlog Ceiling (Kids/Day)",
        min_value=10, max_value=150, value=50, step=10,
        help="Alert triggers when daily apprehension inflow outpaces discharges by this threshold."
    )

    st.markdown("---")
    with st.expander("📖 Statutory Guidance & Notes", expanded=False):
        st.markdown("""
        - **TVPRA of 2008 (8 U.S.C. § 1232):** CBP must transfer unaccompanied children to HHS care within 72 hours (3 days).
        - **Transfer Efficiency:** Daily transfers divided by active CBP custody. A ratio &ge; 0.333 represents full 72-hour turnover compliance.
        - **Flores Settlement:** Mandates prompt release to vetted sponsors in least restrictive settings.
        """)


if df.empty:
    st.error("No reports found within the selected timeframe. Please adjust the sidebar date range.")
    st.stop()


# ---------------------------------------------------------
# Compute Global Metrics
# ---------------------------------------------------------
kpis = compute_executive_kpis(df)
alerts = get_active_alerts_summary(df)
cbp_alert_count = (df['Transfer_Efficiency_Ratio'] < cbp_thresh).sum()
backlog_alert_count = (df['Total_System_Net_Change'] > backlog_thresh).sum()


# ---------------------------------------------------------
# Hero Banner Component
# ---------------------------------------------------------
st.markdown(f"""
<div class="hero-banner">
    <div class="hero-badge">
        <span class="pulse-dot"></span>
        U.S. DEPT OF HEALTH & HUMAN SERVICES • CBP • UNIFIED MENTOR
    </div>
    <h1 class="hero-title">Care Transition Efficiency & Placement Outcome Analytics</h1>
    <p class="hero-subtitle">
        Dynamic process-flow analytics, Little's Law queueing models, and bottleneck surveillance tracking the 
        multi-stage journey of unaccompanied minors from border encounters to safe family reunifications.
    </p>
    <div class="hero-meta-row">
        <div class="hero-meta-item">
            <span>📅 <b>Active Window:</b> {start_d.strftime('%b %d, %Y')} – {end_d.strftime('%b %d, %Y')}</span>
        </div>
        <div class="hero-meta-item">
            <span>📊 <b>Observations:</b> {kpis.get('days_analyzed', 0):,} Reporting Dates</span>
        </div>
        <div class="hero-meta-item">
            <span>👨‍👩‍👧 <b>Reunified to Date:</b> {kpis.get('total_discharges', 0):,} Children</span>
        </div>
        <div class="hero-meta-item">
            <span>🛡️ <b>Statutory Status:</b> TVPRA 72h Compliance at {kpis.get('tvpra_compliance_pct', 0):.1f}%</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# Executive KPI Scorecard Grid (Row 1)
# ---------------------------------------------------------
st.markdown(f"""
<div class="kpi-grid">
    <div class="kpi-card">
        <div class="kpi-stripe stripe-blue"></div>
        <div class="kpi-header">
            <span class="kpi-label">Transfer Efficiency</span>
            <span class="kpi-icon">⚡</span>
        </div>
        <div class="kpi-value">{kpis.get('mean_transfer_efficiency', 0)*100:.1f}%</div>
        <div class="kpi-target-tag tag-info">Target: &gt; 70.0%</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-stripe stripe-green"></div>
        <div class="kpi-header">
            <span class="kpi-label">Discharge Effectiveness</span>
            <span class="kpi-icon">🎯</span>
        </div>
        <div class="kpi-value">{kpis.get('mean_discharge_effectiveness', 0)*100:.2f}%</div>
        <div class="kpi-target-tag tag-success">Daily Placement Rate</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-stripe stripe-purple"></div>
        <div class="kpi-header">
            <span class="kpi-label">Pipeline Throughput</span>
            <span class="kpi-icon">🔄</span>
        </div>
        <div class="kpi-value">{kpis.get('global_throughput', 0):.2f}x</div>
        <div class="kpi-target-tag tag-info">Exits ÷ Inflows Ratio</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-stripe stripe-cyan"></div>
        <div class="kpi-header">
            <span class="kpi-label">TVPRA 72h Compliance</span>
            <span class="kpi-icon">⚖️</span>
        </div>
        <div class="kpi-value">{kpis.get('tvpra_compliance_pct', 0):.1f}%</div>
        <div class="kpi-target-tag tag-success">Statutory 3-Day Mandate</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-stripe stripe-amber"></div>
        <div class="kpi-header">
            <span class="kpi-label">Outcome Stability</span>
            <span class="kpi-icon">📈</span>
        </div>
        <div class="kpi-value">{kpis.get('mean_stability_score', 0):.1f}<span style="font-size:1.1rem;color:#94A3B8">/100</span></div>
        <div class="kpi-target-tag tag-warning">Placement Consistency</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# Secondary Institutional Metrics (Row 2)
# ---------------------------------------------------------
scol1, scol2, scol3, scol4, scol5 = st.columns(5)
with scol1:
    st.markdown(f"""
    <div class="metric-pill-card">
        <span class="metric-pill-label">Total Border Intake</span>
        <span class="metric-pill-val">{kpis.get('total_intake', 0):,}</span>
    </div>
    """, unsafe_allow_html=True)
with scol2:
    st.markdown(f"""
    <div class="metric-pill-card">
        <span class="metric-pill-label">Total CBP &rarr; HHS Transfers</span>
        <span class="metric-pill-val">{kpis.get('total_transfers', 0):,}</span>
    </div>
    """, unsafe_allow_html=True)
with scol3:
    st.markdown(f"""
    <div class="metric-pill-card">
        <span class="metric-pill-label">Total Sponsor Placements</span>
        <span class="metric-pill-val">{kpis.get('total_discharges', 0):,}</span>
    </div>
    """, unsafe_allow_html=True)
with scol4:
    st.markdown(f"""
    <div class="metric-pill-card">
        <span class="metric-pill-label">Avg CBP Turnover</span>
        <span class="metric-pill-val">{kpis.get('avg_cbp_residence_days', 0):.1f} Days</span>
    </div>
    """, unsafe_allow_html=True)
with scol5:
    st.markdown(f"""
    <div class="metric-pill-card">
        <span class="metric-pill-label">Avg HHS Length of Stay</span>
        <span class="metric-pill-val">{kpis.get('avg_hhs_residence_days', 0):.1f} Days</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)


# ---------------------------------------------------------
# Operational Surveillance Ribbon
# ---------------------------------------------------------
st.markdown(f"""
<div class="alert-strip">
    <span style="font-size:0.85rem; font-weight:700; color:#0F172A;">SURVEILLANCE RADAR:</span>
    <span class="badge-pill {'badge-red' if cbp_alert_count > 0 else 'badge-green'}">
        {'⚠️ ' + str(cbp_alert_count) + ' CBP Transfer Slowdowns' if cbp_alert_count > 0 else '✅ CBP Velocity Compliant'}
    </span>
    <span class="badge-pill {'badge-amber' if backlog_alert_count > 0 else 'badge-green'}">
        {'⚠️ ' + str(backlog_alert_count) + ' Acute Backlog Surges' if backlog_alert_count > 0 else '✅ Inflow-Exit Balance Stable'}
    </span>
    <span class="badge-pill {'badge-red' if alerts['high_severity_count'] > 0 else 'badge-green'}">
        {'🚨 ' + str(alerts['high_severity_count']) + ' High ML Anomalies' if alerts['high_severity_count'] > 0 else '✅ ML Risk Baseline Normal'}
    </span>
    <span style="font-size:0.8rem; color:#64748B; margin-left:auto;">
        Monitoring via Isolation Forest & Statistical Z-Scores
    </span>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# Core Navigation Tabs
# ---------------------------------------------------------
tab_flow, tab_eff, tab_bottle, tab_temp, tab_stab, tab_sim, tab_reports = st.tabs([
    "🌊 Care Pipeline Flow",
    "⚡ Velocity & Efficiency",
    "🛑 Bottlenecks & Backlogs",
    "📅 Temporal Dynamics",
    "🎯 Outcome Stability & ML",
    "🧪 Policy & Surge Simulator",
    "📑 Data Explorer & Reports"
])


# =========================================================
# TAB 1: Care Pipeline Flow Visualization
# =========================================================
with tab_flow:
    st.markdown("""
    <div class="chart-shell">
        <div class="chart-shell-header">
            <h3 class="chart-shell-title">Care Pipeline Flow: End-to-End Sankey Trajectory</h3>
            <span class="chart-shell-badge">Stage Movement Balance</span>
        </div>
    """, unsafe_allow_html=True)

    sankey = generate_sankey_data(df)
    fig_sankey = go.Figure(data=[go.Sankey(
        node=dict(
            pad=24,
            thickness=28,
            line=dict(color="#0F172A", width=0.5),
            label=sankey['labels'],
            color=sankey['colors']
        ),
        link=dict(
            source=sankey['sources'],
            target=sankey['targets'],
            value=sankey['values'],
            color="rgba(148, 163, 184, 0.35)"
        )
    )])
    fig_sankey = apply_theme(fig_sankey, "", height=430)
    st.plotly_chart(fig_sankey, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Stock & Flow Comparative Timelines
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div class="chart-shell">
            <div class="chart-shell-header">
                <h3 class="chart-shell-title">HHS Active Shelter Bed Census</h3>
                <span class="chart-shell-badge">Shelter Care Roster</span>
            </div>
        """, unsafe_allow_html=True)
        col_hhs = 'HHS_Care' + suffix if ('HHS_Care' + suffix) in df else 'HHS_Care'
        fig_hhs = go.Figure()
        fig_hhs.add_trace(go.Scatter(
            x=df['Date'],
            y=df[col_hhs],
            name="HHS Care Census",
            line=dict(color="#2563EB", width=2.5),
            fill='tozeroy',
            fillcolor='rgba(37, 99, 235, 0.08)'
        ))
        fig_hhs = apply_theme(fig_hhs, "", height=340)
        fig_hhs.update_layout(yaxis_title="Children in Care", hovermode="x unified")
        st.plotly_chart(fig_hhs, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class="chart-shell">
            <div class="chart-shell-header">
                <h3 class="chart-shell-title">CBP Short-Term Holding Load</h3>
                <span class="chart-shell-badge">Buffer Holding Roster</span>
            </div>
        """, unsafe_allow_html=True)
        col_cbp = 'CBP_Custody' + suffix if ('CBP_Custody' + suffix) in df else 'CBP_Custody'
        fig_cbp = go.Figure()
        fig_cbp.add_trace(go.Scatter(
            x=df['Date'],
            y=df[col_cbp],
            name="CBP Custody",
            line=dict(color="#F59E0B", width=2.5),
            fill='tozeroy',
            fillcolor='rgba(245, 158, 11, 0.1)'
        ))
        fig_cbp.add_hline(y=300, line_dash="dash", line_color="#EF4444", annotation_text="High Stress Ceiling (300)")
        fig_cbp = apply_theme(fig_cbp, "", height=340)
        fig_cbp.update_layout(yaxis_title="Children in CBP Custody", hovermode="x unified")
        st.plotly_chart(fig_cbp, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Inflow vs Outflow Dual Bars
    st.markdown("""
    <div class="chart-shell">
        <div class="chart-shell-header">
            <h3 class="chart-shell-title">Daily Intake (Apprehensions) vs Outflow (Sponsor Placements)</h3>
            <span class="chart-shell-badge">System Balance</span>
        </div>
    """, unsafe_allow_html=True)
    fig_inout = go.Figure()
    fig_inout.add_trace(go.Bar(
        x=df['Date'],
        y=df['Apprehended'],
        name="Apprehensions (Inflow)",
        marker_color="rgba(239, 68, 68, 0.75)"
    ))
    fig_inout.add_trace(go.Bar(
        x=df['Date'],
        y=df['HHS_Discharges'],
        name="Sponsor Discharges (Exit)",
        marker_color="rgba(16, 185, 129, 0.75)"
    ))
    fig_inout = apply_theme(fig_inout, "", height=340)
    fig_inout.update_layout(barmode='group', yaxis_title="Children Count", hovermode="x unified")
    st.plotly_chart(fig_inout, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# TAB 2: Velocity & Efficiency
# =========================================================
with tab_eff:
    e1, e2 = st.columns(2)
    with e1:
        st.markdown("""
        <div class="chart-shell">
            <div class="chart-shell-header">
                <h3 class="chart-shell-title">Transfer Efficiency Ratio (Transfers ÷ CBP Custody)</h3>
                <span class="chart-shell-badge">CBP &rarr; HHS Velocity</span>
            </div>
        """, unsafe_allow_html=True)
        fig_te = go.Figure()
        fig_te.add_trace(go.Scatter(
            x=df['Date'],
            y=df['Transfer_Efficiency_Ratio'],
            name="Daily Ratio",
            mode='markers',
            marker=dict(color="#3B82F6", size=4, opacity=0.35)
        ))
        fig_te.add_trace(go.Scatter(
            x=df['Date'],
            y=df['Transfer_Efficiency_MA7'],
            name="7-Day MA",
            line=dict(color="#1D4ED8", width=2.5)
        ))
        fig_te.add_trace(go.Scatter(
            x=df['Date'],
            y=df['Transfer_Efficiency_MA30'],
            name="30-Day MA",
            line=dict(color="#F59E0B", width=2, dash="dot")
        ))
        fig_te.add_hline(y=0.333, line_dash="dash", line_color="#EF4444", annotation_text="TVPRA 72h Bound (0.33)")
        fig_te = apply_theme(fig_te, "", height=350)
        fig_te.update_layout(yaxis_title="Transfer Ratio", hovermode="x unified")
        st.plotly_chart(fig_te, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with e2:
        st.markdown("""
        <div class="chart-shell">
            <div class="chart-shell-header">
                <h3 class="chart-shell-title">Discharge Effectiveness (Discharges ÷ HHS Care %)</h3>
                <span class="chart-shell-badge">Placement Velocity</span>
            </div>
        """, unsafe_allow_html=True)
        fig_de = go.Figure()
        fig_de.add_trace(go.Scatter(
            x=df['Date'],
            y=df['Discharge_Effectiveness'] * 100.0,
            name="Daily Rate (%)",
            mode='markers',
            marker=dict(color="#10B981", size=4, opacity=0.35)
        ))
        fig_de.add_trace(go.Scatter(
            x=df['Date'],
            y=df['Discharge_Effectiveness_MA7'] * 100.0,
            name="7-Day MA (%)",
            line=dict(color="#047857", width=2.5)
        ))
        fig_de.add_trace(go.Scatter(
            x=df['Date'],
            y=df['Discharge_Effectiveness_MA30'] * 100.0,
            name="30-Day MA (%)",
            line=dict(color="#8B5CF6", width=2, dash="dot")
        ))
        fig_de = apply_theme(fig_de, "", height=350)
        fig_de.update_layout(yaxis_title="Daily Discharge Rate (%)", hovermode="x unified")
        st.plotly_chart(fig_de, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Little's Law Queue Residence Time Distributions
    r1, r2 = st.columns(2)
    with r1:
        st.markdown("""
        <div class="chart-shell">
            <div class="chart-shell-header">
                <h3 class="chart-shell-title">Estimated CBP Holding Residence Time (Days)</h3>
                <span class="chart-shell-badge">W = L / λ (Little's Law)</span>
            </div>
        """, unsafe_allow_html=True)
        fig_cbp_res = px.histogram(
            df[df['Est_CBP_Turnover_Days'] <= 7],
            x="Est_CBP_Turnover_Days",
            nbins=35,
            color_discrete_sequence=["#2563EB"]
        )
        fig_cbp_res.add_vline(x=3.0, line_dash="dash", line_color="#EF4444", annotation_text="TVPRA 72h Ceiling (3 Days)")
        fig_cbp_res = apply_theme(fig_cbp_res, "", height=320)
        fig_cbp_res.update_layout(xaxis_title="Residence Days (CBP)", yaxis_title="Reporting Days Frequency")
        st.plotly_chart(fig_cbp_res, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with r2:
        st.markdown("""
        <div class="chart-shell">
            <div class="chart-shell-header">
                <h3 class="chart-shell-title">Estimated HHS Shelter Length of Stay (Days)</h3>
                <span class="chart-shell-badge">W = L / λ (Little's Law)</span>
            </div>
        """, unsafe_allow_html=True)
        fig_hhs_res = px.histogram(
            df[df['Est_HHS_Stay_Days'] <= 100],
            x="Est_HHS_Stay_Days",
            nbins=35,
            color_discrete_sequence=["#059669"]
        )
        fig_hhs_res.add_vline(x=35.0, line_dash="dash", line_color="#F59E0B", annotation_text="Historical Target (35 Days)")
        fig_hhs_res = apply_theme(fig_hhs_res, "", height=320)
        fig_hhs_res.update_layout(xaxis_title="Length of Stay Days (HHS)", yaxis_title="Reporting Days Frequency")
        st.plotly_chart(fig_hhs_res, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# TAB 3: Bottlenecks & Backlogs
# =========================================================
with tab_bottle:
    b1, b2 = st.columns(2)
    with b1:
        st.markdown("""
        <div class="chart-shell">
            <div class="chart-shell-header">
                <h3 class="chart-shell-title">Daily System Net Flow (Intake − Discharges)</h3>
                <span class="chart-shell-badge">Deficit Surveillance</span>
            </div>
        """, unsafe_allow_html=True)
        fig_bnet = go.Figure()
        colors_net = np.where(df['Total_System_Net_Change'] > 0, '#EF4444', '#10B981')
        fig_bnet.add_trace(go.Bar(
            x=df['Date'],
            y=df['Total_System_Net_Change'],
            marker_color=colors_net,
            name="Daily Net Change"
        ))
        fig_bnet.add_hline(y=backlog_thresh, line_dash="dash", line_color="#F59E0B", annotation_text="Surge Threshold")
        fig_bnet = apply_theme(fig_bnet, "", height=350)
        fig_bnet.update_layout(yaxis_title="Net Children Added / Cleared", hovermode="x unified")
        st.plotly_chart(fig_bnet, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with b2:
        st.markdown("""
        <div class="chart-shell">
            <div class="chart-shell-header">
                <h3 class="chart-shell-title">Cumulative System Backlog Trajectory</h3>
                <span class="chart-shell-badge">Cumulative Deficit Curve</span>
            </div>
        """, unsafe_allow_html=True)
        fig_bcum = go.Figure()
        fig_bcum.add_trace(go.Scatter(
            x=df['Date'],
            y=df['Cumulative_System_Backlog'],
            name="Cumulative Backlog",
            line=dict(color="#8B5CF6", width=2.5),
            fill='tozeroy',
            fillcolor='rgba(139, 92, 246, 0.1)'
        ))
        fig_bcum = apply_theme(fig_bcum, "", height=350)
        fig_bcum.update_layout(yaxis_title="Cumulative Net Balance", hovermode="x unified")
        st.plotly_chart(fig_bcum, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Bottleneck Episodes Table
    st.markdown("""
    <div class="chart-shell">
        <div class="chart-shell-header">
            <h3 class="chart-shell-title">Sustained Bottleneck Episodes (Inflows > Discharges for ≥ 5 Reports)</h3>
            <span class="chart-shell-badge">Episode Analytics</span>
        </div>
    """, unsafe_allow_html=True)
    episodes = detect_bottleneck_episodes(df, min_consecutive_days=5)
    if not episodes.empty:
        st.dataframe(episodes, use_container_width=True)
    else:
        st.info("No sustained bottleneck episodes detected within this reporting window.")
    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# TAB 4: Temporal Dynamics
# =========================================================
with tab_temp:
    dow_df = analyze_day_of_week_dynamics(df)
    t1, t2 = st.columns(2)
    with t1:
        st.markdown("""
        <div class="chart-shell">
            <div class="chart-shell-header">
                <h3 class="chart-shell-title">Transfer Efficiency by Day of Week</h3>
                <span class="chart-shell-badge">CBP &rarr; HHS Speed</span>
            </div>
        """, unsafe_allow_html=True)
        fig_dow_eff = px.bar(
            dow_df.reset_index(),
            x='Day_Of_Week',
            y='Transfer_Efficiency',
            color='Transfer_Efficiency',
            color_continuous_scale='Blues'
        )
        fig_dow_eff = apply_theme(fig_dow_eff, "", height=340)
        fig_dow_eff.update_layout(xaxis_title="Day of Week", yaxis_title="Transfer Efficiency Ratio")
        st.plotly_chart(fig_dow_eff, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with t2:
        st.markdown("""
        <div class="chart-shell">
            <div class="chart-shell-header">
                <h3 class="chart-shell-title">Average Daily Discharges by Day of Week</h3>
                <span class="chart-shell-badge">Sponsor Reunification Volume</span>
            </div>
        """, unsafe_allow_html=True)
        fig_dow_disc = px.bar(
            dow_df.reset_index(),
            x='Day_Of_Week',
            y='Avg_Discharges',
            color='Avg_Discharges',
            color_continuous_scale='Greens'
        )
        fig_dow_disc = apply_theme(fig_dow_disc, "", height=340)
        fig_dow_disc.update_layout(xaxis_title="Day of Week", yaxis_title="Mean Discharges (Kids/Day)")
        st.plotly_chart(fig_dow_disc, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Detailed Table
    st.markdown("""
    <div class="chart-shell">
        <div class="chart-shell-header">
            <h3 class="chart-shell-title">Operational Day-of-Week Summary Roster</h3>
            <span class="chart-shell-badge">Institutional Batching Audit</span>
        </div>
    """, unsafe_allow_html=True)
    st.dataframe(dow_df, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Month over Month Longitudinal View
    st.markdown("""
    <div class="chart-shell">
        <div class="chart-shell-header">
            <h3 class="chart-shell-title">Month-over-Month Longitudinal Flow Trajectory (2023 - 2025)</h3>
            <span class="chart-shell-badge">Monthly Aggregations</span>
        </div>
    """, unsafe_allow_html=True)
    monthly_df = analyze_monthly_trends(df)
    if not monthly_df.empty:
        fig_mom = px.line(
            monthly_df,
            x='Period_Str',
            y=['Total_Apprehended', 'Total_Transfers', 'Total_Discharges'],
            markers=True,
            color_discrete_sequence=['#EF4444', '#3B82F6', '#10B981']
        )
        fig_mom = apply_theme(fig_mom, "", height=360)
        fig_mom.update_layout(xaxis_title="Reporting Month", yaxis_title="Monthly Volume", xaxis_tickangle=-45)
        st.plotly_chart(fig_mom, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# TAB 5: Outcome Stability & ML
# =========================================================
with tab_stab:
    s1, s2 = st.columns(2)
    with s1:
        st.markdown("""
        <div class="chart-shell">
            <div class="chart-shell-header">
                <h3 class="chart-shell-title">Outcome Stability Score (Consistency Index: 0–100)</h3>
                <span class="chart-shell-badge">30-Day Rolling Stability</span>
            </div>
        """, unsafe_allow_html=True)
        fig_stab = go.Figure()
        fig_stab.add_trace(go.Scatter(
            x=df['Date'],
            y=df['Outcome_Stability_Score'],
            name="Stability Score",
            line=dict(color="#059669", width=2.5),
            fill='tozeroy',
            fillcolor='rgba(5, 150, 105, 0.08)'
        ))
        fig_stab.add_hline(y=75, line_dash="dash", line_color="#10B981", annotation_text="Stable Benchmark (75)")
        fig_stab.add_hline(y=50, line_dash="dash", line_color="#F59E0B", annotation_text="Volatile Warning (50)")
        fig_stab = apply_theme(fig_stab, "", height=350)
        fig_stab.update_layout(yaxis_title="Stability Index", hovermode="x unified")
        st.plotly_chart(fig_stab, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with s2:
        st.markdown("""
        <div class="chart-shell">
            <div class="chart-shell-header">
                <h3 class="chart-shell-title">Isolation Forest Multi-Dimensional Anomaly Cluster</h3>
                <span class="chart-shell-badge">Unsupervised ML Detection</span>
            </div>
        """, unsafe_allow_html=True)
        fig_anom = px.scatter(
            df,
            x="HHS_Care",
            y="HHS_Discharges",
            color="Alert_Severity",
            color_discrete_map={"Normal": "#2563EB", "Medium": "#F59E0B", "High": "#EF4444"},
            size=np.where(df['ML_Anomaly'], 12, 5),
            hover_data=['Date', 'Transfer_Efficiency_Ratio', 'Discharge_Effectiveness']
        )
        fig_anom = apply_theme(fig_anom, "", height=350)
        fig_anom.update_layout(xaxis_title="HHS Active Care Census", yaxis_title="Daily Sponsor Discharges")
        st.plotly_chart(fig_anom, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Anomaly Log
    st.markdown("""
    <div class="chart-shell">
        <div class="chart-shell-header">
            <h3 class="chart-shell-title">Automated Anomaly & Disruption Audit Log</h3>
            <span class="chart-shell-badge">Filtered Incident History</span>
        </div>
    """, unsafe_allow_html=True)
    anoms_table = (
        df[df['Alert_Severity'] != 'Normal']
        .sort_values('Date', ascending=False)
        [['Date', 'Alert_Severity', 'Apprehended', 'CBP_Custody', 'CBP_Transfers', 'HHS_Care', 'HHS_Discharges', 'Transfer_Efficiency_Ratio', 'Discharge_Effectiveness']]
    )
    if not anoms_table.empty:
        st.dataframe(anoms_table, use_container_width=True)
    else:
        st.success("No anomalies detected in the selected reporting timeframe.")
    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# TAB 6: Policy & Surge Simulator
# =========================================================
with tab_sim:
    st.markdown("""
    <div class="chart-shell">
        <div class="chart-shell-header">
            <h3 class="chart-shell-title">Forward Contingency Simulator & Stress-Testing Parameters</h3>
            <span class="chart-shell-badge">Queueing Simulation Engine</span>
        </div>
    """, unsafe_allow_html=True)

    sim_c1, sim_c2, sim_c3, sim_c4 = st.columns(4)
    with sim_c1:
        sim_days = st.slider("Simulation Horizon (Days)", min_value=15, max_value=120, value=60, step=15)
    with sim_c2:
        sim_intake = st.slider("Border Intake Surge Multiplier", min_value=0.2, max_value=3.0, value=1.25, step=0.15)
    with sim_c3:
        sim_trans = st.slider("CBP Transfer Capacity Boost (%)", min_value=-50, max_value=100, value=15, step=5) / 100.0
    with sim_c4:
        sim_vet = st.slider("Sponsor Vetting Acceleration (%)", min_value=-50, max_value=100, value=20, step=5) / 100.0

    sim_df = run_pipeline_simulation(
        df,
        days_horizon=sim_days,
        intake_multiplier=sim_intake,
        transfer_efficiency_boost=sim_trans,
        sponsor_vetting_boost=sim_vet
    )

    sim_p1, sim_p2 = st.columns(2)
    with sim_p1:
        fig_s_stocks = go.Figure()
        fig_s_stocks.add_trace(go.Scatter(
            x=sim_df['Date'],
            y=sim_df['Simulated_HHS_Care'],
            name="Projected HHS Beds",
            line=dict(color="#2563EB", width=2.5)
        ))
        fig_s_stocks.add_trace(go.Scatter(
            x=sim_df['Date'],
            y=sim_df['Simulated_CBP_Custody'],
            name="Projected CBP Custody",
            line=dict(color="#F59E0B", width=2.5)
        ))
        fig_s_stocks = apply_theme(fig_s_stocks, "Projected Institutional Roster Balances", height=350)
        fig_s_stocks.update_layout(yaxis_title="Projected Children", hovermode="x unified")
        st.plotly_chart(fig_s_stocks, use_container_width=True)

    with sim_p2:
        fig_s_flows = go.Figure()
        fig_s_flows.add_trace(go.Scatter(
            x=sim_df['Date'],
            y=sim_df['Simulated_Intake'],
            name="Simulated Intake",
            line=dict(color="#EF4444", dash="dot")
        ))
        fig_s_flows.add_trace(go.Scatter(
            x=sim_df['Date'],
            y=sim_df['Simulated_Discharges'],
            name="Simulated Reunifications",
            line=dict(color="#10B981", width=2.5)
        ))
        fig_s_flows.add_trace(go.Scatter(
            x=sim_df['Date'],
            y=sim_df['Cumulative_Backlog'],
            name="Simulated Net Backlog",
            line=dict(color="#8B5CF6", width=2)
        ))
        fig_s_flows = apply_theme(fig_s_flows, "Projected Transition Flows & Cumulative Backlog", height=350)
        fig_s_flows.update_layout(yaxis_title="Simulated Flow Volume", hovermode="x unified")
        st.plotly_chart(fig_s_flows, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# TAB 7: Data Explorer & Reports
# =========================================================
with tab_reports:
    st.markdown("### **Official Deliverables & Submission Package**")

    pdf_exec = os.path.join(os.path.dirname(__file__), "reports", "Executive_Briefing_HHS_CBP.pdf")
    pdf_paper = os.path.join(os.path.dirname(__file__), "reports", "Care_Transition_Analytics_Research_Paper.pdf")

    if not os.path.exists(pdf_exec):
        generate_executive_briefing_pdf(kpis, pdf_exec)
    if not os.path.exists(pdf_paper):
        generate_research_paper_pdf(pdf_paper)

    d1, d2, d3 = st.columns(3)
    with d1:
        st.markdown("""
        <div class="download-card">
            <div>
                <div class="doc-icon">🏛️</div>
                <div class="doc-title">Executive Briefing Memo</div>
                <div class="doc-desc">
                    High-level decision briefing formatted for the HHS Secretary, ORR Director, and CBP leadership.
                    Contains scorecards, compliance analysis, and 30-90-365 day reform plans.
                </div>
            </div>
        """, unsafe_allow_html=True)
        with open(pdf_exec, "rb") as f:
            st.download_button(
                label="📥 Download Executive Briefing (PDF)",
                data=f,
                file_name="Executive_Briefing_HHS_CBP.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        st.markdown("</div>", unsafe_allow_html=True)

    with d2:
        st.markdown("""
        <div class="download-card">
            <div>
                <div class="doc-icon">📑</div>
                <div class="doc-title">Full Research Paper</div>
                <div class="doc-desc">
                    Formal academic research paper covering statutory context, queueing theory, Little's Law,
                    cross-correlation lag structures, and policy implications.
                </div>
            </div>
        """, unsafe_allow_html=True)
        with open(pdf_paper, "rb") as f:
            st.download_button(
                label="📥 Download Research Paper (PDF)",
                data=f,
                file_name="Care_Transition_Analytics_Research_Paper.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        st.markdown("</div>", unsafe_allow_html=True)

    with d3:
        st.markdown("""
        <div class="download-card">
            <div>
                <div class="doc-icon">💾</div>
                <div class="doc-title">Filtered Dataset (CSV)</div>
                <div class="doc-desc">
                    Export the complete sanitized dataset along with all derived feature metrics,
                    moving averages, TVPRA compliance flags, and anomaly severity tags.
                </div>
            </div>
        """, unsafe_allow_html=True)
        csv_bytes = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export Active Cohort (CSV)",
            data=csv_bytes,
            file_name=f"UAC_Pipeline_Data_{start_d}_to_{end_d}.csv",
            mime="text/csv",
            use_container_width=True
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # Filtered Dataset Viewer
    st.markdown("""
    <div class="chart-shell">
        <div class="chart-shell-header">
            <h3 class="chart-shell-title">Sanitized & Feature-Engineered Pipeline Dataset</h3>
            <span class="chart-shell-badge">Active Records: {len_df}</span>
        </div>
    """.format(len_df=len(df)), unsafe_allow_html=True)
    st.dataframe(
        df[['Date', 'Apprehended', 'CBP_Custody', 'CBP_Transfers', 'HHS_Care', 'HHS_Discharges', 'Transfer_Efficiency_Ratio', 'Discharge_Effectiveness', 'Pipeline_Throughput_Rate', 'Outcome_Stability_Score', 'Alert_Severity']],
        use_container_width=True
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # Summary Statistics
    st.markdown("""
    <div class="chart-shell">
        <div class="chart-shell-header">
            <h3 class="chart-shell-title">Descriptive Summary Statistics</h3>
            <span class="chart-shell-badge">Statistical Distributions</span>
        </div>
    """, unsafe_allow_html=True)
    st.dataframe(
        df[['Apprehended', 'CBP_Custody', 'CBP_Transfers', 'HHS_Care', 'HHS_Discharges', 'Transfer_Efficiency_Ratio', 'Discharge_Effectiveness', 'Pipeline_Throughput_Rate', 'Outcome_Stability_Score']].describe().T,
        use_container_width=True
    )
    st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------
st.markdown("---")
st.markdown(
    "<center><p style='color:#64748B; font-size:0.85rem; font-weight:500;'>"
    "Care Transition Efficiency & Placement Outcome Analytics Platform | Unified Mentor Research Project<br/>"
    "U.S. Department of Health and Human Services (HHS) & Customs and Border Protection (CBP)"
    "</p></center>",
    unsafe_allow_html=True
)
