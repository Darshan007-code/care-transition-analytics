"""
Anomaly & Regime Detection Module for UAC Care Pipeline Analytics.
Implements statistical (Z-Score/IQR) and machine learning (Isolation Forest) detection
to identify sudden drops in reunification success, acute backlogs, and flow abnormalities.
"""

from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest


def detect_discharge_anomalies(df: pd.DataFrame, contamination: float = 0.05) -> pd.DataFrame:
    """
    Detect anomalous drops or spikes in sponsor placement outcomes and transition metrics.
    """
    df = df.copy()

    # Statistical Z-Scores
    rolling_mean = df['HHS_Discharges'].rolling(30, min_periods=7).mean().bfill()
    rolling_std = df['HHS_Discharges'].rolling(30, min_periods=7).std().bfill() + 1e-6
    df['Discharge_ZScore'] = (df['HHS_Discharges'] - rolling_mean) / rolling_std

    # Statistical alerts
    df['Sudden_Discharge_Drop'] = df['Discharge_ZScore'] < -2.0
    df['Sudden_Discharge_Surge'] = df['Discharge_ZScore'] > 2.5

    # CBP Transfer Slump alert (Transfer Efficiency < 0.33)
    df['CBP_Transfer_Delay_Alert'] = df['Transfer_Efficiency_Ratio'] < 0.33

    # Backlog Surge Alert (Net daily increase > 50 children)
    df['Backlog_Surge_Alert'] = df['Total_System_Net_Change'] > 50

    # Multi-dimensional ML Anomaly Detection using Isolation Forest
    features = [
        'Apprehended',
        'CBP_Custody',
        'CBP_Transfers',
        'HHS_Care',
        'HHS_Discharges',
        'Transfer_Efficiency_Ratio',
        'Discharge_Effectiveness'
    ]

    valid_mask = df[features].notna().all(axis=1)
    X = df.loc[valid_mask, features]

    iso = IsolationForest(
        n_estimators=100,
        contamination=contamination,
        random_state=42
    )
    predictions = iso.fit_predict(X)
    scores = iso.decision_function(X)

    df['ML_Anomaly'] = False
    df.loc[valid_mask, 'ML_Anomaly'] = predictions == -1
    df['ML_Anomaly_Score'] = 0.0
    df.loc[valid_mask, 'ML_Anomaly_Score'] = -scores  # Higher = more anomalous

    # Severity classification
    df['Alert_Severity'] = 'Normal'
    df.loc[df['Sudden_Discharge_Drop'] | df['CBP_Transfer_Delay_Alert'], 'Alert_Severity'] = 'Medium'
    df.loc[df['ML_Anomaly'] & (df['Alert_Severity'] == 'Medium'), 'Alert_Severity'] = 'High'
    df.loc[df['Backlog_Surge_Alert'] & (df['Alert_Severity'] == 'Normal'), 'Alert_Severity'] = 'Medium'

    return df


def get_active_alerts_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Return summary counts and recent incident logs for dashboard display.
    """
    if 'Alert_Severity' not in df.columns:
        df = detect_discharge_anomalies(df)

    high_count = (df['Alert_Severity'] == 'High').sum()
    medium_count = (df['Alert_Severity'] == 'Medium').sum()
    discharge_drops = df['Sudden_Discharge_Drop'].sum()
    transfer_delays = df['CBP_Transfer_Delay_Alert'].sum()
    backlog_surges = df['Backlog_Surge_Alert'].sum()

    recent_incidents = (
        df[df['Alert_Severity'] != 'Normal']
        .sort_values('Date', ascending=False)
        [['Date', 'Alert_Severity', 'Apprehended', 'CBP_Transfers', 'HHS_Discharges', 'Transfer_Efficiency_Ratio', 'Discharge_Effectiveness']]
        .head(10)
    )

    return {
        'high_severity_count': int(high_count),
        'medium_severity_count': int(medium_count),
        'discharge_drops_count': int(discharge_drops),
        'transfer_delays_count': int(transfer_delays),
        'backlog_surges_count': int(backlog_surges),
        'recent_incidents': recent_incidents
    }
