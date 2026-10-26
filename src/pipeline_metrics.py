"""
Pipeline Metrics & Statistical Engine for Care Transition Efficiency & Placement Outcomes.
Computes executive KPIs, Little's Law queue estimates, TVPRA compliance, and flow dynamics.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np


def compute_executive_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute overarching operational KPIs for a selected date window.
    """
    if df.empty:
        return {}

    total_intake = df['Apprehended'].sum()
    total_transfers = df['CBP_Transfers'].sum()
    total_discharges = df['HHS_Discharges'].sum()
    avg_cbp_custody = df['CBP_Custody'].mean()
    avg_hhs_care = df['HHS_Care'].mean()

    # Core efficiency ratios
    mean_transfer_efficiency = df['Transfer_Efficiency_Ratio'].dropna().mean()
    mean_discharge_effectiveness = df['Discharge_Effectiveness'].dropna().mean()
    
    # Global pipeline throughput: Total Discharges / Total Intake
    global_throughput = (total_discharges / total_intake) if total_intake > 0 else 0.0

    # Backlog accumulation
    net_system_accumulation = total_intake - total_discharges
    daily_avg_backlog_rate = df['Total_System_Net_Change'].mean()

    # Little's Law Residence Time estimates
    # W = L / lambda
    avg_cbp_residence_days = (avg_cbp_custody / (total_transfers / len(df))) if total_transfers > 0 else 0.0
    avg_hhs_residence_days = (avg_hhs_care / (total_discharges / len(df))) if total_discharges > 0 else 0.0

    # TVPRA 72-Hour (3 days) Compliance Proxy:
    # If Transfer_Efficiency_Ratio >= 0.333, CBP turns over custody within ~3 days (72h)
    tvpra_compliant_days = (df['Transfer_Efficiency_Ratio'] >= 0.333).sum()
    tvpra_compliance_pct = (tvpra_compliant_days / len(df)) * 100.0 if len(df) > 0 else 0.0

    # Outcome stability score (mean of rolling score)
    mean_stability = df['Outcome_Stability_Score'].dropna().mean()
    latest_stability = df['Outcome_Stability_Score'].dropna().iloc[-1] if not df['Outcome_Stability_Score'].dropna().empty else 0.0

    return {
        'total_intake': int(total_intake),
        'total_transfers': int(total_transfers),
        'total_discharges': int(total_discharges),
        'avg_cbp_custody': float(avg_cbp_custody),
        'avg_hhs_care': float(avg_hhs_care),
        'mean_transfer_efficiency': float(mean_transfer_efficiency),
        'mean_discharge_effectiveness': float(mean_discharge_effectiveness),
        'global_throughput': float(global_throughput),
        'net_system_accumulation': int(net_system_accumulation),
        'daily_avg_backlog_rate': float(daily_avg_backlog_rate),
        'avg_cbp_residence_days': float(avg_cbp_residence_days),
        'avg_hhs_residence_days': float(avg_hhs_residence_days),
        'tvpra_compliance_pct': float(tvpra_compliance_pct),
        'mean_stability_score': float(mean_stability),
        'latest_stability_score': float(latest_stability),
        'days_analyzed': len(df)
    }


def analyze_day_of_week_dynamics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Examine day-of-week friction, batching, and weekend administrative slowdowns.
    """
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    grouped = df.groupby('Day_Of_Week').agg(
        Records=('Date', 'count'),
        Avg_Apprehensions=('Apprehended', 'mean'),
        Avg_CBP_Custody=('CBP_Custody', 'mean'),
        Avg_Transfers=('CBP_Transfers', 'mean'),
        Avg_HHS_Care=('HHS_Care', 'mean'),
        Avg_Discharges=('HHS_Discharges', 'mean'),
        Transfer_Efficiency=('Transfer_Efficiency_Ratio', 'mean'),
        Discharge_Effectiveness=('Discharge_Effectiveness', 'mean'),
        Throughput_Rate=('Pipeline_Throughput_Rate', 'mean')
    ).reindex(days).fillna(0)

    grouped['Transfer_Efficiency'] = grouped['Transfer_Efficiency'].round(3)
    grouped['Discharge_Effectiveness'] = (grouped['Discharge_Effectiveness'] * 100).round(2)
    grouped['Throughput_Rate'] = grouped['Throughput_Rate'].round(2)

    return grouped


def analyze_monthly_trends(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute month-over-month aggregated volume and efficiency trajectories.
    """
    df_copy = df.copy()
    df_copy['Period'] = df_copy['Date'].dt.to_period('M')

    monthly = df_copy.groupby('Period').agg(
        Days=('Date', 'count'),
        Total_Apprehended=('Apprehended', 'sum'),
        Total_Transfers=('CBP_Transfers', 'sum'),
        Total_Discharges=('HHS_Discharges', 'sum'),
        Mean_CBP_Custody=('CBP_Custody', 'mean'),
        Mean_HHS_Care=('HHS_Care', 'mean'),
        Mean_Transfer_Efficiency=('Transfer_Efficiency_Ratio', 'mean'),
        Mean_Discharge_Effectiveness=('Discharge_Effectiveness', 'mean')
    ).reset_index()

    monthly['Period_Str'] = monthly['Period'].astype(str)
    monthly['Net_Pipeline_Flow'] = monthly['Total_Apprehended'] - monthly['Total_Discharges']
    monthly['Throughput_Ratio'] = np.where(
        monthly['Total_Apprehended'] > 0,
        monthly['Total_Discharges'] / monthly['Total_Apprehended'],
        np.nan
    )
    return monthly


