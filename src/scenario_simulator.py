"""
Policy Scenario & Flow Stress Simulator for UAC Pipeline Analytics.
Simulates dual-stage queueing dynamics under intake surges, transfer constraints,
and case management acceleration scenarios.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np


def run_pipeline_simulation(
    df: pd.DataFrame,
    days_horizon: int = 60,
    intake_multiplier: float = 1.0,
    transfer_efficiency_boost: float = 0.0,
    sponsor_vetting_boost: float = 0.0,
    initial_cbp_custody: Optional[float] = None,
    initial_hhs_care: Optional[float] = None
) -> pd.DataFrame:
    """
    Run forward discrete-time flow simulation of CBP and HHS care stages.
    """
    # Baseline historical averages from the most recent 60 days
    recent_df = df.sort_values('Date').tail(60)
    baseline_intake = recent_df['Apprehended'].mean()
    baseline_trans_eff = recent_df['Transfer_Efficiency_Ratio'].dropna().mean()
    baseline_disc_eff = recent_df['Discharge_Effectiveness'].dropna().mean()

    # Safety fallbacks
    if np.isnan(baseline_trans_eff) or baseline_trans_eff <= 0:
        baseline_trans_eff = 0.70
    if np.isnan(baseline_disc_eff) or baseline_disc_eff <= 0:
        baseline_disc_eff = 0.025
    if np.isnan(baseline_intake) or baseline_intake <= 0:
        baseline_intake = 50.0

    effective_trans_eff = min(1.2, max(0.1, baseline_trans_eff * (1.0 + transfer_efficiency_boost)))
    effective_disc_eff = min(0.10, max(0.005, baseline_disc_eff * (1.0 + sponsor_vetting_boost)))

    curr_cbp = initial_cbp_custody if initial_cbp_custody is not None else recent_df['CBP_Custody'].iloc[-1]
    curr_hhs = initial_hhs_care if initial_hhs_care is not None else recent_df['HHS_Care'].iloc[-1]

    sim_records = []
    base_date = recent_df['Date'].iloc[-1]

    # Pre-generate stochastic intake variations around adjusted mean
    np.random.seed(42)
    daily_intakes = np.random.normal(
        loc=baseline_intake * intake_multiplier,
        scale=max(2.0, (baseline_intake * intake_multiplier) * 0.20),
        size=days_horizon
    )
    daily_intakes = np.clip(daily_intakes, 0, None)

    cum_backlog = 0.0

    for day in range(1, days_horizon + 1):
        sim_date = base_date + pd.Timedelta(days=day)
        intake = daily_intakes[day - 1]

        # CBP Stage: Apprehensions enter CBP
        cbp_pool = curr_cbp + intake
        transfers = min(cbp_pool, cbp_pool * effective_trans_eff)
        curr_cbp = max(0.0, cbp_pool - transfers)

        # HHS Stage: Transfers enter HHS
        hhs_pool = curr_hhs + transfers
        discharges = min(hhs_pool, hhs_pool * effective_disc_eff)
        curr_hhs = max(0.0, hhs_pool - discharges)

        net_flow = intake - discharges
        cum_backlog += net_flow

        sim_records.append({
            'Sim_Day': day,
            'Date': sim_date,
            'Simulated_Intake': round(intake, 1),
            'Simulated_CBP_Custody': round(curr_cbp, 1),
            'Simulated_Transfers': round(transfers, 1),
            'Simulated_HHS_Care': round(curr_hhs, 1),
            'Simulated_Discharges': round(discharges, 1),
            'Simulated_Net_Flow': round(net_flow, 1),
            'Cumulative_Backlog': round(cum_backlog, 1),
            'Transfer_Efficiency': round(effective_trans_eff, 3),
            'Discharge_Effectiveness': round(effective_disc_eff, 4)
        })

    return pd.DataFrame(sim_records)