def generate_sankey_data(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Construct flow links for interactive Sankey diagram of the care transition pipeline.
    Stages:
    0: Apprehension Inflow
    1: Active CBP Buffer
    2: CBP -> HHS Transfer Gate
    3: HHS Sheltered Care
    4: Sponsor Placement (Discharge)
    5: Net System Retention (Backlog accumulation)
    """
    total_app = df['Apprehended'].sum()
    total_trans = df['CBP_Transfers'].sum()
    total_disc = df['HHS_Discharges'].sum()
    
    cbp_retention = max(0, total_app - total_trans)
    hhs_retention = max(0, total_trans - total_disc)

    node_labels = [
        "1. Daily Inflow (Apprehensions)",
        "2. CBP Custody Buffer",
        "3. Inter-Agency Transfer Gate",
        "4. HHS/ORR Care Network",
        "5. Sponsor Reunification (Discharges)",
        "6. Net Care Retention / In-Flight Backlog"
    ]

    node_colors = [
        "#1f77b4",  # Blue
        "#ff7f0e",  # Orange
        "#2ca02c",  # Green
        "#9467bd",  # Purple
        "#2ca02c",  # Emerald Green
        "#d62728"   # Red
    ]

    sources = [0, 1, 2, 3]
    targets = [1, 2, 3, 4]
    values = [total_app, total_trans, total_trans, total_disc]

    if cbp_retention > 0:
        sources.append(1)
        targets.append(5)
        values.append(cbp_retention)

    if hhs_retention > 0:
        sources.append(3)
        targets.append(5)
        values.append(hhs_retention)

    return {
        'labels': node_labels,
        'colors': node_colors,
        'sources': sources,
        'targets': targets,
        'values': values
    }


def detect_bottleneck_episodes(df: pd.DataFrame, min_consecutive_days: int = 5) -> pd.DataFrame:
    """
    Detect sustained operational bottleneck episodes where inflows consistently outpace discharges.
    """
    df_sorted = df.sort_values('Date').copy()
    df_sorted['Inflow_Deficit'] = df_sorted['Apprehended'] > df_sorted['HHS_Discharges']
    
    # Identify contiguous blocks
    df_sorted['Block_ID'] = (df_sorted['Inflow_Deficit'] != df_sorted['Inflow_Deficit'].shift(1)).cumsum()
    
    episodes = []
    for block_id, group in df_sorted[df_sorted['Inflow_Deficit']].groupby('Block_ID'):
        if len(group) >= min_consecutive_days:
            start_date = group['Date'].min()
            end_date = group['Date'].max()
            duration = len(group)
            total_inflow = group['Apprehended'].sum()
            total_outflow = group['HHS_Discharges'].sum()
            net_backlog = total_inflow - total_outflow
            avg_daily_deficit = group['Total_System_Net_Change'].mean()

            episodes.append({
                'Start_Date': start_date.strftime('%Y-%m-%d'),
                'End_Date': end_date.strftime('%Y-%m-%d'),
                'Duration_Days': duration,
                'Total_Inflow': int(total_inflow),
                'Total_Outflow': int(total_outflow),
                'Accumulated_Backlog': int(net_backlog),
                'Daily_Deficit_Rate': round(avg_daily_deficit, 1)
            })

    return pd.DataFrame(episodes)
